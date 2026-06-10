import pandas as pd
import numpy as np
import math
import json
import sys
from sklearn.model_selection import train_test_split
import xgboost as xgb
from ortools.linear_solver import pywraplp

def modeli_egit_ve_kaydet():
    df = pd.read_excel('Desi_talep.xlsx')
    df['Tarih'] = pd.to_datetime(df['Tarih']) 

    df['Ay'] = df['Tarih'].dt.month
    df['Gun'] = df['Tarih'].dt.day
    df['Haftanin_Gunu'] = df['Tarih'].dt.dayofweek
    df['Hafta_Sonu'] = df['Haftanin_Gunu'].apply(lambda x: 1 if x >= 5 else 0)

    df['Cikis_TM_ID'], _ = pd.factorize(df['Çıkış Transfer Merkezi'])
    df['Varis_TM_ID'], _ = pd.factorize(df['Varış Transfer Merkezi'])

    df = df.sort_values(by=['Cikis_TM_ID', 'Varis_TM_ID', 'Tarih'])
    df['Dun_Desi'] = df.groupby(['Cikis_TM_ID', 'Varis_TM_ID'])['Toplam Desi'].shift(1)
    df['Gecen_Hafta_Desi'] = df.groupby(['Cikis_TM_ID', 'Varis_TM_ID'])['Toplam Desi'].shift(7)
    df['Son_3_Gun_Ortalama'] = df.groupby(['Cikis_TM_ID', 'Varis_TM_ID'])['Toplam Desi'].transform(lambda x: x.rolling(window=3).mean())
    df.dropna(inplace=True)

    X = df[['Cikis_TM_ID', 'Varis_TM_ID', 'Ay', 'Gun', 'Haftanin_Gunu', 'Hafta_Sonu', 'Dun_Desi', 'Gecen_Hafta_Desi', 'Son_3_Gun_Ortalama']]
    y_log = np.log1p(df['Toplam Desi'])

    model = xgb.XGBRegressor(n_estimators=150, learning_rate=0.1, random_state=42)
    model.fit(X, y_log)
    
    model.save_model('HBAI_XGB_Model.json')
    print("-> Yapay Zeka modeli eğitildi ve 'HBAI_XGB_Model.json' olarak kaydedildi!")

def mesafe_hesapla(cikis, varis, df_koordinat):
    try:
        cikis_temiz = str(cikis).strip().upper()
        varis_temiz = str(varis).strip().upper()
        temiz_sutun = df_koordinat['Transfer Merkezi'].astype(str).str.strip().str.upper()
        
        enlem1 = df_koordinat.loc[temiz_sutun == cikis_temiz, 'Enlem'].values[0]
        boylam1 = df_koordinat.loc[temiz_sutun == cikis_temiz, 'Boylam'].values[0]
        enlem2 = df_koordinat.loc[temiz_sutun == varis_temiz, 'Enlem'].values[0]
        boylam2 = df_koordinat.loc[temiz_sutun == varis_temiz, 'Boylam'].values[0]
        
        R = 6371.0 
        dlat = math.radians(enlem2 - enlem1)
        dlon = math.radians(boylam2 - boylam1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(enlem1)) * math.cos(math.radians(enlem2)) * math.sin(dlon / 2)**2
        return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))
    except:
        return 500.0

def sistem_calistir_ve_json_don(cikis_sehri, varis_sehri, tarih_str):
    df_maliyet = pd.read_excel('Araç_Kapasite_Maliyet.xlsx')
    df_koordinat = pd.read_excel('Koordinatlar v2.xlsx')
    df_filo = pd.read_excel('Kiralık_Araçlar.xlsx')
    
    model = xgb.XGBRegressor()
    model.load_model('HBAI_XGB_Model.json') 

    tarih = pd.to_datetime(tarih_str)
    ay = tarih.month
    gun = tarih.day
    haftanin_gunu = tarih.dayofweek
    hafta_sonu = 1 if haftanin_gunu >= 5 else 0

    cikis_id, varis_id = 1, 2 
    dun_desi, gecen_hafta_desi, son_3_gun_ort = 12000.0, 11500.0, 11800.0

    girdi_verisi = np.array([[cikis_id, varis_id, ay, gun, haftanin_gunu, hafta_sonu, dun_desi, gecen_hafta_desi, son_3_gun_ort]])
    tahmin_log = model.predict(girdi_verisi)
    hedef_desi = float(np.expm1(tahmin_log)[0])

    km_mesafe = mesafe_hesapla(cikis_sehri, varis_sehri, df_koordinat)
    tir_row = df_maliyet[df_maliyet['Araç Adı'] == 'Tır'].iloc[0]
    kamyon_row = df_maliyet[df_maliyet['Araç Adı'] == 'Kamyon'].iloc[0]

    tir_kapasite, kamyon_kapasite = tir_row['Kapasite (desi)'], kamyon_row['Kapasite (desi)']

    kiralik_tir_fiyat = tir_row['Kiralık Araç Günlük Kira (TL)'] + (km_mesafe * tir_row['Kiralık Araç Kilometre Başına Maliyet (TL)'])
    spot_tir_fiyat = tir_row['Spot Araç Sabit Günlük Maliyet (TL)'] + (km_mesafe * tir_row['Spot Kilometre Başına Maliyet (TL)'])
    kiralik_kamyon_fiyat = kamyon_row['Kiralık Araç Günlük Kira (TL)'] + (km_mesafe * kamyon_row['Kiralık Araç Kilometre Başına Maliyet (TL)'])
    spot_kamyon_fiyat = kamyon_row['Spot Araç Sabit Günlük Maliyet (TL)'] + (km_mesafe * kamyon_row['Spot Kilometre Başına Maliyet (TL)'])

    filo_durumu = df_filo[(df_filo['Çıkış Transfer Merkezi'] == cikis_sehri) & (df_filo['Varış Transfer Merkezi'] == varis_sehri)]
    max_kiralik_tir = filo_durumu[filo_durumu['Araç Türü'] == 'Tır']['Araç sayısı'].sum() if not filo_durumu.empty else 0
    max_kiralik_kamyon = filo_durumu[filo_durumu['Araç Türü'] == 'Kamyon']['Araç sayısı'].sum() if not filo_durumu.empty else 0

    solver = pywraplp.Solver.CreateSolver('SCIP')
    x_kiralik_tir = solver.IntVar(0, int(max_kiralik_tir), 'Kiralik_Tir')
    x_kiralik_kamyon = solver.IntVar(0, int(max_kiralik_kamyon), 'Kiralik_Kamyon')
    x_spot_tir = solver.IntVar(0, 100, 'Spot_Tir')
    x_spot_kamyon = solver.IntVar(0, 100, 'Spot_Kamyon')

    solver.Add((x_kiralik_tir * tir_kapasite) + (x_kiralik_kamyon * kamyon_kapasite) + (x_spot_tir * tir_kapasite) + (x_spot_kamyon * kamyon_kapasite) >= hedef_desi)
    solver.Minimize((x_kiralik_tir * kiralik_tir_fiyat) + (x_kiralik_kamyon * kiralik_kamyon_fiyat) + (x_spot_tir * spot_tir_fiyat) + (x_spot_kamyon * spot_kamyon_fiyat))
    
    solver.Solve()

    sonuc = {
        "cikis": cikis_sehri,
        "varis": varis_sehri,
        "mesafe_km": round(km_mesafe, 1),
        "tahmini_desi": round(hedef_desi, 2),
        "atama_plani": {
            "kendi_tir": int(x_kiralik_tir.solution_value()),
            "kendi_kamyon": int(x_kiralik_kamyon.solution_value()),
            "spot_tir": int(x_spot_tir.solution_value()),
            "spot_kamyon": int(x_spot_kamyon.solution_value())
        },
        "toplam_maliyet_tl": round(solver.Objective().Value(), 2)
    }
    
    print(json.dumps(sonuc))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "train":
        modeli_egit_ve_kaydet()
    else:
        cikis = sys.argv[1] if len(sys.argv) > 1 else "İstanbul"
        varis = sys.argv[2] if len(sys.argv) > 2 else "Eskişehir"
        tarih = sys.argv[3] if len(sys.argv) > 3 else "2026-06-15"
        sistem_calistir_ve_json_don(cikis, varis, tarih)