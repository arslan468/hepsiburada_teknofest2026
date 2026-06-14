import os
import sys
import json
import pandas as pd
from desi_tahmin import desi_tahmin_yap, modeli_egit_ve_kaydet as _desi_egit
from arac_tahmin import arac_atama_hesapla

def modeli_egit_ve_kaydet():
    """
    Desi tahmin modelini eger ve kaydeder.
    Tum egitim mantigi desi_tahmin.py modulunde yonetilir.
    """
    dosya = 'desi_talep.xlsx' if os.path.exists('desi_talep.xlsx') else 'Desi_talep.xlsx'
    df_talep = pd.read_excel(dosya)
    _desi_egit(df_talep)

def sistem_calistir_ve_json_don(cikis_sehri, varis_sehri, tarih_str):
    df_maliyet   = pd.read_excel('Araç_Kapasite_Maliyet.xlsx')
    df_koordinat = pd.read_excel('Koordinatlar v2.xlsx')
    df_filo      = pd.read_excel('Kiralık_Araçlar.xlsx')
    file_name    = 'desi_talep.xlsx' if os.path.exists('desi_talep.xlsx') else 'Desi_talep.xlsx'
    df_talep     = pd.read_excel(file_name)

    # Desi tahmini merkezi modülden yapılıyor
    hedef_desi = desi_tahmin_yap(cikis_sehri, varis_sehri, tarih_str, df_talep)

    sonuc_arac = arac_atama_hesapla(cikis_sehri, varis_sehri, hedef_desi, df_koordinat, df_maliyet, df_filo)

    sonuc = {
        "cikis": cikis_sehri,
        "varis": varis_sehri,
        "mesafe_km": sonuc_arac["mesafe_km"],
        "tahmini_desi": round(hedef_desi, 2),
        "atama_plani": {
            "kendi_tir": sonuc_arac["kendi_tir"],
            "kendi_kamyon": sonuc_arac["kendi_kamyon"],
            "spot_tir": sonuc_arac["spot_tir"],
            "spot_kamyon": sonuc_arac["spot_kamyon"]
        },
        "toplam_maliyet_tl": sonuc_arac["toplam_maliyet_tl"]
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