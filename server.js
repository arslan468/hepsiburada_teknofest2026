const express = require('express');
const cors = require('cors');
const { exec } = require('child_process');
const util = require('util');

// exec fonksiyonunu async/await ile kullanabilmek için promise yapısına çeviriyoruz
const execPromise = util.promisify(exec);

const app = express();
app.use(cors());
app.use(express.json());

app.post('/api/optimize', async (req, res) => {
    const { cikis, varis, tarih } = req.body;

    if (!cikis || !varis || !tarih) {
        return res.status(400).json({ error: 'Eksik parametre: Çıkış, varış ve tarih gereklidir.' });
    }

    try {
        // Parametreleri tırnak içinde göndererek güvenliği ve boşluklu isimleri koruyoruz
        const command = `python3 pipeline.py "${cikis}" "${varis}" "${tarih}"`;
        
        const { stdout, stderr } = await execPromise(command);

        // Python'dan gelen saf JSON string'i parse ediyoruz
        const result = JSON.parse(stdout.trim());
        
        return res.status(200).json(result);
    } catch (error) {
        console.error('İşlem Hatası:', error);
        return res.status(500).json({ error: 'Optimizasyon motoru çalışırken bir hata oluştu.' });
    }
});

const PORT = 5000;
app.listen(PORT, () => {
    console.log(`Backend API ${PORT} portunda çalışıyor.`);
});