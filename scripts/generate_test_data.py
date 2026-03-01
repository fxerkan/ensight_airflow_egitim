"""
Test Verisi Oluşturma Script'i

Sales Datamart Pipeline için test CSV dosyaları oluşturur:
- customers.csv
- products.csv
- transactions.csv

Kullanım:
    python scripts/generate_test_data.py
"""

import pandas as pd
import random
from datetime import datetime, timedelta
import os

# Seed (tekrarlanabilir rastgele veri)
random.seed(42)

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Tarih formatı
today = datetime.now()
date_str = today.strftime('%Y%m%d')

print(f"🔄 Test verileri oluşturuluyor... (Tarih: {date_str})")

# ========== CUSTOMERS ==========
print(f"  📊 Müşteri verisi oluşturuluyor...")

turkish_cities = ['Istanbul', 'Ankara', 'Izmir', 'Bursa', 'Antalya', 'Adana', 'Konya', 'Gaziantep']
first_names = ['Ahmet', 'Mehmet', 'Mustafa', 'Ali', 'Hüseyin', 'Ayşe', 'Fatma', 'Emine', 'Zeynep', 'Hatice']
last_names = ['Yılmaz', 'Kaya', 'Demir', 'Çelik', 'Şahin', 'Yıldız', 'Aydın', 'Özdemir', 'Arslan', 'Doğan']

customers = []
for i in range(1, 101):  # 100 müşteri
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    full_name = f"{first_name} {last_name}"

    customers.append({
        'customer_id': f'CUST{i:05d}',
        'customer_name': full_name,
        'email': f'{first_name.lower()}.{last_name.lower()}@example.com',
        'city': random.choice(turkish_cities),
        'country': 'Turkey',
        'created_date': (today - timedelta(days=random.randint(30, 730))).strftime('%Y-%m-%d')
    })

customers_df = pd.DataFrame(customers)
customers_file = os.path.join(OUTPUT_DIR, f'customers_{date_str}.csv')
customers_df.to_csv(customers_file, index=False, encoding='utf-8-sig')
print(f"     ✅ {len(customers_df)} müşteri → {customers_file}")

# ========== PRODUCTS ==========
print(f"  📦 Ürün verisi oluşturuluyor...")

categories = {
    'Electronics': ['Laptop', 'Desktop PC', 'Tablet', 'Smartphone', 'Smartwatch', 'Monitor', 'Keyboard', 'Mouse'],
    'Home Appliances': ['Çamaşır Makinesi', 'Bulaşık Makinesi', 'Buzdolabı', 'Fırın', 'Süpürge'],
    'Fashion': ['Tişört', 'Pantolon', 'Ceket', 'Ayakkabı', 'Çanta'],
    'Books': ['Roman', 'Bilim Kurgu', 'Tarih', 'Biyografi', 'Çocuk Kitabı'],
}

products = []
product_id = 1
for category, product_list in categories.items():
    for product_name in product_list:
        # Fiyat kategoriye göre
        if category == 'Electronics':
            base_price = random.uniform(1000, 15000)
        elif category == 'Home Appliances':
            base_price = random.uniform(2000, 10000)
        elif category == 'Fashion':
            base_price = random.uniform(100, 2000)
        else:  # Books
            base_price = random.uniform(20, 200)

        products.append({
            'product_id': f'PROD{product_id:04d}',
            'product_name': product_name,
            'category': category,
            'subcategory': f'Sub-{category[:3]}',
            'unit_price': round(base_price, 2)
        })
        product_id += 1

products_df = pd.DataFrame(products)
products_file = os.path.join(OUTPUT_DIR, f'products_{date_str}.csv')
products_df.to_csv(products_file, index=False, encoding='utf-8-sig')
print(f"     ✅ {len(products_df)} ürün → {products_file}")

# ========== TRANSACTIONS ==========
print(f"  💳 İşlem verisi oluşturuluyor...")

transactions = []
transaction_id = 1

# Bugün için 200-500 işlem oluştur
num_transactions = random.randint(200, 500)

for _ in range(num_transactions):
    customer = random.choice(customers)
    product = random.choice(products)

    quantity = random.randint(1, 5)
    unit_price = product['unit_price']
    total_amount = round(quantity * unit_price, 2)
    discount_amount = round(total_amount * random.choice([0, 0, 0.05, 0.10, 0.15]), 2)

    # Bugün içinde rastgele saat
    transaction_time = today - timedelta(
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )

    transactions.append({
        'transaction_id': f'TXN{transaction_id:08d}',
        'customer_id': customer['customer_id'],
        'product_id': product['product_id'],
        'quantity': quantity,
        'unit_price': unit_price,
        'total_amount': total_amount,
        'discount_amount': discount_amount,
        'transaction_timestamp': transaction_time.strftime('%Y-%m-%d %H:%M:%S')
    })
    transaction_id += 1

transactions_df = pd.DataFrame(transactions)
transactions_file = os.path.join(OUTPUT_DIR, f'transactions_{date_str}.csv')
transactions_df.to_csv(transactions_file, index=False, encoding='utf-8-sig')
print(f"     ✅ {len(transactions_df)} işlem → {transactions_file}")

# ========== ÖZET ==========
print(f"\n{'='*70}")
print(f"✅ TEST VERİLERİ BAŞARIYLA OLUŞTURULDU!")
print(f"{'='*70}")
print(f"📁 Dizin: {OUTPUT_DIR}")
print(f"📊 Müşteriler: {len(customers_df)} kayıt")
print(f"📦 Ürünler: {len(products_df)} kayıt")
print(f"💳 İşlemler: {len(transactions_df)} kayıt")
print(f"📅 Tarih: {date_str}")
print(f"{'='*70}\n")

# İstatistikler
total_sales = transactions_df['total_amount'].sum()
total_discount = transactions_df['discount_amount'].sum()
net_sales = total_sales - total_discount

print(f"💰 SATIŞ İSTATİSTİKLERİ:")
print(f"   Toplam Satış: {total_sales:,.2f} TL")
print(f"   Toplam İndirim: {total_discount:,.2f} TL")
print(f"   Net Satış: {net_sales:,.2f} TL")
print(f"   Ortalama İşlem: {net_sales / len(transactions_df):,.2f} TL")
print(f"\n")
