'use client';
import { useState } from 'react';

export default function Home() {
  const [formData, setFormData] = useState({ cikis: '', varis: '', tarih: '' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Form elemanlarını güncelleme
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // API İsteği
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('http://localhost:5000/api/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) throw new Error('API Hatası');
      
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError('Optimizasyon sırasında hata oluştu.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Kontrol Paneli (Form) */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h2 className="text-xl font-bold mb-4 text-gray-800">Rota Optimizasyon Planlayıcı</h2>
          <form onSubmit={handleSubmit} className="flex flex-col md:flex-row gap-4 items-end">
            <div className="flex-1 w-full">
              <label className="block text-sm font-medium text-gray-700 mb-1">Çıkış Şehri</label>
              <select name="cikis" onChange={handleChange} required className="w-full p-2 border rounded-md">
                <option value="">Seçiniz</option>
                <option value="İstanbul">İstanbul</option>
                <option value="Kocaeli">Kocaeli</option>
              </select>
            </div>
            
            <div className="flex-1 w-full">
              <label className="block text-sm font-medium text-gray-700 mb-1">Varış Şehri</label>
              <select name="varis" onChange={handleChange} required className="w-full p-2 border rounded-md">
                <option value="">Seçiniz</option>
                <option value="Eskişehir">Eskişehir</option>
                <option value="Ankara">Ankara</option>
              </select>
            </div>

            <div className="flex-1 w-full">
              <label className="block text-sm font-medium text-gray-700 mb-1">Tarih</label>
              <input type="date" name="tarih" onChange={handleChange} required className="w-full p-2 border rounded-md" />
            </div>

            <button 
              type="submit" 
              disabled={loading}
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-blue-300 w-full md:w-auto h-[42px] transition-colors">
              {loading ? 'Hesaplanıyor...' : 'Optimize Et'}
            </button>
          </form>
          {error && <p className="text-red-500 mt-4 text-sm">{error}</p>}
        </div>

        {/* Sonuç Ekranı */}
        {result && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Kart 1: Özet */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <h3 className="text-gray-500 text-sm font-medium">Toplam Maliyet</h3>
              <p className="text-3xl font-bold text-gray-900 mt-2">{result.toplam_maliyet_tl.toLocaleString('tr-TR')} ₺</p>
              <div className="mt-4 pt-4 border-t text-sm text-gray-600">
                <p>Mesafe: {result.mesafe_km} km</p>
                <p>Tahmini Hacim: {result.tahmini_desi} Desi</p>
              </div>
            </div>

            {/* Kart 2: Rota Bilgisi */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <h3 className="text-gray-500 text-sm font-medium">Rota Çıktısı</h3>
              <div className="mt-4 flex items-center justify-between text-lg font-semibold text-gray-800">
                <span>{result.cikis}</span>
                <span className="text-blue-500">➔</span>
                <span>{result.varis}</span>
              </div>
            </div>

            {/* Kart 3: Atama Planı */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <h3 className="text-gray-500 text-sm font-medium">Araç Atama Planı</h3>
              <div className="mt-4 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Kendi Tır</span>
                  <span className="font-semibold">{result.atama_plani.kendi_tir}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Kendi Kamyon</span>
                  <span className="font-semibold">{result.atama_plani.kendi_kamyon}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Spot Tır</span>
                  <span className="font-semibold">{result.atama_plani.spot_tir}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Spot Kamyon</span>
                  <span className="font-semibold">{result.atama_plani.spot_kamyon}</span>
                </div>
              </div>
            </div>

          </div>
        )}
      </div>
    </div>
  );
}