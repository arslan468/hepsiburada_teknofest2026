import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
import pandas as pd
import numpy as np
from datetime import timedelta
from desi_tahmin import desi_tahmin_yap, modeli_yukle
from arac_tahmin import arac_atama_hesapla

print("-> Veriler yükleniyor...")
# Excel verilerini SADECE BİR KERE yüklüyoruz (hız için)
df_maliyet = pd.read_excel('Araç_Kapasite_Maliyet.xlsx')
df_koordinat = pd.read_excel('Koordinatlar v2.xlsx')
df_filo = pd.read_excel('Kiralık_Araçlar.xlsx')
file_name = 'desi_talep.xlsx' if os.path.exists('desi_talep.xlsx') else 'Desi_talep.xlsx'
df_talep = pd.read_excel(file_name)

# Model ve şehir eşleşme tablosunu merkezi modülünden yükle
_, sehir_mapping = modeli_yukle()
print("-> Model ve şehir ID eşleşme tablosu başarıyla yüklendi!")

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
            sonuc_arac = arac_atama_hesapla(cikis, varis, hedef_desi, df_koordinat, df_maliyet, df_filo)
            
            kendi_tir_adet = sonuc_arac["kendi_tir"]
            kendi_kamyon_adet = sonuc_arac["kendi_kamyon"]
            spot_tir_adet = sonuc_arac["spot_tir"]
            spot_kamyon_adet = sonuc_arac["spot_kamyon"]
            fiyatlar = sonuc_arac["fiyatlar"]
            
            atamalar = []
            if kendi_tir_adet > 0: atamalar.append(("Kiralık Tır", kendi_tir_adet, kendi_tir_adet * fiyatlar["kiralik_tir_fiyat"]))
            if kendi_kamyon_adet > 0: atamalar.append(("Kiralık Kamyon", kendi_kamyon_adet, kendi_kamyon_adet * fiyatlar["kiralik_kamyon_fiyat"]))
            if spot_tir_adet > 0: atamalar.append(("Spot Tır", spot_tir_adet, spot_tir_adet * fiyatlar["spot_tir_fiyat"]))
            if spot_kamyon_adet > 0: atamalar.append(("Spot Kamyon", spot_kamyon_adet, spot_kamyon_adet * fiyatlar["spot_kamyon_fiyat"]))
            
            if not atamalar:
                atama_listesi.append({
                    'Tarih': tarih_str,
                    'Çıkış Şehri': cikis,
                    'Varış Şehri': varis,
                    'Tahmini Desi (Desi)': round(hedef_desi, 2),
                    'Mesafe (KM)': round(sonuc_arac["mesafe_km"], 1),
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
                        'Mesafe (KM)': round(sonuc_arac["mesafe_km"], 1),
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