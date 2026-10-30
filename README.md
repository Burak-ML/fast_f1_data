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

Sürücü, başlangıç sırası, pist sıcaklığı ve yağmur seçilerek sürücünün kaçıncı bitireceği hesaplanır. Makine öğrenmesi modeli **eğitilmez**; geçmiş yarışlardan çıkarılan istatistiklerle (pandas) hesap yapılır ve sonucun nereden geldiği ekranda gösterilir.

```
tahmin = bu başlangıç sırasından genelde bitilen yer   (yalnızca kuru yarışlardan)
       + takımın sıradan kazandırdığı / kaybettirdiği
       + sürücünün takımının üstüne kattığı
       + yağmurun / sıcak pistin sıralamayı ortaya doğru karıştırması
```

- **Küçük örneklem koruması:** Az yarışa dayanan her etki sıfıra doğru küçültülür; tek iyi hafta sonu bir sürücüyü olduğundan iyi göstermez.
- **Doğrulama:** Son yarışlar hesaba katılmaz, sonra bu yarışlar tahmin edilir. Sonuç "sürücü başladığı sırada bitirir" varsayımıyla karşılaştırılır (`python -m analysis.report`), her adımın katkısı ayrı ayrı görünür.
- **Sınırlar:** Güvenlik aracı ve arızalar tahmin edilemez. Bitirmeyen sürücüler (DNF) veriye alınmaz.

```bash
# Veriyi indir (OpenF1, anahtar gerekmez) -> analysis/data/race_dataset.csv
python -m analysis.collect --years 2024 2025
python -m analysis.report          # doğruluk raporu
uvicorn backend.app.main:app --reload   # GET /predict/options, POST /predict
# Arayüz: http://localhost:5173/predict
```

Testler: `python -m pytest test_ml.py test_collect.py`. Hesap testleri yapay veriye bilinçli etkiler yerleştirip bulunduğunu doğrular; toplayıcı testleri sahte bir OpenF1 yanıtıyla çevrimdışı çalışır. Veri formatı ve toplama ayrıntıları: `analysis/data/README.md`.

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
