"""
DAG 3: Operator Showcase - Farklı Operator Tipleri

Bu DAG çeşitli operator tiplerini gösterir:
- BashOperator
- PythonOperator
- EmailOperator (config gerektirir)
- FileSensor
- TimeSensor
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from airflow.sensors.filesystem import FileSensor
from airflow.sensors.time_delta import TimeDeltaSensor
from airflow.operators.dummy import DummyOperator
from datetime import datetime, timedelta
import json

default_args = {
    'owner': 'data-team',
    'retries': 2,
    'retry_delay': timedelta(minutes=3),
}

def process_data(**kwargs):
    """Veri işleme fonksiyonu"""
    data = {
        'execution_date': str(kwargs['execution_date']),
        'dag_run_id': kwargs['run_id'],
        'records_processed': 1500,
        'status': 'success'
    }
    print(f"📊 İşlenen Veri:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return data

def validate_data(**kwargs):
    """Veri doğrulama fonksiyonu"""
    # Önceki task'tan veri al (XCom kullanımı)
    ti = kwargs['ti']
    data = ti.xcom_pull(task_ids='process_data')

    if data and data.get('records_processed', 0) > 0:
        print(f"✅ Doğrulama başarılı: {data['records_processed']} kayıt")
        return True
    else:
        raise ValueError("❌ Veri doğrulama başarısız!")

with DAG(
    dag_id='03_operators_showcase',
    default_args=default_args,
    description='Farklı Airflow operator tiplerinin örnekleri',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['egitim', 'operators', 'showcase'],
) as dag:

    # ========== DUMMY OPERATOR ==========
    # Placeholder task (hiçbir şey yapmaz)
    start = DummyOperator(task_id='start')

    # ========== BASH OPERATOR ==========
    # Shell komutları çalıştırma
    check_environment = BashOperator(
        task_id='check_environment',
        bash_command='''
            echo "=== Sistem Bilgileri ==="
            echo "Tarih: $(date)"
            echo "Dizin: $(pwd)"
            echo "Python: $(python --version)"
            echo "Airflow: $(airflow version)"
        ''',
    )

    # ========== PYTHON OPERATOR ==========
    # Python fonksiyonu çalıştırma
    process_data_task = PythonOperator(
        task_id='process_data',
        python_callable=process_data,
        provide_context=True,
    )

    validate_data_task = PythonOperator(
        task_id='validate_data',
        python_callable=validate_data,
        provide_context=True,
    )

    # ========== FILE SENSOR ==========
    # Dosya varlığını kontrol etme (timeout eklendi)
    # Not: Bu task dosya oluşturulmadığı için timeout olacak (demo amaçlı)
    wait_for_file = FileSensor(
        task_id='wait_for_file',
        filepath='/opt/airflow/data/sample_data.csv',
        poke_interval=10,  # 10 saniyede bir kontrol
        timeout=60,  # 60 saniye timeout
        mode='poke',  # poke: senkron, reschedule: async
        soft_fail=True,  # Fail olsa bile devam et (demo için)
    )

    # ========== TIME SENSOR ==========
    # Belirli bir süre bekle
    wait_5_seconds = TimeDeltaSensor(
        task_id='wait_5_seconds',
        delta=timedelta(seconds=5),
    )

    # ========== EMAIL OPERATOR ==========
    # Email gönderme (SMTP config gerektirir - bu örnekte skip edilecek)
    # Not: Gerçek kullanım için airflow.cfg'de smtp ayarları yapılmalı
    send_notification = EmailOperator(
        task_id='send_notification',
        to='team@example.com',
        subject='Airflow DAG Tamamlandı - {{ ds }}',
        html_content='''
        <h3>Pipeline Raporu</h3>
        <p>DAG: {{ dag.dag_id }}</p>
        <p>Çalıştırma Tarihi: {{ ds }}</p>
        <p>Durum: ✅ Başarılı</p>
        ''',
        # Email gönderimi devre dışı (demo için)
        # trigger_rule='none_failed',
    )
    # Email task'ını skip et (SMTP config olmadığı için)
    send_notification.trigger_rule = 'all_done'

    # ========== BASH SCRIPT ÇALIŞTIRMA ==========
    run_python_script = BashOperator(
        task_id='run_python_script',
        bash_command='python -c "print(\'Python script çalıştırıldı\'); print(sum(range(100)))"',
    )

    # ========== DUMMY OPERATOR ==========
    end = DummyOperator(task_id='end')

    # ========== DEPENDENCIES ==========
    start >> check_environment >> wait_5_seconds
    wait_5_seconds >> [process_data_task, wait_for_file]
    process_data_task >> validate_data_task
    [validate_data_task, wait_for_file] >> run_python_script
    run_python_script >> send_notification >> end
