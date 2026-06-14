import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
import pandas as pd
import numpy as np
from ortools.linear_solver import pywraplp
from datetime import timedelta
from desi_tahmin import desi_tahmin_yap, modeli_yukle

print("-> Veriler yükleniyor...")
# Excel verilerini SADECE BİR KERE yüklüyoruz (hız için)
df_maliyet = pd.read_excel('Araç_Kapasite_Maliyet.xlsx')
df_koordinat = pd.read_excel('Koordinatlar v2.xlsx')
df_filo = pd.read_excel('Kiralık_Araçlar.xlsx')
file_name = 'desi_talep.xlsx' if os.path.exists('desi_talep.xlsx') else 'desi_takep.xlsx'
df_talep = pd.read_excel(file_name)

# Model ve şehir eşleşme tablosunu merkezi modülünden yükle
_, sehir_mapping = modeli_yukle()
print("-> Model ve şehir ID eşleşme tablosu başarıyla yüklendi!")

tir_row = df_maliyet[df_maliyet['Araç Adı'] == 'Tır'].iloc[0]
kamyon_row = df_maliyet[df_maliyet['Araç Adı'] == 'Kamyon'].iloc[0]

tir_kapasite = tir_row['Kapasite (desi)']
kamyon_kapasite = kamyon_row['Kapasite (desi)']

# 2. Şehirler ve Tarihler
sehirler = [
    'Balıkesir', 'Bilecik', 'Denizli', 'Erzincan', 'Eskişehir',
    'Isparta', 'İstanbul', 'Karaman', 'Kocaeli', 'Kütahya',
    'Manisa', 'Mardin', 'Mersin', 'Sivas', 'Şanlıurfa',
    'Tekirdağ', 'Yalova', 'Zonguldak'
]

start_date = pd.to_datetime('2026-05-11')
dates = [start_date + timedelta(days=i) for i in range(7)]


desi_listesi = []
atama_listesi = []

toplam_kombinasyon = len(dates) * len(sehirler) * (len(sehirler) - 1)
mevcut = 0

print(f"-> Toplam {toplam_kombinasyon} rota senaryosu hesaplanıyor. Lütfen bekleyin...")

for tarih in dates:
    ay = tarih.month
    gun = tarih.day
    haftanin_gunu = tarih.dayofweek
    hafta_sonu = 1 if haftanin_gunu >= 5 else 0
    tarih_str = tarih.strftime('%Y-%m-%d')
    
    for cikis in sehirler:
        for varis in sehirler:
            if cikis == varis:
                continue
            
            mevcut += 1
            if mevcut % 500 == 0:
                print(f"   İşlenen: {mevcut}/{toplam_kombinasyon}")
                
            # 1. Adım: Yapay Zeka ile Desi Tahmini (merkezi modülden)
            hedef_desi = desi_tahmin_yap(cikis, varis, tarih_str, df_talep)
            
            desi_listesi.append({
                'Tarih': tarih_str,
                'Çıkış Şehri': cikis,
                'Varış Şehri': varis,
                'Tahmini Desi (Desi)': round(hedef_desi, 2)
            })
            
            # 2. Adım: Matematiksel Optimizasyon (Araç Atama)
            km_mesafe = mesafe_hesapla(cikis, varis, df_koordinat)
            
            kiralik_tir_fiyat = tir_row['Kiralık Araç Günlük Kira (TL)'] + (km_mesafe * tir_row['Kiralık Araç Kilometre Başına Maliyet (TL)'])
            spot_tir_fiyat = tir_row['Spot Araç Sabit Günlük Maliyet (TL)'] + (km_mesafe * tir_row['Spot Kilometre Başına Maliyet (TL)'])
            kiralik_kamyon_fiyat = kamyon_row['Kiralık Araç Günlük Kira (TL)'] + (km_mesafe * kamyon_row['Kiralık Araç Kilometre Başına Maliyet (TL)'])
            spot_kamyon_fiyat = kamyon_row['Spot Araç Sabit Günlük Maliyet (TL)'] + (km_mesafe * kamyon_row['Spot Kilometre Başına Maliyet (TL)'])

            filo_durumu = df_filo[(df_filo['Çıkış Transfer Merkezi'] == cikis) & (df_filo['Varış Transfer Merkezi'] == varis)]
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
            
            kendi_tir_adet = int(x_kiralik_tir.solution_value())
            kendi_kamyon_adet = int(x_kiralik_kamyon.solution_value())
            spot_tir_adet = int(x_spot_tir.solution_value())
            spot_kamyon_adet = int(x_spot_kamyon.solution_value())
            
            atamalar = []
            if kendi_tir_adet > 0: atamalar.append(("Kiralık Tır", kendi_tir_adet, kendi_tir_adet * kiralik_tir_fiyat))
            if kendi_kamyon_adet > 0: atamalar.append(("Kiralık Kamyon", kendi_kamyon_adet, kendi_kamyon_adet * kiralik_kamyon_fiyat))
            if spot_tir_adet > 0: atamalar.append(("Spot Tır", spot_tir_adet, spot_tir_adet * spot_tir_fiyat))
            if spot_kamyon_adet > 0: atamalar.append(("Spot Kamyon", spot_kamyon_adet, spot_kamyon_adet * spot_kamyon_fiyat))
            
            if not atamalar:
                atama_listesi.append({
                    'Tarih': tarih_str,
                    'Çıkış Şehri': cikis,
                    'Varış Şehri': varis,
                    'Tahmini Desi (Desi)': round(hedef_desi, 2),
                    'Mesafe (KM)': round(km_mesafe, 1),
                    'Araç Türü': 'Atama Yapılamadı',
                    'Araç Adedi (Adet)': 0,
                    'Toplam Maliyet (TL)': 0
                })
            else:
                for arac_turu, adet, maliyet in atamalar:
                    atama_listesi.append({
                        'Tarih': tarih_str,
                        'Çıkış Şehri': cikis,
                        'Varış Şehri': varis,
                        'Tahmini Desi (Desi)': round(hedef_desi, 2),
                        'Mesafe (KM)': round(km_mesafe, 1),
                        'Araç Türü': arac_turu,
                        'Araç Adedi (Adet)': adet,
                        'Toplam Maliyet (TL)': round(maliyet, 2)
                    })

# Excel dosyalarını oluşturma
print("-> Veriler DataFrame'lere dönüştürülüyor...")
df_desi = pd.DataFrame(desi_listesi)
df_atama = pd.DataFrame(atama_listesi)

print("-> Excel dosyaları kaydediliyor...")
df_desi.to_excel('Tahmini_Desi_1_Hafta.xlsx', index=False)
df_atama.to_excel('Arac_Atama_Plani_1_Hafta.xlsx', index=False)

print("✅ İŞLEM TAMAMLANDI! 'Tahmini_Desi_1_Hafta.xlsx' ve 'Arac_Atama_Plani_1_Hafta.xlsx' dosyaları başarıyla oluşturuldu.")