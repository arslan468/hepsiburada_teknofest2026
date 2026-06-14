import os
import json
import warnings
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

warnings.filterwarnings('ignore')

SUTUN_CIKIS  = 'Çıkış Transfer Merkezi'
SUTUN_VARIS  = 'Varış Transfer Merkezi'
SUTUN_TARIH  = 'Tarih'
SUTUN_TALEP  = 'Toplam Desi'

MODEL_DOSYASI   = 'HBAI_XGB_Model.json'
MAPPING_DOSYASI = 'sehir_mapping.json'

# Kullanılacak özellik listesi (eğitim ve tahmin sırasında aynı sıra kullanılmalı)
FEATURES = [
    'Gun', 'Ay', 'Yil', 'Hafta_No', 'Gunun_Sirasi',
    'Haftanin_Gunu', 'Haftasonu', 'Pazartesi', 'Cuma', 'Mevsim',
    'Sehir_A_kod', 'Sehir_B_kod',
    'lag_1', 'lag_2', 'lag_3', 'lag_7', 'lag_14',
    'ma_3', 'ma_7', 'ma_14', 'std_7'
]

# Singleton: model ve encoder'lar tek seferlik yüklenir
_model    = None
_le_a     = None
_le_b     = None
_sehir_mapping = None


# =============================================================
#  BÖLÜM 1  —  ÖZELLİK ÜRETİMİ  (Feature Engineering)
# =============================================================
def ozellikleri_uret(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ham Excel verisini alır, eğitim/tahmin için gereken tüm özellikleri hesaplar.
    Girdi df'in şu sütunları içermesi beklenir:
        SUTUN_CIKIS, SUTUN_VARIS, SUTUN_TARIH, SUTUN_TALEP
    """
    df = df.copy()

    # Sütun adlarını iç standartta yeniden adlandır
    df = df.rename(columns={
        SUTUN_CIKIS: 'Sehir_A',
        SUTUN_VARIS: 'Sehir_B',
        SUTUN_TARIH: 'Tarih',
        SUTUN_TALEP: 'Talep',
    })

    df['Tarih'] = pd.to_datetime(df['Tarih'])
    df = df.dropna(subset=['Talep'])
    df = df.sort_values(['Sehir_A', 'Sehir_B', 'Tarih']).reset_index(drop=True)

    # ── Tarih tabanlı özellikler ────────────────────────────────
    df['Gun']           = df['Tarih'].dt.day
    df['Ay']            = df['Tarih'].dt.month
    df['Yil']           = df['Tarih'].dt.year
    df['Hafta_No']      = df['Tarih'].dt.isocalendar().week.astype(int)
    df['Gunun_Sirasi']  = df['Tarih'].dt.dayofyear
    df['Haftanin_Gunu'] = df['Tarih'].dt.dayofweek   # 0=Pzt, 6=Paz

    # ── Haftasonu / gün bayrakları ──────────────────────────────
    df['Haftasonu'] = (df['Haftanin_Gunu'] >= 5).astype(int)
    df['Pazartesi'] = (df['Haftanin_Gunu'] == 0).astype(int)
    df['Cuma']      = (df['Haftanin_Gunu'] == 4).astype(int)

    # ── Mevsim (0=Kış, 1=İlkbahar, 2=Yaz, 3=Sonbahar) ─────────
    df['Mevsim'] = df['Ay'].map({
        12: 0, 1: 0, 2: 0,
         3: 1, 4: 1, 5: 1,
         6: 2, 7: 2, 8: 2,
         9: 3, 10: 3, 11: 3
    })

    # ── Şehir kodlama (LabelEncoder) ────────────────────────────
    le_a = LabelEncoder()
    le_b = LabelEncoder()
    df['Sehir_A_kod'] = le_a.fit_transform(df['Sehir_A'])
    df['Sehir_B_kod'] = le_b.fit_transform(df['Sehir_B'])

    # ── Lag features (geçmiş günlerin talepleri) ─────────────────
    for lag in [1, 2, 3, 7, 14]:
        df[f'lag_{lag}'] = df.groupby(['Sehir_A', 'Sehir_B'])['Talep'].shift(lag)

    # ── Hareketli Ortalama (Moving Average) ─────────────────────
    for w in [3, 7, 14]:
        df[f'ma_{w}'] = df.groupby(['Sehir_A', 'Sehir_B'])['Talep'].transform(
            lambda x: x.shift(1).rolling(w, min_periods=1).mean()
        )

    # ── Standart sapma (volatilite ölçüsü) ──────────────────────
    df['std_7'] = df.groupby(['Sehir_A', 'Sehir_B'])['Talep'].transform(
        lambda x: x.shift(1).rolling(7, min_periods=1).std().fillna(0)
    )

    return df, le_a, le_b


# =============================================================
#  BÖLÜM 2  —  MODEL EĞİTİMİ
# =============================================================
def modeli_egit_ve_kaydet(df_talep: pd.DataFrame = None):
    """
    Desi tahmin modelini eğitir, performans metriklerini basar,
    modeli ve şehir eşleme tablosunu diske kaydeder.

    Parametreler:
        df_talep : Geçmiş veri DataFrame'i. None ise Desi_talep.xlsx okunur.
    """
    global _model, _le_a, _le_b, _sehir_mapping

    if df_talep is None:
        dosya = 'desi_talep.xlsx' if os.path.exists('desi_talep.xlsx') else 'Desi_talep.xlsx'
        print(f'-> Veri yükleniyor: {dosya}')
        df_talep = pd.read_excel(dosya)

    print(f'   {len(df_talep)} satır, {len(df_talep.columns)} sütun yüklendi.')

    # Özellik üretimi
    df, le_a, le_b = ozellikleri_uret(df_talep)
    df_model = df.dropna(subset=FEATURES + ['Talep']).copy()
    print(f'-> Özellik üretimi tamamlandı. Modele uygun satır: {len(df_model)}')

    # Eğitim / Test bölme — son 20 günlük veri test seti
    esik = df_model['Tarih'].max() - pd.Timedelta(days=20)
    train = df_model[df_model['Tarih'] <= esik]
    test  = df_model[df_model['Tarih'] >  esik]

    X_train, y_train = train[FEATURES], train['Talep']
    X_test,  y_test  = test[FEATURES],  test['Talep']

    print(f'   Eğitim: {len(train)} satır  |  Test: {len(test)} satır')

    # XGBoost modeli — Early Stopping ile
    callbacks = [
        xgb.callback.EarlyStopping(rounds=30, metric_name='rmse', save_best=True)
    ]
    model = xgb.XGBRegressor(
        objective        = 'reg:squarederror',
        n_estimators     = 500,
        max_depth        = 6,
        learning_rate    = 0.05,
        subsample        = 0.8,
        colsample_bytree = 0.8,
        min_child_weight = 3,
        gamma            = 0.1,
        random_state     = 42,
        verbosity        = 0,
        callbacks        = callbacks,
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    print(f'-> Model eğitildi. En iyi iterasyon: {model.best_iteration}')

    # Performans metrikleri
    y_pred = model.predict(X_test)
    mae  = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2   = r2_score(y_test, y_pred)
    mape = np.mean(np.abs((y_test - y_pred) / (y_test + 1e-9))) * 100

    print(f'   MAE  : {mae:.2f}  |  RMSE: {rmse:.2f}  |  MAPE: %{mape:.1f}  |  R²: {r2:.4f}')
    if r2 >= 0.85:
        print('   ✅ Model çok iyi (R² ≥ 0.85)')
    elif r2 >= 0.70:
        print('   ✅ Model iyi (R² ≥ 0.70)')
    elif r2 >= 0.50:
        print('   ⚠️  Model orta (R² ≥ 0.50)')
    else:
        print('   ❌ Model zayıf — veri veya özellik mühendisliğini gözden geçirin')

    # En önemli 5 özellik
    imp = sorted(zip(FEATURES, model.feature_importances_), key=lambda x: -x[1])
    print('   Top 5 Özellik:', [(f, round(v, 4)) for f, v in imp[:5]])

    # Şehir eşleme tablosunu JSON olarak kaydet
    cikis_map = {isim: int(idx) for idx, isim in enumerate(le_a.classes_)}
    varis_map = {isim: int(idx) for idx, isim in enumerate(le_b.classes_)}
    sehir_mapping = {'cikis': cikis_map, 'varis': varis_map}
    with open(MAPPING_DOSYASI, 'w', encoding='utf-8') as f:
        json.dump(sehir_mapping, f, ensure_ascii=False, indent=2)
    print(f'-> Şehir ID eşleme tablosu kaydedildi → {MAPPING_DOSYASI}')

    # Modeli kaydet
    model.save_model(MODEL_DOSYASI)
    print(f'-> Model kaydedildi → {MODEL_DOSYASI}')

    # Singleton'ları güncelle
    _model         = model
    _le_a          = le_a
    _le_b          = le_b
    _sehir_mapping = sehir_mapping

    return model, le_a, le_b


# =============================================================
#  BÖLÜM 3  —  MODEL YÜKLEME  (Singleton)
# =============================================================
def modeli_yukle():
    """
    Daha önce eğitilmiş XGBoost modelini ve şehir eşleme tablosunu yükler.
    Tekrar çağrıldığında aynı nesneyi döner (singleton pattern).

    Döndürür: (model, sehir_mapping)
    """
    global _model, _sehir_mapping

    if _model is None:
        _model = xgb.XGBRegressor()
        _model.load_model(MODEL_DOSYASI)

    if _sehir_mapping is None:
        try:
            with open(MAPPING_DOSYASI, 'r', encoding='utf-8') as f:
                _sehir_mapping = json.load(f)
        except FileNotFoundError:
            print(f"[UYARI] {MAPPING_DOSYASI} bulunamadı! Önce 'python pipeline.py train' çalıştırın.")
            _sehir_mapping = {'cikis': {}, 'varis': {}}

    return _model, _sehir_mapping


# =============================================================
#  BÖLÜM 4  —  TAHMİN SATIRINI OLUŞTUR
# =============================================================
def _tahmin_satiri_olustur(cikis: str, varis: str, tarih_str: str,
                            df_talep: pd.DataFrame,
                            sehir_mapping: dict) -> pd.DataFrame:
    """
    Tek bir (çıkış, varış, tarih) kombinasyonu için FEATURES sırasında
    bir tahmin satırı oluşturur. Geçmiş lag ve hareketli ortalama değerleri
    gerçek veri üzerinden hesaplanır.
    """
    tarih = pd.to_datetime(tarih_str)

    # Rotaya ait geçmiş veriyi filtrele
    cikis_temiz = str(cikis).strip().upper()
    varis_temiz = str(varis).strip().upper()
    df_rota = df_talep[
        (df_talep[SUTUN_CIKIS].astype(str).str.strip().str.upper() == cikis_temiz) &
        (df_talep[SUTUN_VARIS].astype(str).str.strip().str.upper() == varis_temiz)
    ].copy()

    df_rota[SUTUN_TARIH] = pd.to_datetime(df_rota[SUTUN_TARIH])
    df_rota = df_rota.sort_values(SUTUN_TARIH)
    # Sadece hedef tarihten önceki verileri kullan (veri sızıntısını önle)
    df_gecmis = df_rota[df_rota[SUTUN_TARIH] < tarih]

    vals = df_gecmis[SUTUN_TALEP].values if len(df_gecmis) > 0 else np.array([12000.0])
    n    = len(vals)
    genel_ort = float(np.mean(vals))

    def lag(k):
        return float(vals[-k]) if n >= k else genel_ort

    def ma(k):
        return float(np.mean(vals[-k:])) if n > 0 else genel_ort

    def std(k):
        return float(np.std(vals[-k:])) if n >= 2 else 0.0

    # Mevsim kodu
    ay = tarih.month
    mevsim = {12: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1,
               6: 2, 7: 2, 8: 2, 9: 3, 10: 3, 11: 3}[ay]

    # Şehir ID'leri: eşleme tablosundan al, yoksa 0
    cikis_id = sehir_mapping['cikis'].get(cikis, 0)
    varis_id = sehir_mapping['varis'].get(varis, 0)

    satir = {
        'Gun'           : tarih.day,
        'Ay'            : ay,
        'Yil'           : tarih.year,
        'Hafta_No'      : tarih.isocalendar()[1],
        'Gunun_Sirasi'  : tarih.dayofyear,
        'Haftanin_Gunu' : tarih.dayofweek,
        'Haftasonu'     : int(tarih.dayofweek >= 5),
        'Pazartesi'     : int(tarih.dayofweek == 0),
        'Cuma'          : int(tarih.dayofweek == 4),
        'Mevsim'        : mevsim,
        'Sehir_A_kod'   : cikis_id,
        'Sehir_B_kod'   : varis_id,
        'lag_1'         : lag(1),
        'lag_2'         : lag(2),
        'lag_3'         : lag(3),
        'lag_7'         : lag(7),
        'lag_14'        : lag(14),
        'ma_3'          : ma(3),
        'ma_7'          : ma(7),
        'ma_14'         : ma(14),
        'std_7'         : std(7),
    }
    return pd.DataFrame([satir])


# =============================================================
#  BÖLÜM 5  —  ANA TAHMİN FONKSİYONU  (dışarıdan çağrılan)
# =============================================================
def desi_tahmin_yap(cikis: str, varis: str, tarih_str: str,
                    df_talep: pd.DataFrame) -> float:
    """
    Verilen çıkış-varış rotası ve tarih için yapay zeka modeli ile desi tahmini yapar.

    Parametreler:
        cikis     : Çıkış şehri  (örn: 'İstanbul')
        varis     : Varış şehri  (örn: 'Eskişehir')
        tarih_str : 'YYYY-MM-DD' formatında hedef tarih
        df_talep  : Geçmiş desi talep verisi (DataFrame)

    Döndürür:
        float — Tahmini desi miktarı (negatif olamaz)
    """
    model, sehir_mapping = modeli_yukle()
    X = _tahmin_satiri_olustur(cikis, varis, tarih_str, df_talep, sehir_mapping)
    tahmin = model.predict(X)[0]
    return max(0.0, round(float(tahmin), 2))
