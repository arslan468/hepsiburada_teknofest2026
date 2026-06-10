from ortools.linear_solver import pywraplp

def rotayi_optimize_et(hedef_desi):
    print(f"\n--- GOOGLE OR-TOOLS OPTİMİZASYON MOTORU ---")
    print(f"Taşınacak Hedef Kargo: {hedef_desi} Desi\n")

    solver = pywraplp.Solver.CreateSolver('SCIP')
    if not solver:
        print("Çözücü başlatılamadı!")
        return

    sabit_tir_kapasite = 15000
    sabit_tir_maliyet = 10000    
    
    sabit_kamyon_kapasite = 5000
    sabit_kamyon_maliyet = 4000  
    
    spot_tir_kapasite = 15000
    spot_tir_maliyet = 18000    
    
    spot_kamyon_kapasite = 5000
    spot_kamyon_maliyet = 7500   

    x_sabit_tir = solver.IntVar(0, 5, 'Sabit_Tir')       # Filomuzda max 5 tır var diyelim
    x_sabit_kamyon = solver.IntVar(0, 5, 'Sabit_Kamyon') # Filomuzda max 5 kamyon var
    x_spot_tir = solver.IntVar(0, 100, 'Spot_Tir')       # Paramız varsa sınırsız kiralayabiliriz
    x_spot_kamyon = solver.IntVar(0, 100, 'Spot_Kamyon')

    solver.Add(
        (x_sabit_tir * sabit_tir_kapasite) + 
        (x_sabit_kamyon * sabit_kamyon_kapasite) + 
        (x_spot_tir * spot_tir_kapasite) + 
        (x_spot_kamyon * spot_kamyon_kapasite) >= hedef_desi
    )
    solver.Minimize(
        (x_sabit_tir * sabit_tir_maliyet) + 
        (x_sabit_kamyon * sabit_kamyon_maliyet) + 
        (x_spot_tir * spot_tir_maliyet) + 
        (x_spot_kamyon * spot_kamyon_maliyet)
    )

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print("MÜKEMMEL ÇÖZÜM BULUNDU! İşte Atama Planı:")
        print(f"Kendi Tırlarımız (15K Desi)    : {int(x_sabit_tir.solution_value())} adet")
        print(f"Kendi Kamyonlarımız (5K Desi)  : {int(x_sabit_kamyon.solution_value())} adet")
        print(f"Kiralık Spot Tırlar (15K Desi) : {int(x_spot_tir.solution_value())} adet")
        print(f"Kiralık Spot Kamyonlar (5K D.) : {int(x_spot_kamyon.solution_value())} adet")
        
        toplam_fatura = solver.Objective().Value()
        print(f"\n--> TOPLAM OPERASYON MALİYETİ: {toplam_fatura:,.2f} TL")
    else:
        print("Matematiksel bir çözüm bulunamadı. Kısıtları kontrol et.")

rotayi_optimize_et(26445)