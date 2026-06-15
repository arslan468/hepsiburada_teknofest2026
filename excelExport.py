import pandas as pd
import numpy as np
import math
import xgboost as xgb
from ortools.linear_solver import pywraplp

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

def rota_hesapla(cikis_sehri, varis_sehri, tarih_str, model, df_maliyet, df_koordinat, df_filo):
    tarih = pd.to_datetime(tarih_str)
    ay, gun, haftanin_gunu = tarih.month, tarih.day, tarih.dayofweek
    hafta_sonu = 1 if haftanin_gunu >= 5 else 0

    cikis_id, varis_id = 1, 2 
    dun_desi, gecen_hafta_desi, son_3_gun_ort = 12000.0, 11500.0, 11800.0

    girdi_verisi = np.array([[cikis_id, varis_id, ay, gun, haftanin_gunu, hafta_sonu, dun_desi, gecen_hafta_desi, son_3_gun_ort]])
    hedef_desi = float(np.expm1(model.predict(girdi_verisi))[0])

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

    return {
        "Tarih": tarih_str,
        "Çıkış Merkezi": cikis_sehri,
        "Varış Merkezi": varis_sehri,
        "Mesafe (KM)": round(km_mesafe, 1),
        "YZ Tahmini Yük (Desi)": round(hedef_desi, 2),
        "Kendi Tırımız": int(x_kiralik_tir.solution_value()),
        "Kendi Kamyonumuz": int(x_kiralik_kamyon.solution_value()),
        "Spot Tır (Kiralık)": int(x_spot_tir.solution_value()),
        "Spot Kamyon (Kiralık)": int(x_spot_kamyon.solution_value()),
        "Optimum Maliyet (TL)": round(solver.Objective().Value(), 2)
    }

if __name__ == "__main__":
    print("Sistem dosyaları ve Yapay Zeka modeli yükleniyor...")
    df_maliyet = pd.read_excel('Araç_Kapasite_Maliyet.xlsx')
    df_koordinat = pd.read_excel('Koordinatlar v2.xlsx')
    df_filo = pd.read_excel('Kiralık_Araçlar.xlsx')
    
    model = xgb.XGBRegressor()
    model.load_model('HBAI_XGB_Model.json')

    gunluk_plan = [
        {"cikis": "İstanbul", "varis": "Eskişehir", "tarih": "2026-06-15"},
        {"cikis": "İstanbul", "varis": "Ankara", "tarih": "2026-06-15"},
        {"cikis": "İstanbul", "varis": "Kocaeli", "tarih": "2026-06-15"},
        {"cikis": "İzmir", "varis": "Trabzon", "tarih": "2026-06-16"}
    ]

    print(f"\n{len(gunluk_plan)} farklı rota için optimizasyon başlatıldı...")
    rapor_satirlari = []

    for rota in gunluk_plan:
        print(f"Hesaplanıyor: {rota['cikis']} -> {rota['varis']}")
        sonuc = rota_hesapla(rota['cikis'], rota['varis'], rota['tarih'], model, df_maliyet, df_koordinat, df_filo)
        rapor_satirlari.append(sonuc)

    df_rapor = pd.DataFrame(rapor_satirlari)
    
    rapor_adi = 'Hepsiburada_Gunluk_Plan.xlsx'
    df_rapor.to_excel(rapor_adi, index=False)
    
    print("\n" + "="*50)
    print(f"🚀 İŞLEM TAMAM! Rapor kaydedildi: {rapor_adi}")
    print("="*50)