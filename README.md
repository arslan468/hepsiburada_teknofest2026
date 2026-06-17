# Hepsiburada & Teknofest 2026 - Yapay Zeka Destekli Lojistik Optimizasyonu

Bu proje, Teknofest 2026 Lojistik Ağ Optimizasyonu yarışması (Temel İşlevli Çözüm / MVP aşaması) için geliştirilmiş, yapay zeka ve matematiksel optimizasyon destekli bir rota ve araç atama motorudur. 

Sistem, geçmiş kargo hacim verilerine dayanarak (Zaman Serisi Projeksiyonu) gelecek kargo hacmini (desi) tahmin eder. Ardından kiralık ve spot araç havuzunu kullanarak maliyeti minimize eden en verimli rotaları planlar. Tüm bu yapı, TypeScript ve Node.js kullanılarak uçtan uca modern bir web uygulaması olarak tasarlanmıştır.

## 🚀 Kullanılan Teknolojiler

* **Frontend:** React, Vite, Tailwind CSS, Framer Motion (Animasyonlar), Lucide React (İkonlar)
* **Backend:** Node.js, Express.js
* **Tahmin & Optimizasyon:** TypeScript tabanlı özel Heuristic Algoritma (Mesafe hesaplama, Konsolidasyon, Spot/Kiralık Araç Maliyet Optimizasyonu)
* **Veri İşleme:** `xlsx` ile Excel export, Node.js dosya sistemi entegrasyonu

## 📂 Proje Mimarisi

1.  **Optimizasyon Motoru (`pipeline.ts`):** 
    * `src/data/desi_talep.csv` verisini analiz ederek haftalık trendleri çıkartır ve gelecek talepleri hesaplar.
    * Koordinat verileri üzerinden Haversine formülü ile şehirler arası mesafeleri tespit eder.
    * Kiralık araç kapasitelerini doldurmaya öncelik verir, ardından boşlukları ve kalan yükleri yol üstü konsolidasyon algoritmasıyla Spot araçlarla destekler.
    * Optimizasyon sonuçlarını `tahmin_desi.xlsx`, `arac_planlama.xlsx` ve dashboard verisi olarak `summary_dashboard.json`'a kaydeder.
2.  **Express.js API (`server.ts`):** 
    * Frontend ile motor arasındaki iletişimi sağlar. `/api/run-pipeline` isteği geldiğinde `pipeline.ts` komutunu arka planda tetikler.
    * Optimizasyon sonuçlarını, özet verileri ve Excel raporlarını kullanıcıya iletir.
3.  **Vite / React Arayüzü (`index.html` & `src/`):** 
    * Elde edilen JSON formatındaki özet bilgileri, modern KPI kartları ve interaktif grafikler halinde görselleştirir.

## 🛠 Kurulum ve Çalıştırma

Projeyi bilgisayarınızda çalıştırmak için aşağıdaki adımları sırasıyla uygulayabilirsiniz:

### 1. Bağımlılıkları Yükleyin
Proje klasörünün içerisinde bir terminal açın ve gerekli paketleri indirmek için şu komutu çalıştırın:
```bash
npm install
```

### 2. Uygulamayı Başlatın
Paketler yüklendikten sonra, geliştirme sunucusunu (hem backend hem frontend) başlatmak için şu komutu girin:
```bash
npm run dev
```

### 3. Kullanıma Başlayın
Terminalde "Lojistik Server çalışıyor" mesajını gördükten sonra tarayıcınızdan şu adrese giderek uygulamaya erişebilirsiniz:
**http://localhost:3000**

## 📦 Production (Üretim) Ortamı İçin Derleme

Projeyi production standartlarında çalıştırılabilir bir formata (build) dönüştürmek ve ayağa kaldırmak isterseniz:
```bash
npm run build
npm run start
```
