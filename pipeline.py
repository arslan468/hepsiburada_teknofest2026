import os
import math
import sys
import json
import pandas as pd
from desi_tahmin import desi_tahmin_yap, modeli_egit_ve_kaydet as _desi_egit

def modeli_egit_ve_kaydet():
    """
    Desi tahmin modelini eger ve kaydeder.
    Tum egitim mantigi desi_tahmin.py modulunde yonetilir.
    """
    dosya = 'desi_talep.xlsx' if os.path.exists('desi_talep.xlsx') else 'Desi_talep.xlsx'
    df_talep = pd.read_excel(dosya)
    _desi_egit(df_talep)

def mesafe_hesapla(cikis, varis, df_koordinat):
    try:
        cikis_temiz = str(cikis).strip().replace('i', 'İ').replace('ı', 'I').upper()
        varis_temiz = str(varis).strip().replace('i', 'İ').replace('ı', 'I').upper()
        temiz_sutun = df_koordinat['Transfer Merkezi'].astype(str).str.strip().str.replace('i', 'İ').str.replace('ı', 'I').str.upper()
        
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
    from ortools.linear_solver import pywraplp
    df_maliyet   = pd.read_excel('Araç_Kapasite_Maliyet.xlsx')
    df_koordinat = pd.read_excel('Koordinatlar v2.xlsx')
    df_filo      = pd.read_excel('Kiralık_Araçlar.xlsx')
    file_name    = 'desi_talep.xlsx' if __import__('os').path.exists('desi_talep.xlsx') else 'Desi_talep.xlsx'
    df_talep     = pd.read_excel(file_name)

    # Desi tahmini merkezi modülden yapılıyor
    hedef_desi = desi_tahmin_yap(cikis_sehri, varis_sehri, tarih_str, df_talep)

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