import { useState, useEffect, useRef } from "react";
import { 
  Play, 
  Download, 
  Truck, 
  TrendingUp, 
  MapPin, 
  RotateCcw, 
  FileText, 
  CheckCircle, 
  Calendar, 
  DollarSign, 
  Activity, 
  ChevronRight,
  TrendingDown,
  Layers,
  ChevronDown,
  ChevronUp
} from "lucide-react";

interface KPI {
  total_rented_cost: number;
  total_spot_cost: number;
  total_cost: number;
  total_predicted_desi: number;
  total_shipped_desi: number;
  total_vehicles_sent: number;
  total_routes_optimized: number;
}

interface DailySummary {
  date: string;
  rented_cost: number;
  spot_cost: number;
  total_cost: number;
  desi: number;
  vehicles: number;
}

interface VehicleInfo {
  count: number;
  cost: number;
}

interface CityStat {
  city: string;
  outbound_desi: number;
  inbound_desi: number;
  lat: number;
  lng: number;
}

interface DashboardData {
  status: string;
  generated_at: string;
  kpis: KPI;
  daily_summary: DailySummary[];
  vehicle_distribution: { [key: string]: VehicleInfo };
  city_stats: CityStat[];
}

export default function App() {
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [data, setData] = useState<DashboardData | null>(null);
  const [notRunYet, setNotRunYet] = useState(false);
  const [selectedCity, setSelectedCity] = useState<CityStat | null>(null);
  const [isConsoleExpanded, setIsConsoleExpanded] = useState(false);
  
  const consoleEndRef = useRef<HTMLDivElement>(null);

  // Sayfa yüklendiğinde mevcut veriyi çekmeyi dene
  useEffect(() => {
    fetchSummary();
  }, []);

  useEffect(() => {
    if (consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs]);

  const fetchSummary = async () => {
    try {
      const res = await fetch("/api/dashboard-summary");
      if (res.status === 200) {
        const payload = await res.json();
        setData(payload);
        setNotRunYet(false);
      } else if (res.status === 404) {
        setNotRunYet(true);
      }
    } catch (err) {
      console.error("Dashboard özeti yüklenirken hata oluştu:", err);
    }
  };

  const handleRunPipeline = async () => {
    setIsRunning(true);
    setLogs(["[SİSTEM] TEKNOFEST 2026 Yapay Zeka Destekli Lojistik Anahat Optimizasyon Simülatörü başlatılıyor...", "[SİSTEM] Bağımlılıklar doğrulanıyor, Python çekirdeği yükleniyor..."]);
    
    try {
      const res = await fetch("/api/run-pipeline", { method: "POST" });
      const result = await res.json();
      
      if (result.status === "success") {
        const consoleOutputs = result.stdout ? result.stdout.split("\n") : [];
        setLogs(prev => [...prev, ...consoleOutputs, "[Başarı] Çekirdek optimizasyon ve zaman serisi tamamlandı. Excel çıktıları hazırlandı."]);
        await fetchSummary();
      } else {
        const errOutputs = result.stderr ? result.stderr.split("\n") : [];
        setLogs(prev => [...prev, `[Hata] Optimizasyon başarısız oldu: ${result.message}`, ...errOutputs]);
      }
    } catch (err: any) {
      setLogs(prev => [...prev, `[Hata] Ağ bağlantısında hata oluştu: ${err.message}`]);
    } finally {
      setIsRunning(false);
    }
  };

  const handleDownload = async (endpoint: string, filename: string) => {
    try {
      const res = await fetch(endpoint);
      if (!res.ok) throw new Error("Excel dosyası bulunamadı. Lütfen önce simülasyonu çalıştırın.");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error("İndirme hatası:", err);
      setLogs(prev => [...prev, `[Hata] İndirme hatası: ${err.message}`]);
    }
  };

  // Coğrafi Koordinat Normalize Edilmiş Nokta bulma (Türkiye Haritası Çizimi)
  // Enlem sınırları: ~36 to 42, Boylam sınırları: ~26 to 45
  const getMapCoords = (lat: number, lng: number) => {
    const minLat = 35.5;
    const maxLat = 42.5;
    const minLng = 25.5;
    const maxLng = 45.0;

    const x = ((lng - minLng) / (maxLng - minLng)) * 100;
    const y = 100 - ((lat - minLat) / (maxLat - minLat)) * 100; // Enlemi ters çevirerek SVG koordinatına uyduruyoruz

    return { x: `${x}%`, y: `${y}%` };
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-teal-500 selection:text-slate-950">
      {/* ÜST LOGO & BANNER */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="bg-teal-500 text-slate-950 p-2.5 rounded-xl font-bold tracking-wider text-sm flex items-center gap-1.5 shadow-lg shadow-teal-500/20">
              <Truck className="w-5 h-5 animate-pulse" />
              <span>TEKNOFEST 2026</span>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-slate-200 tracking-tight">Hepsiburada Lojistik Optimizasyonu</h1>
              <p className="text-xs text-slate-400">Yapay Zeka Destekli Anahat Planlama Simülatörü</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <button 
              onClick={handleRunPipeline}
              disabled={isRunning}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium transition-all duration-200 shadow-md ${
                isRunning 
                  ? "bg-slate-800 text-slate-400 cursor-not-allowed" 
                  : "bg-teal-400 text-slate-950 hover:bg-teal-300 hover:shadow-teal-400/20 cursor-pointer"
              }`}
            >
              {isRunning ? (
                <>
                  <RotateCcw className="w-4 h-4 animate-spin" />
                  <span>İşleniyor...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-slate-950" />
                  <span>Simülatörü Çalıştır</span>
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        
        {/* LİVE METRİK / KPI ALANI */}
        {data && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 animate-fade-in">
            <div className="bg-slate-900/70 border border-slate-800 p-6 rounded-2xl relative overflow-hidden group">
              <div className="absolute right-4 top-4 bg-teal-500/10 p-3 rounded-xl text-teal-400 group-hover:scale-110 transition-transform duration-200">
                <DollarSign className="w-6 h-6" />
              </div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-widest">Toplam Maliyet</p>
              <h3 className="text-3xl font-bold text-slate-100 mt-2 font-mono">
                {data.kpis.total_cost.toLocaleString("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} <span className="text-sm font-sans font-medium text-teal-400">TL</span>
              </h3>
              <div className="mt-4 flex items-center gap-2 text-xs text-slate-400 border-t border-slate-800/60 pt-3">
                <span className="text-teal-400 font-semibold font-mono">
                  {((data.kpis.total_rented_cost / data.kpis.total_cost) * 100).toFixed(0)}%
                </span>
                <span>Kiralık batık maliyet payı</span>
              </div>
            </div>

            <div className="bg-slate-900/70 border border-slate-800 p-6 rounded-2xl relative overflow-hidden group">
              <div className="absolute right-4 top-4 bg-blue-500/10 p-3 rounded-xl text-blue-400 group-hover:scale-110 transition-transform duration-200">
                <TrendingUp className="w-6 h-6" />
              </div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-widest">Tahmini Toplam Desi</p>
              <h3 className="text-3xl font-bold text-slate-100 mt-2 font-mono">
                {data.kpis.total_predicted_desi.toLocaleString("tr-TR")} <span className="text-sm font-sans font-medium text-blue-400">Desi</span>
              </h3>
              <div className="mt-4 flex items-center gap-2 text-xs text-slate-400 border-t border-slate-800/60 pt-3">
                <span className="text-blue-400 font-semibold">11 - 17 Mayıs</span>
                <span>Tahmin Dönemi</span>
              </div>
            </div>

            <div className="bg-slate-900/70 border border-slate-800 p-6 rounded-2xl relative overflow-hidden group">
              <div className="absolute right-4 top-4 bg-indigo-500/10 p-3 rounded-xl text-indigo-400 group-hover:scale-110 transition-transform duration-200">
                <Truck className="w-6 h-6" />
              </div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-widest">Planlanan Sefer Sayısı</p>
              <h3 className="text-3xl font-bold text-slate-100 mt-2 font-mono">
                {data.kpis.total_vehicles_sent} <span className="text-sm font-sans font-medium text-indigo-400">Araç</span>
              </h3>
              <div className="mt-4 flex items-center gap-2 text-xs text-slate-400 border-t border-slate-800/60 pt-3">
                <span className="text-indigo-400 font-semibold">{(data.kpis.total_shipped_desi / data.kpis.total_vehicles_sent).toFixed(0)}</span>
                <span>Araç başına ortalama desi</span>
              </div>
            </div>

            <div className="bg-slate-900/70 border border-slate-800 p-6 rounded-2xl relative overflow-hidden group">
              <div className="absolute right-4 top-4 bg-emerald-500/10 p-3 rounded-xl text-emerald-400 group-hover:scale-110 transition-transform duration-200">
                <Layers className="w-6 h-6" />
              </div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-widest">Optimize Edilen Hat</p>
              <h3 className="text-3xl font-bold text-slate-100 mt-2 font-mono">
                {data.kpis.total_routes_optimized} <span className="text-sm font-sans font-medium text-emerald-400">Hat</span>
              </h3>
              <div className="mt-4 flex items-center gap-2 text-xs text-slate-400 border-t border-slate-800/60 pt-3">
                <span className="text-emerald-400 font-semibold">Haversine</span>
                <span>Uzaklık Modeli Entegrasyonu</span>
              </div>
            </div>
          </div>
        )}

        {/* NOT RUN YET / BOŞ EKRAN UYARISI */}
        {notRunYet && !isRunning && (
          <div className="bg-slate-900/40 border border-dashed border-slate-800 rounded-3xl p-16 text-center max-w-2xl mx-auto space-y-6">
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl w-fit mx-auto text-teal-400">
              <Activity className="w-10 h-10 animate-pulse" />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-semibold">Simülasyon Deformasyonu Tespit Edildi</h2>
              <p className="text-slate-400 text-sm max-w-md mx-auto">
                Modelinizin doğrulaması henüz yapılmadı. Sağ üst köşedeki düğmeyi kullanarak Python makine öğrenmesi ve optimizasyon motorunu çalıştırabilirsiniz.
              </p>
            </div>
            <button 
              onClick={handleRunPipeline}
              className="px-6 py-3 bg-teal-400 text-slate-950 font-semibold rounded-xl hover:bg-teal-300 transition-colors shadow-lg shadow-teal-500/10 inline-flex items-center gap-2"
            >
              <Play className="w-4 h-4 fill-slate-950" />
              <span>Süreci Başlat</span>
            </button>
          </div>
        )}

        {/* LİVE TERMİNAL & LOGS */}
        {(isRunning || logs.length > 0) && (
          <div className="bg-slate-900/80 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl">
            <div className="px-6 py-4 bg-slate-900 border-b border-slate-800/60 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-2.5 h-2.5 rounded-full bg-teal-400 animate-pulse"></div>
                <span className="text-sm font-semibold text-slate-200">Python Lojistik Optimizasyon İşlem Konsolu</span>
              </div>
              <button 
                onClick={() => setIsConsoleExpanded(!isConsoleExpanded)}
                className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 cursor-pointer transition-colors"
              >
                <span>{isConsoleExpanded ? "Küçült" : "Genişlet"}</span>
                {isConsoleExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>
            </div>
            <div className={`p-6 font-mono text-xs text-slate-300 bg-black/60 overflow-y-auto space-y-1.5 transition-all duration-300 ${
              isConsoleExpanded ? "max-h-96" : "max-h-40"
            }`}>
              {logs.map((log, index) => (
                <div key={index} className={`${
                  log.startsWith("[Hata]") ? "text-rose-400" : 
                  log.startsWith("[SİSTEM]") ? "text-cyan-400/85" : 
                  log.startsWith("[Başarı]") || log.startsWith("[OK]") ? "text-emerald-400" : "text-slate-300"
                }`}>
                  <span className="text-slate-600 select-none mr-2 font-sans">[{index + 1}]</span>
                  {log}
                </div>
              ))}
              <div ref={consoleEndRef} />
            </div>
          </div>
        )}

        {/* VERİ GÖRSELLEŞTİRME & HARİTA ALANI */}
        {data && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* SOL TARAF: İNDİRME ALANI & ANALİZLER */}
            <div className="lg:col-span-4 space-y-8">
              {/* EXCEL ÇIKTILARI (TESLİMAT ŞABLONLARI) */}
              <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-6">
                <div className="space-y-1">
                  <h3 className="font-semibold text-slate-200 flex items-center gap-2">
                    <FileText className="w-4 h-4 text-teal-400" />
                    <span>Yarışma Çıktı Dosyaları</span>
                  </h3>
                  <p className="text-xs text-slate-400">Teknik değerlendirmeden tam puan almak üzere şablonu çizilmiş Excel tabloları:</p>
                </div>
                
                <div className="space-y-4">
                  {/* 1. Tahmin Desi Dosyası (Sütunlar: Tarih, Çıkış TM, Varış TM, Tahmin Edilen Desi) */}
                  <button 
                    onClick={() => handleDownload("/api/download/tahmin-desi", "tahmin_desi.xlsx")}
                    className="w-full flex items-center justify-between p-4 bg-slate-950 hover:bg-slate-950/80 border border-slate-800 rounded-2xl transition-all duration-200 group hover:border-teal-500/40 cursor-pointer"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-teal-400/10 text-teal-400 rounded-lg">
                        <TrendingUp className="w-5 h-5" />
                      </div>
                      <div className="text-left">
                        <h4 className="text-sm font-medium text-slate-200 group-hover:text-teal-400 transition-colors">tahmin_desi.xlsx</h4>
                        <p className="text-3xs text-slate-500">4 Sütun: Tarih, Çıkış, Varış, Tahmin edilen Desi</p>
                      </div>
                    </div>
                    <Download className="w-4 h-4 text-slate-500 group-hover:text-teal-400 transition-colors" />
                  </button>

                  {/* 2. Araç Planlama Dosyası (Sütunlar: Tarih, Araç Tipi, Çıkış TM, Varış TM, Atanan Desi, Maliyet) */}
                  <button 
                    onClick={() => handleDownload("/api/download/arac-planlama", "arac_planlama.xlsx")}
                    className="w-full flex items-center justify-between p-4 bg-slate-950 hover:bg-slate-950/80 border border-slate-800 rounded-2xl transition-all duration-200 group hover:border-teal-500/40 cursor-pointer"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-indigo-400/10 text-indigo-400 rounded-lg">
                        <Truck className="w-5 h-5" />
                      </div>
                      <div className="text-left">
                        <h4 className="text-sm font-medium text-slate-200 group-hover:text-indigo-400 transition-colors">arac_planlama.xlsx</h4>
                        <p className="text-3xs text-slate-500">6 Sütun: Tarih, Araç Tipi, Çıkış, Varış, Desi, Maliyet</p>
                      </div>
                    </div>
                    <Download className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 transition-colors" />
                  </button>
                </div>
              </div>

              {/* FİLO DAĞILIMI VE MALİYET KİŞİSELLEŞTİRME */}
              <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-6">
                <div className="space-y-1">
                  <h3 className="font-semibold text-slate-200 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-teal-400" />
                    <span>Araç Türü ve Dağılım Payı</span>
                  </h3>
                  <p className="text-xs text-slate-400">Optimizasyonda kullanılan araç mülkiyeti ve sayılarının analizi:</p>
                </div>
                
                <div className="space-y-4">
                  {(Object.entries(data.vehicle_distribution) as [string, VehicleInfo][]).map(([vName, info]) => (
                    <div key={vName} className="p-4 bg-slate-950 border border-slate-800/80 rounded-2xl space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium text-slate-200">{vName}</span>
                        <span className="text-slate-400 text-xs font-mono">{info.count} Sefer</span>
                      </div>
                      <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
                        <div 
                          className="bg-teal-400 h-full rounded-full transition-all duration-300"
                          style={{ width: `${Math.min((info.count / data.kpis.total_vehicles_sent) * 100, 100)}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-[11px] text-slate-500">
                        <span>Lojistik Maliyet Payı:</span>
                        <span className="font-mono text-teal-400">{info.cost.toLocaleString("tr-TR")} TL</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* SAĞ TARAF: COĞRAFİ TÜRKİYE LOJİSTİK HARİTASI & INTERACTIVE STATS */}
            <div className="lg:col-span-8 space-y-8">
              {/* HARESINE ETKİLEŞİMLİ TÜRKİYE TM MATRİS HARİTASI */}
              <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <h3 className="font-semibold text-slate-200 flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-teal-400" />
                      <span>Transfer Merkezleri (TM) Küresel Koordinat Ağ Topolojisi</span>
                    </h3>
                    <p className="text-xs text-slate-400">Haversine formülüyle mesafeleri hesaplanan 18 Transfer Merkezi:</p>
                  </div>
                </div>

                {/* INTERACTIVE HARİTA CANVAS ALANI (TÜRKİYE PROJEKSİYONU) */}
                <div className="relative border border-slate-800/80 bg-slate-950/70 rounded-2xl h-96 overflow-hidden flex items-center justify-center group">
                  <div className="absolute inset-0 opacity-15 select-none pointer-events-none bg-[radial-gradient(#1e293b_1.5px,transparent_1px)] [background-size:24px_24px]"></div>
                  
                  {/* Nodes (Şehirler) */}
                  <div className="absolute inset-0">
                    <svg className="w-full h-full absolute inset-0 pointer-events-none">
                      {/* Harita çizgileri (Seçilen şehirle diğer şehirler arasındaki mesafeleri çizmek) */}
                      {selectedCity && data.city_stats.map((c) => {
                        if (c.city === selectedCity.city) return null;
                        const start = getMapCoords(selectedCity.lat, selectedCity.lng);
                        const end = getMapCoords(c.lat, c.lng);
                        return (
                          <g key={c.city}>
                            <line 
                              x1={start.x} 
                              y1={start.y} 
                              x2={end.x} 
                              y2={end.y} 
                              className="stroke-teal-500/25 stroke-1" 
                              strokeDasharray="4 4"
                            />
                            {/* Mesafe Etiketi orta noktaya */}
                            <text 
                              x={`calc((${start.x} + ${end.x}) / 2)`}
                              y={`calc((${start.y} + ${end.y}) / 2)`}
                              fill="#94a3b8" 
                              className="text-[9px] font-mono fill-slate-400"
                              textAnchor="middle"
                            >
                              {Math.round(data.distances[selectedCity.city][c.city])} km
                            </text>
                          </g>
                        );
                      })}
                    </svg>

                    {data.city_stats.map((c) => {
                      const pos = getMapCoords(c.lat, c.lng);
                      const isSelected = selectedCity?.city === c.city;
                      return (
                        <button
                          key={c.city}
                          onClick={() => setSelectedCity(isSelected ? null : c)}
                          style={{ left: pos.x, top: pos.y }}
                          className={`absolute w-4 h-4 -ml-2 -mt-2 rounded-full cursor-pointer flex items-center justify-center transition-all duration-200 ${
                            isSelected 
                              ? "bg-teal-400 shadow-lg shadow-teal-400/40 scale-125 z-40" 
                              : "bg-slate-800 border border-slate-700 hover:bg-teal-500/80 hover:scale-110 z-20"
                          }`}
                          title={`${c.city} (Çıkış: ${c.outbound_desi.toLocaleString()} Desi, Giriş: ${c.inbound_desi.toLocaleString()} Desi)`}
                        >
                          <div className={`rounded-full ${isSelected ? "w-2 h-2 bg-slate-950" : "w-1.5 h-1.5 bg-slate-400 group-hover:bg-slate-950"}`}></div>
                          <span className={`absolute top-5 left-1/2 -translate-x-1/2 px-2 py-0.5 whitespace-nowrap rounded bg-slate-900 border border-slate-800 text-[10px] drop-shadow-md text-slate-300 font-medium ${
                            isSelected ? "text-teal-400 border-teal-500/40 z-50 text-xs font-semibold" : ""
                          }`}>
                            {c.city}
                          </span>
                        </button>
                      );
                    })}
                  </div>

                  {/* Sol Altta Harita Legend Paneli */}
                  <div className="absolute bottom-4 left-4 bg-slate-900/90 border border-slate-800 p-4 rounded-xl text-3xs text-slate-400 space-y-2 z-35 backdrop-blur-sm shadow-md">
                    <p className="font-semibold text-slate-200 text-xs flex items-center gap-1">
                      <Layers className="w-3.5 h-3.5 text-teal-400" />
                      <span>İnteraktif Mesafe Gösterici</span>
                    </p>
                    <p>Mesafe ve topoğrafyaları görmek için haritadaki şehirlere tıklayın.</p>
                    <div className="flex gap-4 pt-1 font-mono text-[10px]">
                      <div className="flex items-center gap-1.5">
                        <div className="w-2.5 h-2.5 rounded bg-teal-400"></div>
                        <span>Seçili TM</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <div className="w-2.5 h-2.5 rounded bg-slate-800 border border-slate-700"></div>
                        <span>Aktif TM</span>
                      </div>
                    </div>
                  </div>

                  {/* Seçili Şehir Detay Bilgisi */}
                  {selectedCity && (
                    <div className="absolute top-4 right-4 bg-slate-900/95 border border-teal-500/30 p-4 rounded-xl text-xs text-slate-300 w-60 z-35 backdrop-blur-sm shadow-xl space-y-3">
                      <div className="flex justify-between items-center border-b border-slate-800/80 pb-2">
                        <h4 className="font-bold text-teal-400 text-sm flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5" />
                          <span>{selectedCity.city} TM</span>
                        </h4>
                        <button 
                          onClick={() => setSelectedCity(null)}
                          className="text-slate-500 hover:text-slate-300"
                        >
                          Kapat
                        </button>
                      </div>
                      <div className="space-y-1.5 text-slate-400 font-mono text-3xs">
                        <div className="flex justify-between">
                          <span>Koordinat:</span>
                          <span className="text-slate-200">{selectedCity.lat.toFixed(4)}N, {selectedCity.lng.toFixed(4)}E</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Tahmini Çıkış:</span>
                          <span className="text-teal-400 font-semibold">{selectedCity.outbound_desi.toLocaleString("tr-TR")} Desi</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Tahmini Giriş:</span>
                          <span className="text-blue-400 font-semibold">{selectedCity.inbound_desi.toLocaleString("tr-TR")} Desi</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* GÜNLÜK DESİ VE MALİYET GRAFİK PANORAMASI */}
              <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-6">
                <div className="space-y-1">
                  <h3 className="font-semibold text-slate-200 flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-teal-400" />
                    <span>Günlük Planlama & Toplam Harcama Grafiği</span>
                  </h3>
                  <p className="text-xs text-slate-400">11-17 Mayıs 2026 lojistik operasyonu günlük maliyet ve taşınan desi hacmi değişim grafiği:</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-7 gap-4 pt-2">
                  {data.daily_summary.map((day) => {
                    const maxCost = Math.max(...data.daily_summary.map(d => d.total_cost));
                    const maxDesi = Math.max(...data.daily_summary.map(d => d.desi));
                    const costHeight = maxCost > 0 ? (day.total_cost / maxCost) * 100 : 0;
                    const desiHeight = maxDesi > 0 ? (day.desi / maxDesi) * 100 : 0;

                    // Günü kısaltalım (Örn: 2026-05-11 -> Pazartesi)
                    const dateObj = new Date(day.date);
                    const dayLabels = ["Paz", "Pzt", "Sal", "Çar", "Per", "Cum", "Cmt"];
                    const dayLabel = dayLabels[dateObj.getDay()];

                    return (
                      <div key={day.date} className="bg-slate-950 border border-slate-800 p-4 rounded-2xl flex flex-col justify-between items-center text-center space-y-4">
                        {/* Çubuklar */}
                        <div className="w-full h-32 flex justify-center items-end gap-1.5 pt-2">
                          {/* Maliyet Çubuğu */}
                          <div 
                            style={{ height: `${costHeight}%` }}
                            className="bg-teal-500/85 w-3.5 rounded-t-sm transition-all duration-300 cursor-pointer"
                            title={`Maliyet: ${day.total_cost.toLocaleString()} TL`}
                          />
                          {/* Desi Çubuğu */}
                          <div 
                            style={{ height: `${desiHeight}%` }}
                            className="bg-blue-400/85 w-3.5 rounded-t-sm transition-all duration-300 cursor-pointer"
                            title={`Hacim: ${day.desi.toLocaleString()} Desi`}
                          />
                        </div>

                        {/* Gün Bilgisi */}
                        <div className="border-t border-slate-800/80 w-full pt-2.5">
                          <span className="text-[11px] font-semibold text-slate-300 block">{dayLabel}</span>
                          <span className="text-[9px] text-slate-500 block font-mono">{day.date.substring(5)}</span>
                        </div>

                        {/* Değer Bilgileri */}
                        <div className="space-y-1 font-mono text-[9px] w-full border-t border-slate-800/40 pt-2 text-slate-400">
                          <p className="text-teal-400">{(day.total_cost / 1000).toFixed(0)}k TL</p>
                          <p className="text-blue-400">{(day.desi / 1000).toFixed(0)}k Desi</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
