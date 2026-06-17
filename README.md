# Hepsiburada & Teknofest 2026 - Yapay Zeka Destekli Lojistik Optimizasyonu

Bu proje, Teknofest 2026 Lojistik Ağ Optimizasyonu yarışması (Temel İşlevli Çözüm / MVP aşaması) için geliştirilmiş, yapay zeka destekli bir rota ve araç atama motorudur. 

Sistem, geçmiş verilere dayanarak (XGBoost) kargo hacmini (desi) tahmin eder ve Google OR-Tools kullanarak bu yükü en düşük maliyetle (Kiralık ve Spot Tır/Kamyon) varış noktasına ulaştırmak için matematiksel optimizasyon yapar. Python tabanlı bu motor, Express.js (Backend) ve Next.js (Frontend) mimarisi ile web ortamına entegre edilmiştir.

## 🚀 Kullanılan Teknolojiler

* **Frontend:** Next.js (App Router), React, Tailwind CSS
* **Backend:** Node.js, Express.js
* **Yapay Zeka & Optimizasyon (Python):** XGBoost, Google OR-Tools (SCIP), Pandas, Scikit-learn
* **Haberleşme:** Child Process (Backend üzerinden Python tetikleme)

## 📂 Proje Mimarisi

1.  **Python Motoru (`pipeline.py` vb.):** Çıkış şehri, varış şehri ve tarih bilgilerini parametre olarak alır. XGBoost modelinden `HBAI_XGB_Model.json` dosyası ile tahmini desi değerini çeker, `Koordinatlar v2.xlsx` ile mesafeyi hesaplar ve `optimization.py` mantığıyla maliyeti minimize eden araç atamasını JSON formatında `stdout` olarak fırlatır.
2.  **Express.js API (`server.js`):** `/api/optimize` endpoint'i üzerinden gelen POST isteklerini alır, `child_process.exec` ile `pipeline.py` dosyasını çalıştırır ve dönen JSON sonucunu frontend'e iletir.
3.  **Next.js Arayüzü (`page.js`):** Kullanıcıdan alınan rota bilgilerini backend'e gönderir, işlem sürerken yükleme ekranı gösterir ve sonuçları (Maliyet, Desi, Rota, Atama Planı) modern kartlar halinde ekrana basar.

