
<div  align="center">

  

# 🚛 Hepsiburada & Teknofest 2026

### Yapay Zeka Destekli Lojistik Anahat Optimizasyonu

  


**TEKNOFEST 2026 Lojistik Ağ Optimizasyonu Yarışması — Temel İşlevli Çözüm (MVP)**

  

*Geçmiş kargo verilerinden talep tahmini yapan ve maliyet-minimize eden araç planlama simülatörü.*

  

</div>

  

---

  

## 📌 Proje Hakkında

  

Bu proje, **Teknofest 2026 Lojistik Ağ Optimizasyonu** yarışması için geliştirilmiş, uçtan uca çalışan bir yapay zeka destekli rota ve araç atama motorudur.

  

Sistem iki temel adımda çalışır:

  

1.  **Talep Tahmini:** Geçmiş kargo hacim verilerine (desi) dayalı zaman serisi projeksiyonu ile 11–17 Mayıs 2026 haftasına ait günlük talepleri tahmin eder.

2.  **Maliyet Optimizasyonu:** Kiralık ve Spot araç filosunu kullanarak, yol üstü konsolidasyon heuristiği ile toplam nakliye maliyetini minimize eden atama planı oluşturur.

  

Tüm bu yapı, **TypeScript** ve **Node.js** kullanılarak modern bir full-stack web uygulaması olarak tasarlanmıştır.

  

---
## 💰 Hesaplanan Minimum Maliyet Özeti
* **Sefer Bilgisi:** 98 Kiralık 501 Spot olmak üzere planlanan toplam 599 sefer planlanmıştır.

* **Kiralık Araç Detayları:** 70 Tır, 28 Kamyon seferi için hesaplanan maliyet 599.127 + 171.856 = 770.983 TL

* **Spot Araç Detayları:** 114 Tır, 387 Kamyon seferi için hesaplanan maliyet 2.479.744 + 6.540.064 = 9.019.808 TL

* **Toplam Maliyet:** 9.790.791 TL olarak hesaplanmıştır.

* **Hesaplanan Tahmini Desi:** 11-17 Mayıs haftası için tahmin edilen toplam desi 5.052.037 Desidir.
---

  

## 🚀 Kullanılan Teknolojiler

  

| Katman | Teknoloji |

|:---|:---|

| **Frontend** | React 19, Vite 6, Tailwind CSS 4, Framer Motion, Lucide React |

| **Backend** | Node.js, Express.js 4 |

| **Tahmin & Optimizasyon** | TypeScript tabanlı Heuristic Algoritma (Haversine mesafe, Yol Üstü Konsolidasyon, Spot/Kiralık Maliyet Minimizasyonu) |

| **Veri İşleme** | `xlsx` kütüphanesi ile Excel export, `fs` ile dosya sistemi entegrasyonu |

| **Geliştirme Araçları** | tsx (TypeScript runner), esbuild, ESLint |

  

---

  

## 📂 Proje Mimarisi

  

```

hepsiburada_teknofest2026/

├── server.ts # Express.js API sunucusu (Backend)

├── pipeline.ts # Tahmin + Optimizasyon motoru

├── index.html # Uygulama giriş noktası

├── vite.config.ts # Vite yapılandırması

├── package.json # Bağımlılıklar ve script'ler

├── tsconfig.json # TypeScript yapılandırması

├── src/

│ ├── App.tsx # Ana React bileşeni (Dashboard UI)

│ ├── main.tsx # React giriş noktası

│ ├── index.css # Global stiller

│ └── data/

│ ├── desi_talep.csv # 📊 Tarihsel kargo talep verisi (girdi)

│ ├── tahmin_desi.xlsx # 📈 Üretilen talep tahmini (çıktı)

│ ├── arac_planlama.xlsx # 🚛 Üretilen araç atama planı (çıktı)

│ └── summary_dashboard.json # 📋 Dashboard özet verisi (çıktı)

└── assets/

```

  

### Bileşen Detayları

  

#### 1️⃣ Optimizasyon Motoru — `pipeline.ts`

> Projenin beyni. Tüm iş mantığı burada çalışır.

  

-  `src/data/desi_talep.csv` verisinden haftalık trendleri çıkartarak gelecek talepleri hesaplar

- Haversine formülü ile 18 şehir arasındaki mesafe matrisini oluşturur

- Kiralık araçların kapasitesini öncelikli olarak doldurur

- Kalan yükleri **yol üstü konsolidasyon** algoritmasıyla Spot araçlara dağıtır

- Sonuçları `.xlsx` ve `.json` formatında dışa aktarır

  

#### 2️⃣ API Sunucusu — `server.ts`

> Frontend ile motor arasındaki köprü.

  

-  `POST /api/run-pipeline` → Pipeline'ı tetikler

-  `GET /api/dashboard-summary` → Özet KPI verilerini döner

-  `GET /api/download/tahmin-desi` → Tahmin Excel dosyasını indirir

-  `GET /api/download/arac-planlama` → Planlama Excel dosyasını indirir

  

#### 3️⃣ Dashboard Arayüzü — `src/App.tsx`

> Sonuçları görselleştiren modern web arayüzü.

  

- Toplam maliyet, desi, sefer sayısı gibi KPI kartları

- Günlük maliyet dağılımı grafikleri

- Şehir bazlı istatistikler ve interaktif harita

- Excel rapor indirme butonları

  

---

  

## 🛠 Kurulum ve Çalıştırma

  

### Ön Gereksinimler

  

- [Node.js](https://nodejs.org/) (v18 veya üzeri)

- npm (Node.js ile birlikte gelir)

  

### 1. Projeyi Klonlayın

```bash

git  clone  https://github.com/hepsiburada/hepsiburada_teknofest2026.git

cd  hepsiburada_teknofest2026

```

  

### 2. Bağımlılıkları Yükleyin

```bash

npm  install

```

  

### 3. Geliştirme Sunucusunu Başlatın

```bash

npm  run  dev

```

  

### 4. Tarayıcıda Açın

Terminalde `Lojistik Server çalışıyor` mesajını gördükten sonra:

  

👉 **http://localhost:3000**

  

---

  

## 📦 Kullanılabilir Komutlar

  

| Komut | Açıklama |

|:---|:---|

| `npm install` | Proje bağımlılıklarını indirir (`node_modules/` klasörüne) |

| `npm run dev` | Geliştirme sunucusunu başlatır (backend + frontend) |

| `npm run build` | Production için derlenmiş çıktı üretir (`dist/` klasörüne) |

| `npm run start` | Derlenmiş production sunucusunu çalıştırır |

| `npm run lint` | TypeScript tip kontrolü yapar |

  

---

  

## 🔄 Çalışma Akışı

  

```

┌──────────────────┐ ┌─────────────────────┐ ┌──────────────────┐

│ 📊 Tarihsel │ │ 🧠 pipeline.ts │ │ 📈 Çıktılar │

│ Kargo Verisi │────▶│ │────▶│ │

│ (desi_talep.csv)│ │ 1. Talep Tahmini │ │ tahmin_desi.xlsx│

│ │ │ 2. Mesafe Hesabı │ │ arac_planlama.xlsx│

│ │ │ 3. Araç Atama │ │ summary.json │

│ │ │ 4. Maliyet Optim. │ │ │

└──────────────────┘ └─────────────────────┘ └────────┬─────────┘

│

▼

┌──────────────────┐

│ 🖥 Dashboard │

│ (React + Vite) │

│ localhost:3000 │

└──────────────────┘

```

  

---

  

<div  align="center">

  

**Hepsiburada × Teknofest 2026** · Lojistik Ağ Optimizasyonu

  

</div>