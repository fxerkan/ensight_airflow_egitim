"""
DAG 9: Sales Datamart Pipeline ⭐ DEMO PROJECT

Uçtan uca çalışan Sales Datamart ETL Pipeline:
- Star Schema (Dimension + Fact tables)
- GCS → Staging → Dimensions → Fact
- SCD Type 1 (Slowly Changing Dimensions)
- Data Quality Checks
- Daily Summary Report

TABLES:
- DimCustomer: Müşteri bilgileri
- DimProduct: Ürün bilgileri
- DimDate: Tarih dimension
- FactSalesTransaction: Satış işlemleri (fact)
"""

from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime, timedelta
import os

# GCP Configuration
PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'MY_GCP_PROJECT_ID')
GCS_BUCKET = os.getenv('GCS_BUCKET', 'my-sales-data-bucket')
DATASET = 'sales_datamart'
STAGING_DATASET = 'staging'

default_args = {
    'owner': 'data-engineering-team',
    'depends_on_past': False,
    'email': ['data-team@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def log_pipeline_start(**kwargs):
    """Pipeline başlangıç logu"""
    print(f"\n{'🚀'*30}")
    print(f"  SALES DATAMART PIPELINE BAŞLADI")
    print(f"{'🚀'*30}")
    print(f"  Tarih: {kwargs['ds']}")
    print(f"  Execution Date: {kwargs['execution_date']}")
    print(f"  Project: {PROJECT_ID}")
    print(f"  Dataset: {DATASET}")
    print(f"{'='*60}\n")

def log_pipeline_complete(**kwargs):
    """Pipeline tamamlanma logu"""
    print(f"\n{'✅'*30}")
    print(f"  SALES DATAMART PIPELINE TAMAMLANDI")
    print(f"{'✅'*30}")
    print(f"  Tarih: {kwargs['ds']}")
    print(f"  Toplam Task: {len(kwargs['dag'].task_ids)}")
    print(f"  Durum: SUCCESS")
    print(f"{'='*60}\n")

with DAG(
    dag_id='09_sales_datamart_pipeline',
    default_args=default_args,
    description='⭐ Uçtan Uca Sales Datamart ETL Pipeline - Star Schema',
    schedule_interval='0 3 * * *',  # Her gün 03:00
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['demo', 'sales-datamart', 'star-schema', 'bigquery'],
    params={
        'project_id': PROJECT_ID,
        'dataset': DATASET,
        'gcs_bucket': GCS_BUCKET
    },
) as dag:

    # ========== BAŞLANGIÇ ==========
    start = DummyOperator(task_id='start')

    log_start = PythonOperator(
        task_id='log_pipeline_start',
        python_callable=log_pipeline_start,
    )

    # ========== EXTRACT: GCS SENSORS ==========
    check_customers_file = GCSObjectExistenceSensor(
        task_id='check_customers_file',
        bucket=GCS_BUCKET,
        object='raw/customers_{{ ds_nodash }}.csv',
        timeout=600,
        poke_interval=30,
        mode='poke',
        soft_fail=True,  # Demo için - gerçek üretimde False olmalı
    )

    check_products_file = GCSObjectExistenceSensor(
        task_id='check_products_file',
        bucket=GCS_BUCKET,
        object='raw/products_{{ ds_nodash }}.csv',
        timeout=600,
        poke_interval=30,
        mode='poke',
        soft_fail=True,
    )

    check_transactions_file = GCSObjectExistenceSensor(
        task_id='check_transactions_file',
        bucket=GCS_BUCKET,
        object='raw/transactions_{{ ds_nodash }}.csv',
        timeout=600,
        poke_interval=30,
        mode='poke',
        soft_fail=True,
    )

    # ========== EXTRACT: LOAD TO STAGING ==========
    load_customers_staging = GCSToBigQueryOperator(
        task_id='load_customers_staging',
        bucket=GCS_BUCKET,
        source_objects=['raw/customers_{{ ds_nodash }}.csv'],
        destination_project_dataset_table=f'{PROJECT_ID}.{STAGING_DATASET}.customers_raw',
        schema_fields=[
            {'name': 'customer_id', 'type': 'STRING'},
            {'name': 'customer_name', 'type': 'STRING'},
            {'name': 'email', 'type': 'STRING'},
            {'name': 'city', 'type': 'STRING'},
            {'name': 'country', 'type': 'STRING'},
            {'name': 'created_date', 'type': 'STRING'},
        ],
        write_disposition='WRITE_TRUNCATE',
        skip_leading_rows=1,
        autodetect=False,
    )

    load_products_staging = GCSToBigQueryOperator(
        task_id='load_products_staging',
        bucket=GCS_BUCKET,
        source_objects=['raw/products_{{ ds_nodash }}.csv'],
        destination_project_dataset_table=f'{PROJECT_ID}.{STAGING_DATASET}.products_raw',
        schema_fields=[
            {'name': 'product_id', 'type': 'STRING'},
            {'name': 'product_name', 'type': 'STRING'},
            {'name': 'category', 'type': 'STRING'},
            {'name': 'subcategory', 'type': 'STRING'},
            {'name': 'unit_price', 'type': 'FLOAT'},
        ],
        write_disposition='WRITE_TRUNCATE',
        skip_leading_rows=1,
        autodetect=False,
    )

    load_transactions_staging = GCSToBigQueryOperator(
        task_id='load_transactions_staging',
        bucket=GCS_BUCKET,
        source_objects=['raw/transactions_{{ ds_nodash }}.csv'],
        destination_project_dataset_table=f'{PROJECT_ID}.{STAGING_DATASET}.transactions_raw',
        schema_fields=[
            {'name': 'transaction_id', 'type': 'STRING'},
            {'name': 'customer_id', 'type': 'STRING'},
            {'name': 'product_id', 'type': 'STRING'},
            {'name': 'quantity', 'type': 'INTEGER'},
            {'name': 'unit_price', 'type': 'FLOAT'},
            {'name': 'total_amount', 'type': 'FLOAT'},
            {'name': 'discount_amount', 'type': 'FLOAT'},
            {'name': 'transaction_timestamp', 'type': 'STRING'},
        ],
        write_disposition='WRITE_TRUNCATE',
        skip_leading_rows=1,
        autodetect=False,
    )

    # ========== TRANSFORM: DIMENSION TABLES ==========

    # DIMDATE: Tarih dimension'ı (one-time population, idempotent)
    populate_dim_date = BigQueryInsertJobOperator(
        task_id='populate_dim_date',
        configuration={
            "query": {
                "query": f"""
                    -- DimDate tablosunu doldur (2020-2030)
                    CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.{DATASET}.DimDate` (
                        date_key INT64,
                        full_date DATE,
                        year INT64,
                        quarter INT64,
                        month INT64,
                        month_name STRING,
                        week INT64,
                        day INT64,
                        day_name STRING,
                        is_weekend BOOL,
                        is_holiday BOOL
                    );

                    MERGE `{PROJECT_ID}.{DATASET}.DimDate` T
                    USING (
                        SELECT
                            CAST(FORMAT_DATE('%Y%m%d', date) AS INT64) as date_key,
                            date as full_date,
                            EXTRACT(YEAR FROM date) as year,
                            EXTRACT(QUARTER FROM date) as quarter,
                            EXTRACT(MONTH FROM date) as month,
                            FORMAT_DATE('%B', date) as month_name,
                            EXTRACT(WEEK FROM date) as week,
                            EXTRACT(DAY FROM date) as day,
                            FORMAT_DATE('%A', date) as day_name,
                            CASE WHEN EXTRACT(DAYOFWEEK FROM date) IN (1, 7) THEN TRUE ELSE FALSE END as is_weekend,
                            FALSE as is_holiday
                        FROM
                            UNNEST(GENERATE_DATE_ARRAY('2020-01-01', '2030-12-31')) as date
                    ) S
                    ON T.date_key = S.date_key
                    WHEN NOT MATCHED THEN
                        INSERT (date_key, full_date, year, quarter, month, month_name, week, day, day_name, is_weekend, is_holiday)
                        VALUES (S.date_key, S.full_date, S.year, S.quarter, S.month, S.month_name, S.week, S.day, S.day_name, S.is_weekend, S.is_holiday)
                """,
                "useLegacySql": False
            }
        },
        location='US',
    )

    # DIMCUSTOMER: Müşteri dimension (SCD Type 1 - en son durum)
    upsert_dim_customer = BigQueryInsertJobOperator(
        task_id='upsert_dim_customer',
        configuration={
            "query": {
                "query": f"""
                    -- DimCustomer tablosunu oluştur/güncelle
                    CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.{DATASET}.DimCustomer` (
                        customer_key INT64,
                        customer_id STRING,
                        customer_name STRING,
                        email STRING,
                        city STRING,
                        country STRING,
                        created_date DATE,
                        effective_date TIMESTAMP,
                        is_current BOOL
                    )
                    PARTITION BY DATE(effective_date)
                    CLUSTER BY customer_id;

                    MERGE `{PROJECT_ID}.{DATASET}.DimCustomer` T
                    USING (
                        SELECT
                            FARM_FINGERPRINT(customer_id) as customer_key,
                            customer_id,
                            customer_name,
                            email,
                            city,
                            country,
                            PARSE_DATE('%Y-%m-%d', created_date) as created_date,
                            CURRENT_TIMESTAMP() as effective_date,
                            TRUE as is_current
                        FROM `{PROJECT_ID}.{STAGING_DATASET}.customers_raw`
                    ) S
                    ON T.customer_id = S.customer_id
                    WHEN MATCHED THEN
                        UPDATE SET
                            customer_name = S.customer_name,
                            email = S.email,
                            city = S.city,
                            country = S.country,
                            effective_date = S.effective_date
                    WHEN NOT MATCHED THEN
                        INSERT (customer_key, customer_id, customer_name, email, city, country, created_date, effective_date, is_current)
                        VALUES (S.customer_key, S.customer_id, S.customer_name, S.email, S.city, S.country, S.created_date, S.effective_date, S.is_current)
                """,
                "useLegacySql": False
            }
        },
        location='US',
    )

    # DIMPRODUCT: Ürün dimension (SCD Type 1)
    upsert_dim_product = BigQueryInsertJobOperator(
        task_id='upsert_dim_product',
        configuration={
            "query": {
                "query": f"""
                    -- DimProduct tablosunu oluştur/güncelle
                    CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.{DATASET}.DimProduct` (
                        product_key INT64,
                        product_id STRING,
                        product_name STRING,
                        category STRING,
                        subcategory STRING,
                        unit_price FLOAT64,
                        effective_date TIMESTAMP,
                        is_current BOOL
                    )
                    PARTITION BY DATE(effective_date)
                    CLUSTER BY product_id;

                    MERGE `{PROJECT_ID}.{DATASET}.DimProduct` T
                    USING (
                        SELECT
                            FARM_FINGERPRINT(product_id) as product_key,
                            product_id,
                            product_name,
                            category,
                            subcategory,
                            CAST(unit_price AS FLOAT64) as unit_price,
                            CURRENT_TIMESTAMP() as effective_date,
                            TRUE as is_current
                        FROM `{PROJECT_ID}.{STAGING_DATASET}.products_raw`
                    ) S
                    ON T.product_id = S.product_id
                    WHEN MATCHED THEN
                        UPDATE SET
                            product_name = S.product_name,
                            category = S.category,
                            subcategory = S.subcategory,
                            unit_price = S.unit_price,
                            effective_date = S.effective_date
                    WHEN NOT MATCHED THEN
                        INSERT (product_key, product_id, product_name, category, subcategory, unit_price, effective_date, is_current)
                        VALUES (S.product_key, S.product_id, S.product_name, S.category, S.subcategory, S.unit_price, S.effective_date, S.is_current)
                """,
                "useLegacySql": False
            }
        },
        location='US',
    )

    # ========== LOAD: FACT TABLE ==========
    insert_fact_sales = BigQueryInsertJobOperator(
        task_id='insert_fact_sales',
        configuration={
            "query": {
                "query": f"""
                    -- FactSalesTransaction tablosu
                    CREATE TABLE IF NOT EXISTS `{PROJECT_ID}.{DATASET}.FactSalesTransaction` (
                        transaction_id STRING,
                        date_key INT64,
                        customer_key INT64,
                        product_key INT64,
                        quantity INT64,
                        unit_price FLOAT64,
                        total_amount FLOAT64,
                        discount_amount FLOAT64,
                        net_amount FLOAT64,
                        transaction_timestamp TIMESTAMP
                    )
                    PARTITION BY DATE(transaction_timestamp)
                    CLUSTER BY customer_key, product_key;

                    INSERT INTO `{PROJECT_ID}.{DATASET}.FactSalesTransaction`
                    SELECT
                        t.transaction_id,
                        CAST(FORMAT_TIMESTAMP('%Y%m%d', PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', t.transaction_timestamp)) AS INT64) as date_key,
                        FARM_FINGERPRINT(t.customer_id) as customer_key,
                        FARM_FINGERPRINT(t.product_id) as product_key,
                        CAST(t.quantity AS INT64) as quantity,
                        CAST(t.unit_price AS FLOAT64) as unit_price,
                        CAST(t.total_amount AS FLOAT64) as total_amount,
                        CAST(t.discount_amount AS FLOAT64) as discount_amount,
                        CAST(t.total_amount - t.discount_amount AS FLOAT64) as net_amount,
                        PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', t.transaction_timestamp) as transaction_timestamp
                    FROM `{PROJECT_ID}.{STAGING_DATASET}.transactions_raw` t
                    WHERE DATE(PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', t.transaction_timestamp)) = '{{ ds }}'
                """,
                "useLegacySql": False
            }
        },
        location='US',
    )

    # ========== DATA QUALITY CHECKS ==========
    validate_fact_count = BigQueryInsertJobOperator(
        task_id='validate_fact_count',
        configuration={
            "query": {
                "query": f"""
                    SELECT
                        CASE
                            WHEN COUNT(*) = 0 THEN ERROR('Fact tabloya veri eklenmedi!')
                            ELSE 'VALIDATION_PASSED'
                        END as validation
                    FROM `{PROJECT_ID}.{DATASET}.FactSalesTransaction`
                    WHERE DATE(transaction_timestamp) = '{{ ds }}'
                """,
                "useLegacySql": False
            }
        },
        location='US',
    )

    # ========== REPORTING ==========
    create_daily_report = BigQueryInsertJobOperator(
        task_id='create_daily_report',
        configuration={
            "query": {
                "query": f"""
                    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.DailySalesReport` AS
                    SELECT
                        d.full_date,
                        d.day_name,
                        d.is_weekend,
                        COUNT(DISTINCT f.transaction_id) as total_transactions,
                        COUNT(DISTINCT f.customer_key) as unique_customers,
                        COUNT(DISTINCT f.product_key) as unique_products,
                        SUM(f.quantity) as total_quantity,
                        SUM(f.total_amount) as total_sales,
                        SUM(f.discount_amount) as total_discounts,
                        SUM(f.net_amount) as net_sales,
                        AVG(f.net_amount) as avg_transaction_value,
                        MIN(f.net_amount) as min_transaction,
                        MAX(f.net_amount) as max_transaction,
                        CURRENT_TIMESTAMP() as report_generated_at
                    FROM `{PROJECT_ID}.{DATASET}.FactSalesTransaction` f
                    JOIN `{PROJECT_ID}.{DATASET}.DimDate` d ON f.date_key = d.date_key
                    WHERE d.full_date = '{{ ds }}'
                    GROUP BY d.full_date, d.day_name, d.is_weekend
                """,
                "useLegacySql": False
            }
        },
        location='US',
    )

    # ========== BİTİŞ ==========
    log_complete = PythonOperator(
        task_id='log_pipeline_complete',
        python_callable=log_pipeline_complete,
    )

    end = DummyOperator(task_id='end')

    # ========== DEPENDENCIES ==========

    # Start
    start >> log_start

    # Extract: File checks
    log_start >> [check_customers_file, check_products_file, check_transactions_file]

    # Load to Staging
    check_customers_file >> load_customers_staging
    check_products_file >> load_products_staging
    check_transactions_file >> load_transactions_staging

    # Transform Dimensions
    load_customers_staging >> upsert_dim_customer
    load_products_staging >> upsert_dim_product
    load_transactions_staging >> populate_dim_date

    # Load Fact (wait for all dimensions)
    [upsert_dim_customer, upsert_dim_product, populate_dim_date] >> insert_fact_sales

    # Validation
    insert_fact_sales >> validate_fact_count

    # Reporting
    validate_fact_count >> create_daily_report

    # Complete
    create_daily_report >> log_complete >> end

# DAG Documentation
dag.doc_md = """
# 🌟 Sales Datamart Pipeline - Demo Project

## Genel Bakış
Uçtan uca çalışan **Star Schema** tabanlı Sales Datamart ETL pipeline'ı.

## Mimari: Star Schema

### Dimension Tables
- **DimCustomer**: Müşteri bilgileri (SCD Type 1)
- **DimProduct**: Ürün katalog (SCD Type 1)
- **DimDate**: Tarih dimension (2020-2030)

### Fact Table
- **FactSalesTransaction**: Satış işlemleri (partitioned by date)

## Pipeline Akışı

```
GCS Files → Staging → Dimensions → Fact → Quality Check → Report
```

1. **Extract**: GCS'den CSV dosyaları kontrol ve yükleme
2. **Transform**: Dimension tablolarını doldur/güncelle
3. **Load**: Fact tablosuna işlemleri ekle
4. **Validate**: Data quality checks
5. **Report**: Günlük satış raporu oluştur

## Veri Akışı

```
customers.csv    →  staging.customers_raw    →  DimCustomer
products.csv     →  staging.products_raw     →  DimProduct
transactions.csv →  staging.transactions_raw →  FactSalesTransaction
                                              →  DailySalesReport
```

## Test Etmek İçin

```bash
# 1. Test verisi oluştur
python scripts/generate_test_data.py

# 2. GCS'e yükle (gerçek ortamda)
gsutil cp data/*.csv gs://{GCS_BUCKET}/raw/

# 3. DAG'i manuel tetikle
airflow dags trigger 09_sales_datamart_pipeline

# 4. WebUI'dan izle
# http://localhost:8080/dags/09_sales_datamart_pipeline/grid
```

## Sorgular

### Günlük Satış Özeti
```sql
SELECT * FROM `{PROJECT_ID}.{DATASET}.DailySalesReport`
ORDER BY full_date DESC
LIMIT 7
```

### Top 10 Müşteri
```sql
SELECT
    c.customer_name,
    c.city,
    COUNT(f.transaction_id) as order_count,
    SUM(f.net_amount) as total_spent
FROM `{PROJECT_ID}.{DATASET}.FactSalesTransaction` f
JOIN `{PROJECT_ID}.{DATASET}.DimCustomer` c ON f.customer_key = c.customer_key
GROUP BY c.customer_name, c.city
ORDER BY total_spent DESC
LIMIT 10
```
"""
