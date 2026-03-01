# Airflow & BigQuery Eğitim Notları

## İçindekiler

Bu klasör, Apache Airflow ve BigQuery entegrasyonu için kapsamlı eğitim materyallerini içerir.

### Eğitim Modülleri

#### 1. [Airflow Giriş](01-giris.md)

**Süre:** 30 dakika

**İçerik:**

- Airflow Nedir?
- Workflow Orchestration kavramı
- Airflow mimarisi (Scheduler, Executor, WebServer, Database)
- DAG (Directed Acyclic Graph) kavramı
- Kullanım senaryoları
- Görseller ve referanslar

**Anahtar Konular:**

- Orchestration vs Execution
- Scheduler, Executor, Web Server, Metadata DB
- Worker ve Triggerer
- DAG anatomy

---

#### 2. [Kurulum](02-kurulum.md)

**Süre:** 45 dakika

**İçerik:**

- Docker Compose ile Airflow kurulumu (adım adım)
- Dizin yapısı açıklaması
- airflow.cfg dosyası ve önemli parametreler
- Cloud Composer kurulumu
- Troubleshooting

**Anahtar Konular:**

- Docker Compose setup
- LocalExecutor vs CeleryExecutor
- Konfigürasyon parametreleri
- GCP Cloud Composer

**Uygulamalar:**

```bash
# Airflow başlatma
docker compose up -d

# WebUI'ya erişim
http://localhost:8080
```

---

#### 3. [DAG Geliştirme](03-dag-gelistirme.md)

**Süre:** 60 dakika

**İçerik:**

- DAG anatomisi
- Hello World DAG örneği
- Task dependencies (>>, <<, chain)
- DAG parametreleri (schedule_interval, start_date, catchup, tags)
- WebUI'dan DAG görünümü
- Best practices

**Anahtar Konular:**

- DAG tanımlama
- Task dependencies
- Schedule interval (cron expressions)
- Catchup vs backfill
- Default arguments

**Uygulamalar:**

- Hello World DAG yazma
- Linear ve paralel pipeline'lar
- Branching (conditional logic)

---

#### 4. [Operator&#39;ler](04-operatorler.md)

**Süre:** 60 dakika

**İçerik:**

- Operator kavramı
- BashOperator, PythonOperator, EmailOperator
- Sensor Operators (FileSensor, TimeSensor, etc.)
- TaskFlow API (@task decorator)
- Provider packages

**Anahtar Konular:**

- Operator vs Hook vs Sensor
- TaskFlow API (modern approach)
- Context variables
- XCom (cross-communication)
- Sensor modes (poke vs reschedule)

**Uygulamalar:**

```python
# TaskFlow API örneği
@task
def extract() -> dict:
    return {'data': [1, 2, 3]}

@task
def transform(data: dict) -> dict:
    return {'total': sum(data['data'])}
```

---

#### 5. [WebUI ve Yönetim](05-webui-yonetim.md)

**Süre:** 45 dakika

**İçerik:**

- DAG View'ları (Grid, Graph, Calendar, Gantt)
- DAG çalıştırma yöntemleri (manual trigger, schedule)
- Scheduling ve cron expressions
- Backfill işlemleri
- Hata ayıklama (logs, rendered templates)
- Connection ve Variable yönetimi

**Anahtar Konular:**

- Grid View (task instance durumları)
- Graph View (dependency grafiği)
- Gantt Chart (performance analizi)
- Manual trigger vs scheduled runs
- Clear/rerun tasks
- Connection kurulumu

**Uygulamalar:**

- WebUI'dan DAG tetikleme
- Task log görüntüleme
- Connection ekleme (Google Cloud)
- Variable yönetimi

---

#### 6. [Deployment ve CI/CD](06-deployment-cicd.md)

**Süre:** 45 dakika

**İçerik:**

- Deployment stratejisi (Dev → Test → Staging → Prod)
- Git workflow (GitFlow)
- Azure DevOps pipeline örneği
- GitHub Actions örneği
- Cloud Composer deployment
- Best practices

**Anahtar Konular:**

- Environment separation
- Secrets management
- DAG versioning
- Automated testing
- Blue-green deployment
- Rollback stratejisi

**Uygulamalar:**

```yaml
# GitHub Actions pipeline
- name: Test DAGs
  run: pytest tests/

- name: Deploy to Production
  run: gsutil rsync -r dags/ gs://airflow-prod/dags/
```

---

#### 7. [BigQuery Entegrasyonu](07-bigquery-entegrasyonu.md)

**Süre:** 60 dakika

**İçerik:**

- BigQuery Operators
- Connection kurulumu (Service Account)
- BigQueryInsertJobOperator örnekleri
- GCSToBigQueryOperator, BigQueryToGCSOperator
- Data quality checks
- Best practices

**Anahtar Konular:**

- BigQueryInsertJobOperator (query execution)
- GCS ↔ BigQuery transfer
- Partitioning ve clustering
- Incremental loading
- MERGE (upsert) operations
- Cost optimization

**Uygulamalar:**

```python
# BigQuery query
create_table = BigQueryInsertJobOperator(
    task_id='create_table',
    configuration={
        "query": {
            "query": "CREATE TABLE IF NOT EXISTS ...",
            "useLegacySql": False
        }
    }
)

# GCS to BigQuery load
load_data = GCSToBigQueryOperator(
    task_id='load_from_gcs',
    bucket='my-bucket',
    source_objects=['data.csv'],
    destination_project_dataset_table='project.dataset.table'
)
```

---

#### 8. [Sales Datamart Demo](08-sales-datamart-demo.md) ⭐ **DEMO PROJE**

**Süre:** 90 dakika

**İçerik:**

- Sales Datamart projesi detaylı anlatım
- Star Schema mimarisi
- Dimension Tables (DimCustomer, DimProduct, DimDate)
- Fact Table (FactSalesTransaction)
- DAG pipeline akışı (09_sales_datamart_pipeline.py)
- Test verileri ve çalıştırma
- Analiz sorguları

**Anahtar Konular:**

- Star Schema design
- SCD Type 1 (Slowly Changing Dimensions)
- Surrogate keys (FARM_FINGERPRINT)
- Incremental fact loading
- Daily reporting
- BI analysis queries

**Pipeline Akışı:**

```
GCS Files → Staging Tables → Dimension Tables → Fact Table → Report
```

**Tables:**

- `DimCustomer`: Müşteri bilgileri
- `DimProduct`: Ürün katalog
- `DimDate`: Tarih dimension (2020-2030)
- `FactSalesTransaction`: Satış işlemleri
- `DailySalesReport`: Günlük özet

**Uygulamalar:**

- Test verisi oluşturma
- DAG'i çalıştırma
- BigQuery'de analiz sorguları:
  - Top 10 müşteri
  - Kategori bazlı satış
  - Aylık trend analizi
  - Hafta sonu vs hafta içi

---

## Eğitim Programı

### Gün 1: Temel Kavramlar (4 saat)

- ☕ 09:00 - 09:30: Giriş ve Airflow Nedir
- 📚 09:30 - 10:15: Kurulum (Docker Compose)
- 🛠️ 10:15 - 11:15: DAG Geliştirme
- ☕ 11:15 - 11:30: Kahve Molası
- 📝 11:30 - 12:30: Operator'ler ve TaskFlow API

### Gün 2: İleri Seviye ve BigQuery (4 saat)

- ☕ 09:00 - 09:45: WebUI ve Yönetim
- 🔧 09:45 - 10:30: Deployment ve CI/CD
- ☕ 10:30 - 10:45: Kahve Molası
- 💾 10:45 - 11:45: BigQuery Entegrasyonu
- ⭐ 11:45 - 13:00: Sales Datamart Demo (Hands-on)

---

## Ön Gereksinimler

### Teknik Gereksinimler

- Docker Desktop kurulu
- Python 3.10+ kurulu
- Git kurulu
- Metin editörü (VS Code önerilir)
- Minimum 8GB RAM
- 10GB disk alanı

### Bilgi Seviyesi

- Temel Python bilgisi
- SQL bilgisi (SELECT, JOIN, GROUP BY)
- Temel Linux/Bash komutları
- (Opsiyonel) Google Cloud Platform deneyimi

---

## Ek Kaynaklar

### Resmi Dokümantasyon

- [Apache Airflow Docs](https://airflow.apache.org/docs/)
- [BigQuery Docs](https://cloud.google.com/bigquery/docs)
- [Cloud Composer Docs](https://cloud.google.com/composer/docs)

### Topluluk Kaynakları

- [Astronomer Guides](https://docs.astronomer.io/learn)
- [Airflow Slack](https://apache-airflow.slack.com/)
- [Stack Overflow - Airflow Tag](https://stackoverflow.com/questions/tagged/airflow)

### Blog ve Makaleler

- [Medium - Airflow Tutorials](https://medium.com/tag/apache-airflow)
- [Google Cloud Blog](https://cloud.google.com/blog/products/data-analytics)

---

## Proje Dosyaları

### Dizin Yapısı

```
airflow & bigquery eğitimi/
├── dags/                          # DAG dosyaları
│   ├── 01_hello_world_dag.py
│   ├── 04_taskflow_api_dag.py
│   ├── 06_bigquery_basic_dag.py
│   ├── 07_bigquery_etl_dag.py
│   └── 09_sales_datamart_pipeline.py ⭐
├── egitim-notlari/               # Bu klasör
│   ├── 01-giris.md
│   ├── 02-kurulum.md
│   ├── ...
│   └── 08-sales-datamart-demo.md
├── config/
│   └── airflow.cfg
├── data/                          # Test verileri
├── scripts/                       # Yardımcı script'ler
├── docker-compose.yaml
└── README.md
```

---

## Yardım ve Destek

### Sorular

Eğitim sırasında sorularınızı çekinmeden sorun!

### Hata Durumunda

1. DAG import errors: `airflow dags list-import-errors`
2. Log'ları kontrol edin
3. Docker container'ları restart edin: `docker compose restart`

### İletişim

- Email: [data-team@example.com]
- Slack: #airflow-egitim

---

## Sertifika

Eğitimi tamamlayan katılımcılara "Apache Airflow & BigQuery" katılım belgesi verilecektir.

**Gereksinimler:**

- Tüm modüllere katılım
- Hands-on uygulamaları tamamlama
- Sales Datamart demo projesini çalıştırma

---

## Değerlendirme

Lütfen eğitim sonunda geri bildirim formunu doldurun:

- Eğitim içeriği
- Eğitmen performansı
- Materyal kalitesi
- İyileştirme önerileri

---

## Lisans

Bu eğitim materyali sadece [Ensight] çalışanları için hazırlanmıştır.

© 2024 - Tüm hakları saklıdır, FXerkan.
