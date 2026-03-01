# Sales Datamart Pipeline - Demo Projesi

## İçindekiler
1. [Proje Genel Bakış](#proje-genel-bakis)
2. [Star Schema Mimarisi](#star-schema-mimarisi)
3. [Dimension Tables](#dimension-tables)
4. [Fact Table](#fact-table)
5. [DAG Pipeline Akışı](#dag-pipeline-akisi)
6. [Kod Açıklaması](#kod-aciklamasi)
7. [Test ve Çalıştırma](#test-ve-calistirma)
8. [Sorgular ve Analizler](#sorgular-ve-analizler)
9. [Referanslar](#referanslar)

---

## Proje Genel Bakış

**Sales Datamart Pipeline**, uçtan uca çalışan bir veri ambarı (data warehouse) ETL projesidir.

### Özellikler

- ✅ **Star Schema** mimarisi
- ✅ **Dimension Tables** (DimCustomer, DimProduct, DimDate)
- ✅ **Fact Table** (FactSalesTransaction)
- ✅ **SCD Type 1** (Slowly Changing Dimensions)
- ✅ **Incremental Loading**
- ✅ **Data Quality Checks**
- ✅ **Daily Reporting**

### Teknoloji Stack'i

| Katman | Teknoloji |
|--------|-----------|
| **Orchestration** | Apache Airflow |
| **Data Warehouse** | Google BigQuery |
| **Storage** | Google Cloud Storage (GCS) |
| **Source Data** | CSV Files |
| **Scheduling** | Cron (daily 03:00) |

---

## Star Schema Mimarisi

### Star Schema Nedir?

**Star Schema**, fact table'ı merkezde, dimension table'ları etrafında olan bir veri modelleme tekniğidir.

```
                    ┌──────────────┐
                    │  DimCustomer │
                    └───────┬──────┘
                            │
┌──────────────┐    ┌───────▼──────────────┐    ┌──────────────┐
│  DimProduct  │────│ FactSalesTransaction │────│   DimDate    │
└──────────────┘    └──────────────────────┘    └──────────────┘
```

### Avantajları

- ✅ **Basit ve Anlaşılır**: İş kullanıcıları kolayca anlayabilir
- ✅ **Performanslı**: Query'ler hızlı çalışır
- ✅ **Ölçeklenebilir**: Yeni dimension eklemek kolay
- ✅ **BI Tool Friendly**: Power BI, Tableau ile uyumlu

### Projemizdeki Star Schema

```
DimCustomer (Müşteri Bilgileri)
├── customer_key (PK)
├── customer_id (Business Key)
├── customer_name
├── email
├── city
├── country
└── created_date

DimProduct (Ürün Katalog)
├── product_key (PK)
├── product_id (Business Key)
├── product_name
├── category
├── subcategory
└── unit_price

DimDate (Tarih Dimension)
├── date_key (PK - YYYYMMDD format)
├── full_date
├── year, quarter, month, week, day
├── month_name, day_name
└── is_weekend, is_holiday

FactSalesTransaction (Satış İşlemleri)
├── transaction_id (PK)
├── date_key (FK → DimDate)
├── customer_key (FK → DimCustomer)
├── product_key (FK → DimProduct)
├── quantity
├── unit_price
├── total_amount
├── discount_amount
├── net_amount
└── transaction_timestamp
```

---

## Dimension Tables

### DimCustomer

**Müşteri bilgilerini saklar.**

```sql
CREATE TABLE `project.sales_datamart.DimCustomer` (
    customer_key INT64,              -- Surrogate key (hash)
    customer_id STRING,               -- Business key
    customer_name STRING,
    email STRING,
    city STRING,
    country STRING,
    created_date DATE,
    effective_date TIMESTAMP,         -- SCD için
    is_current BOOL                   -- SCD için
)
PARTITION BY DATE(effective_date)
CLUSTER BY customer_id;
```

**SCD Type 1:**
- En güncel durum saklanır
- Değişiklik olunca UPDATE yapılır
- Geçmiş değerler saklanmaz

**Upsert Mantığı:**
```sql
MERGE DimCustomer T
USING staging.customers_raw S
ON T.customer_id = S.customer_id
WHEN MATCHED THEN
    UPDATE SET
        customer_name = S.customer_name,
        email = S.email,
        effective_date = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
    INSERT (customer_key, customer_id, customer_name, ...)
    VALUES (FARM_FINGERPRINT(S.customer_id), S.customer_id, S.customer_name, ...)
```

### DimProduct

**Ürün kataloğunu saklar.**

```sql
CREATE TABLE `project.sales_datamart.DimProduct` (
    product_key INT64,                -- Surrogate key
    product_id STRING,                -- Business key
    product_name STRING,
    category STRING,
    subcategory STRING,
    unit_price FLOAT64,
    effective_date TIMESTAMP,
    is_current BOOL
)
PARTITION BY DATE(effective_date)
CLUSTER BY product_id;
```

**Kategori Hiyerarşisi:**
```
Electronics
├── Laptops
│   ├── Gaming Laptops
│   └── Business Laptops
└── Phones
    ├── Smartphones
    └── Feature Phones
```

### DimDate

**Tarih dimension'ı. 2020-2030 arası tüm günleri içerir.**

```sql
CREATE TABLE `project.sales_datamart.DimDate` (
    date_key INT64,                   -- 20240101 format
    full_date DATE,                   -- 2024-01-01
    year INT64,                       -- 2024
    quarter INT64,                    -- 1 (Q1)
    month INT64,                      -- 1 (Ocak)
    month_name STRING,                -- 'January'
    week INT64,                       -- 1 (yılın 1. haftası)
    day INT64,                        -- 1
    day_name STRING,                  -- 'Monday'
    is_weekend BOOL,                  -- True/False
    is_holiday BOOL                   -- True/False (manual set)
);
```

**Populate:**
```sql
INSERT INTO DimDate
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
FROM UNNEST(GENERATE_DATE_ARRAY('2020-01-01', '2030-12-31')) as date
```

**Kullanım:**
- Trend analizi (aylık, çeyreksel, yıllık)
- Hafta sonu vs hafta içi karşılaştırma
- Tatil günleri analizi

---

## Fact Table

### FactSalesTransaction

**Her satış işlemini saklar.**

```sql
CREATE TABLE `project.sales_datamart.FactSalesTransaction` (
    transaction_id STRING,             -- PK
    date_key INT64,                    -- FK → DimDate
    customer_key INT64,                -- FK → DimCustomer
    product_key INT64,                 -- FK → DimProduct
    quantity INT64,                    -- Measures
    unit_price FLOAT64,
    total_amount FLOAT64,
    discount_amount FLOAT64,
    net_amount FLOAT64,                -- Calculated: total - discount
    transaction_timestamp TIMESTAMP
)
PARTITION BY DATE(transaction_timestamp)
CLUSTER BY customer_key, product_key;
```

**Measures (Ölçüler):**
- `quantity`: Satılan ürün adedi
- `unit_price`: Birim fiyat
- `total_amount`: Toplam tutar (brüt)
- `discount_amount`: İndirim tutarı
- `net_amount`: Net tutar (total - discount)

**Foreign Keys:**
- `date_key` → DimDate.date_key
- `customer_key` → DimCustomer.customer_key
- `product_key` → DimProduct.product_key

**Insert Mantığı:**
```sql
INSERT INTO FactSalesTransaction
SELECT
    t.transaction_id,
    CAST(FORMAT_TIMESTAMP('%Y%m%d', timestamp) AS INT64) as date_key,
    FARM_FINGERPRINT(t.customer_id) as customer_key,
    FARM_FINGERPRINT(t.product_id) as product_key,
    t.quantity,
    t.unit_price,
    t.total_amount,
    t.discount_amount,
    t.total_amount - t.discount_amount as net_amount,
    PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', t.transaction_timestamp)
FROM staging.transactions_raw t
WHERE DATE(PARSE_TIMESTAMP(...)) = '{{ ds }}'
```

---

## DAG Pipeline Akışı

Dosya: `dags/09_sales_datamart_pipeline.py`

### Pipeline Adımları

```
1. START
2. Log Pipeline Start
3. EXTRACT Phase (Parallel)
   ├── Check customers.csv (GCS Sensor)
   ├── Check products.csv (GCS Sensor)
   └── Check transactions.csv (GCS Sensor)
4. LOAD TO STAGING (Parallel)
   ├── Load customers → staging.customers_raw
   ├── Load products → staging.products_raw
   └── Load transactions → staging.transactions_raw
5. TRANSFORM DIMENSIONS (Parallel)
   ├── Populate DimDate
   ├── Upsert DimCustomer
   └── Upsert DimProduct
6. LOAD FACT
   └── Insert into FactSalesTransaction
7. VALIDATE
   └── Data Quality Check
8. REPORT
   └── Create DailySalesReport
9. Log Pipeline Complete
10. END
```

### Görsel Pipeline

```
                              ┌─ check_customers ─ load_customers ─ upsert_customer ─┐
                              │                                                       │
start ─ log_start ────────────┼─ check_products ── load_products ── upsert_product ──┼─ insert_fact ─ validate ─ report ─ log_complete ─ end
                              │                                                       │
                              └─ check_transactions load_transactions populate_date ─┘
```

---

## Kod Açıklaması

### 1. GCS Sensor (File Check)

```python
check_customers_file = GCSObjectExistenceSensor(
    task_id='check_customers_file',
    bucket=GCS_BUCKET,
    object='raw/customers_{{ ds_nodash }}.csv',  # customers_20240101.csv
    timeout=600,        # 10 dakika bekle
    poke_interval=30,   # 30 saniyede bir kontrol et
    mode='poke',
    soft_fail=True      # Demo için - prod'da False
)
```

**Açıklama:**
- GCS'de dosya var mı kontrol eder
- `{{ ds_nodash }}`: YYYYMMDD format (20240101)
- `soft_fail=True`: Dosya yoksa skip et, fail etme (demo için)

### 2. GCSToBigQueryOperator (Staging Load)

```python
load_customers_staging = GCSToBigQueryOperator(
    task_id='load_customers_staging',
    bucket=GCS_BUCKET,
    source_objects=['raw/customers_{{ ds_nodash }}.csv'],
    destination_project_dataset_table=f'{PROJECT_ID}.staging.customers_raw',
    schema_fields=[
        {'name': 'customer_id', 'type': 'STRING'},
        {'name': 'customer_name', 'type': 'STRING'},
        {'name': 'email', 'type': 'STRING'},
        {'name': 'city', 'type': 'STRING'},
        {'name': 'country', 'type': 'STRING'},
    ],
    write_disposition='WRITE_TRUNCATE',  # Her seferinde üzerine yaz
    skip_leading_rows=1,  # Header row
    autodetect=False
)
```

### 3. Dimension Upsert (MERGE)

```python
upsert_dim_customer = BigQueryInsertJobOperator(
    task_id='upsert_dim_customer',
    configuration={
        "query": {
            "query": f"""
                -- Tablo yoksa oluştur
                CREATE TABLE IF NOT EXISTS `{PROJECT}.sales_datamart.DimCustomer` (
                    customer_key INT64,
                    customer_id STRING,
                    ...
                )
                PARTITION BY DATE(effective_date)
                CLUSTER BY customer_id;

                -- Upsert yap
                MERGE DimCustomer T
                USING staging.customers_raw S
                ON T.customer_id = S.customer_id
                WHEN MATCHED THEN
                    UPDATE SET
                        customer_name = S.customer_name,
                        email = S.email,
                        effective_date = CURRENT_TIMESTAMP()
                WHEN NOT MATCHED THEN
                    INSERT (customer_key, customer_id, ...)
                    VALUES (FARM_FINGERPRINT(S.customer_id), S.customer_id, ...)
            """,
            "useLegacySql": False
        }
    }
)
```

**FARM_FINGERPRINT:**
- String'i INT64'e hash eder
- Surrogate key oluşturmak için kullanılır
- Deterministic (aynı input → aynı output)

### 4. Fact Insert

```python
insert_fact_sales = BigQueryInsertJobOperator(
    task_id='insert_fact_sales',
    configuration={
        "query": {
            "query": f"""
                INSERT INTO FactSalesTransaction
                SELECT
                    t.transaction_id,
                    CAST(FORMAT_TIMESTAMP('%Y%m%d', timestamp) AS INT64) as date_key,
                    FARM_FINGERPRINT(t.customer_id) as customer_key,
                    FARM_FINGERPRINT(t.product_id) as product_key,
                    t.quantity,
                    t.unit_price,
                    t.total_amount,
                    t.discount_amount,
                    t.total_amount - t.discount_amount as net_amount,
                    PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', t.transaction_timestamp)
                FROM staging.transactions_raw t
                WHERE DATE(PARSE_TIMESTAMP(...)) = '{{{{ ds }}}}'  # Incremental
            """,
            "useLegacySql": False
        }
    }
)
```

**Incremental Loading:**
- `WHERE DATE(...) = '{{ ds }}'`: Sadece bugünün verisi
- Her gün çalıştığında sadece o günün verisi eklenir

### 5. Data Quality Check

```python
validate_fact_count = BigQueryInsertJobOperator(
    task_id='validate_fact_count',
    configuration={
        "query": {
            "query": f"""
                SELECT
                    CASE
                        WHEN COUNT(*) = 0 THEN ERROR('Fact tabloya veri eklenmedi!')
                        ELSE 'VALIDATION_PASSED'
                    END
                FROM FactSalesTransaction
                WHERE DATE(transaction_timestamp) = '{{{{ ds }}}}'
            """,
            "useLegacySql": False
        }
    }
)
```

### 6. Daily Report

```python
create_daily_report = BigQueryInsertJobOperator(
    task_id='create_daily_report',
    configuration={
        "query": {
            "query": f"""
                CREATE OR REPLACE TABLE DailySalesReport AS
                SELECT
                    d.full_date,
                    d.day_name,
                    COUNT(DISTINCT f.transaction_id) as total_transactions,
                    COUNT(DISTINCT f.customer_key) as unique_customers,
                    SUM(f.quantity) as total_quantity,
                    SUM(f.net_amount) as net_sales,
                    AVG(f.net_amount) as avg_transaction_value
                FROM FactSalesTransaction f
                JOIN DimDate d ON f.date_key = d.date_key
                WHERE d.full_date = '{{{{ ds }}}}'
                GROUP BY d.full_date, d.day_name
            """,
            "useLegacySql": False
        }
    }
)
```

---

## Test ve Çalıştırma

### 1. Test Verisi Oluşturma

```bash
# Script ile test verisi oluştur
python scripts/generate_test_data.py
```

**Oluşturulacak dosyalar:**
- `data/customers_20240101.csv`
- `data/products_20240101.csv`
- `data/transactions_20240101.csv`

### 2. DAG'i Test Etme

```bash
# DAG'i test et
docker exec airflow-webserver-1 \
  airflow dags test 09_sales_datamart_pipeline 2024-01-01

# Tek bir task'ı test et
docker exec airflow-webserver-1 \
  airflow tasks test 09_sales_datamart_pipeline upsert_dim_customer 2024-01-01
```

### 3. Manuel Tetikleme

**WebUI'dan:**
1. http://localhost:8080 → DAGs
2. `09_sales_datamart_pipeline` bulun
3. ▶️ Play butonuna tıklayın

**CLI'dan:**
```bash
docker exec airflow-webserver-1 \
  airflow dags trigger 09_sales_datamart_pipeline
```

---

## Sorgular ve Analizler

### 1. Günlük Satış Özeti

```sql
SELECT *
FROM `project.sales_datamart.DailySalesReport`
ORDER BY full_date DESC
LIMIT 7
```

### 2. Top 10 Müşteri (En Yüksek Harcama)

```sql
SELECT
    c.customer_name,
    c.city,
    c.country,
    COUNT(f.transaction_id) as order_count,
    SUM(f.net_amount) as total_spent,
    AVG(f.net_amount) as avg_order_value
FROM FactSalesTransaction f
JOIN DimCustomer c ON f.customer_key = c.customer_key
GROUP BY c.customer_name, c.city, c.country
ORDER BY total_spent DESC
LIMIT 10
```

### 3. Kategori Bazlı Satış Analizi

```sql
SELECT
    p.category,
    p.subcategory,
    COUNT(f.transaction_id) as order_count,
    SUM(f.quantity) as total_quantity,
    SUM(f.net_amount) as net_sales,
    SUM(f.discount_amount) as total_discounts
FROM FactSalesTransaction f
JOIN DimProduct p ON f.product_key = p.product_key
GROUP BY p.category, p.subcategory
ORDER BY net_sales DESC
```

### 4. Aylık Trend Analizi

```sql
SELECT
    d.year,
    d.month,
    d.month_name,
    COUNT(DISTINCT f.transaction_id) as total_transactions,
    COUNT(DISTINCT f.customer_key) as unique_customers,
    SUM(f.net_amount) as net_sales,
    AVG(f.net_amount) as avg_transaction_value
FROM FactSalesTransaction f
JOIN DimDate d ON f.date_key = d.date_key
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month
```

### 5. Hafta Sonu vs Hafta İçi Karşılaştırma

```sql
SELECT
    CASE WHEN d.is_weekend THEN 'Weekend' ELSE 'Weekday' END as day_type,
    COUNT(f.transaction_id) as total_transactions,
    SUM(f.net_amount) as net_sales,
    AVG(f.net_amount) as avg_transaction_value
FROM FactSalesTransaction f
JOIN DimDate d ON f.date_key = d.date_key
GROUP BY day_type
```

---

## Referanslar

### Star Schema
- [Kimball Star Schema](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/star-schema-olap-cube/)
- [BigQuery Best Practices - Schema Design](https://cloud.google.com/bigquery/docs/best-practices-performance-patterns)

### Slowly Changing Dimensions (SCD)
- [SCD Type 1, 2, 3 Explained](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-2/)

---

## Star Schema Detaylı Diagram (ASCII Art)

```
                    FACT TABLE (Center)
            ╔═══════════════════════════════╗
            ║  FactSalesTransaction         ║
            ╟───────────────────────────────╢
            ║ • transaction_id (PK)         ║
            ║ • date_key (FK)        ───┐   ║
            ║ • customer_key (FK)    ───┼───╬──┐
            ║ • product_key (FK)     ───┼───╬──┼───┐
            ║                            │   ║  │   │
            ║ MEASURES:                  │   ║  │   │
            ║ • quantity                 │   ║  │   │
            ║ • unit_price               │   ║  │   │
            ║ • total_amount             │   ║  │   │
            ║ • discount_amount          │   ║  │   │
            ║ • net_amount               │   ║  │   │
            ║ • transaction_timestamp    │   ║  │   │
            ╚═══════════════════════════════╝  │   │
                            │                  │   │
            ┌───────────────┘                  │   │
            │                                  │   │
            ▼                                  ▼   ▼
    ╔═══════════════╗              ╔═══════════════╗  ╔═══════════════╗
    ║   DimDate     ║              ║  DimCustomer  ║  ║  DimProduct   ║
    ╟───────────────╢              ╟───────────────╢  ╟───────────────╢
    ║ date_key (PK) ║              ║ cust_key (PK) ║  ║ prod_key (PK) ║
    ║ full_date     ║              ║ customer_id   ║  ║ product_id    ║
    ║ year          ║              ║ cust_name     ║  ║ product_name  ║
    ║ quarter       ║              ║ email         ║  ║ category      ║
    ║ month         ║              ║ city          ║  ║ subcategory   ║
    ║ month_name    ║              ║ country       ║  ║ unit_price    ║
    ║ week          ║              ║ created_date  ║  ║ effective_dt  ║
    ║ day           ║              ║ effective_dt  ║  ║ is_current    ║
    ║ day_name      ║              ║ is_current    ║  ╚═══════════════╝
    ║ is_weekend    ║              ╚═══════════════╝
    ║ is_holiday    ║
    ╚═══════════════╝

RELATIONSHIP LINES:
─── = ONE-TO-MANY
FK  = Foreign Key
PK  = Primary Key
```

### Data Flow Diagram

```
                    ┌─────────────────────────────────────┐
                    │      DATA SOURCES (CSV Files)       │
                    │                                     │
                    │  ┌───────────┐  ┌──────────┐      │
                    │  │customers  │  │ products │      │
                    │  │   .csv    │  │   .csv   │      │
                    │  └───────────┘  └──────────┘      │
                    │         ┌──────────────┐          │
                    │         │transactions  │          │
                    │         │     .csv     │          │
                    │         └──────────────┘          │
                    └──────────────┬──────────────────────┘
                                   │ (1) Upload to GCS
                                   ▼
                    ┌──────────────────────────────────────┐
                    │    GOOGLE CLOUD STORAGE (GCS)        │
                    │                                      │
                    │  gs://bucket/raw/customers_YYYYMMDD  │
                    │  gs://bucket/raw/products_YYYYMMDD   │
                    │  gs://bucket/raw/transactions_YYYYMMDD│
                    └──────────────┬───────────────────────┘
                                   │ (2) GCSToBigQueryOperator
                                   ▼
        ┌───────────────────────────────────────────────────────┐
        │        BIGQUERY: STAGING LAYER                        │
        │                                                       │
        │  staging.customers_raw                                │
        │  staging.products_raw                                 │
        │  staging.transactions_raw                             │
        │                                                       │
        │  • Raw CSV data loaded as-is                         │
        │  • Temporary tables                                  │
        │  • Daily truncate and reload                         │
        └──────────────┬────────────────────────────────────────┘
                       │ (3) TRANSFORM & UPSERT
                       ▼
        ┌───────────────────────────────────────────────────────┐
        │      BIGQUERY: DATAMART LAYER (Star Schema)           │
        │                                                       │
        │  ┌─────────────────────────────────────────────┐    │
        │  │ DIMENSION TABLES (SCD Type 1)               │    │
        │  │                                             │    │
        │  │  sales_datamart.DimCustomer                 │    │
        │  │    • Upsert from staging                    │    │
        │  │    • Deduplication                          │    │
        │  │    • Surrogate key (FARM_FINGERPRINT)       │    │
        │  │                                             │    │
        │  │  sales_datamart.DimProduct                  │    │
        │  │    • Upsert from staging                    │    │
        │  │                                             │    │
        │  │  sales_datamart.DimDate                     │    │
        │  │    • Pre-populated (2020-2030)              │    │
        │  └─────────────────────────────────────────────┘    │
        │                                                       │
        │  ┌─────────────────────────────────────────────┐    │
        │  │ FACT TABLE (Incremental)                    │    │
        │  │                                             │    │
        │  │  sales_datamart.FactSalesTransaction        │    │
        │  │    • INSERT from staging (daily)            │    │
        │  │    • Join with dimensions                   │    │
        │  │    • Calculate measures                     │    │
        │  └─────────────────────────────────────────────┘    │
        └──────────────┬────────────────────────────────────────┘
                       │ (4) AGGREGATE
                       ▼
        ┌───────────────────────────────────────────────────────┐
        │      BIGQUERY: REPORTING LAYER                        │
        │                                                       │
        │  sales_datamart.DailySalesReport                      │
        │    • Pre-aggregated metrics                          │
        │    • Fast dashboard queries                          │
        └───────────────────────────────────────────────────────┘
                       │ (5) VISUALIZE
                       ▼
        ┌───────────────────────────────────────────────────────┐
        │  BI TOOLS: Looker Studio, Power BI, Tableau          │
        └───────────────────────────────────────────────────────┘
```

---

## SCD Type 1 vs Type 2

### SCD Type 1: Overwrite (Current Project)

**Behavior:** Sadece güncel durum saklanır, geçmiş üzerine yazılır.

```sql
-- Type 1 MERGE
MERGE DimCustomer T
USING staging.customers_raw S
ON T.customer_id = S.customer_id
WHEN MATCHED THEN
    UPDATE SET  -- Overwrite
        customer_name = S.customer_name,
        email = S.email,
        updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
    INSERT (customer_key, customer_id, customer_name, email, created_at)
    VALUES (FARM_FINGERPRINT(S.customer_id), S.customer_id, S.customer_name, S.email, CURRENT_TIMESTAMP())
```

**Avantajlar:**
- ✅ Basit
- ✅ Az storage
- ✅ Hızlı query'ler

**Dezavantajlar:**
- ❌ Geçmiş kaybı
- ❌ Audit trail yok

### SCD Type 2: Historical Tracking

**Behavior:** Her değişiklik yeni row olarak eklenir, geçmiş korunur.

```sql
-- Type 2 Implementation
CREATE TABLE DimCustomer_SCD2 (
    customer_key INT64,            -- Surrogate key
    customer_id STRING,            -- Business key
    customer_name STRING,
    email STRING,
    effective_start_date DATE,     -- Version start
    effective_end_date DATE,       -- Version end (9999-12-31 for current)
    is_current BOOL                -- TRUE for current version
);

-- Type 2 MERGE (complex)
MERGE DimCustomer_SCD2 T
USING staging.customers_raw S
ON T.customer_id = S.customer_id AND T.is_current = TRUE
WHEN MATCHED AND (T.customer_name != S.customer_name OR T.email != S.email) THEN
    -- Expire old version
    UPDATE SET
        effective_end_date = CURRENT_DATE(),
        is_current = FALSE
WHEN NOT MATCHED BY TARGET THEN
    -- Insert new customer
    INSERT (customer_key, customer_id, customer_name, email, effective_start_date, effective_end_date, is_current)
    VALUES (FARM_FINGERPRINT(CONCAT(S.customer_id, CAST(CURRENT_TIMESTAMP() AS STRING))),
            S.customer_id, S.customer_name, S.email, CURRENT_DATE(), DATE('9999-12-31'), TRUE);

-- Insert new version (separate query after MERGE)
INSERT INTO DimCustomer_SCD2
SELECT
    FARM_FINGERPRINT(CONCAT(customer_id, CAST(CURRENT_TIMESTAMP() AS STRING))) as customer_key,
    customer_id,
    customer_name,
    email,
    CURRENT_DATE() as effective_start_date,
    DATE('9999-12-31') as effective_end_date,
    TRUE as is_current
FROM staging.customers_raw S
WHERE EXISTS (
    SELECT 1 FROM DimCustomer_SCD2 T
    WHERE T.customer_id = S.customer_id
      AND T.is_current = FALSE  -- Old version exists
      AND (T.customer_name != S.customer_name OR T.email != S.email)  -- Changed
);
```

**Query with SCD Type 2:**

```sql
-- Point-in-time query
SELECT
    f.transaction_id,
    c.customer_name,  -- Name at transaction time
    f.total_amount
FROM FactSalesTransaction f
JOIN DimCustomer_SCD2 c
  ON f.customer_key = c.customer_key
  AND DATE(f.transaction_timestamp) BETWEEN c.effective_start_date AND c.effective_end_date
WHERE DATE(f.transaction_timestamp) = '2024-01-15'
```

**Avantajlar:**
- ✅ Full history
- ✅ Point-in-time queries
- ✅ Audit trail

**Dezavantajlar:**
- ❌ Kompleks
- ❌ Fazla storage
- ❌ Yavaş query'ler (daha fazla row)

---

## MERGE (UPSERT) Query Step-by-Step

### Step-by-Step Explanation

```sql
-- STEP 1: Target table (T) ve Source table (S) tanımla
MERGE `project.sales_datamart.DimCustomer` T
USING `project.staging.customers_raw` S

-- STEP 2: Join condition (business key match)
ON T.customer_id = S.customer_id

-- STEP 3: MATCHED durumu (update)
--   Kayıt her iki tabloda da varsa (customer_id match)
WHEN MATCHED THEN
    UPDATE SET
        customer_name = S.customer_name,    -- Staging'den güncelle
        email = S.email,
        city = S.city,
        country = S.country,
        effective_date = CURRENT_TIMESTAMP()  -- Update timestamp

-- STEP 4: NOT MATCHED durumu (insert)
--   Kayıt sadece staging'de varsa (yeni müşteri)
WHEN NOT MATCHED THEN
    INSERT (
        customer_key,                         -- Surrogate key
        customer_id,                          -- Business key
        customer_name,
        email,
        city,
        country,
        created_date,
        effective_date,
        is_current
    )
    VALUES (
        FARM_FINGERPRINT(S.customer_id),     -- Hash surrogate key
        S.customer_id,
        S.customer_name,
        S.email,
        S.city,
        S.country,
        CURRENT_DATE(),
        CURRENT_TIMESTAMP(),
        TRUE
    )

-- OPTIONAL STEP 5: WHEN NOT MATCHED BY SOURCE (delete handling)
WHEN NOT MATCHED BY SOURCE THEN
    UPDATE SET is_current = FALSE  -- Soft delete
```

### Real Example with Data

**Before MERGE:**

DimCustomer (target):
| customer_key | customer_id | customer_name | email |
|--------------|-------------|---------------|-------|
| 123 | CUST001 | John Doe | john@old.com |
| 456 | CUST002 | Jane Smith | jane@email.com |

customers_raw (source):
| customer_id | customer_name | email |
|-------------|---------------|-------|
| CUST001 | John Doe | john@new.com | ← Email changed
| CUST002 | Jane Smith | jane@email.com | ← No change
| CUST003 | Bob Wilson | bob@email.com | ← New customer

**After MERGE:**

DimCustomer:
| customer_key | customer_id | customer_name | email |
|--------------|-------------|---------------|-------|
| 123 | CUST001 | John Doe | john@new.com | ← Updated
| 456 | CUST002 | Jane Smith | jane@email.com | ← Same
| 789 | CUST003 | Bob Wilson | bob@email.com | ← Inserted

---

## Performance Optimization

### Partitioning Strategy

```sql
-- Fact table: Partition by transaction date
CREATE TABLE FactSalesTransaction (
    transaction_id STRING,
    date_key INT64,
    customer_key INT64,
    product_key INT64,
    quantity INT64,
    total_amount FLOAT64,
    transaction_timestamp TIMESTAMP
)
PARTITION BY DATE(transaction_timestamp)
CLUSTER BY customer_key, product_key
OPTIONS(
    partition_expiration_days=365,  -- Keep 1 year
    require_partition_filter=TRUE    -- Force date filter
);

-- Dimension tables: Partition by effective_date
CREATE TABLE DimCustomer (
    customer_key INT64,
    customer_id STRING,
    customer_name STRING,
    effective_date TIMESTAMP
)
PARTITION BY DATE(effective_date)
CLUSTER BY customer_id
OPTIONS(
    partition_expiration_days=NULL  -- Never expire
);
```

### Clustering Keys

**How to choose clustering keys:**
1. Most filtered columns
2. Most joined columns
3. High cardinality columns
4. Max 4 columns

**Example:**
```sql
-- Fact table clustering
CLUSTER BY customer_key, product_key

-- Why?
SELECT *
FROM FactSalesTransaction
WHERE customer_key = 12345  -- Clustering key used
  AND product_key = 67890   -- Clustering key used
  AND DATE(transaction_timestamp) = '2024-01-15'  -- Partition filter
```

### Expected Data Volumes

| Table | Row Count | Size | Growth Rate | Retention |
|-------|-----------|------|-------------|-----------|
| **DimCustomer** | 100K - 1M | 100 MB - 1 GB | +5K/month | Permanent |
| **DimProduct** | 10K - 100K | 10 MB - 100 MB | +500/month | Permanent |
| **DimDate** | 3,652 | <1 MB | Fixed (2020-2030) | Permanent |
| **FactSalesTransaction** | 10M - 1B | 10 GB - 1 TB | +50K/day | 1-5 years |
| **DailySalesReport** | 365 - 3,650 | 1 MB - 10 MB | +1/day | 5-10 years |

### Query Performance Metrics

**Baseline metrics (partition + clustering):**

| Query Type | Expected Time | Bytes Scanned | Cost |
|------------|---------------|---------------|------|
| Daily aggregation | <2s | 100 MB | $0.0005 |
| Monthly aggregation | <5s | 3 GB | $0.015 |
| Customer lifetime value | <10s | 10 GB | $0.05 |
| Full table scan | 30s - 5min | 100 GB - 1 TB | $0.50 - $5.00 |

---

## SQL Analiz Sorguları (10+ Örnek)

### 1. Top 10 Müşteriler (Lifetime Value)

```sql
SELECT
    c.customer_id,
    c.customer_name,
    c.city,
    c.country,
    COUNT(DISTINCT f.transaction_id) as total_orders,
    SUM(f.quantity) as total_items_purchased,
    SUM(f.net_amount) as lifetime_value,
    AVG(f.net_amount) as avg_order_value,
    MIN(DATE(f.transaction_timestamp)) as first_purchase_date,
    MAX(DATE(f.transaction_timestamp)) as last_purchase_date
FROM `project.sales_datamart.FactSalesTransaction` f
JOIN `project.sales_datamart.DimCustomer` c
  ON f.customer_key = c.customer_key
GROUP BY c.customer_id, c.customer_name, c.city, c.country
ORDER BY lifetime_value DESC
LIMIT 10
```

### 2. Kategori Bazlı Satış (Hierarchy Drill-Down)

```sql
SELECT
    p.category,
    p.subcategory,
    COUNT(DISTINCT f.transaction_id) as order_count,
    SUM(f.quantity) as units_sold,
    SUM(f.total_amount) as gross_sales,
    SUM(f.discount_amount) as total_discounts,
    SUM(f.net_amount) as net_sales,
    ROUND(SUM(f.discount_amount) / SUM(f.total_amount) * 100, 2) as discount_rate_pct
FROM `project.sales_datamart.FactSalesTransaction` f
JOIN `project.sales_datamart.DimProduct` p
  ON f.product_key = p.product_key
GROUP BY p.category, p.subcategory
ORDER BY net_sales DESC
```

### 3. Aylık Trend Analizi (Time Series)

```sql
SELECT
    d.year,
    d.month,
    d.month_name,
    COUNT(DISTINCT f.transaction_id) as total_transactions,
    COUNT(DISTINCT f.customer_key) as unique_customers,
    SUM(f.quantity) as total_units,
    SUM(f.net_amount) as net_sales,
    AVG(f.net_amount) as avg_transaction_value,
    -- MoM growth
    LAG(SUM(f.net_amount)) OVER (ORDER BY d.year, d.month) as prev_month_sales,
    ROUND((SUM(f.net_amount) - LAG(SUM(f.net_amount)) OVER (ORDER BY d.year, d.month))
          / LAG(SUM(f.net_amount)) OVER (ORDER BY d.year, d.month) * 100, 2) as mom_growth_pct
FROM `project.sales_datamart.FactSalesTransaction` f
JOIN `project.sales_datamart.DimDate` d
  ON f.date_key = d.date_key
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month
```

### 4. Hafta Sonu vs Hafta İçi Karşılaştırma

```sql
SELECT
    CASE
        WHEN d.is_weekend THEN 'Weekend'
        ELSE 'Weekday'
    END as day_type,
    COUNT(DISTINCT f.transaction_id) as total_transactions,
    SUM(f.net_amount) as net_sales,
    AVG(f.net_amount) as avg_transaction_value,
    -- Basket size
    AVG(f.quantity) as avg_items_per_order
FROM `project.sales_datamart.FactSalesTransaction` f
JOIN `project.sales_datamart.DimDate` d
  ON f.date_key = d.date_key
WHERE d.year = 2024
GROUP BY day_type
```

### 5. Customer Segmentation (RFM Analysis)

```sql
WITH customer_metrics AS (
    SELECT
        c.customer_id,
        c.customer_name,
        MAX(DATE(f.transaction_timestamp)) as last_purchase_date,
        COUNT(DISTINCT f.transaction_id) as frequency,
        SUM(f.net_amount) as monetary_value
    FROM `project.sales_datamart.FactSalesTransaction` f
    JOIN `project.sales_datamart.DimCustomer` c
      ON f.customer_key = c.customer_key
    GROUP BY c.customer_id, c.customer_name
),
rfm_scores AS (
    SELECT
        *,
        -- Recency: Days since last purchase
        DATE_DIFF(CURRENT_DATE(), last_purchase_date, DAY) as recency_days,
        -- RFM scores (1-5)
        NTILE(5) OVER (ORDER BY DATE_DIFF(CURRENT_DATE(), last_purchase_date, DAY) DESC) as r_score,
        NTILE(5) OVER (ORDER BY frequency) as f_score,
        NTILE(5) OVER (ORDER BY monetary_value) as m_score
    FROM customer_metrics
)
SELECT
    customer_id,
    customer_name,
    recency_days,
    frequency,
    monetary_value,
    r_score,
    f_score,
    m_score,
    (r_score + f_score + m_score) as rfm_total,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score <= 2 THEN 'New Customers'
        WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
        WHEN r_score <= 2 AND f_score <= 2 THEN 'Lost'
        ELSE 'Others'
    END as customer_segment
FROM rfm_scores
ORDER BY rfm_total DESC
```

### 6. Product Affinity (Market Basket Analysis)

```sql
WITH product_pairs AS (
    SELECT
        f1.product_key as product_a_key,
        f2.product_key as product_b_key,
        COUNT(DISTINCT f1.transaction_id) as co_occurrence_count
    FROM `project.sales_datamart.FactSalesTransaction` f1
    JOIN `project.sales_datamart.FactSalesTransaction` f2
      ON f1.transaction_id = f2.transaction_id
      AND f1.product_key < f2.product_key  -- Avoid duplicates
    GROUP BY f1.product_key, f2.product_key
    HAVING co_occurrence_count >= 10  -- Min support
)
SELECT
    pa.product_name as product_a,
    pb.product_name as product_b,
    pp.co_occurrence_count,
    ROUND(pp.co_occurrence_count * 100.0 / total_transactions.cnt, 2) as support_pct
FROM product_pairs pp
JOIN `project.sales_datamart.DimProduct` pa
  ON pp.product_a_key = pa.product_key
JOIN `project.sales_datamart.DimProduct` pb
  ON pp.product_b_key = pb.product_key
CROSS JOIN (
    SELECT COUNT(DISTINCT transaction_id) as cnt
    FROM `project.sales_datamart.FactSalesTransaction`
) total_transactions
ORDER BY co_occurrence_count DESC
LIMIT 20
```

### 7. Cohort Analysis (Customer Retention)

```sql
WITH customer_cohorts AS (
    SELECT
        customer_key,
        DATE_TRUNC(MIN(DATE(transaction_timestamp)), MONTH) as cohort_month
    FROM `project.sales_datamart.FactSalesTransaction`
    GROUP BY customer_key
),
cohort_data AS (
    SELECT
        c.cohort_month,
        DATE_TRUNC(DATE(f.transaction_timestamp), MONTH) as transaction_month,
        COUNT(DISTINCT f.customer_key) as customer_count
    FROM `project.sales_datamart.FactSalesTransaction` f
    JOIN customer_cohorts c
      ON f.customer_key = c.customer_key
    GROUP BY c.cohort_month, DATE_TRUNC(DATE(f.transaction_timestamp), MONTH)
)
SELECT
    cohort_month,
    transaction_month,
    customer_count,
    FIRST_VALUE(customer_count) OVER (
        PARTITION BY cohort_month
        ORDER BY transaction_month
    ) as cohort_size,
    ROUND(customer_count * 100.0 /
        FIRST_VALUE(customer_count) OVER (PARTITION BY cohort_month ORDER BY transaction_month)
    , 2) as retention_rate
FROM cohort_data
ORDER BY cohort_month, transaction_month
```

### 8. Sales Velocity (Trending Products)

```sql
WITH product_sales AS (
    SELECT
        p.product_id,
        p.product_name,
        p.category,
        DATE_TRUNC(DATE(f.transaction_timestamp), WEEK) as week,
        SUM(f.net_amount) as weekly_sales
    FROM `project.sales_datamart.FactSalesTransaction` f
    JOIN `project.sales_datamart.DimProduct` p
      ON f.product_key = p.product_key
    WHERE DATE(f.transaction_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 WEEK)
    GROUP BY p.product_id, p.product_name, p.category, week
)
SELECT
    product_id,
    product_name,
    category,
    -- Last 4 weeks average
    AVG(CASE WHEN week >= DATE_SUB(CURRENT_DATE(), INTERVAL 4 WEEK) THEN weekly_sales END) as last_4w_avg,
    -- Previous 4 weeks average
    AVG(CASE WHEN week < DATE_SUB(CURRENT_DATE(), INTERVAL 4 WEEK)
               AND week >= DATE_SUB(CURRENT_DATE(), INTERVAL 8 WEEK)
        THEN weekly_sales END) as prev_4w_avg,
    -- Growth rate
    ROUND((AVG(CASE WHEN week >= DATE_SUB(CURRENT_DATE(), INTERVAL 4 WEEK) THEN weekly_sales END) -
           AVG(CASE WHEN week < DATE_SUB(CURRENT_DATE(), INTERVAL 4 WEEK) AND week >= DATE_SUB(CURRENT_DATE(), INTERVAL 8 WEEK) THEN weekly_sales END))
          / AVG(CASE WHEN week < DATE_SUB(CURRENT_DATE(), INTERVAL 4 WEEK) AND week >= DATE_SUB(CURRENT_DATE(), INTERVAL 8 WEEK) THEN weekly_sales END) * 100, 2) as growth_rate_pct
FROM product_sales
GROUP BY product_id, product_name, category
HAVING prev_4w_avg IS NOT NULL  -- Filter out products with insufficient history
ORDER BY growth_rate_pct DESC
LIMIT 20
```

### 9. Geographic Sales Distribution

```sql
SELECT
    c.country,
    c.city,
    COUNT(DISTINCT f.customer_key) as unique_customers,
    COUNT(DISTINCT f.transaction_id) as total_orders,
    SUM(f.net_amount) as total_sales,
    AVG(f.net_amount) as avg_order_value,
    -- Rank within country
    RANK() OVER (PARTITION BY c.country ORDER BY SUM(f.net_amount) DESC) as city_rank_in_country
FROM `project.sales_datamart.FactSalesTransaction` f
JOIN `project.sales_datamart.DimCustomer` c
  ON f.customer_key = c.customer_key
GROUP BY c.country, c.city
ORDER BY total_sales DESC
```

### 10. Discount Effectiveness Analysis

```sql
SELECT
    CASE
        WHEN f.discount_amount = 0 THEN 'No Discount'
        WHEN f.discount_amount / f.total_amount <= 0.10 THEN '1-10%'
        WHEN f.discount_amount / f.total_amount <= 0.20 THEN '11-20%'
        WHEN f.discount_amount / f.total_amount <= 0.30 THEN '21-30%'
        ELSE '>30%'
    END as discount_bucket,
    COUNT(DISTINCT f.transaction_id) as order_count,
    AVG(f.quantity) as avg_items_per_order,
    AVG(f.total_amount) as avg_gross_order_value,
    AVG(f.net_amount) as avg_net_order_value,
    SUM(f.discount_amount) as total_discount_given,
    SUM(f.net_amount) as total_revenue
FROM `project.sales_datamart.FactSalesTransaction` f
GROUP BY discount_bucket
ORDER BY
    CASE discount_bucket
        WHEN 'No Discount' THEN 1
        WHEN '1-10%' THEN 2
        WHEN '11-20%' THEN 3
        WHEN '21-30%' THEN 4
        ELSE 5
    END
```

---

## Monitoring ve Alerting

### Pipeline SLA

```python
from datetime import timedelta

with DAG(
    'sales_datamart_pipeline',
    sla_miss_callback=send_sla_alert,
    default_args={
        'sla': timedelta(hours=1),  # Pipeline 1 saatte tamamlanmalı
    }
) as dag:
    # Tasks...
    pass

def send_sla_alert(dag, task_list, blocking_task_list, slas, blocking_tis):
    """Send alert when SLA missed"""
    message = f"SLA missed for DAG: {dag.dag_id}\n"
    message += f"Tasks: {[t.task_id for t in task_list]}"
    send_to_slack(message)
```

### Data Quality Alerts

```python
@task
def data_quality_check():
    """Comprehensive data quality checks"""
    from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook

    hook = BigQueryHook(gcp_conn_id='google_cloud_default')

    checks = {
        'row_count': "SELECT COUNT(*) FROM FactSalesTransaction WHERE DATE(transaction_timestamp) = CURRENT_DATE()",
        'null_check': "SELECT COUNTIF(customer_key IS NULL OR product_key IS NULL) FROM FactSalesTransaction",
        'duplicate_check': "SELECT COUNT(*) - COUNT(DISTINCT transaction_id) FROM FactSalesTransaction",
        'negative_amount': "SELECT COUNTIF(net_amount < 0) FROM FactSalesTransaction"
    }

    alerts = []

    for check_name, query in checks.items():
        result = hook.get_first(query)
        value = result[0]

        if check_name == 'row_count' and value == 0:
            alerts.append(f"⚠️ Zero rows loaded today")
        elif check_name != 'row_count' and value > 0:
            alerts.append(f"⚠️ {check_name} failed: {value} issues found")

    if alerts:
        send_to_slack("\n".join(alerts))
        raise AirflowFailException("Data quality checks failed")

    return "All checks passed ✅"
```

### Volume Checks

```python
@task
def volume_check():
    """Check if data volume is within expected range"""
    from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook

    hook = BigQueryHook(gcp_conn_id='google_cloud_default')

    # Today's count
    today_count = hook.get_first(
        "SELECT COUNT(*) FROM FactSalesTransaction WHERE DATE(transaction_timestamp) = CURRENT_DATE()"
    )[0]

    # 7-day average
    avg_count = hook.get_first("""
        SELECT AVG(cnt) FROM (
            SELECT COUNT(*) as cnt
            FROM FactSalesTransaction
            WHERE DATE(transaction_timestamp) BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY)
                                                   AND DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
            GROUP BY DATE(transaction_timestamp)
        )
    """)[0]

    # Alert if today is >50% different from average
    if today_count < avg_count * 0.5:
        send_to_slack(f"⚠️ Volume alert: Today {today_count} << Avg {avg_count:.0f}")
    elif today_count > avg_count * 1.5:
        send_to_slack(f"ℹ️ Volume spike: Today {today_count} >> Avg {avg_count:.0f}")

    return f"Volume check: {today_count} (avg: {avg_count:.0f})"
```

### Freshness Checks

```python
@task
def freshness_check():
    """Check if data is fresh (updated recently)"""
    from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook

    hook = BigQueryHook(gcp_conn_id='google_cloud_default')

    result = hook.get_first("""
        SELECT TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(transaction_timestamp), HOUR)
        FROM FactSalesTransaction
    """)

    hours_since_last_update = result[0]

    if hours_since_last_update > 24:
        send_to_slack(f"⚠️ Data freshness alert: Last update was {hours_since_last_update} hours ago")
        raise AirflowFailException("Data too stale")

    return f"Data is fresh (last update: {hours_since_last_update} hours ago)"
```

---

## Genişletme Önerileri

### 1. Ek Dimension'lar

**DimPromotion (Promosyon bilgileri):**
```sql
CREATE TABLE DimPromotion (
    promotion_key INT64,
    promotion_id STRING,
    promotion_name STRING,
    discount_type STRING,  -- 'Percentage', 'Fixed Amount'
    discount_value FLOAT64,
    start_date DATE,
    end_date DATE,
    is_active BOOL
)
PARTITION BY start_date
CLUSTER BY promotion_id;
```

**DimLocation (Lokasyon hiyerarşisi):**
```sql
CREATE TABLE DimLocation (
    location_key INT64,
    country STRING,
    region STRING,
    city STRING,
    postal_code STRING,
    latitude FLOAT64,
    longitude FLOAT64
)
CLUSTER BY country, city;
```

### 2. Ek Fact Table'lar

**FactInventory (Stok hareketleri):**
```sql
CREATE TABLE FactInventory (
    inventory_id STRING,
    date_key INT64,
    product_key INT64,
    location_key INT64,
    quantity_on_hand INT64,
    quantity_reserved INT64,
    quantity_available INT64,
    snapshot_timestamp TIMESTAMP
)
PARTITION BY DATE(snapshot_timestamp)
CLUSTER BY product_key, location_key;
```

**FactReturns (İadeler):**
```sql
CREATE TABLE FactReturns (
    return_id STRING,
    date_key INT64,
    customer_key INT64,
    product_key INT64,
    original_transaction_id STRING,
    return_quantity INT64,
    return_amount FLOAT64,
    return_reason STRING,
    return_timestamp TIMESTAMP
)
PARTITION BY DATE(return_timestamp)
CLUSTER BY customer_key, product_key;
```

### 3. Real-Time Streaming

**Dataflow + Pub/Sub entegrasyonu:**

```python
# Airflow DAG to monitor streaming job
from airflow.providers.google.cloud.operators.dataflow import DataflowStartFlexTemplateOperator

start_streaming = DataflowStartFlexTemplateOperator(
    task_id='start_realtime_streaming',
    location='us-central1',
    body={
        "launch_parameter": {
            "container_spec_gcs_path": "gs://bucket/streaming-pipeline-spec.json",
            "job_name": "realtime-sales-streaming",
            "parameters": {
                "input_subscription": "projects/PROJECT/subscriptions/sales-events",
                "output_table": "PROJECT:sales_datamart.FactSalesTransaction_RT"
            }
        }
    }
)
```

### 4. Machine Learning Integration

**BigQuery ML model training:**

```sql
-- Train sales forecasting model
CREATE OR REPLACE MODEL `project.ml.sales_forecast_model`
OPTIONS(
    model_type='ARIMA_PLUS',
    time_series_timestamp_col='date',
    time_series_data_col='net_sales'
) AS
SELECT
    DATE(transaction_timestamp) as date,
    SUM(net_amount) as net_sales
FROM `project.sales_datamart.FactSalesTransaction`
WHERE DATE(transaction_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR)
GROUP BY date
ORDER BY date;

-- Generate forecast
SELECT
    forecast_timestamp,
    forecast_value,
    standard_error,
    confidence_level
FROM ML.FORECAST(
    MODEL `project.ml.sales_forecast_model`,
    STRUCT(30 AS horizon)  -- 30 days forecast
);
```

---

## Production Deployment Checklist

### Pre-Deployment
- [ ] Test data generated and uploaded to GCS
- [ ] Service account permissions verified
- [ ] BigQuery datasets created (staging, sales_datamart)
- [ ] Airflow connections configured
- [ ] DAG validated locally
- [ ] Unit tests passing
- [ ] Integration tests passing

### Deployment
- [ ] DAG deployed to Airflow
- [ ] DAG unpaused
- [ ] Manual trigger successful
- [ ] All tasks completed successfully
- [ ] Data quality checks passed
- [ ] Monitoring dashboards configured
- [ ] Alerts configured (Slack/Email)

### Post-Deployment (24h monitoring)
- [ ] Daily runs successful
- [ ] Performance metrics within SLA
- [ ] No errors in logs
- [ ] Data volume as expected
- [ ] Query performance acceptable
- [ ] Cost within budget

### Documentation
- [ ] Runbook created
- [ ] Alert response procedures documented
- [ ] Troubleshooting guide updated
- [ ] Data dictionary published
- [ ] BI dashboard links shared

---

## Sık Sorulan Sorular (FAQ)

**S1: Star schema vs Snowflake schema?**

A:
- **Star**: Denormalized, simple, fast queries (RECOMMENDED for BI)
- **Snowflake**: Normalized, complex, less storage

**S2: Surrogate key vs Natural key?**

A:
- **Surrogate**: FARM_FINGERPRINT(customer_id), stable, fast joins
- **Natural**: customer_id, can change, slower
- Use surrogate for fact table FK's

**S3: DimDate nasıl doldurulur?**

A:
```sql
INSERT INTO DimDate
SELECT ... FROM UNNEST(GENERATE_DATE_ARRAY('2020-01-01', '2030-12-31'))
```
Once populate, sonra kullan.

**S4: MERGE vs INSERT performance?**

A:
- **MERGE**: Slower (check + update/insert)
- **INSERT**: Faster (append only)
- Use MERGE for dimensions, INSERT for facts

**S5: Incremental fact loading best practice?**

A:
```sql
WHERE DATE(transaction_timestamp) = '{{ ds }}'
```
Daily partition filter = fast + cheap

**S6: Data quality checks ne sıklıkla?**

A:
- **Real-time**: Critical checks (null, duplicate)
- **Daily**: Volume, freshness
- **Weekly**: Trend anomalies

**S7: Cost optimization için en önemli?**

A:
1. Partitioning (mandatory)
2. Clustering (highly recommended)
3. SELECT specific columns (not *)

**S8: SCD Type 1 vs Type 2 ne zaman?**

A:
- **Type 1**: Performance critical, history not needed
- **Type 2**: Audit requirements, point-in-time queries

**S9: Fact table ne kadar büyük olabilir?**

A: BigQuery 10TB+ table'ları handle eder. Partition + cluster ile performans problemi yok.

**S10: Real-time vs Batch?**

A:
- **Batch**: Cost-effective, simpler, 1-24 hour latency OK
- **Real-time**: Expensive, complex, <1 min latency needed

---

## Sonraki Adımlar

- **[06-deployment-cicd.md](06-deployment-cicd.md)**: Production deployment
- Looker Studio veya Power BI ile dashboard oluşturma
- SCD Type 2 implementation (history tracking)
- Real-time streaming entegrasyonu
