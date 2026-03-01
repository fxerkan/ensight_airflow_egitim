"""
DAG 2: Task Dependencies - Bağımlılık Örnekleri

Bu DAG farklı dependency pattern'lerini gösterir:
- Linear (Sıralı)
- Fan-out (Dallanma)
- Fan-in (Birleşme)
- Diamond pattern
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.models.baseoperator import chain
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-team',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

def print_task_info(task_name, **kwargs):
    """Task bilgilerini yazdır"""
    print(f"🔹 Task: {task_name}")
    print(f"⏰ Başlama: {datetime.now()}")
    return f"{task_name} tamamlandı"

with DAG(
    dag_id='02_dependencies_example',
    default_args=default_args,
    description='Farklı task dependency pattern örnekleri',
    schedule_interval=None,  # Manuel tetikleme
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['egitim', 'dependencies', 'pattern'],
) as dag:

    # ========== BAŞLANGIÇ ==========
    start = BashOperator(
        task_id='start',
        bash_command='echo "Pipeline başladı"',
    )

    # ========== FAN-OUT (Dallanma) ==========
    # Bir task'tan birden fazla task'a
    extract_1 = PythonOperator(
        task_id='extract_customers',
        python_callable=print_task_info,
        op_kwargs={'task_name': 'Extract Customers'},
    )

    extract_2 = PythonOperator(
        task_id='extract_products',
        python_callable=print_task_info,
        op_kwargs={'task_name': 'Extract Products'},
    )

    extract_3 = PythonOperator(
        task_id='extract_orders',
        python_callable=print_task_info,
        op_kwargs={'task_name': 'Extract Orders'},
    )

    # ========== PARALEL İŞLEMLER ==========
    transform_1 = BashOperator(
        task_id='transform_customers',
        bash_command='echo "Transforming customers..." && sleep 2',
    )

    transform_2 = BashOperator(
        task_id='transform_products',
        bash_command='echo "Transforming products..." && sleep 2',
    )

    transform_3 = BashOperator(
        task_id='transform_orders',
        bash_command='echo "Transforming orders..." && sleep 2',
    )

    # ========== FAN-IN (Birleşme) ==========
    # Birden fazla task'tan bir task'a
    load_datawarehouse = PythonOperator(
        task_id='load_datawarehouse',
        python_callable=print_task_info,
        op_kwargs={'task_name': 'Load to Data Warehouse'},
    )

    # ========== DATA QUALITY ==========
    quality_check = BashOperator(
        task_id='data_quality_check',
        bash_command='echo "Data quality check passed ✅"',
    )

    # ========== REPORTING ==========
    generate_report = BashOperator(
        task_id='generate_report',
        bash_command='echo "Rapor oluşturuldu 📊"',
    )

    # ========== BİTİŞ ==========
    end = BashOperator(
        task_id='end',
        bash_command='echo "Pipeline tamamlandı ✅"',
    )

    # ========== DEPENDENCIES ==========

    # Linear: start -> fan-out
    start >> [extract_1, extract_2, extract_3]

    # Extract -> Transform (her biri kendi transform'una)
    extract_1 >> transform_1
    extract_2 >> transform_2
    extract_3 >> transform_3

    # Fan-in: transforms -> load
    [transform_1, transform_2, transform_3] >> load_datawarehouse

    # Linear: load -> quality -> report -> end
    load_datawarehouse >> quality_check >> generate_report >> end

    # Alternatif yazım (chain kullanımı):
    # chain(start, [extract_1, extract_2, extract_3])
    # chain(transform_1, load_datawarehouse, quality_check, generate_report, end)
