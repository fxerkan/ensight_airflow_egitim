"""
DAG 6: BigQuery Temel Kullanım

BigQuery ile temel operasyonlar:
- Query çalıştırma (BigQueryInsertJobOperator)
- Tablo oluşturma
- Veri sorgulama
- Data quality check

NOT: Bu DAG'in çalışması için BigQuery connection kurulmalıdır.
Connection ID: google_cloud_default
"""

from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryInsertJobOperator,
    BigQueryCheckOperator,
    BigQueryValueCheckOperator,
    BigQueryGetDataOperator
)
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os

# GCP Configuration (environment variables veya .env'den)
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'MY_GCP_PROJECT_ID')
DATASET = os.getenv('GCP_DATASET', 'sales_datamart')

default_args = {
    'owner': 'data-team',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def print_query_results(**kwargs):
    """BigQuery sorgu sonuçlarını yazdır"""
    ti = kwargs['ti']
    results = ti.xcom_pull(task_ids='get_sample_data')

    if results:
        print(f"\n📊 BigQuery Sorgu Sonuçları:")
        print(f"{'='*60}")
        for row in results:
            print(row)
        print(f"{'='*60}")
        print(f"Toplam Kayıt: {len(results)}\n")
    else:
        print("❌ Sonuç bulunamadı!")

with DAG(
    dag_id='06_bigquery_basic',
    default_args=default_args,
    description='BigQuery temel operasyonları ve sorgu çalıştırma',
    schedule_interval=None,  # Manuel
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['egitim', 'bigquery', 'temel'],
) as dag:

    # ========== 1. TABLO OLUŞTURMA ==========
    create_sample_table = BigQueryInsertJobOperator(
        task_id='create_sample_table',
        configuration={
            "query": {
                "query": f"""
                    CREATE TABLE IF NOT EXISTS `{GCP_PROJECT_ID}.{DATASET}.sample_sales` (
                        order_id STRING,
                        customer_id STRING,
                        product_name STRING,
                        quantity INT64,
                        unit_price FLOAT64,
                        total_amount FLOAT64,
                        order_date DATE,
                        created_at TIMESTAMP
                    )
                    PARTITION BY order_date
                    OPTIONS(
                        description="Örnek satış verisi tablosu - Eğitim amaçlı",
                        labels=[("env", "development"), ("team", "data-engineering")]
                    )
                """,
                "useLegacySql": False
            }
        },
        location='US',
        gcp_conn_id='google_cloud_default',
    )

    # ========== 2. ÖRNEK VERİ EKLEME ==========
    insert_sample_data = BigQueryInsertJobOperator(
        task_id='insert_sample_data',
        configuration={
            "query": {
                "query": f"""
                    INSERT INTO `{GCP_PROJECT_ID}.{DATASET}.sample_sales`
                    (order_id, customer_id, product_name, quantity, unit_price, total_amount, order_date, created_at)
                    VALUES
                        ('ORD001', 'CUST001', 'Laptop', 2, 3500.00, 7000.00, '2024-01-15', CURRENT_TIMESTAMP()),
                        ('ORD002', 'CUST002', 'Telefon', 1, 2500.00, 2500.00, '2024-01-16', CURRENT_TIMESTAMP()),
                        ('ORD003', 'CUST001', 'Tablet', 3, 1500.00, 4500.00, '2024-01-17', CURRENT_TIMESTAMP()),
                        ('ORD004', 'CUST003', 'Kulaklık', 5, 250.00, 1250.00, '2024-01-18', CURRENT_TIMESTAMP()),
                        ('ORD005', 'CUST002', 'Laptop', 1, 3500.00, 3500.00, '2024-01-19', CURRENT_TIMESTAMP())
                """,
                "useLegacySql": False
            }
        },
        location='US',
        gcp_conn_id='google_cloud_default',
    )

    # ========== 3. VERİ SORGULAMA ==========
    query_sales_summary = BigQueryInsertJobOperator(
        task_id='query_sales_summary',
        configuration={
            "query": {
                "query": f"""
                    SELECT
                        order_date,
                        COUNT(*) as order_count,
                        SUM(quantity) as total_quantity,
                        SUM(total_amount) as total_sales,
                        AVG(total_amount) as avg_order_value
                    FROM `{GCP_PROJECT_ID}.{DATASET}.sample_sales`
                    GROUP BY order_date
                    ORDER BY order_date DESC
                """,
                "useLegacySql": False,
                "destinationTable": {
                    "projectId": GCP_PROJECT_ID,
                    "datasetId": DATASET,
                    "tableId": "daily_sales_summary"
                },
                "writeDisposition": "WRITE_TRUNCATE",
                "createDisposition": "CREATE_IF_NEEDED"
            }
        },
        location='US',
        gcp_conn_id='google_cloud_default',
    )

    # ========== 4. DATA QUALITY CHECK ==========
    # Check 1: Row count kontrolü
    check_row_count = BigQueryCheckOperator(
        task_id='check_row_count',
        sql=f"""
            SELECT COUNT(*) > 0
            FROM `{GCP_PROJECT_ID}.{DATASET}.sample_sales`
        """,
        use_legacy_sql=False,
        location='US',
        gcp_conn_id='google_cloud_default',
    )

    # Check 2: Değer kontrolü (toplam satış > 0)
    check_total_sales = BigQueryValueCheckOperator(
        task_id='check_total_sales',
        sql=f"""
            SELECT SUM(total_amount)
            FROM `{GCP_PROJECT_ID}.{DATASET}.sample_sales`
        """,
        pass_value=1000.0,  # Minimum beklenen değer
        use_legacy_sql=False,
        location='US',
        gcp_conn_id='google_cloud_default',
    )

    # ========== 5. VERİ ÇEKME (Python'a) ==========
    get_sample_data = BigQueryGetDataOperator(
        task_id='get_sample_data',
        dataset_id=DATASET,
        table_id='sample_sales',
        max_results=10,
        selected_fields='order_id,product_name,total_amount,order_date',
        gcp_conn_id='google_cloud_default',
    )

    # ========== 6. SONUÇLARI YAZDIRMA ==========
    print_results = PythonOperator(
        task_id='print_results',
        python_callable=print_query_results,
        provide_context=True,
    )

    # ========== DEPENDENCIES ==========
    create_sample_table >> insert_sample_data >> query_sales_summary
    query_sales_summary >> [check_row_count, check_total_sales]
    [check_row_count, check_total_sales] >> get_sample_data >> print_results

# DAG Açıklaması (WebUI'da görünür)
dag.doc_md = """
### BigQuery Temel Kullanım DAG'i

Bu DAG BigQuery'nin temel operasyonlarını gösterir:

1. **Tablo Oluşturma**: Partitioned table oluşturma
2. **Veri Ekleme**: INSERT statement ile veri ekleme
3. **Veri Sorgulama**: Aggregate query ve sonucu yeni tabloya yazma
4. **Data Quality**: Row count ve value check
5. **Veri Çekme**: BigQuery'den Python'a veri çekme

**Gereksinimler:**
- BigQuery API enabled
- Service Account permissions
- Connection ID: `google_cloud_default`

**Kullanım:**
```bash
# Manuel tetikleme
airflow dags trigger 06_bigquery_basic

# Test
airflow dags test 06_bigquery_basic 2024-01-01
```
"""
