"""
DAG 8: Datamart SQL Pipeline - External SQL Scripts

BigQuery ETL Pipeline with Mixed SQL Approach:
- HARDCODED SQL: Staging tablosu oluşturma ve veri yükleme (Python içinde)
- EXTERNAL SQL: Transformation, Summary ve Quality Checks (sql/ dizininden)

Pipeline Adımları:
1. CREATE STAGING (Hardcoded) - Staging tablo oluştur
2. LOAD SAMPLE DATA (Hardcoded) - Örnek veri yükle
3. TRANSFORM (External SQL) - sql/datamart/01_transform_sales.sql
4. SUMMARIZE (External SQL) - sql/datamart/02_create_summary.sql
5. QUALITY CHECK (External SQL) - sql/datamart/03_quality_checks.sql

Katmanlı Mimari:
- staging.sales_raw         → Ham veri (CSV'den gelecek)
- datamart.sales_cleaned    → Temizlenmiş veri (transformation)
- datamart.daily_sales_summary → Özet rapor (aggregation)

NOT: SQL dosyaları sanki GCS bucket'dan okunuyormuş gibi repo içinden okunuyor.
Gerçek üretimde sql/ klasörü GCS bucket'da olabilir.
"""

from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime, timedelta
import os
from pathlib import Path

# GCP Configuration
PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'MY_GCP_PROJECT_ID')
DATASET_STAGING = 'staging'
DATASET_DATAMART = 'datamart'

# SQL Scripts Directory (GCS bucket'dan okunuyormuş gibi local'den okuyoruz)
SQL_DIR = Path(__file__).parent.parent / 'sql' / 'datamart'

default_args = {
    'owner': 'data-engineering-team',
    'depends_on_past': False,
    'email': ['data-team@example.com'],
    'email_on_failure': False,  # Demo için
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}


def load_sql_file(sql_file_name: str) -> str:
    """
    SQL dosyasını repo içinden oku (GCS bucket simulation).

    Gerçek üretimde bu fonksiyon GCS'den okuyabilir:
    - from google.cloud import storage
    - storage.Client().bucket('my-bucket').blob(f'sql/{sql_file_name}').download_as_text()

    Args:
        sql_file_name: SQL dosyasının adı (örn: '01_transform_sales.sql')

    Returns:
        SQL script içeriği
    """
    sql_file_path = SQL_DIR / sql_file_name

    if not sql_file_path.exists():
        raise FileNotFoundError(f"SQL dosyası bulunamadı: {sql_file_path}")

    print(f"📁 SQL dosyası okunuyor: {sql_file_path}")

    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    print(f"✅ SQL dosyası başarıyla okundu: {len(sql_content)} karakter")
    return sql_content


def log_pipeline_start(**kwargs):
    """Pipeline başlangıç logu"""
    print(f"\n{'='*70}")
    print(f"  🚀 DATAMART SQL PIPELINE BAŞLADI")
    print(f"{'='*70}")
    print(f"  Tarih: {kwargs['ds']}")
    print(f"  Project: {PROJECT_ID}")
    print(f"  SQL Directory: {SQL_DIR}")
    print(f"{'='*70}\n")


def log_pipeline_complete(**kwargs):
    """Pipeline tamamlanma logu"""
    ti = kwargs['ti']

    # Quality check sonucunu al
    quality_result = ti.xcom_pull(task_ids='run_quality_checks')

    print(f"\n{'='*70}")
    print(f"  ✅ DATAMART SQL PIPELINE TAMAMLANDI")
    print(f"{'='*70}")
    print(f"  Tarih: {kwargs['ds']}")
    print(f"  Durum: SUCCESS")
    print(f"  Quality Check: {quality_result if quality_result else 'N/A'}")
    print(f"{'='*70}\n")


with DAG(
    dag_id='08_datamart_sql_pipeline',
    default_args=default_args,
    description='BigQuery ETL with External SQL Scripts - Hardcoded + External Mix',
    schedule_interval='0 4 * * *',  # Her gün 04:00
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['egitim', 'bigquery', 'sql-pipeline', 'datamart'],
    params={
        'project_id': PROJECT_ID,
        'staging_dataset': DATASET_STAGING,
        'datamart_dataset': DATASET_DATAMART,
    },
    render_template_as_native_obj=True,
) as dag:

    # ========== START ==========
    start = DummyOperator(task_id='start')

    log_start = PythonOperator(
        task_id='log_pipeline_start',
        python_callable=log_pipeline_start,
    )

    # ==========================================================
    # STEP 1: CREATE STAGING TABLE (HARDCODED SQL)
    # ==========================================================
    create_staging_table = BigQueryInsertJobOperator(
        task_id='create_staging_table',
        configuration={
            "query": {
                "query": f"""
                    -- Staging tablosu oluştur (ham veri için)
                    CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.{DATASET_STAGING}.sales_raw` (
                        order_id STRING,
                        customer_id STRING,
                        product_id STRING,
                        product_name STRING,
                        category STRING,
                        quantity INT64,
                        unit_price FLOAT64,
                        total_amount FLOAT64,
                        discount_amount FLOAT64,
                        order_date STRING,  -- String olarak gelecek, dönüştüreceğiz
                        loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
                    )
                    PARTITION BY DATE(loaded_at)
                    OPTIONS(
                        description="Staging - Ham satış verisi (CSV'den yüklenir)",
                        labels=[("layer", "staging"), ("source", "csv")]
                    )
                """,
                "useLegacySql": False
            }
        },
        location='US',
        gcp_conn_id='google_cloud_default',
    )

    # ==========================================================
    # STEP 2: LOAD SAMPLE DATA (HARDCODED SQL)
    # ==========================================================
    load_sample_data = BigQueryInsertJobOperator(
        task_id='load_sample_data',
        configuration={
            "query": {
                "query": f"""
                    -- Staging'e örnek veri yükle
                    -- Gerçek üretimde GCSToBigQueryOperator kullanılır

                    TRUNCATE TABLE `{PROJECT_ID}.{DATASET_STAGING}.sales_raw`;

                    INSERT INTO `{PROJECT_ID}.{DATASET_STAGING}.sales_raw`
                    (order_id, customer_id, product_id, product_name, category, quantity,
                     unit_price, total_amount, discount_amount, order_date, loaded_at)
                    VALUES
                        -- Electronics
                        ('ORD{{{{ ds_nodash }}}}001', 'CUST001', 'PROD001', 'Laptop Pro 15"', 'Electronics', 2, 4500.00, 9000.00, 500.00, '{{{{ ds }}}}', CURRENT_TIMESTAMP()),
                        ('ORD{{{{ ds_nodash }}}}002', 'CUST002', 'PROD002', 'Smartphone X', 'Electronics', 1, 3200.00, 3200.00, 0.00, '{{{{ ds }}}}', CURRENT_TIMESTAMP()),
                        ('ORD{{{{ ds_nodash }}}}003', 'CUST003', 'PROD003', 'Wireless Headphones', 'Electronics', 3, 850.00, 2550.00, 150.00, '{{{{ ds }}}}', CURRENT_TIMESTAMP()),
                        ('ORD{{{{ ds_nodash }}}}004', 'CUST001', 'PROD004', 'Tablet 10"', 'Electronics', 1, 1800.00, 1800.00, 100.00, '{{{{ ds }}}}', CURRENT_TIMESTAMP()),
                        ('ORD{{{{ ds_nodash }}}}005', 'CUST004', 'PROD005', '4K Monitor', 'Electronics', 2, 2200.00, 4400.00, 400.00, '{{{{ ds }}}}', CURRENT_TIMESTAMP()),

                        -- Fashion
                        ('ORD{{{{ ds_nodash }}}}006', 'CUST005', 'PROD006', 'Winter Jacket', 'Fashion', 1, 1200.00, 1200.00, 200.00, '{{{{ ds }}}}', CURRENT_TIMESTAMP()),
                        ('ORD{{{{ ds_nodash }}}}007', 'CUST002', 'PROD007', 'Running Shoes', 'Fashion', 2, 650.00, 1300.00, 0.00, '{{{{ ds }}}}', CURRENT_TIMESTAMP()),
                        ('ORD{{{{ ds_nodash }}}}008', 'CUST006', 'PROD008', 'Leather Bag', 'Fashion', 1, 850.00, 850.00, 50.00, '{{{{ ds }}}}', CURRENT_TIMESTAMP()),
                        ('ORD{{{{ ds_nodash }}}}009', 'CUST003', 'PROD009', 'Sunglasses', 'Fashion', 3, 320.00, 960.00, 60.00, '{{{{ ds }}}}', CURRENT_TIMESTAMP()),

                        -- Home
                        ('ORD{{{{ ds_nodash }}}}010', 'CUST007', 'PROD010', 'Coffee Maker', 'Home', 1, 450.00, 450.00, 50.00, '{{{{ ds }}}}', CURRENT_TIMESTAMP()),
                        ('ORD{{{{ ds_nodash }}}}011', 'CUST004', 'PROD011', 'Vacuum Cleaner', 'Home', 1, 1800.00, 1800.00, 0.00, '{{{{ ds }}}}', CURRENT_TIMESTAMP()),
                        ('ORD{{{{ ds_nodash }}}}012', 'CUST005', 'PROD012', 'Bed Sheets Set', 'Home', 2, 350.00, 700.00, 100.00, '{{{{ ds }}}}', CURRENT_TIMESTAMP()),
                        ('ORD{{{{ ds_nodash }}}}013', 'CUST008', 'PROD013', 'Kitchen Knife Set', 'Home', 1, 580.00, 580.00, 80.00, '{{{{ ds }}}}', CURRENT_TIMESTAMP()),

                        -- High value orders
                        ('ORD{{{{ ds_nodash }}}}014', 'CUST006', 'PROD014', 'Smart TV 65"', 'Electronics', 1, 8500.00, 8500.00, 1000.00, '{{{{ ds }}}}', CURRENT_TIMESTAMP()),
                        ('ORD{{{{ ds_nodash }}}}015', 'CUST007', 'PROD015', 'Gaming Console', 'Electronics', 1, 2800.00, 2800.00, 200.00, '{{{{ ds }}}}', CURRENT_TIMESTAMP());
                """,
                "useLegacySql": False
            }
        },
        location='US',
        gcp_conn_id='google_cloud_default',
    )

    # ==========================================================
    # STEP 3: TRANSFORM SALES DATA (EXTERNAL SQL)
    # ==========================================================
    transform_sales_data = BigQueryInsertJobOperator(
        task_id='transform_sales_data',
        configuration={
            "query": {
                "query": load_sql_file('01_transform_sales.sql'),
                "useLegacySql": False
            }
        },
        params={
            'project_id': PROJECT_ID,
            'staging_dataset': DATASET_STAGING,
            'datamart_dataset': DATASET_DATAMART,
        },
        location='US',
        gcp_conn_id='google_cloud_default',
    )

    # ==========================================================
    # STEP 4: CREATE SUMMARY REPORT (EXTERNAL SQL)
    # ==========================================================
    create_summary_report = BigQueryInsertJobOperator(
        task_id='create_summary_report',
        configuration={
            "query": {
                "query": load_sql_file('02_create_summary.sql'),
                "useLegacySql": False
            }
        },
        params={
            'project_id': PROJECT_ID,
            'datamart_dataset': DATASET_DATAMART,
        },
        location='US',
        gcp_conn_id='google_cloud_default',
    )

    # ==========================================================
    # STEP 5: RUN QUALITY CHECKS (EXTERNAL SQL)
    # ==========================================================
    run_quality_checks = BigQueryInsertJobOperator(
        task_id='run_quality_checks',
        configuration={
            "query": {
                "query": load_sql_file('03_quality_checks.sql'),
                "useLegacySql": False
            }
        },
        params={
            'project_id': PROJECT_ID,
            'datamart_dataset': DATASET_DATAMART,
        },
        location='US',
        gcp_conn_id='google_cloud_default',
    )

    # ========== LOGGING ==========
    log_complete = PythonOperator(
        task_id='log_pipeline_complete',
        python_callable=log_pipeline_complete,
    )

    end = DummyOperator(task_id='end')

    # ==========================================================
    # DEPENDENCIES
    # ==========================================================

    # Start
    start >> log_start

    # Staging (Hardcoded SQL)
    log_start >> create_staging_table >> load_sample_data

    # Transformation (External SQL)
    load_sample_data >> transform_sales_data

    # Summary Report (External SQL)
    transform_sales_data >> create_summary_report

    # Quality Checks (External SQL)
    create_summary_report >> run_quality_checks

    # Complete
    run_quality_checks >> log_complete >> end


# ========== DAG DOCUMENTATION ==========
dag.doc_md = """
# 📊 Datamart SQL Pipeline - Mixed Approach

## Genel Bakış

Bu DAG, **BigQuery ETL pipeline**'ında **hardcoded** ve **external SQL** scriptlerinin
birlikte kullanımını gösterir.

## SQL Yaklaşımları

### 🔹 Hardcoded SQL (Python İçinde)
Aşağıdaki taskler SQL'i doğrudan Python'da tanımlar:
- `create_staging_table` - Staging tablo oluşturma
- `load_sample_data` - Test verisi yükleme

**Avantajlar:**
- Hızlı değişiklik
- Airflow template değişkenleri kullanımı kolay
- Debugging kolay

### 🔹 External SQL (Dosyadan Okunur)
Aşağıdaki taskler SQL'i `sql/datamart/` dizininden okur:
- `transform_sales_data` → `01_transform_sales.sql`
- `create_summary_report` → `02_create_summary.sql`
- `run_quality_checks` → `03_quality_checks.sql`

**Avantajlar:**
- SQL'i version control'de ayrı takip edebilme
- SQL Developer'lar IDE'de çalışabilir
- Kod tekrarını önler
- Gerçek üretimde GCS bucket'dan okunabilir

## Pipeline Akışı

```
┌─────────────────────────────────────────────────────────────┐
│  STAGING LAYER (Hardcoded SQL)                              │
├─────────────────────────────────────────────────────────────┤
│  1. create_staging_table   → staging.sales_raw oluştur      │
│  2. load_sample_data        → Örnek veri yükle              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  DATAMART LAYER (External SQL)                              │
├─────────────────────────────────────────────────────────────┤
│  3. transform_sales_data    → datamart.sales_cleaned        │
│     (01_transform_sales.sql)                                │
│     • Veri temizleme                                        │
│     • Tarih dönüşümü                                        │
│     • Hesaplanan alanlar                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  REPORTING LAYER (External SQL)                             │
├─────────────────────────────────────────────────────────────┤
│  4. create_summary_report   → datamart.daily_sales_summary  │
│     (02_create_summary.sql)                                 │
│     • Günlük KPI'lar                                        │
│     • Kategori breakdown                                    │
│     • Veri kalitesi skorları                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  QUALITY CHECKS (External SQL)                              │
├─────────────────────────────────────────────────────────────┤
│  5. run_quality_checks      → Validation                    │
│     (03_quality_checks.sql)                                 │
│     • Row count, NULL check                                 │
│     • Duplicate check                                       │
│     • Business rule validation                              │
│     • ERROR() ile fail etme                                 │
└─────────────────────────────────────────────────────────────┘
```

## Katmanlı Mimari

| Layer | Tablo | Açıklama | SQL Tipi |
|-------|-------|----------|----------|
| **Staging** | `staging.sales_raw` | Ham CSV verisi | Hardcoded |
| **Datamart** | `datamart.sales_cleaned` | Temizlenmiş veri | External |
| **Reporting** | `datamart.daily_sales_summary` | Günlük özet | External |

## SQL Dosyaları

SQL scriptleri `sql/datamart/` dizininde:

1. **01_transform_sales.sql**
   - Staging → Datamart transformation
   - Veri temizleme ve zenginleştirme
   - Incremental load (bugünün verisi)

2. **02_create_summary.sql**
   - Günlük özet rapor
   - KPI hesaplamaları
   - MERGE ile upsert

3. **03_quality_checks.sql**
   - Çoklu veri kalitesi kontrolleri
   - ERROR() ile pipeline fail
   - Detaylı hata mesajları

## Test ve Çalıştırma

### Manuel Tetikleme
```bash
# DAG'i tetikle
airflow dags trigger 08_datamart_sql_pipeline

# WebUI'dan izle
open http://localhost:8080/dags/08_datamart_sql_pipeline/grid
```

### Backfill (Geçmiş Tarih)
```bash
# Belirli bir tarih için çalıştır
airflow dags backfill 08_datamart_sql_pipeline \\
    --start-date 2024-01-15 \\
    --end-date 2024-01-15
```

### Test Mode
```bash
# Tüm pipeline'ı test et
docker exec airflow-webserver-1 \\
    airflow dags test 08_datamart_sql_pipeline 2024-01-15

# Tek bir task'ı test et
docker exec airflow-webserver-1 \\
    airflow tasks test 08_datamart_sql_pipeline transform_sales_data 2024-01-15
```

## BigQuery'de Sorgular

### 1. Günlük Özet Raporu
```sql
SELECT *
FROM `{PROJECT_ID}.datamart.daily_sales_summary`
ORDER BY report_date DESC
LIMIT 7;
```

### 2. Kategori Bazlı Satışlar
```sql
SELECT
    category,
    COUNT(*) as order_count,
    SUM(net_amount) as total_sales,
    AVG(discount_percentage) as avg_discount_pct
FROM `{PROJECT_ID}.datamart.sales_cleaned`
GROUP BY category
ORDER BY total_sales DESC;
```

### 3. Veri Kalitesi Skoru
```sql
SELECT
    report_date,
    data_quality_score,
    valid_records_count,
    invalid_records_count
FROM `{PROJECT_ID}.datamart.daily_sales_summary`
ORDER BY report_date DESC
LIMIT 30;
```

## GCS Entegrasyonu (Gelecekte)

Gerçek üretimde SQL dosyaları GCS bucket'da tutulabilir:

```python
from google.cloud import storage

def load_sql_from_gcs(bucket_name: str, sql_file_name: str) -> str:
    \"\"\"GCS'den SQL dosyası oku\"\"\"
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(f'sql/datamart/{{sql_file_name}}')
    return blob.download_as_text()

# Kullanım
sql_content = load_sql_from_gcs('my-sql-scripts-bucket', '01_transform_sales.sql')
```

## Best Practices

### ✅ Hardcoded SQL Kullan:
- Basit CREATE/DROP operasyonları
- Test data insertion
- Single-use SQL'ler
- Hızlı prototipleme

### ✅ External SQL Kullan:
- Kompleks transformasyonlar
- Tekrar kullanılabilir SQL'ler
- SQL Developer collaboration
- Version control gereken SQL'ler
- Production ETL queries

## Monitoring

### Task Durumları
```bash
# Task loglarını görüntüle
airflow tasks logs 08_datamart_sql_pipeline transform_sales_data 2024-01-15
```

### BigQuery Job History
```sql
-- Son çalışan job'ları görüntüle
SELECT
    job_id,
    creation_time,
    user_email,
    statement_type,
    total_bytes_processed,
    total_slot_ms
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
ORDER BY creation_time DESC
LIMIT 20;
```

## Referanslar

- [BigQuery SQL Reference](https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax)
- [Airflow BigQuery Provider](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/bigquery.html)
- [08-sales-datamart-demo.md](../egitim-notlari/08-sales-datamart-demo.md)
"""
