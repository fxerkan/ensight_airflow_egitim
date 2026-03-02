# SQL Scripts Dizini

Bu dizin, Airflow DAG'lerinde kullanılan **external SQL scriptlerini** içerir.

## Dizin Yapısı

```
sql/
├── README.md
└── datamart/
    ├── 01_transform_sales.sql     # Staging → Datamart transformation
    ├── 02_create_summary.sql      # Günlük özet rapor oluşturma
    └── 03_quality_checks.sql      # Veri kalitesi kontrolleri
```

## Kullanım

### Airflow DAG'den SQL Dosyası Okuma

```python
from pathlib import Path

def load_sql_file(sql_file_name: str) -> str:
    """SQL dosyasını repo içinden oku"""
    sql_dir = Path(__file__).parent.parent / 'sql' / 'datamart'
    sql_file_path = sql_dir / sql_file_name

    with open(sql_file_path, 'r', encoding='utf-8') as f:
        return f.read()

# BigQueryInsertJobOperator ile kullanım
transform_task = BigQueryInsertJobOperator(
    task_id='transform_sales_data',
    configuration={
        "query": {
            "query": load_sql_file('01_transform_sales.sql'),
            "useLegacySql": False
        }
    },
    params={
        'project_id': 'my-project',
    }
)
```

## SQL Dosyaları

### 01_transform_sales.sql
**Amaç:** Staging layer'dan veriyi okur, temizler ve datamart layer'a yükler.

**Kaynak:** `staging.sales_raw`
**Hedef:** `datamart.sales_cleaned`

**İşlemler:**
- Veri temizleme (NULL check, negatif değer kontrolü)
- Tarih dönüşümü (STRING → DATE)
- Hesaplanan alanlar (discount_percentage, net_amount)
- Kategorizasyon (order_size_category)
- Data quality flag'leme

**Airflow Variables:**
- `{{ params.project_id }}` - GCP Project ID
- `{{ ds }}` - Execution date (YYYY-MM-DD)

---

### 02_create_summary.sql
**Amaç:** Günlük satış özet raporunu oluşturur.

**Kaynak:** `datamart.sales_cleaned`
**Hedef:** `datamart.daily_sales_summary`

**Metrikler:**
- Toplam satış, sipariş sayısı, müşteri sayısı
- Kategori bazlı breakdown (Electronics, Fashion, Home)
- Sipariş büyüklüğü dağılımı (Small, Medium, Large, Extra Large)
- İndirim analizi
- Veri kalitesi skorları

**Özellikler:**
- MERGE kullanarak upsert (aynı tarih için yeniden çalıştırılabilir)
- Partitioned table (report_date)

**Airflow Variables:**
- `{{ params.project_id }}` - GCP Project ID
- `{{ ds }}` - Execution date (YYYY-MM-DD)

---

### 03_quality_checks.sql
**Amaç:** Veri kalitesi kontrolleri yapar, hata bulursa pipeline'ı durdurur.

**Kontroller:**
1. **Row Count Check** - Minimum veri kontrolü
2. **Null Check** - Kritik alanlarda NULL kontrolü
3. **Value Range Check** - Negatif değer, sıfır kontrolü
4. **Business Rule Check** - İş kuralları (discount > total, vs.)
5. **Duplicate Check** - Tekrar eden order_id kontrolü
6. **Quality Score Check** - Minimum %95 veri kalitesi

**Özellikler:**
- ERROR() fonksiyonu ile pipeline fail
- Detaylı hata mesajları
- Özet quality score

**Airflow Variables:**
- `{{ params.project_id }}` - GCP Project ID
- `{{ ds }}` - Execution date (YYYY-MM-DD)

---

## Airflow Template Variables

SQL dosyalarında aşağıdaki Airflow template değişkenleri kullanılabilir:

| Variable | Açıklama | Örnek Değer |
|----------|----------|-------------|
| `{{ ds }}` | Execution date (YYYY-MM-DD) | `2024-01-15` |
| `{{ ds_nodash }}` | Execution date (YYYYMMDD) | `20240115` |
| `{{ params.project_id }}` | GCP Project ID | `my-project` |
| `{{ params.staging_dataset }}` | Staging dataset | `staging` |
| `{{ params.datamart_dataset }}` | Datamart dataset | `datamart` |

## Best Practices

### ✅ DO: External SQL Kullan

**Avantajlar:**
- SQL'i version control'de ayrı takip edebilme
- SQL Developer'lar IDE'lerinde çalışabilir
- Kod tekrarını önler
- Gerçek üretimde GCS bucket'dan okunabilir
- SQL syntax highlighting ve linting

**Ne zaman kullan:**
- Kompleks transformasyonlar (100+ satır)
- Tekrar kullanılabilir SQL'ler
- SQL Developer collaboration
- Production ETL queries

### ⚠️ Dikkat: Hardcoded SQL

**Dezavantajlar:**
- Python içinde SQL yazmak zor
- IDE'de syntax highlighting yok
- Kod tekrarı

**Ne zaman kullan:**
- Basit CREATE/DROP operasyonları
- Test data insertion
- Single-use SQL'ler (<50 satır)
- Hızlı prototipleme

---

## GCS Entegrasyonu (Gelecekte)

Gerçek üretimde SQL dosyaları GCS bucket'da tutulabilir:

### SQL Dosyalarını GCS'e Yükleme

```bash
# SQL dosyalarını GCS'e yükle
gsutil -m cp -r sql/ gs://my-sql-scripts-bucket/
```

### GCS'den SQL Dosyası Okuma

```python
from google.cloud import storage

def load_sql_from_gcs(bucket_name: str, sql_file_path: str) -> str:
    """GCS'den SQL dosyası oku"""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(sql_file_path)
    sql_content = blob.download_as_text()
    return sql_content

# Kullanım
sql = load_sql_from_gcs(
    bucket_name='my-sql-scripts-bucket',
    sql_file_path='sql/datamart/01_transform_sales.sql'
)
```

### GCS Bucket Yapısı

```
gs://my-sql-scripts-bucket/
├── sql/
│   ├── datamart/
│   │   ├── 01_transform_sales.sql
│   │   ├── 02_create_summary.sql
│   │   └── 03_quality_checks.sql
│   ├── staging/
│   │   └── ...
│   └── reporting/
│       └── ...
└── templates/
    └── ...
```

---

## SQL Development Workflow

### 1. BigQuery Console'da Geliştir

```sql
-- BigQuery Console'da SQL'i yaz ve test et
SELECT
    order_id,
    customer_id,
    total_amount
FROM `project.staging.sales_raw`
WHERE order_date = '2024-01-15'
LIMIT 10;
```

### 2. SQL Dosyasına Kaydet

```bash
# SQL'i dosyaya kaydet
nano sql/datamart/01_transform_sales.sql
```

### 3. Airflow Template Variables Ekle

```sql
-- Hardcoded değerleri Airflow template ile değiştir
WHERE order_date = DATE('{{ ds }}')
```

### 4. DAG'de Kullan

```python
# DAG'de SQL dosyasını kullan
transform_task = BigQueryInsertJobOperator(
    task_id='transform_sales_data',
    configuration={
        "query": {
            "query": load_sql_file('01_transform_sales.sql'),
            "useLegacySql": False
        }
    }
)
```

### 5. Test Et

```bash
# Airflow'da test et
airflow tasks test 08_datamart_sql_pipeline transform_sales_data 2024-01-15
```

---

## Troubleshooting

### SQL Dosyası Bulunamıyor Hatası

```python
FileNotFoundError: SQL dosyası bulunamadı: /path/to/sql/datamart/01_transform_sales.sql
```

**Çözüm:**
- Dosya yolunu kontrol et
- SQL dizini var mı kontrol et
- Dosya adını kontrol et (case-sensitive)

### Airflow Template Render Hatası

```
jinja2.exceptions.UndefinedError: 'ds' is undefined
```

**Çözüm:**
- DAG'de `render_template_as_native_obj=True` ekle
- Template değişkenini kontrol et ({{ ds }} doğru yazılmış mı?)

### BigQuery Syntax Error

```
Syntax error: Expected end of input but got keyword SELECT
```

**Çözüm:**
- SQL'i BigQuery Console'da test et
- `;` karakterlerini kontrol et
- Yorum satırlarını kontrol et

---

## Referanslar

- [BigQuery SQL Reference](https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax)
- [Airflow Templating](https://airflow.apache.org/docs/apache-airflow/stable/templates-ref.html)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [Google Cloud Storage Python Client](https://cloud.google.com/python/docs/reference/storage/latest)
