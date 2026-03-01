"""
DAG 7: BigQuery ETL Pipeline

Kapsamlı BigQuery ETL örneği:
- GCS'den BigQuery'e veri yükleme
- Transform işlemleri
- Incremental load
- Data quality checks
- Export to GCS

NOT: GCS bucket ve BigQuery dataset oluşturulmalıdır.
"""

from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.providers.google.cloud.transfers.bigquery_to_gcs import BigQueryToGCSOperator
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.providers.google.cloud.sensors.bigquery import BigQueryTableExistenceSensor
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os

# GCP Configuration
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'MY_GCP_PROJECT_ID')
GCS_BUCKET = os.getenv('GCS_BUCKET', 'my-sales-data-bucket')
DATASET_STAGING = 'staging'
DATASET_PROD = 'analytics'

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email': ['data-team@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def log_pipeline_status(**kwargs):
    """Pipeline durumunu logla"""
    execution_date = kwargs['execution_date']
    print(f"\n{'='*70}")
    print(f"  BigQuery ETL Pipeline - Durum Logu")
    print(f"{'='*70}")
    print(f"  Çalıştırma Tarihi: {execution_date}")
    print(f"  DAG ID: {kwargs['dag'].dag_id}")
    print(f"  Run ID: {kwargs['run_id']}")
    print(f"  Durum: ✅ Başarılı")
    print(f"{'='*70}\n")

with DAG(
    dag_id='07_bigquery_etl_pipeline',
    default_args=default_args,
    description='Complete BigQuery ETL: GCS → Staging → Transform → Production',
    schedule_interval='0 2 * * *',  # Her gün 02:00
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['egitim', 'bigquery', 'etl', 'production'],
) as dag:

    # ========== STEP 1: SOURCE FILE CHECK ==========
    check_source_file = GCSObjectExistenceSensor(
        task_id='check_source_file',
        bucket=GCS_BUCKET,
        object='raw/sales_{{ ds_nodash }}.csv',
        timeout=600,  # 10 dakika
        poke_interval=60,  # 1 dakikada bir kontrol
        mode='poke',
    )

    # ========== STEP 2: LOAD TO STAGING ==========
    load_to_staging = GCSToBigQueryOperator(
        task_id='load_to_staging',
        bucket=GCS_BUCKET,
        source_objects=['raw/sales_{{ ds_nodash }}.csv'],
        destination_project_dataset_table=f'{GCP_PROJECT_ID}.{DATASET_STAGING}.sales_raw',
        schema_fields=[
            {'name': 'order_id', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'customer_id', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'product_id', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'quantity', 'type': 'INTEGER', 'mode': 'REQUIRED'},
            {'name': 'unit_price', 'type': 'FLOAT', 'mode': 'REQUIRED'},
            {'name': 'total_amount', 'type': 'FLOAT', 'mode': 'REQUIRED'},
            {'name': 'order_date', 'type': 'STRING', 'mode': 'REQUIRED'},  # String olarak gelecek
        ],
        write_disposition='WRITE_TRUNCATE',  # Her seferinde üzerine yaz
        skip_leading_rows=1,  # Header row'u atla
        field_delimiter=',',
        autodetect=False,  # Schema'yı manuel belirledik
        location='US',
    )

    # ========== STEP 3: VALIDATE STAGING DATA ==========
    validate_staging = BigQueryInsertJobOperator(
        task_id='validate_staging',
        configuration={
            "query": {
                "query": f"""
                    -- Staging data validation
                    SELECT
                        CASE
                            WHEN COUNT(*) = 0 THEN ERROR('Staging tabloda veri yok!')
                            WHEN COUNT(*) > 100000 THEN ERROR('Beklenmedik yüksek veri hacmi!')
                            WHEN COUNTIF(total_amount < 0) > 0 THEN ERROR('Negatif tutar var!')
                            WHEN COUNTIF(quantity < 0) > 0 THEN ERROR('Negatif miktar var!')
                            ELSE 'VALIDATION_PASSED'
                        END as validation_result
                    FROM `{GCP_PROJECT_ID}.{DATASET_STAGING}.sales_raw`
                """,
                "useLegacySql": False
            }
        },
        location='US',
        gcp_conn_id='google_cloud_default',
    )

    # ========== STEP 4: TRANSFORM AND LOAD TO PRODUCTION ==========
    transform_and_load = BigQueryInsertJobOperator(
        task_id='transform_and_load',
        configuration={
            "query": {
                "query": f"""
                    -- Transform ve production'a insert
                    INSERT INTO `{GCP_PROJECT_ID}.{DATASET_PROD}.sales`
                    SELECT
                        order_id,
                        customer_id,
                        product_id,
                        quantity,
                        unit_price,
                        total_amount,
                        PARSE_DATE('%Y%m%d', order_date) as order_date,  -- String'den Date'e
                        CURRENT_TIMESTAMP() as ingestion_timestamp,
                        '{{ ds }}' as partition_date
                    FROM `{GCP_PROJECT_ID}.{DATASET_STAGING}.sales_raw`
                    WHERE
                        -- Data quality filters
                        total_amount > 0
                        AND quantity > 0
                        AND order_id IS NOT NULL
                """,
                "useLegacySql": False
            }
        },
        location='US',
        gcp_conn_id='google_cloud_default',
    )

    # ========== STEP 5: CREATE AGGREGATES ==========
    create_daily_summary = BigQueryInsertJobOperator(
        task_id='create_daily_summary',
        configuration={
            "query": {
                "query": f"""
                    -- Günlük özet tablosu (MERGE kullanarak upsert)
                    MERGE `{GCP_PROJECT_ID}.{DATASET_PROD}.daily_sales_summary` T
                    USING (
                        SELECT
                            order_date,
                            COUNT(DISTINCT order_id) as total_orders,
                            COUNT(DISTINCT customer_id) as unique_customers,
                            COUNT(DISTINCT product_id) as unique_products,
                            SUM(quantity) as total_quantity,
                            SUM(total_amount) as total_sales,
                            AVG(total_amount) as avg_order_value,
                            MIN(total_amount) as min_order_value,
                            MAX(total_amount) as max_order_value,
                            CURRENT_TIMESTAMP() as updated_at
                        FROM `{GCP_PROJECT_ID}.{DATASET_PROD}.sales`
                        WHERE partition_date = '{{ ds }}'
                        GROUP BY order_date
                    ) S
                    ON T.order_date = S.order_date
                    WHEN MATCHED THEN
                        UPDATE SET
                            total_orders = S.total_orders,
                            unique_customers = S.unique_customers,
                            unique_products = S.unique_products,
                            total_quantity = S.total_quantity,
                            total_sales = S.total_sales,
                            avg_order_value = S.avg_order_value,
                            min_order_value = S.min_order_value,
                            max_order_value = S.max_order_value,
                            updated_at = S.updated_at
                    WHEN NOT MATCHED THEN
                        INSERT (order_date, total_orders, unique_customers, unique_products,
                                total_quantity, total_sales, avg_order_value,
                                min_order_value, max_order_value, updated_at)
                        VALUES (S.order_date, S.total_orders, S.unique_customers, S.unique_products,
                                S.total_quantity, S.total_sales, S.avg_order_value,
                                S.min_order_value, S.max_order_value, S.updated_at)
                """,
                "useLegacySql": False
            }
        },
        location='US',
        gcp_conn_id='google_cloud_default',
    )

    # ========== STEP 6: DATA QUALITY CHECK ==========
    final_quality_check = BigQueryInsertJobOperator(
        task_id='final_quality_check',
        configuration={
            "query": {
                "query": f"""
                    -- Final quality check
                    SELECT
                        CASE
                            WHEN staging_count = 0 THEN ERROR('Staging boş!')
                            WHEN prod_count = 0 THEN ERROR('Production\'a veri yüklenmedi!')
                            WHEN prod_count > staging_count THEN ERROR('Production\'da fazla veri var!')
                            ELSE 'QUALITY_CHECK_PASSED'
                        END as result
                    FROM (
                        SELECT
                            (SELECT COUNT(*) FROM `{GCP_PROJECT_ID}.{DATASET_STAGING}.sales_raw`) as staging_count,
                            (SELECT COUNT(*) FROM `{GCP_PROJECT_ID}.{DATASET_PROD}.sales` WHERE partition_date = '{{ ds }}') as prod_count
                    )
                """,
                "useLegacySql": False
            }
        },
        location='US',
        gcp_conn_id='google_cloud_default',
    )

    # ========== STEP 7: EXPORT SUMMARY TO GCS ==========
    export_summary = BigQueryToGCSOperator(
        task_id='export_summary',
        source_project_dataset_table=f'{GCP_PROJECT_ID}.{DATASET_PROD}.daily_sales_summary',
        destination_cloud_storage_uris=[f'gs://{GCS_BUCKET}/reports/daily_summary_{{{{ ds }}}}.csv'],
        export_format='CSV',
        print_header=True,
    )

    # ========== STEP 8: LOG PIPELINE STATUS ==========
    log_status = PythonOperator(
        task_id='log_pipeline_status',
        python_callable=log_pipeline_status,
        provide_context=True,
    )

    # ========== DEPENDENCIES ==========
    check_source_file >> load_to_staging >> validate_staging
    validate_staging >> transform_and_load >> create_daily_summary
    create_daily_summary >> final_quality_check
    final_quality_check >> export_summary >> log_status

# DAG Documentation
dag.doc_md = """
### BigQuery ETL Pipeline

Complete end-to-end ETL pipeline with BigQuery:

**Pipeline Akışı:**
1. GCS'de kaynak dosya kontrolü (Sensor)
2. CSV'den Staging tabloya yükleme (GCSToBigQuery)
3. Staging data validation
4. Transform ve Production tabloya yükleme
5. Aggregate tabloları oluşturma (MERGE)
6. Final quality checks
7. Summary raporu GCS'e export
8. Pipeline durum logu

**Özellikler:**
- Incremental loading
- Data quality validations
- MERGE kullanarak upsert
- Partitioned tables
- Error handling

**Gereksinimler:**
- GCS bucket: `{GCS_BUCKET}`
- BigQuery datasets: `staging`, `analytics`
- Service Account permissions

**Test:**
```bash
# Test verisi oluştur (önce GCS'e yüklenme li)
airflow dags test 07_bigquery_etl_pipeline 2024-01-01
```
"""
