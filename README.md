# F1 Data Analysis

**Python · SQL · PostgreSQL · FastAPI · React**

2024 ve 2025 Formula 1 sezonlarındaki yarış, sürücü ve takım verilerini analiz etmek için geliştirdiğim web uygulaması. Python tabanlı API, PostgreSQL sorguları ve etkileşimli arayüzü bir araya getiriyor.

> **Kısaca:** Ham yarış verilerinden sürücü performansı, tur süreleri ve takım karşılaştırmaları üretmek.

### Bu projede neler var?

- **Veri analizi:** yarış sonuçları, tur süreleri, podyum ve DNF oranlarının karşılaştırılması
- **SQL ve veritabanı:** yıl bazlı tablolar, parametrik sorgular, `UNION ALL` ve sayfalama
- **Uygulama geliştirme:** FastAPI servisleri ve React tabanlı analiz ekranları

**English:** A Formula 1 data analysis app for the 2024–2025 seasons, combining PostgreSQL queries, a Python/FastAPI backend and interactive driver/team comparisons.

---

## 💡 Fikir ve Motivasyon

Formula 1 verilerinde yarış sonuçları, tur zamanları ve takım performansı farklı tablolarda tutuluyor. Bu bilgileri ortak bir analiz arayüzünde birleştirmek ve anlamlı karşılaştırmalar üretmek istedim.

**Temel tasarım kararı:** Tüm veriyi çekmek yerine, frontend filtreleme + backend pagination + UNION ALL sorgu stratejisi. Bu yaklaşım, gereksiz veri aktarımını ve bellekte tutulan sonuç miktarını azaltmayı hedefliyor.

---

## 🏗️ Mimari

```
Frontend (React + TypeScript + Vite)
    ↓ Filtre parametreleri
FastAPI Backend (Python)
    ↓ Parameterize SQL + UNION ALL
PostgreSQL (Railway)
    ├── results_2024
    ├── results_2025
    ├── lap_times_2024
    ├── lap_times_2025
    └── ...
```

**RAM-Verimli Sorgu Mimarisi:**
```python
class F1AnalysisService:
    # Yıl bazında UNION ALL sorguları
    # Pagination (limit/offset)
    # Parameterized queries (SQL injection güvenli)
    # SQLAlchemy connection pooling
```

---

## ⚙️ Analiz Modülleri

### 🏎️ Sürücü Analizi
- **Performans Sıralaması** — kazanma, podyum, DNF oranı
- **Tur Süresi Analizi** — en iyi tur, ortalama, tutarlılık
- **Yarış Bazında Karşılaştırma** — sürücüler arası

### 🏭 Takım / Constructor Analizi
- Takım puan gelişimi (sezon boyunca)
- Takım güvenilirlik skoru
- Sürücü çift performans karşılaştırması

### 🗓️ Sezon Görünümü
- 2024-2025 sezon verileri
- Pist bazında analizler
- Hava koşulu etkisi

---

## 🔮 Yarış Sonucu Tahmini

Sürücü, takım, pist, başlangıç sırası ve hava durumu (hava/pist sıcaklığı, yağmur) seçilerek sürücünün kaçıncı bitireceği tahmin edilir.

- **Model:** `ml/model.py`, scikit-learn `HistGradientBoostingRegressor`
- **Değerlendirme:** Son yarışlar eğitimden ayrılır (zamana göre bölme). Model, "sürücü başladığı sırada bitirir" varsayımıyla karşılaştırılır; sonuç `ml/artifacts/metrics.json` içinde ve arayüzde gösterilir.
- **Sınırlar:** Güvenlik aracı, yağmur değişimi ve arızalar tahmin edilemez. Bitirmeyen sürücüler (DNF) eğitim verisine alınmaz.

```bash
# 1) Eğitim verisini ml/data/race_dataset.csv olarak hazırla (sütunlar: ml/data/README.md)
python -m ml.train --data ml/data/race_dataset.csv

# 2) API: GET /predict/options, POST /predict
uvicorn backend.app.main:app --reload
# 3) Arayüz: http://localhost:5173/predict
```

Testler: `python -m pytest test_ml.py` (yapay veriyle sadece boru hattını doğrular).

---

## 🛠️ Tech Stack

| Katman | Teknoloji |
|--------|-----------|
| Backend | Python, FastAPI |
| ORM / SQL | SQLAlchemy, Ham SQL (UNION ALL) |
| Veritabanı | PostgreSQL (Railway) |
| Frontend | React 19, TypeScript, Vite |
| Stil | TailwindCSS |
| Veri Güvenliği | Parameterized queries |

---

## 📁 Proje Yapısı

```
f1DataAnalysis/
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── main.py                  # FastAPI + health check
│       ├── routes/
│       │   └── analysis.py          # API endpoint'leri
│       └── services/
│           ├── f1_analysis_service.py  # Ana analiz motoru (510 satır)
│           └── analysis_service.py    # Yardımcı sorgular
├── frontend/
│   └── src/                         # React + TypeScript UI
├── database/                        # SQL şemaları ve seed
├── docs/                            # Teknik dokümantasyon
└── test_backend.py                  # Backend test suite
```

---

## 🚀 Kurulum

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# DATABASE_URL=postgresql://...
uvicorn app.main:app --reload
# → http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## 🔗 API Endpoint'leri

| Endpoint | Açıklama |
|----------|----------|
| `GET /` | API durum kontrolü |
| `GET /health` | PostgreSQL bağlantı testi |
| `GET /analysis/drivers` | Sürücü performans sıralaması |
| `GET /analysis/constructors` | Takım analizi |
| `GET /analysis/laps` | Tur süresi verileri |

---

## 📊 Veri Güvenliği

Tüm SQL sorguları parameterized (hazırlanmış ifadeler) kullanır:
```python
# ✅ Güvenli
conn.execute(text("SELECT * FROM results WHERE driver = :driver_id"), 
             {"driver_id": driver_id})

# ❌ ASLA
f"SELECT * FROM results WHERE driver = '{driver_id}'"
```

---

<div align="center">
<img src="https://img.shields.io/badge/FastAPI-Python-009688?style=flat-square&logo=fastapi" />
<img src="https://img.shields.io/badge/PostgreSQL-Database-316192?style=flat-square&logo=postgresql" />
<img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react" />
<img src="https://img.shields.io/badge/SQLAlchemy-ORM-D71F00?style=flat-square" />
<img src="https://img.shields.io/badge/F1-2024--2025-E10600?style=flat-square" />

</div>
