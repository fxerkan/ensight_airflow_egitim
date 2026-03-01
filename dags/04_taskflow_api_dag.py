"""
DAG 4: TaskFlow API - Modern Airflow Yaklaşımı (Airflow 2.0+)

TaskFlow API (@task decorator) kullanarak:
- Daha temiz kod
- Otomatik XCom yönetimi
- Type hints desteği
- Kolay veri paylaşımı
"""

from airflow.decorators import dag, task
from datetime import datetime, timedelta
import json

# Default arguments
default_args = {
    'owner': 'data-team',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

@dag(
    dag_id='04_taskflow_api_example',
    default_args=default_args,
    description='TaskFlow API (@task decorator) kullanım örneği',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['egitim', 'taskflow', 'modern'],
)
def taskflow_etl_pipeline():
    """
    Modern Airflow TaskFlow API ile ETL Pipeline
    """

    @task
    def extract_data() -> dict:
        """
        Extract: Veri kaynağından veri çek
        Return: Dictionary olarak veri döndür (otomatik XCom)
        """
        print("📥 Veri çekiliyor...")

        # Simüle edilmiş veri
        data = {
            'customers': [
                {'id': 1, 'name': 'Ahmet Yılmaz', 'city': 'Istanbul'},
                {'id': 2, 'name': 'Ayşe Demir', 'city': 'Ankara'},
                {'id': 3, 'name': 'Mehmet Kaya', 'city': 'Izmir'},
            ],
            'orders': [
                {'order_id': 101, 'customer_id': 1, 'amount': 250.50},
                {'order_id': 102, 'customer_id': 2, 'amount': 175.00},
                {'order_id': 103, 'customer_id': 1, 'amount': 450.75},
            ],
            'extract_timestamp': str(datetime.now())
        }

        print(f"✅ {len(data['customers'])} müşteri ve {len(data['orders'])} sipariş çekildi")
        return data

    @task
    def transform_data(data: dict) -> dict:
        """
        Transform: Veriyi dönüştür ve zenginleştir
        Args: Önceki task'tan otomatik gelen veri
        Return: Dönüştürülmüş veri
        """
        print("🔄 Veri dönüştürülüyor...")

        # Müşteri bazında toplam sipariş tutarı hesapla
        customer_totals = {}
        for order in data['orders']:
            customer_id = order['customer_id']
            amount = order['amount']

            if customer_id not in customer_totals:
                customer_totals[customer_id] = 0
            customer_totals[customer_id] += amount

        # Müşteri bilgilerini zenginleştir
        enriched_customers = []
        for customer in data['customers']:
            customer_id = customer['id']
            enriched_customers.append({
                'customer_id': customer_id,
                'customer_name': customer['name'],
                'city': customer['city'],
                'total_orders': customer_totals.get(customer_id, 0),
                'customer_segment': 'VIP' if customer_totals.get(customer_id, 0) > 300 else 'Standard'
            })

        transformed_data = {
            'customers': enriched_customers,
            'summary': {
                'total_customers': len(enriched_customers),
                'total_revenue': sum(customer_totals.values()),
                'vip_customers': len([c for c in enriched_customers if c['customer_segment'] == 'VIP'])
            },
            'transform_timestamp': str(datetime.now())
        }

        print(f"✅ {transformed_data['summary']['total_customers']} müşteri dönüştürüldü")
        print(f"💰 Toplam Gelir: {transformed_data['summary']['total_revenue']:.2f} TL")
        return transformed_data

    @task
    def load_data(data: dict) -> str:
        """
        Load: Dönüştürülmüş veriyi hedef sisteme yükle
        Args: Transform task'tan gelen veri
        Return: Yükleme durumu
        """
        print("💾 Veri yükleniyor...")

        # Simüle edilmiş veri yükleme
        print(f"📊 Özet İstatistikler:")
        print(f"  - Toplam Müşteri: {data['summary']['total_customers']}")
        print(f"  - VIP Müşteri: {data['summary']['vip_customers']}")
        print(f"  - Toplam Gelir: {data['summary']['total_revenue']:.2f} TL")

        # Her müşteriyi yazdır
        print(f"\n📋 Müşteri Detayları:")
        for customer in data['customers']:
            print(f"  {customer['customer_name']} ({customer['city']}) - "
                  f"{customer['total_orders']:.2f} TL - {customer['customer_segment']}")

        print(f"\n✅ Veri başarıyla yüklendi!")
        return "success"

    @task
    def send_summary(load_status: str, summary_data: dict):
        """
        Summary: Özet rapor oluştur
        Args:
            load_status: Load task'tan gelen durum
            summary_data: Transform task'tan gelen özet bilgi
        """
        print("📧 Özet rapor oluşturuluyor...")

        if load_status == "success":
            print(f"\n{'='*50}")
            print(f"ETL PİPELİNE RAPORU")
            print(f"{'='*50}")
            print(f"Durum: ✅ Başarılı")
            print(f"Toplam Müşteri: {summary_data['summary']['total_customers']}")
            print(f"VIP Müşteri: {summary_data['summary']['vip_customers']}")
            print(f"Toplam Gelir: {summary_data['summary']['total_revenue']:.2f} TL")
            print(f"Tarih: {summary_data['transform_timestamp']}")
            print(f"{'='*50}")
        else:
            print("❌ Pipeline başarısız!")

    # ========== TASK ÇAĞRILARI VE DEPENDENCIES ==========
    # TaskFlow API ile otomatik dependency ve veri aktarımı

    # Extract
    extracted_data = extract_data()

    # Transform (extract'tan veriyi al)
    transformed_data = transform_data(extracted_data)

    # Load (transform'dan veriyi al)
    load_status = load_data(transformed_data)

    # Summary (hem load_status hem de transformed_data al)
    send_summary(load_status, transformed_data)

# DAG instance oluştur
dag_instance = taskflow_etl_pipeline()
