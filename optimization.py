import pandas as pd
import math
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
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        gercek_mesafe = R * c
        return gercek_mesafe
        
    except IndexError:
        print(f"[UYARI] {cikis} veya {varis} koordinat tablosunda bulunamadı! Varsayılan değer atanıyor.")
        return 500

def rotayi_optimize_et(cikis_sehri, varis_sehri, hedef_desi):
    df_maliyet = pd.read_excel('Araç_Kapasite_Maliyet.xlsx')
    df_koordinat = pd.read_excel('Koordinatlar v2.xlsx')
    df_filo = pd.read_excel('Kiralık_Araçlar.xlsx')

    km_mesafe = mesafe_hesapla(cikis_sehri, varis_sehri, df_koordinat)

    tir_row = df_maliyet[df_maliyet['Araç Adı'] == 'Tır'].iloc[0]
    kamyon_row = df_maliyet[df_maliyet['Araç Adı'] == 'Kamyon'].iloc[0]

    tir_kapasite = tir_row['Kapasite (desi)']
    kamyon_kapasite = kamyon_row['Kapasite (desi)']

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

    solver.Add(
        (x_kiralik_tir * tir_kapasite) + 
        (x_kiralik_kamyon * kamyon_kapasite) + 
        (x_spot_tir * tir_kapasite) + 
        (x_spot_kamyon * kamyon_kapasite) >= hedef_desi
    )

    solver.Minimize(
        (x_kiralik_tir * kiralik_tir_fiyat) + 
        (x_kiralik_kamyon * kiralik_kamyon_fiyat) + 
        (x_spot_tir * spot_tir_fiyat) + 
        (x_spot_kamyon * spot_kamyon_fiyat)
    )

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print(f"kendi Kiralık Tırımız ({tir_kapasite} Desi)   : {int(x_kiralik_tir.solution_value())} adetkullanılacak")
        print(f"kendi Kiralık Kamyonumuz ({kamyon_kapasite} D.): {int(x_kiralik_kamyon.solution_value())} adet kullanılacak")
        print(f"dışarıdan Spot Tır ({tir_kapasite} Desi)    : {int(x_spot_tir.solution_value())} adet KIRALANACAK")
        print(f"dışarıdan Spot Kamyon ({kamyon_kapasite} D.) : {int(x_spot_kamyon.solution_value())} adet KIRALANACAK")
        
        toplam_fatura = solver.Objective().Value()
        print(f"\n--> TOPLAM OPERASYON MALIYETI: {toplam_fatura:,.2f} TL")
    else:
        print("hata")

