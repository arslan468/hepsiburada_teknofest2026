import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { exec } from "child_process";
import fs from "fs";

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // API: Lojistik Optimizasyon Pipeline'ını tetikle
  app.post("/api/run-pipeline", (req, res) => {
    console.log("Optimizasyon süreci tetiklendi...");
    
    // pipeline.ts dosyasını tsx ile çalıştır
    exec("npx tsx pipeline.ts", (error, stdout, stderr) => {
      if (error) {
        console.error("Pipeline hatası:", error);
        return res.status(500).json({
          status: "error",
          message: error.message,
          stdout,
          stderr
        });
      }
      
      console.log("Pipeline başarıyla tamamlandı.");
      res.json({
        status: "success",
        stdout,
        stderr
      });
    });
  });

  // API: Özet Dashboard istatistiklerini getir
  app.get("/api/dashboard-summary", (req, res) => {
    const summaryPath = path.join(process.cwd(), "src", "data", "summary_dashboard.json");
    if (fs.existsSync(summaryPath)) {
      try {
        const data = fs.readFileSync(summaryPath, "utf-8");
        return res.json(JSON.parse(data));
      } catch (err: any) {
        return res.status(500).json({ status: "error", message: "Veri okunamadı: " + err.message });
      }
    } else {
      return res.status(404).json({
        status: "not_run",
        message: "Lojistik simülatörü henüz çalıştırılmadı. Lütfen süreci başlatın."
      });
    }
  });

  // API: Excel İndirme Noktaları
  app.get("/api/download/tahmin-desi", (req, res) => {
    const filePath = path.join(process.cwd(), "src", "data", "tahmin_desi.xlsx");
    if (fs.existsSync(filePath)) {
      res.setHeader("Content-Disposition", "attachment; filename=tahmin_desi.xlsx");
      res.setHeader("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
      res.sendFile(filePath);
    } else {
      res.status(404).send("Dosya bulunamadı. Lütfen önce simülasyonu çalıştırın.");
    }
  });

  app.get("/api/download/arac-planlama", (req, res) => {
    const filePath = path.join(process.cwd(), "src", "data", "arac_planlama.xlsx");
    if (fs.existsSync(filePath)) {
      res.setHeader("Content-Disposition", "attachment; filename=arac_planlama.xlsx");
      res.setHeader("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
      res.sendFile(filePath);
    } else {
      res.status(404).send("Dosya bulunamadı. Lütfen önce simülasyonu çalıştırın.");
    }
  });

  // Vite entegrasyonu (Development & Production)
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Lojistik Server çalışıyor: http://0.0.0.0:${PORT}`);
  });
}

startServer();
