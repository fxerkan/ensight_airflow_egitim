"""
DAG 1: Hello World - İlk Airflow DAG Örneği

Bu DAG Airflow'un en temel yapısını gösterir:
- BashOperator ile komut çalıştırma
- PythonOperator ile Python fonksiyonu çalıştırma
- Basit task dependency
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# Default arguments - Tüm task'lar için geçerli
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email': ['team@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def merhaba_python(**kwargs):
    """Python task fonksiyonu"""
    execution_date = kwargs['execution_date']
    print(f"🎉 Merhaba Airflow!")
    print(f"📅 Çalıştırma Tarihi: {execution_date}")
    print(f"🔧 DAG ID: {kwargs['dag'].dag_id}")
    print(f"📝 Task ID: {kwargs['task_instance'].task_id}")
    return "Başarılı!"

# DAG tanımı
with DAG(
    dag_id='01_hello_world',
    default_args=default_args,
    description='İlk basit Airflow DAG örneği - Merhaba Dünya',
    schedule_interval='@daily',  # Her gün çalışır
    start_date=datetime(2024, 1, 1),
    catchup=False,  # Geçmiş tarihler için çalıştırma
    tags=['egitim', 'baslangic', 'hello-world'],
) as dag:

    # Task 1: Bash komutu ile tarih yazdır
    task_tarih = BashOperator(
        task_id='tarih_yazdir',
        bash_command='date "+%Y-%m-%d %H:%M:%S" && echo "Airflow çalışıyor!"',
    )

    # Task 2: Python fonksiyonu çalıştır
    task_python = PythonOperator(
        task_id='merhaba_python',
        python_callable=merhaba_python,
        provide_context=True,
    )

    # Task 3: Başka bir Bash komutu
    task_bilgi = BashOperator(
        task_id='sistem_bilgisi',
        bash_command='echo "Hostname: $(hostname)" && echo "User: $(whoami)"',
    )

    # Task 4: Başarı mesajı
    task_basari = BashOperator(
        task_id='basari_mesaji',
        bash_command='echo "✅ DAG başarıyla tamamlandı!"',
    )

    # Task Dependencies (Sıralama)
    # task_tarih çalışır -> task_python çalışır -> task_bilgi çalışır -> task_basari çalışır
    task_tarih >> task_python >> task_bilgi >> task_basari
