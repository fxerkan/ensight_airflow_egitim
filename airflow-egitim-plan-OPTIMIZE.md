# AIRFLOW 101 EĞİTİM PLANI - OPTİMİZE (60-80 SLAYT)

## 📋 EĞİTİM GENEL BAKIŞ

**Süre:** 2 Gün (16 saat)
**Hedef Slayt:** 60-80 slayt (yoğun, pratik odaklı)
**Seviye:** Başlangıç
**Dil:** Türkçe
**Ortam:** Docker Compose (Local) + GCP Cloud Composer (Production)

---

## 🎯 SUNUM YAPISI

### **GÜN 1: TEMELLERİ VE GELİŞTİRME (35-40 slayt)**

#### **BÖLÜM 1: GİRİŞ (5-6 slayt)**
1. Kapak + Gündem
2. Airflow Nedir? (Workflow Orchestration)
3. Airflow Mimarisi (Scheduler, Executor, WebServer, DB, Workers)
4. DAG Kavramı (Directed Acyclic Graph)
5. Kullanım Senaryoları

#### **BÖLÜM 2: KURULUM (6-7 slayt)**
6. Docker Compose Kurulumu
7. Dizin Yapısı (dags/, logs/, plugins/)
8. İlk Başlatma ve WebUI Erişimi
9. Airflow Konfigürasyonu (airflow.cfg)
10. Cloud Composer Genel Bakış
11. Pratik: İlk Kurulum Demo

#### **BÖLÜM 3: İLK DAG GELİŞTİRME (8-9 slayt)**
12. DAG Anatomisi (Kod Yapısı)
13. Hello World DAG Örneği
14. Task Dependencies (>>, <<, chain)
15. DAG Parametreleri (schedule_interval, start_date, catchup)
16. Pratik: İlk DAG'i Oluştur ve Çalıştır
17. WebUI Graph View
18. WebUI Tree View
19. Task Instance Logs

#### **BÖLÜM 4: OPERATOR'LER (7-8 slayt)**
20. Operator Nedir?
21. BashOperator
22. PythonOperator
23. EmailOperator & Notification
24. Sensor Operators (FileSensor, TimeSensor)
25. TaskFlow API (@task decorator) - Modern Yaklaşım
26. Operator Örnekleri (Karşılaştırmalı)

#### **BÖLÜM 5: GELİŞTİRME ORTAMI VE TEST (5-6 slayt)**
27. IDE Kurulumu (VS Code + Extension)
28. DAG Geliştirme Best Practices
29. Local Testing (airflow dags test, tasks test)
30. DAG Parse Check
31. Unit Testing

---

### **GÜN 2: PRODUCTION VE BIGQUERY (35-40 slayt)**

#### **BÖLÜM 6: AIRFLOW WEBUI VE YÖNETİM (6-7 slayt)**
32. WebUI Detaylı Anlatım (DAGs, Graph, Gantt, Code)
33. DAG Çalıştırma (Manual, Schedule, Trigger)
34. Scheduling (Cron, @daily, timedelta)
35. Backfill İşlemleri
36. Hata Ayıklama (Clear, Mark Success, Retry)
37. Task Instance State Diagram

#### **BÖLÜM 7: DAG İLETİŞİM VE PARAMETRELERİ (5-6 slayt)**
38. XCom (Cross-Communication)
39. Variables (Admin Panel)
40. Connections (Database, API, Cloud)
41. ExternalTaskSensor
42. TriggerDagRunOperator
43. Jinja Templating

#### **BÖLÜM 8: DEPLOYMENT VE CI/CD (7-8 slayt)**
44. Deployment Stratejisi (Dev → Test → Prod)
45. Git Workflow
46. Azure DevOps Pipeline (YAML)
47. GitHub Actions Pipeline (YAML)
48. Cloud Composer Deployment
49. Pratik: CI/CD Demo
50. Best Practices & Anti-Patterns

#### **BÖLÜM 9: BIGQUERY ENTEGRASYONU ⭐ (10-12 slayt)**
51. BigQuery Operatörleri Genel Bakış
52. BigQuery Connection Kurulumu (Service Account)
53. BigQueryInsertJobOperator (Query Çalıştırma)
54. GCSToBigQueryOperator (Veri Yükleme)
55. BigQueryToGCSOperator (Export)
56. Data Quality Checks (BigQueryCheckOperator)
57. BigQueryTableExistenceSensor
58. Dataform Integration ⭐
59. BigQuery Best Practices
60. Pratik: BigQuery ETL Pipeline

#### **BÖLÜM 10: SALES DATAMART PIPELINE DEMO ⭐ (8-10 slayt)**
61. Proje Mimarisi (Star Schema)
62. Dimension Tables (DimCustomer, DimProduct, DimDate)
63. Fact Table (FactSalesTransaction)
64. DAG Yapısı ve Akışı
65. Extract: GCS Sensor + Load to Staging
66. Transform: Dimension Upsert
67. Load: Fact Insert
68. Data Quality & Reporting
69. Pratik: Pipeline Çalıştırma
70. Sonuçları İnceleme

#### **BÖLÜM 11: KAPANIŞ (3-4 slayt)**
71. Troubleshooting ve Common Issues
72. İleri Seviye Konular (Dynamic DAGs, Pools)
73. Özet ve Kaynaklar
74. Soru & Cevap

---

## 📁 DİZİN YAPISI

```
airflow & bigquery eğitimi/
├── docker-compose.yaml
├── .env
├── README.md
├── airflow-egitim-sunum.pptx
├── egitim-notlari/
│   ├── 01-giris.md
│   ├── 02-kurulum.md
│   ├── 03-dag-gelistirme.md
│   ├── 04-operatorler.md
│   ├── 05-webui-yonetim.md
│   ├── 06-deployment-cicd.md
│   ├── 07-bigquery-entegrasyonu.md
│   └── 08-sales-datamart-demo.md
├── dags/
│   ├── 01_hello_world_dag.py
│   ├── 02_dependencies_example_dag.py
│   ├── 03_operators_showcase_dag.py
│   ├── 04_taskflow_api_dag.py
│   ├── 05_xcom_example_dag.py
│   ├── 06_bigquery_basic_dag.py
│   ├── 07_bigquery_etl_dag.py
│   ├── 08_dataform_trigger_dag.py
│   └── 09_sales_datamart_pipeline.py
├── scripts/
│   ├── generate_test_data.py
│   ├── upload_to_gcs.sh
│   └── setup_bigquery_tables.sql
├── data/
│   ├── customers_sample.csv
│   ├── products_sample.csv
│   └── transactions_sample.csv
├── tests/
│   └── test_dags.py
├── screenshots/
│   └── (WebUI ekran görüntüleri)
├── config/
│   └── airflow.cfg
└── cicd/
    ├── azure-pipelines.yml
    └── .github/workflows/deploy.yml
```

---

## 🎨 SUNUM TASARIMI

### Tema:
- **Kurumsal, profesyonel**
- **Renk paleti:** Mavi tonları (Airflow teması), turuncu aksan
- **Font:** Segoe UI / Calibri (Türkçe karakter desteği)

### Her Slayt:
- **Başlık:** Net ve kısa
- **İçerik:** Bullet points, kod blokları, diyagramlar
- **Görsel:** Ekran görüntüsü, diyagram veya ikon
- **Notlar Bölümü:** Detaylı açıklama, link'ler, ek bilgiler

### Kod Blokları:
- Syntax highlighting
- Satır numaraları
- Açıklamalı (comment)

---

## 📝 MARKDOWN İÇERİK DETAYI

Her markdown dosyası:
1. **Teorik Açıklama**
2. **Kod Örnekleri** (çalışır durumda)
3. **Adım Adım Talimatlar**
4. **Pratik Uygulamalar**
5. **Kaynaklar ve Linkler**

---

## 🧪 TEST SENARYOLARI

### Test 1: Docker Compose Başlatma
```bash
cd "/Users/erkan.ciftci/repo_local/airflow & bigquery eğitimi"
docker-compose up -d
# Bekle: webserver health check
# Erişim: http://localhost:8080
```

### Test 2: Her DAG'i Çalıştır
```bash
# Sırayla test et
airflow dags test 01_hello_world_dag 2024-01-01
airflow dags test 02_dependencies_example_dag 2024-01-01
# ... (tüm DAG'ler)
```

### Test 3: BigQuery Connection (Mock)
- Local test için mock connection
- Gerçek GCP credentials sağlandığında güncelle

---

## ✅ SLAYT DAĞILIMI ÖZET

| Bölüm | Slayt Sayısı | İçerik |
|-------|--------------|--------|
| Giriş | 5-6 | Airflow nedir, mimari, DAG kavramı |
| Kurulum | 6-7 | Docker, dizin yapısı, Cloud Composer |
| İlk DAG | 8-9 | Kod yapısı, dependencies, WebUI |
| Operator'ler | 7-8 | Bash, Python, TaskFlow API |
| Geliştirme Ortamı | 5-6 | IDE, testing, best practices |
| WebUI & Yönetim | 6-7 | Çalıştırma, scheduling, backfill |
| DAG İletişim | 5-6 | XCom, Variables, Connections |
| Deployment & CI/CD | 7-8 | Git, Azure DevOps, GitHub Actions |
| **BigQuery** | **10-12** | **Operatörler, ETL, Dataform** |
| **Sales Datamart** | **8-10** | **Demo proje (uçtan uca)** |
| Kapanış | 3-4 | Troubleshooting, özet, kaynaklar |
| **TOPLAM** | **60-73** | **Optimize edilmiş** |

---

## 🚀 SONRAKI ADIMLAR

1. ✅ Bu planı onayla
2. ⏳ Docker Compose + Demo DAG'ler oluştur
3. ⏳ Markdown detaylı içerikleri yaz
4. ⏳ Docker ortamını test et, screenshot al
5. ⏳ PPTX sunumunu oluştur (Türkçe, 60-80 slayt)

---

## 📌 ÖNEMLİ NOTLAR

- **Tüm içerik Türkçe**
- **GCP Project ID ve Composer URL:** Placeholder kullan, sonra güncelle
  - Placeholder: `MY_GCP_PROJECT_ID`
  - Placeholder: `my-composer-env-url`
- **BigQuery bölümü:** En önemli bölüm (10-12 slayt)
- **Sales Datamart:** Uçtan uca çalışan demo (8-10 slayt)
- **Kod örnekleri:** Kopyala-yapıştır yapılabilir
- **Screenshots:** Docker çalıştıktan sonra al
