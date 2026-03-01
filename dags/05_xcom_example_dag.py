"""
DAG 5: XCom (Cross-Communication) Örneği

XCom ile task'lar arası veri paylaşımı:
- xcom_push: Veri gönderme
- xcom_pull: Veri alma
- Return value: Otomatik XCom push
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import json
import random

default_args = {
    'owner': 'data-team',
    'retries': 1,
    'retry_delay': timedelta(minutes=3),
}

def generate_sales_data(**kwargs):
    """
    Rastgele satış verisi oluştur ve XCom'a gönder
    """
    print("📊 Satış verisi oluşturuluyor...")

    # Rastgele satış verisi
    sales_data = {
        'total_sales': round(random.uniform(10000, 50000), 2),
        'transaction_count': random.randint(100, 500),
        'avg_transaction': 0,
        'top_product': random.choice(['Laptop', 'Telefon', 'Tablet', 'Kulaklık']),
        'region': random.choice(['İstanbul', 'Ankara', 'İzmir'])
    }

    sales_data['avg_transaction'] = round(
        sales_data['total_sales'] / sales_data['transaction_count'], 2
    )

    print(f"✅ Satış Verisi Oluşturuldu:")
    print(json.dumps(sales_data, indent=2, ensure_ascii=False))

    # Manuel XCom push (farklı key'lerle)
    ti = kwargs['ti']
    ti.xcom_push(key='total_sales', value=sales_data['total_sales'])
    ti.xcom_push(key='transaction_count', value=sales_data['transaction_count'])

    # Return ile otomatik XCom push (key: return_value)
    return sales_data

def analyze_sales(**kwargs):
    """
    XCom'dan satış verisini al ve analiz et
    """
    print("🔍 Satış verisi analiz ediliyor...")

    ti = kwargs['ti']

    # Method 1: Belirli key ile pull
    total_sales = ti.xcom_pull(task_ids='generate_sales', key='total_sales')
    transaction_count = ti.xcom_pull(task_ids='generate_sales', key='transaction_count')

    # Method 2: Return value pull (default key)
    sales_data = ti.xcom_pull(task_ids='generate_sales')

    print(f"\n📈 Analiz Sonuçları:")
    print(f"  Toplam Satış: {total_sales:,.2f} TL")
    print(f"  İşlem Sayısı: {transaction_count}")
    print(f"  Ortalama İşlem: {sales_data['avg_transaction']:,.2f} TL")
    print(f"  En Çok Satan Ürün: {sales_data['top_product']}")
    print(f"  Bölge: {sales_data['region']}")

    # Performans kategorisi belirle
    performance = "Mükemmel" if total_sales > 35000 else "İyi" if total_sales > 20000 else "Orta"

    analysis_result = {
        'sales_data': sales_data,
        'performance': performance,
        'recommendation': 'Stoğu artır' if total_sales > 35000 else 'Mevcut stok yeterli'
    }

    return analysis_result

def generate_report(**kwargs):
    """
    Analiz sonucunu XCom'dan al ve rapor oluştur
    """
    print("📄 Rapor oluşturuluyor...")

    ti = kwargs['ti']

    # Önceki task'tan veri al
    analysis = ti.xcom_pull(task_ids='analyze_sales')

    if not analysis:
        print("❌ Analiz verisi bulunamadı!")
        return

    sales_data = analysis['sales_data']

    print(f"\n{'='*60}")
    print(f"GÜNLÜK SATIŞ RAPORU")
    print(f"{'='*60}")
    print(f"Tarih: {kwargs['ds']}")
    print(f"\n📊 SATIŞ BİLGİLERİ:")
    print(f"  Toplam Satış: {sales_data['total_sales']:,.2f} TL")
    print(f"  İşlem Sayısı: {sales_data['transaction_count']}")
    print(f"  Ortalama İşlem: {sales_data['avg_transaction']:,.2f} TL")
    print(f"\n🏆 PERFORMANS:")
    print(f"  Kategori: {analysis['performance']}")
    print(f"  En Çok Satan: {sales_data['top_product']}")
    print(f"  Bölge: {sales_data['region']}")
    print(f"\n💡 ÖNERİ:")
    print(f"  {analysis['recommendation']}")
    print(f"{'='*60}\n")

    # XCom'a rapor durumu push et
    ti.xcom_push(key='report_status', value='completed')

    return {
        'report_generated': True,
        'timestamp': str(datetime.now())
    }

def check_report_status(**kwargs):
    """
    Rapor durumunu kontrol et
    """
    ti = kwargs['ti']

    # Tüm önceki task'lardan XCom verilerini al
    report_info = ti.xcom_pull(task_ids='generate_report')
    report_status = ti.xcom_pull(task_ids='generate_report', key='report_status')

    print(f"📋 Rapor Durumu Kontrolü:")
    print(f"  Durum: {report_status}")
    print(f"  Rapor Oluşturuldu: {report_info.get('report_generated', False)}")
    print(f"  Zaman: {report_info.get('timestamp', 'N/A')}")

    if report_status == 'completed':
        print(f"✅ Tüm işlemler başarıyla tamamlandı!")
    else:
        print(f"⚠️ Rapor durumu beklenmedik!")

with DAG(
    dag_id='05_xcom_example',
    default_args=default_args,
    description='XCom ile task\'lar arası veri paylaşımı örneği',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['egitim', 'xcom', 'communication'],
) as dag:

    # Task 1: Veri oluştur ve XCom'a push et
    generate_sales = PythonOperator(
        task_id='generate_sales',
        python_callable=generate_sales_data,
        provide_context=True,
    )

    # Task 2: XCom'dan veri al ve analiz et
    analyze_sales_task = PythonOperator(
        task_id='analyze_sales',
        python_callable=analyze_sales,
        provide_context=True,
    )

    # Task 3: Rapor oluştur
    generate_report_task = PythonOperator(
        task_id='generate_report',
        python_callable=generate_report,
        provide_context=True,
    )

    # Task 4: Rapor durumunu kontrol et
    check_status = PythonOperator(
        task_id='check_report_status',
        python_callable=check_report_status,
        provide_context=True,
    )

    # Task 5: Bash ile XCom verisi kullanımı (Jinja template)
    print_summary = BashOperator(
        task_id='print_summary',
        bash_command='echo "Pipeline tamamlandı - Execution Date: {{ ds }}"',
    )

    # Dependencies
    generate_sales >> analyze_sales_task >> generate_report_task >> check_status >> print_summary
