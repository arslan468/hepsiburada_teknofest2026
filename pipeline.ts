import fs from "fs";
import path from "path";
import * as XLSX from "xlsx";

// --- 1. COĞRAFİ VERİLER VE HAVERSINE MESAFE MOTORU ---
const COORDS: { [key: string]: [number, number] } = {
  "Mersin": [36.8000, 34.6333],
  "Kütahya": [39.4167, 29.9833],
  "Kocaeli": [40.8533, 29.8815],
  "Eskişehir": [39.7767, 30.5206],
  "İstanbul": [41.0082, 28.9784],
  "Bilecik": [40.1506, 29.9792],
  "Balıkesir": [39.6484, 27.8826],
  "Şanlıurfa": [37.1591, 38.7969],
  "Tekirdağ": [40.9781, 27.5115],
  "Sivas": [39.7477, 37.0179],
  "Yalova": [40.6500, 29.2667],
  "Manisa": [38.6191, 27.4289],
  "Isparta": [37.7648, 30.5566],
  "Mardin": [37.3212, 40.7245],
  "Erzincan": [39.7500, 39.5000],
  "Zonguldak": [41.4564, 31.7987],
  "Karaman": [37.1759, 33.2287],
  "Denizli": [37.7765, 29.0864]
};

const CITIES = Object.keys(COORDS).sort();

function haversineDistance(city1: string, city2: string): number {
  if (city1 === city2) return 0.0;
  const [lat1, lon1] = COORDS[city1];
  const [lat2, lon2] = COORDS[city2];

  const R = 6371.0; // Earth radius in kilometers

  const lat1Rad = (lat1 * Math.PI) / 180;
  const lon1Rad = (lon1 * Math.PI) / 180;
  const lat2Rad = (lat2 * Math.PI) / 180;
  const lon2Rad = (lon2 * Math.PI) / 180;

  const dlat = lat2Rad - lat1Rad;
  const dlon = lon2Rad - lon1Rad;

  const a =
    Math.sin(dlat / 2) ** 2 +
    Math.cos(lat1Rad) * Math.cos(lat2Rad) * Math.sin(dlon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c;
}

// Distance matrix pre-cached
const DISTANCES: { [key: string]: { [key: string]: number } } = {};
for (const c1 of CITIES) {
  DISTANCES[c1] = {};
  for (const c2 of CITIES) {
    DISTANCES[c1][c2] = haversineDistance(c1, c2);
  }
}

// --- 2. FİLO PARAMETRELERİ (Kapasite & Maliyet Matrisleri) ---
const VEHICLES: {
  [key: string]: {
    kapasite: number;
    kiralık_sabit: number;
    kiralık_km: number;
    spot_sabit: number;
    spot_km: number;
    min_doluluk_oranı: number;
  };
} = {
  "Tır": {
    kapasite: 22400,
    kiralık_sabit: 7000,
    kiralık_km: 13,
    spot_sabit: 11700,
    spot_km: 25,
    min_doluluk_oranı: 0.10
  },
  "Kamyon": {
    kapasite: 12000,
    kiralık_sabit: 5000,
    kiralık_km: 10,
    spot_sabit: 7638,
    spot_km: 21,
    min_doluluk_oranı: 0.10
  },
  "Hafif Kamyon": {
    kapasite: 7200,
    kiralık_sabit: 5000,
    kiralık_km: 10,
    spot_sabit: 8750,
    spot_km: 20,
    min_doluluk_oranı: 0.10
  },
  "Kamyonet": {
    kapasite: 5600,
    kiralık_sabit: 3750,
    kiralık_km: 6,
    spot_sabit: 4750,
    spot_km: 18,
    min_doluluk_oranı: 0.10
  }
};

const KİRALIK_FİLO = [
  { cikis: "İstanbul", varis: "Yalova", tip: "Tır", adet: 2 },
  { cikis: "İstanbul", varis: "Eskişehir", tip: "Tır", adet: 2 },
  { cikis: "Kocaeli", varis: "Yalova", tip: "Tır", adet: 1 },
  { cikis: "İstanbul", varis: "Manisa", tip: "Tır", adet: 1 },
  { cikis: "İstanbul", varis: "Balıkesir", tip: "Tır", adet: 1 },
  { cikis: "İstanbul", varis: "Tekirdağ", tip: "Tır", adet: 1 },
  { cikis: "Kocaeli", varis: "İstanbul", tip: "Tır", adet: 1 },
  { cikis: "Kocaeli", varis: "Tekirdağ", tip: "Tır", adet: 1 },
  { cikis: "Yalova", varis: "Eskişehir", tip: "Kamyon", adet: 1 },
  { cikis: "Kocaeli", varis: "Balıkesir", tip: "Kamyon", adet: 1 },
  { cikis: "Kocaeli", varis: "Eskişehir", tip: "Kamyon", adet: 1 },
  { cikis: "Yalova", varis: "Tekirdağ", tip: "Kamyon", adet: 1 }
];

// --- 3. YARDIMCI GÖREV FONSİYONLARI ---
function parseDesi(val: string): number {
  if (!val) return 0;
  const sanitized = val.replace(/"/g, "").replace(/,/g, ".").trim();
  const num = parseFloat(sanitized);
  return isNaN(num) ? 0 : num;
}

// Split CSV lines accurately respecting quotes
function parseCsvLine(line: string): string[] {
  const result: string[] = [];
  let current = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim());
      current = "";
    } else {
      current += char;
    }
  }
  result.push(current.trim());
  return result;
}

// --- 4. TAHMİN MOTORU (DEMAND FORECASTING) ---
function buildDemandForecast(): any[] {
  const csvPath = path.join(process.cwd(), "src", "data", "desi_talep.csv");
  if (!fs.existsSync(csvPath)) {
    throw new Error(`Tarihsel kargo talep verisi bulunamadı: ${csvPath}`);
  }

  console.log("Tarihsel talep verileri yüklenip Node JS ortamında parse ediliyor...");
  const csvContent = fs.readFileSync(csvPath, "utf-8");
  const rows = csvContent.split("\n").map(r => r.trim()).filter(r => r.length > 0);

  // Parse header
  const header = parseCsvLine(rows[0]);
  const originIdx = header.indexOf("Çıkış Transfer Merkezi");
  const destIdx = header.indexOf("Varış Transfer Merkezi");
  const dateIdx = header.indexOf("Tarih");
  const desiIdx = header.indexOf("Toplam Desi");

  // Rota bazlı istatistikleri ve haftalık trendleri çıkartalım
  const routeStats: { [key: string]: { totalDesi: number; count: number; weekdayTotals: number[]; weekdayCounts: number[] } } = {};

  for (let i = 1; i < rows.length; i++) {
    const parts = parseCsvLine(rows[i]);
    if (parts.length < header.length) continue;

    const origin = parts[originIdx];
    const dest = parts[destIdx];
    const dateStr = parts[dateIdx];
    const desi = parseDesi(parts[desiIdx]);

    const date = new Date(dateStr);
    if (isNaN(date.getTime())) continue;

    const routeKey = `${origin}->${dest}`;
    if (!routeStats[routeKey]) {
      routeStats[routeKey] = {
        totalDesi: 0,
        count: 0,
        weekdayTotals: Array(7).fill(0),
        weekdayCounts: Array(7).fill(0)
      };
    }

    const stats = routeStats[routeKey];
    stats.totalDesi += desi;
    stats.count += 1;

    const weekday = date.getUTCDay(); // 0 is Sunday, 1 is Monday ... 6 is Saturday (UTC)
    stats.weekdayTotals[weekday] += desi;
    stats.weekdayCounts[weekday] += 1;
  }

  // 11 - 17 Mayıs 2026 zaman serisi projeksiyonu
  const forecastRecords: any[] = [];
  const forecastDays = [
    "2026-05-11", // Pazartesi
    "2026-05-12", // Salı
    "2026-05-13", // Çarşamba
    "2026-05-14", // Perşembe
    "2026-05-15", // Cuma
    "2026-05-16", // Cumartesi
    "2026-05-17"  // Pazar
  ];

  // Organik büyüme / trend çarpanı: +%4.2 (trend_factor = 1.042)
  const trendFactor = 1.042;

  console.log("Haftalık döngülere (seasonality) ve trend katsayısına göre tahminler yapılıyor...");
  
  for (const dateStr of forecastDays) {
    const dayObj = new Date(dateStr);
    const weekday = dayObj.getUTCDay();

    for (const c1 of CITIES) {
      for (const c2 of CITIES) {
        if (c1 === c2) continue;

        const routeKey = `${c1}->${c2}`;
        let predictedDesi = 0;

        if (routeStats[routeKey]) {
          const stats = routeStats[routeKey];
          const avgDesi = stats.totalDesi / stats.count;

          // Haftanın bu günü için çarpan
          const dayAvg = stats.weekdayCounts[weekday] > 0 
            ? stats.weekdayTotals[weekday] / stats.weekdayCounts[weekday] 
            : avgDesi;
          
          const factor = avgDesi > 0 ? (dayAvg / avgDesi) : 1.0;

          predictedDesi = avgDesi * factor * trendFactor;
        }

        // Düşük kargo gürültüsünü engellemek için filtreleme yapalım (Zero-Imputation)
        if (predictedDesi < 5.0) {
          predictedDesi = 0.0;
        } else {
          predictedDesi = Math.round(predictedDesi * 100) / 100;
        }

        forecastRecords.push({
          "Tarih": dateStr,
          "Çıkış TM": c1,
          "Varış TM": c2,
          "Tahmin Edilen Desi": predictedDesi
        });
      }
    }
  }

  console.log(`Toplam ${forecastRecords.length} adet rota-gün tahmini yapıldı.`);
  return forecastRecords;
}

// --- 5. YOL-ÜSTÜ (ROUTE CONSOLIDATION) HEURISTICS ---
function getOnTheWayCities(origin: string, destination: string, maxTolerance = 1.20): string[] {
  const directDist = DISTANCES[origin][destination];
  if (directDist === 0) return [];

  const candidates: { city: string; detour: number }[] = [];
  for (const city of CITIES) {
    if (city !== origin && city !== destination) {
      const detourDist = DISTANCES[origin][city] + DISTANCES[city][destination];
      if (detourDist <= directDist * maxTolerance) {
        candidates.push({ city, detour: detourDist });
      }
    }
  }

  candidates.sort((a, b) => a.detour - b.detour);
  return candidates.map(c => c.city);
}

// --- 6. SPOT ARAÇ KOMBİNASYONU OPTİMİZASYON SOLVER ---
interface SpotAllocation {
  "Araç Tipi": string;
  "Atanan Desi": number;
  "Maliyet": number;
}

function solveSpotVehiclesForRoute(demand: number, distance: number): { combo: SpotAllocation[]; cost: number } {
  if (demand <= 0) return { combo: [], cost: 0 };

  const spotTypes = ["Tır", "Kamyon"];
  const costs: { [key: string]: number } = {};

  for (const t of spotTypes) {
    const vInfo = VEHICLES[t];
    costs[t] = vInfo.spot_sabit + (distance * vInfo.spot_km);
  }

  let bestCost = Infinity;
  let bestCombination: SpotAllocation[] = [];

  function search(remainingDemand: number, currentCombo: SpotAllocation[], currentCost: number) {
    if (currentCost >= bestCost) return;

    if (remainingDemand <= 0) {
      if (currentCost < bestCost) {
        bestCost = currentCost;
        bestCombination = JSON.parse(JSON.stringify(currentCombo));
      }
      return;
    }

    for (const t of spotTypes) {
      const vInfo = VEHICLES[t];
      const cap = vInfo.kapasite;
      const minLoad = cap * vInfo.min_doluluk_oranı;

      let allocated = Math.min(remainingDemand, cap);
      if (allocated < minLoad) {
        allocated = minLoad; // Asgari doluluk sınırı %10'a çekilir
      }

      currentCombo.push({
        "Araç Tipi": `Spot ${t === "Tır" ? "TIR" : t}`,
        "Atanan Desi": Math.round(allocated * 100) / 100,
        "Maliyet": Math.round(costs[t] * 100) / 100
      });

      search(remainingDemand - allocated, currentCombo, currentCost + costs[t]);
      currentCombo.pop();
    }
  }

  search(demand, [], 0);
  return { combo: bestCombination, cost: bestCost };
}

// --- 7. NİHAİ PLANLAMA VE DAĞITIM ENTEGRASYONU ---
function optimizeLogistics(forecastRecords: any[]): { planningRecords: any[]; rentedCost: number; spotCost: number } {
  const planningRecords: any[] = [];
  const dates = Array.from(new Set(forecastRecords.map(r => r["Tarih"]))).sort();

  console.log("\nLojistik anahat operasyonel planlaması başlatılıyor...");

  let totalRentedCost = 0.0;
  let totalSpotCost = 0.0;

  for (const date of dates) {
    console.log(`Tarih: ${date} optimize ediliyor...`);

    // Günlük talep haritasını kuralım: demandMap[origin][dest]
    const demandMap: { [key: string]: { [key: string]: number } } = {};
    for (const c1 of CITIES) {
      demandMap[c1] = {};
      for (const c2 of CITIES) {
        demandMap[c1][c2] = 0.0;
      }
    }

    forecastRecords
      .filter(r => r["Tarih"] === date)
      .forEach(r => {
        demandMap[r["Çıkış TM"]][r["Varış TM"]] = r["Tahmin Edilen Desi"];
      });

    // 1. Adım: Mevcut Kiralık Araçları Tanımla (Batık Maliyetli)
    const rentedVehicles: any[] = [];
    for (const assign of KİRALIK_FİLO) {
      for (let a = 0; a < assign.adet; a++) {
        rentedVehicles.push({
          cikis: assign.cikis,
          varis: assign.varis,
          tip: assign.tip,
          kapasite: VEHICLES[assign.tip].kapasite,
          kalan_kapasite: VEHICLES[assign.tip].kapasite,
          sabit_cost: VEHICLES[assign.tip].kiralık_sabit,
          km_oran: VEHICLES[assign.tip].kiralık_km,
          aktarma_rotası: [assign.cikis, assign.varis],
          atanan_hacimler: [] as any[]
        });
      }
    }

    // 2. Adım: Kiralık araçlarla doğrudan talepleri (A -> B) yükleyelim
    for (const v of rentedVehicles) {
      const origin = v.cikis;
      const dest = v.varis;
      const dem = demandMap[origin][dest];

      if (dem > 0) {
        const loaded = Math.min(dem, v.kalan_kapasite);
        demandMap[origin][dest] -= loaded;
        v.kalan_kapasite -= loaded;
        v.atanan_hacimler.push({
          cikis: origin,
          varis: dest,
          desi: loaded
        });
      }
    }

    // 3. Adım: Yol Üstü Konsolidasyon Heuristiği (Boş yer kaldıysa C -> B yönünü topla)
    for (const v of rentedVehicles) {
      if (v.kalan_kapasite <= 100) continue;

      const origin = v.cikis;
      const dest = v.varis;

      const onTheWay = getOnTheWayCities(origin, dest, 1.20);
      for (const intermediateCity of onTheWay) {
        if (v.kalan_kapasite <= 50) break;

        const cToBDemand = demandMap[intermediateCity][dest];
        if (cToBDemand > 0) {
          const loaded = Math.min(cToBDemand, v.kalan_kapasite);
          demandMap[intermediateCity][dest] -= loaded;
          v.kalan_kapasite -= loaded;
          
          if (!v.aktarma_rotası.includes(intermediateCity)) {
            v.aktarma_rotası.splice(1, 0, intermediateCity);
          }
          v.atanan_hacimler.push({
            cikis: intermediateCity,
            varis: dest,
            desi: loaded
          });
        }
      }
    }

    // 4. Adım: Kiralık Araçları Maliyetlendir ve Kaydet
    for (const v of rentedVehicles) {
      const toplamAtanan = v.atanan_hacimler.reduce((acc: number, item: any) => acc + item.desi, 0);
      let actualDistance = 0.0;
      if (toplamAtanan > 0) {
        actualDistance = DISTANCES[v.cikis][v.varis];
      }

      const totalCost = v.sabit_cost + (actualDistance * v.km_oran);
      totalRentedCost += totalCost;

      planningRecords.push({
        "Tarih": date,
        "Araç Tipi": `Kiralık ${v.tip === "Tır" ? "TIR" : v.tip}`,
        "Çıkış TM": v.cikis,
        "Varış TM": v.varis,
        "Atanan Desi": Math.round(toplamAtanan * 100) / 100,
        "Maliyet": Math.round(totalCost * 100) / 100,
        "Mesafe_KM": Math.round(actualDistance * 10) / 10,
        "Yol_Üstü_TM": v.aktarma_rotası.length > 2 ? v.aktarma_rotası.slice(1, -1).join(", ") : "Yok"
      });
    }

    // 5. Adım: Kalan Artık Talepler / Spot Seferler (Uğrama Destekli)
    for (const c1 of CITIES) {
      for (const c2 of CITIES) {
        if (c1 === c2) continue;

        const residualDemand = demandMap[c1][c2];
        if (residualDemand > 0) {
          const distance = DISTANCES[c1][c2];
          const { combo, cost } = solveSpotVehiclesForRoute(residualDemand, distance);

          totalSpotCost += cost;
          for (const spotVeh of combo) {
            const capacity = spotVeh["Araç Tipi"].includes("TIR") ? 7000 : 3000;
            let loadedDesi = spotVeh["Atanan Desi"];
            let leftoverCapacity = capacity - loadedDesi;
            const aktarmaRotası = [c1, c2];

            // Eğer araçta boş yer kaldıysa, yol üstü TM'lerden aynı varış noktasına (c2) olan yükleri de toplayalım
            if (leftoverCapacity > 50) {
              const onTheWay = getOnTheWayCities(c1, c2, 1.20);
              for (const intermediateCity of onTheWay) {
                if (leftoverCapacity <= 50) break;

                const cToBDemand = demandMap[intermediateCity][c2];
                if (cToBDemand > 0) {
                  const extraLoaded = Math.min(cToBDemand, leftoverCapacity);
                  demandMap[intermediateCity][c2] -= extraLoaded;
                  leftoverCapacity -= extraLoaded;
                  loadedDesi += extraLoaded;

                  if (!aktarmaRotası.includes(intermediateCity)) {
                    aktarmaRotası.splice(1, 0, intermediateCity);
                  }
                }
              }
            }

            planningRecords.push({
              "Tarih": date,
              "Araç Tipi": spotVeh["Araç Tipi"],
              "Çıkış TM": c1,
              "Varış TM": c2,
              "Atanan Desi": Math.round(loadedDesi * 100) / 100,
              "Maliyet": spotVeh["Maliyet"],
              "Mesafe_KM": Math.round(distance * 10) / 10,
              "Yol_Üstü_TM": aktarmaRotası.length > 2 ? aktarmaRotası.slice(1, -1).join(", ") : "Yok"
            });
          }
          // Doğrudan c1 -> c2 bacağı için spot seviyesinde planlama yapıldığından bu değeri sıfırlıyoruz
          demandMap[c1][c2] = 0.0;
        }
      }
    }
  }

  console.log(`\nLojistik Planlama Tamamlandı.`);
  console.log(`Kiralık Filo Toplamı: ${totalRentedCost.toLocaleString("tr-TR")} TL`);
  console.log(`Spot Filo Toplamı:    ${totalSpotCost.toLocaleString("tr-TR")} TL`);

  return { planningRecords, rentedCost: totalRentedCost, spotCost: totalSpotCost };
}

// --- 8. ANAMODÜL EXECUTION & EXCEL EXPORT ---
function main() {
  const dataDir = path.join(process.cwd(), "src", "data");
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
  }

  // 1. Tahminleri üretelim
  const forecastRecords = buildDemandForecast();

  // Excel 1: tahmin_desi.xlsx (Sütunlar: Tarih, Çıkış TM, Varış TM, Tahmin Edilen Desi)
  const tahminSheetData = forecastRecords
    .filter(r => r["Tahmin Edilen Desi"] > 0)
    .map(r => ({
      "Tarih": r["Tarih"],
      "Çıkış TM": r["Çıkış TM"],
      "Varış TM": r["Varış TM"],
      "Tahmin Edilen Desi": r["Tahmin Edilen Desi"]
    }));

  const wbTahmin = XLSX.utils.book_new();
  const wsTahmin = XLSX.utils.json_to_sheet(tahminSheetData);
  XLSX.utils.book_append_sheet(wbTahmin, wsTahmin, "Tahmin Edilen Desiler");
  XLSX.writeFile(wbTahmin, path.join(dataDir, "tahmin_desi.xlsx"));
  console.log("[OK] tahmin_desi.xlsx başarıyla yazıldı.");

  // 2. Planlama ve Optimizasyon
  const { planningRecords, rentedCost, spotCost } = optimizeLogistics(forecastRecords);

  // Excel 2: arac_planlama.xlsx (Sütunlar: Tarih, Araç Tipi, Çıkış TM, Varış TM, Atanan Desi, Maliyet)
  const planSheetData = planningRecords
    .filter(r => r["Atanan Desi"] > 0)
    .map(r => ({
      "Tarih": r["Tarih"],
      "Araç Tipi": r["Araç Tipi"],
      "Çıkış TM": r["Çıkış TM"],
      "Varış TM": r["Varış TM"],
      "Atanan Desi": r["Atanan Desi"],
      "Maliyet": r["Maliyet"]
    }));

  const wbPlan = XLSX.utils.book_new();
  const wsPlan = XLSX.utils.json_to_sheet(planSheetData);
  XLSX.utils.book_append_sheet(wbPlan, wsPlan, "Araç Planlama");
  XLSX.writeFile(wbPlan, path.join(dataDir, "arac_planlama.xlsx"));
  console.log("[OK] arac_planlama.xlsx başarıyla yazıldı.");

  // 3. Web Dashboard için summary_dashboard.json çıktısı
  const totalPredict = forecastRecords.reduce((acc, r) => acc + r["Tahmin Edilen Desi"], 0);
  const totalShip = planningRecords.reduce((acc, r) => acc + r["Atanan Desi"], 0);

  const dashboardPayload: any = {
    status: "success",
    generated_at: new Date().toISOString().replace("T", " ").substring(0, 19),
    kpis: {
      total_rented_cost: Math.round(rentedCost * 100) / 100,
      total_spot_cost: Math.round(spotCost * 100) / 100,
      total_cost: Math.round((rentedCost + spotCost) * 100) / 100,
      total_predicted_desi: Math.round(totalPredict * 100) / 100,
      total_shipped_desi: Math.round(totalShip * 100) / 100,
      total_vehicles_sent: planningRecords.length,
      total_routes_optimized: forecastRecords.filter(r => r["Tahmin Edilen Desi"] > 0).length
    },
    daily_summary: [] as any[],
    vehicle_distribution: {} as any,
    city_stats: [] as any[],
    distances: DISTANCES
  };

  // Günlük Özetler
  const daysMap: { [key: string]: { rented_cost: number; spot_cost: number; total_cost: number; desi: number; vehicles: number } } = {};
  for (const r of planningRecords) {
    const d = r["Tarih"];
    if (!daysMap[d]) {
      daysMap[d] = { rented_cost: 0, spot_cost: 0, total_cost: 0, desi: 0, vehicles: 0 };
    }
    const m = daysMap[d];
    m.vehicles += 1;
    m.desi += r["Atanan Desi"];
    m.total_cost += r["Maliyet"];
    if (r["Araç Tipi"].startsWith("Kiralık")) {
      m.rented_cost += r["Maliyet"];
    } else {
      m.spot_cost += r["Maliyet"];
    }
  }

  for (const [date, m] of Object.entries(daysMap)) {
    dashboardPayload.daily_summary.push({
      date,
      rented_cost: Math.round(m.rented_cost * 100) / 100,
      spot_cost: Math.round(m.spot_cost * 100) / 100,
      total_cost: Math.round(m.total_cost * 100) / 100,
      desi: Math.round(m.desi * 100) / 100,
      vehicles: m.vehicles
    });
  }

  dashboardPayload.daily_summary.sort((a: any, b: any) => a.date.localeCompare(b.date));

  // Araç Dağılımı
  for (const r of planningRecords) {
    const t = r["Araç Tipi"];
    if (!dashboardPayload.vehicle_distribution[t]) {
      dashboardPayload.vehicle_distribution[t] = { count: 0, cost: 0 };
    }
    dashboardPayload.vehicle_distribution[t].count += 1;
    dashboardPayload.vehicle_distribution[t].cost += r["Maliyet"];
  }

  for (const t of Object.keys(dashboardPayload.vehicle_distribution)) {
    dashboardPayload.vehicle_distribution[t].cost = Math.round(dashboardPayload.vehicle_distribution[t].cost * 100) / 100;
  }

  // Şehir Bazlı İstatistikler
  for (const city of CITIES) {
    const outs = forecastRecords
      .filter(r => r["Çıkış TM"] === city)
      .reduce((acc, r) => acc + r["Tahmin Edilen Desi"], 0);
    const ins = forecastRecords
      .filter(r => r["Varış TM"] === city)
      .reduce((acc, r) => acc + r["Tahmin Edilen Desi"], 0);

    if (outs > 0 || ins > 0) {
      dashboardPayload.city_stats.push({
        city,
        outbound_desi: Math.round(outs * 100) / 100,
        inbound_desi: Math.round(ins * 100) / 100,
        lat: COORDS[city][0],
        lng: COORDS[city][1]
      });
    }
  }

  fs.writeFileSync(
    path.join(dataDir, "summary_dashboard.json"),
    JSON.stringify(dashboardPayload, null, 2),
    "utf-8"
  );
  console.log("[OK] summary_dashboard.json başarıyla yazıldı.");
}

main();
