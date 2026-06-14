import math
import sys
import json
import subprocess

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

def _solve_in_subprocess(hedef_desi, tir_kapasite, kamyon_kapasite,
                         kiralik_tir_fiyat, spot_tir_fiyat,
                         kiralik_kamyon_fiyat, spot_kamyon_fiyat,
                         max_kiralik_tir, max_kiralik_kamyon):
    inputs = {
        "hedef_desi": float(hedef_desi),
        "tir_kapasite": int(tir_kapasite),
        "kamyon_kapasite": int(kamyon_kapasite),
        "kiralik_tir_fiyat": float(kiralik_tir_fiyat),
        "spot_tir_fiyat": float(spot_tir_fiyat),
        "kiralik_kamyon_fiyat": float(kiralik_kamyon_fiyat),
        "spot_kamyon_fiyat": float(spot_kamyon_fiyat),
        "max_kiralik_tir": int(max_kiralik_tir),
        "max_kiralik_kamyon": int(max_kiralik_kamyon)
    }
    
    # Run this file as a subprocess to isolate ortools from pandas/pyarrow/xgboost protobuf conflicts
    res = subprocess.run(
        [sys.executable, __file__],
        input=json.dumps(inputs),
        text=True,
        capture_output=True
    )
    if res.returncode != 0:
        raise RuntimeError(f"Solver subprocess failed with exit code {res.returncode}. Stderr: {res.stderr}")
    return json.loads(res.stdout)

def arac_atama_hesapla(cikis_sehri, varis_sehri, hedef_desi, df_koordinat, df_maliyet, df_filo):
    km_mesafe = mesafe_hesapla(cikis_sehri, varis_sehri, df_koordinat)
    
    tir_row = df_maliyet[df_maliyet['Araç Adı'] == 'Tır'].iloc[0]
    kamyon_row = df_maliyet[df_maliyet['Araç Adı'] == 'Kamyon'].iloc[0]

    tir_kapasite = int(tir_row['Kapasite (desi)'])
    kamyon_kapasite = int(kamyon_row['Kapasite (desi)'])

    kiralik_tir_fiyat = float(tir_row['Kiralık Araç Günlük Kira (TL)'] + (km_mesafe * tir_row['Kiralık Araç Kilometre Başına Maliyet (TL)']))
    spot_tir_fiyat = float(tir_row['Spot Araç Sabit Günlük Maliyet (TL)'] + (km_mesafe * tir_row['Spot Kilometre Başına Maliyet (TL)']))
    kiralik_kamyon_fiyat = float(kamyon_row['Kiralık Araç Günlük Kira (TL)'] + (km_mesafe * kamyon_row['Kiralık Araç Kilometre Başına Maliyet (TL)']))
    spot_kamyon_fiyat = float(kamyon_row['Spot Araç Sabit Günlük Maliyet (TL)'] + (km_mesafe * kamyon_row['Spot Kilometre Başına Maliyet (TL)']))

    filo_durumu = df_filo[(df_filo['Çıkış Transfer Merkezi'] == cikis_sehri) & (df_filo['Varış Transfer Merkezi'] == varis_sehri)]
    max_kiralik_tir = int(filo_durumu[filo_durumu['Araç Türü'] == 'Tır']['Araç sayısı'].sum()) if not filo_durumu.empty else 0
    max_kiralik_kamyon = int(filo_durumu[filo_durumu['Araç Türü'] == 'Kamyon']['Araç sayısı'].sum()) if not filo_durumu.empty else 0

    sol = _solve_in_subprocess(
        hedef_desi, tir_kapasite, kamyon_kapasite,
        kiralik_tir_fiyat, spot_tir_fiyat,
        kiralik_kamyon_fiyat, spot_kamyon_fiyat,
        max_kiralik_tir, max_kiralik_kamyon
    )

    return {
        "mesafe_km": round(km_mesafe, 1),
        "kendi_tir": sol["kendi_tir"],
        "kendi_kamyon": sol["kendi_kamyon"],
        "spot_tir": sol["spot_tir"],
        "spot_kamyon": sol["spot_kamyon"],
        "toplam_maliyet_tl": sol["toplam_maliyet_tl"],
        "fiyatlar": {
            "kiralik_tir_fiyat": kiralik_tir_fiyat,
            "spot_tir_fiyat": spot_tir_fiyat,
            "kiralik_kamyon_fiyat": kiralik_kamyon_fiyat,
            "spot_kamyon_fiyat": spot_kamyon_fiyat
        }
    }

if __name__ == '__main__':
    # Subprocess execution entrypoint
    try:
        # Read from stdin
        data = json.load(sys.stdin)
        
        hedef_desi = data["hedef_desi"]
        tir_kapasite = data["tir_kapasite"]
        kamyon_kapasite = data["kamyon_kapasite"]
        kiralik_tir_fiyat = data["kiralik_tir_fiyat"]
        spot_tir_fiyat = data["spot_tir_fiyat"]
        kiralik_kamyon_fiyat = data["kiralik_kamyon_fiyat"]
        spot_kamyon_fiyat = data["spot_kamyon_fiyat"]
        max_kiralik_tir = data["max_kiralik_tir"]
        max_kiralik_kamyon = data["max_kiralik_kamyon"]
        
        # Load ortools inside the subprocess
        from ortools.linear_solver import pywraplp
        
        solver = pywraplp.Solver.CreateSolver('SCIP')
        if not solver:
            sys.exit(1)
            
        x_kiralik_tir = solver.IntVar(0, int(max_kiralik_tir), 'Kiralik_Tir')
        x_kiralik_kamyon = solver.IntVar(0, int(max_kiralik_kamyon), 'Kiralik_Kamyon')
        x_spot_tir = solver.IntVar(0, 100, 'Spot_Tir')
        x_spot_kamyon = solver.IntVar(0, 100, 'Spot_Kamyon')

        solver.Add((x_kiralik_tir * tir_kapasite) + (x_kiralik_kamyon * kamyon_kapasite) + (x_spot_tir * tir_kapasite) + (x_spot_kamyon * kamyon_kapasite) >= hedef_desi)
        solver.Minimize((x_kiralik_tir * kiralik_tir_fiyat) + (x_kiralik_kamyon * kiralik_kamyon_fiyat) + (x_spot_tir * spot_tir_fiyat) + (x_spot_kamyon * spot_kamyon_fiyat))
        
        solver.Solve()
        
        output = {
            "kendi_tir": int(x_kiralik_tir.solution_value()),
            "kendi_kamyon": int(x_kiralik_kamyon.solution_value()),
            "spot_tir": int(x_spot_tir.solution_value()),
            "spot_kamyon": int(x_spot_kamyon.solution_value()),
            "toplam_maliyet_tl": round(solver.Objective().Value(), 2)
        }
        print(json.dumps(output))
    except Exception as e:
        print(f"Error in solver subprocess: {str(e)}", file=sys.stderr)
        sys.exit(1)
