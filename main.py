import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import xgboost as xgb

df = pd.read_excel('Desi_talep.xlsx')
df['Tarih'] = pd.to_datetime(df['Tarih']) 

df['Ay'] = df['Tarih'].dt.month
df['Gun'] = df['Tarih'].dt.day
df['Haftanin_Gunu'] = df['Tarih'].dt.dayofweek
df['Hafta_Sonu'] = df['Haftanin_Gunu'].apply(lambda x: 1 if x >= 5 else 0)

df['Cikis_TM_ID'], cikis_isimleri = pd.factorize(df['Çıkış Transfer Merkezi'])
df['Varis_TM_ID'], varis_isimleri = pd.factorize(df['Varış Transfer Merkezi'])

df = df.sort_values(by=['Cikis_TM_ID', 'Varis_TM_ID', 'Tarih'])
df['Dun_Desi'] = df.groupby(['Cikis_TM_ID', 'Varis_TM_ID'])['Toplam Desi'].shift(1)
df['Gecen_Hafta_Desi'] = df.groupby(['Cikis_TM_ID', 'Varis_TM_ID'])['Toplam Desi'].shift(7)
df['Son_3_Gun_Ortalama'] = df.groupby(['Cikis_TM_ID', 'Varis_TM_ID'])['Toplam Desi'].transform(lambda x: x.rolling(window=3).mean())
df.dropna(inplace=True)

X = df[['Cikis_TM_ID', 'Varis_TM_ID', 'Ay', 'Gun', 'Haftanin_Gunu', 'Hafta_Sonu', 'Dun_Desi', 'Gecen_Hafta_Desi', 'Son_3_Gun_Ortalama']]
y_log = np.log1p(df['Toplam Desi'])

X_train, X_test, y_train_log, y_test_log = train_test_split(X, y_log, test_size=0.2, random_state=42)

model = xgb.XGBRegressor(
    n_estimators=150,
    learning_rate=0.1,
    random_state=42
)

model.fit(X_train, y_train_log)

tahminler_log = model.predict(X_test)
tahminler = np.expm1(tahminler_log)
y_test_gercek = np.expm1(y_test_log)

hata_payi = mean_absolute_error(y_test_gercek, tahminler)

print(f"yanilma payi: {hata_payi:.2f} Desi")

kiyaslama = pd.DataFrame({'gercek DEsi': y_test_gercek.values[:5], 'tahmini': tahminler[:5]})
print(kiyaslama.round(2))