# AIRFLOW & BIGQUERY EĞİTİMİ

Apache Airflow 101 ve BigQuery entegrasyonu eğitim malzemeleri.

## 📋 İçerik

- **Docker Compose Ortamı**: Local Airflow kurulumu
- **Demo DAG'ler**: 9 farklı örnek DAG
- **BigQuery Entegrasyonu**: GCP entegrasyon örnekleri
- **Sales Datamart**: Uçtan uca Star Schema demo projesi
- **Eğitim Sunumu**: PowerPoint (PPTX) sunum
- **Detaylı Notlar**: Markdown formatında eğitim içerikleri

## 🚀 Hızlı Başlangıç

### Gereksinimler

- Docker Desktop
- Python 3.8+
- 4GB+ RAM
- 10GB+ Disk alanı

### Kurulum

1. **Docker Ortamını Başlat**

```bash
# Dizine git
cd "airflow & bigquery eğitimi"

# Docker Compose ile başlat
docker-compose up airflow-init
docker-compose up -d

# Logları izle
docker-compose logs -f
```

2. **Airflow UI'a Eriş**

```
URL: http://localhost:8080
Username: airflow
Password: airflow
```

3. **Test Verisi Oluştur**

```bash
# Test CSV dosyaları oluştur
python scripts/generate_test_data.py
```

## 📁 Dizin Yapısı

```
airflow & bigquery eğitimi/
├── docker-compose.yaml          # Docker Compose konfigürasyonu
├── .env                          # Environment variables
├── README.md                     # Bu dosya
├── airflow-egitim-sunum.pptx    # PowerPoint sunumu
│
├── dags/                         # Airflow DAG dosyaları
│   ├── 01_hello_world_dag.py
│   ├── 02_dependencies_example_dag.py
│   ├── 03_operators_showcase_dag.py
│   ├── 04_taskflow_api_dag.py
│   ├── 05_xcom_example_dag.py
│   ├── 06_bigquery_basic_dag.py
│   ├── 07_bigquery_etl_dag.py
│   └── 09_sales_datamart_pipeline.py
│
├── scripts/                      # Yardımcı scriptler
│   └── generate_test_data.py    # Test veri oluşturma
│
├── data/                         # Test verileri
│   ├── customers_*.csv
│   ├── products_*.csv
│   └── transactions_*.csv
│
├── egitim-notlari/              # Detaylı eğitim içerikleri (Markdown)
│   ├── 01-giris.md
│   ├── 02-kurulum.md
│   ├── 03-dag-gelistirme.md
│   ├── 04-operatorler.md
│   ├── 05-webui-yonetim.md
│   ├── 06-deployment-cicd.md
│   ├── 07-bigquery-entegrasyonu.md
│   └── 08-sales-datamart-demo.md
│
├── tests/                        # Unit testler
│   └── test_dags.py
│
├── cicd/                         # CI/CD pipeline örnekleri
│   ├── azure-pipelines.yml
│   └── .github/
│       └── workflows/
│           └── deploy.yml
│
├── screenshots/                  # WebUI ekran görüntüleri
│
├── logs/                         # Airflow logları
├── plugins/                      # Custom Airflow plugins
└── config/                       # Airflow konfigürasyon
```

## 📚 Demo DAG'ler

### Temel Örnekler

| DAG | Açıklama | Seviye |
|-----|----------|--------|
| `01_hello_world` | İlk basit DAG örneği | Başlangıç |
| `02_dependencies_example` | Task bağımlılıkları (fan-out, fan-in) | Başlangıç |
| `03_operators_showcase` | Farklı operator tipleri | Orta |
| `04_taskflow_api_example` | Modern TaskFlow API (@task) | Orta |
| `05_xcom_example` | Task'lar arası veri paylaşımı | Orta |

### BigQuery Örnekleri

| DAG | Açıklama | Seviye |
|-----|----------|--------|
| `06_bigquery_basic` | BigQuery temel operasyonlar | Orta |
| `07_bigquery_etl_pipeline` | GCS → BigQuery ETL | İleri |
| `09_sales_datamart_pipeline` | ⭐ Sales Datamart (Star Schema) | İleri |

## 🎯 Sales Datamart Demo

Uçtan uca çalışan Star Schema tabanlı veri ambarı örneği:

### Tablolar

**Dimension Tables:**
- `DimCustomer`: Müşteri bilgileri
- `DimProduct`: Ürün kataloğu
- `DimDate`: Tarih dimension (2020-2030)

**Fact Table:**
- `FactSalesTransaction`: Satış işlemleri

### Çalıştırma

```bash
# 1. Test verisi oluştur
python scripts/generate_test_data.py

# 2. DAG'i tetikle (WebUI'dan veya CLI)
airflow dags trigger 09_sales_datamart_pipeline

# 3. WebUI'dan izle
# Graph view, Gantt chart, Logs
```

## 🔧 Yardımcı Komutlar

### Docker Yönetimi

```bash
# Durdur
docker-compose down

# Tamamen temizle (volumes dahil)
docker-compose down -v

# Yeniden başlat
docker-compose restart

# Loglar
docker-compose logs -f webserver
docker-compose logs -f scheduler
```

### Airflow CLI

```bash
# DAG listesi
docker exec -it airflow-webserver airflow dags list

# DAG test et
docker exec -it airflow-webserver airflow dags test <dag_id> 2024-01-01

# Task test et
docker exec -it airflow-webserver airflow tasks test <dag_id> <task_id> 2024-01-01

# DAG trigger
docker exec -it airflow-webserver airflow dags trigger <dag_id>
```

### Veritabanı

```bash
# PostgreSQL'e bağlan
docker exec -it airflow-postgres psql -U airflow -d airflow

# Örnek query
SELECT dag_id, state, execution_date FROM dag_run ORDER BY execution_date DESC LIMIT 10;
```

## 📖 Eğitim Sunumu

PowerPoint sunumu: `airflow-egitim-sunum.pptx`

**İçerik:**
- 60-80 slayt
- Türkçe
- Kod örnekleri
- Ekran görüntüleri
- Her slaytın notlar bölümünde detaylı açıklama

**Bölümler:**
1. Giriş ve Temeller
2. Kurulum
3. DAG Geliştirme
4. Operator'ler
5. Geliştirme Ortamı
6. WebUI & Yönetim
7. DAG İletişimi
8. Deployment & CI/CD
9. BigQuery Entegrasyonu ⭐
10. Sales Datamart Demo ⭐
11. Kapanış

## 🔗 Kaynaklar

### Resmi Dokümantasyon
- [Apache Airflow Docs](https://airflow.apache.org/docs/)
- [BigQuery Docs](https://cloud.google.com/bigquery/docs)
- [Cloud Composer Docs](https://cloud.google.com/composer/docs)

### Eğitim Kaynakları
- [Astronomer Academy](https://academy.astronomer.io/)
- [DataCamp Airflow Course](https://www.datacamp.com/courses/introduction-to-apache-airflow-in-python)

### Provider Docs
- [Google Cloud Provider](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/)
- [BigQuery Operators](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/bigquery.html)

## 🐛 Troubleshooting

### DAG görünmüyor
```bash
# Parse hatalarını kontrol et
docker exec -it airflow-webserver airflow dags list-import-errors

# DAG dosyasını Python ile çalıştır
python dags/my_dag.py
```

### Task failed
```bash
# Logları kontrol et (WebUI)
# Veya CLI ile:
docker exec -it airflow-webserver airflow tasks logs <dag_id> <task_id> <execution_date>
```

### BigQuery connection hatası
- Service Account JSON key'i kontrol et
- IAM permissions kontrol et (BigQuery Admin, Storage Admin)
- Connection ID: `google_cloud_default`

## 📧 İletişim

Sorularınız için:
- GitHub Issues
- Email: data-team@example.com

## 📝 Lisans

Eğitim amaçlı kullanım için.

---

**Son Güncelleme:** 2024
**Versiyon:** 1.0
**Airflow Versiyonu:** 2.8.1
