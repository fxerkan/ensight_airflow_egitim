# Airflow Quickstart - 5 Dakikada Başla

> **Hedef**: 5 dakikada Airflow kurulumu yapın, ilk DAG'inizi çalıştırın ve temel özellikleri öğrenin.

## İçindekiler
1. [Hızlı Kurulum (2 dakika)](#hizli-kurulum)
2. [İlk DAG (2 dakika)](#ilk-dag)
3. [WebUI Kullanımı (1 dakika)](#webui-kullanimi)
4. [İlk 10 Komut](#ilk-10-komut)
5. [Sonraki Adımlar](#sonraki-adimlar)

---

## Hızlı Kurulum

### Adım 1: Docker Compose ile Başlat (30 saniye)

```bash
# Proje dizini oluştur
mkdir airflow-quickstart && cd airflow-quickstart
mkdir -p dags logs plugins config

# Docker Compose dosyasını indir
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.8.1/docker-compose.yaml'

# Environment dosyası oluştur
echo "AIRFLOW_UID=50000" > .env

# Initialize database
docker compose up airflow-init

# Tüm servisleri başlat
docker compose up -d
```

**Beklenen Çıktı:**
```
✔ Container airflow-postgres-1       Started
✔ Container airflow-webserver-1      Started
✔ Container airflow-scheduler-1      Started
```

### Adım 2: WebUI'ya Giriş (30 saniye)

1. Tarayıcıda aç: http://localhost:8080
2. Login:
   - **Username**: `airflow`
   - **Password**: `airflow`

---

## İlk DAG

### Hello World DAG (60 saniye)

`dags/hello_world.py` dosyası oluşturun:

```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id='hello_world',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['quickstart']
) as dag:

    hello = BashOperator(
        task_id='say_hello',
        bash_command='echo "Hello Airflow! Bugün $(date)"'
    )

    goodbye = BashOperator(
        task_id='say_goodbye',
        bash_command='echo "Goodbye! Pipeline tamamlandı."'
    )

    hello >> goodbye
```

### DAG'i Test Et (30 saniye)

```bash
# DAG'in import olup olmadığını kontrol et
docker exec airflow-webserver-1 airflow dags list | grep hello

# DAG'i test et
docker exec airflow-webserver-1 \
  airflow dags test hello_world 2024-01-01
```

**Beklenen Çıktı:**
```
Hello Airflow! Bugün ...
Goodbye! Pipeline tamamlandı.
```

---

## WebUI Kullanımı

### DAG'i Manuel Çalıştır (15 saniye)

1. http://localhost:8080 → DAGs sayfası
2. `hello_world` DAG'ini bulun
3. ▶️ **Play** butonuna tıklayın
4. **Trigger DAG** butonuna basın

### Task Durumunu İzle (15 saniye)

1. DAG adına tıklayın → **Grid View**
2. Task'ların renklerini izleyin:
   - 🟡 Sarı: Running
   - 🟢 Yeşil: Success
   - 🔴 Kırmızı: Failed
3. Task'a tıklayıp **Log** butonuna basarak log'ları görün

### Graph View (15 saniye)

1. **`g` tuşuna** basarak **Graph View**'a geçin
2. Task dependency'leri görün: `hello → goodbye`
3. Task'a tıklayarak detayları görün

---

## İlk 10 Komut

### Temel Komutlar

```bash
# 1. DAG listesi
docker exec airflow-webserver-1 airflow dags list

# 2. DAG'i pause/unpause
docker exec airflow-webserver-1 airflow dags unpause hello_world
docker exec airflow-webserver-1 airflow dags pause hello_world

# 3. DAG'i trigger et
docker exec airflow-webserver-1 airflow dags trigger hello_world

# 4. DAG'i test et (database'e yazmaz)
docker exec airflow-webserver-1 airflow dags test hello_world 2024-01-01

# 5. Task'ı test et
docker exec airflow-webserver-1 \
  airflow tasks test hello_world say_hello 2024-01-01

# 6. Task log'larını görüntüle
docker exec airflow-webserver-1 \
  airflow tasks logs hello_world say_hello 2024-01-01

# 7. Import errors kontrol et
docker exec airflow-webserver-1 airflow dags list-import-errors

# 8. Connection ekle
docker exec airflow-webserver-1 \
  airflow connections add my_conn --conn-type http

# 9. Variable ekle
docker exec airflow-webserver-1 \
  airflow variables set my_var my_value

# 10. Scheduler health check
docker exec airflow-scheduler-1 airflow jobs check
```

---

## İkinci DAG - ETL Örneği

`dags/simple_etl.py`:

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id='simple_etl',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['etl', 'quickstart']
)
def simple_etl_pipeline():

    @task
    def extract():
        """Veri çek"""
        data = [
            {'id': 1, 'name': 'Product A', 'price': 100},
            {'id': 2, 'name': 'Product B', 'price': 200},
        ]
        print(f"Extracted {len(data)} rows")
        return data

    @task
    def transform(data: list):
        """Veriyi dönüştür"""
        for item in data:
            item['price_with_tax'] = item['price'] * 1.18
        print(f"Transformed {len(data)} rows")
        return data

    @task
    def load(data: list):
        """Veriyi yükle"""
        for item in data:
            print(f"Loading: {item}")
        print(f"Loaded {len(data)} rows successfully")

    # Pipeline tanımı
    extracted_data = extract()
    transformed_data = transform(extracted_data)
    load(transformed_data)

# DAG instance oluştur
dag = simple_etl_pipeline()
```

**Test Et:**
```bash
docker exec airflow-webserver-1 \
  airflow dags test simple_etl 2024-01-01
```

---

## Common Pitfalls ve Çözümleri

### 1. DAG Görünmüyor

**Problem**: WebUI'da DAG listede yok

**Çözüm:**
```bash
# Import errors kontrol et
docker exec airflow-webserver-1 airflow dags list-import-errors

# DAG dosyasını Python olarak çalıştır
docker exec airflow-webserver-1 python /opt/airflow/dags/my_dag.py

# Scheduler log'larını kontrol et
docker logs airflow-scheduler-1 --tail 50
```

### 2. Task Stuck in Queued

**Problem**: Task "queued" state'de kalıyor

**Çözüm:**
```bash
# Scheduler çalışıyor mu?
docker ps | grep scheduler

# Worker çalışıyor mu? (CeleryExecutor varsa)
docker ps | grep worker

# Scheduler'ı restart et
docker compose restart airflow-scheduler
```

### 3. Port Already in Use

**Problem**: "Port 8080 already in use"

**Çözüm:**
```bash
# Portu kullanan process'i bul
lsof -i :8080

# Farklı port kullan (docker-compose.yaml'de)
ports:
  - "8081:8080"  # 8081'i kullan
```

### 4. Permission Denied (Linux)

**Problem**: Log dosyalarına yazma izni yok

**Çözüm:**
```bash
# Klasörlere izin ver
sudo chown -R 50000:0 dags/ logs/ plugins/

# Veya .env'de AIRFLOW_UID belirle
echo "AIRFLOW_UID=$(id -u)" >> .env
```

---

## Özet Komutlar

### Kurulum
```bash
mkdir airflow-quickstart && cd airflow-quickstart
mkdir -p dags logs plugins
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.8.1/docker-compose.yaml'
echo "AIRFLOW_UID=50000" > .env
docker compose up airflow-init
docker compose up -d
```

### DAG Yönetimi
```bash
# List, trigger, test
airflow dags list
airflow dags trigger my_dag
airflow dags test my_dag 2024-01-01
```

### Debug
```bash
# Errors, logs
airflow dags list-import-errors
airflow tasks logs my_dag my_task 2024-01-01
docker logs airflow-scheduler-1
```

### Cleanup
```bash
# Tüm servisleri durdur ve temizle
docker compose down -v
```

---

## Sonraki Adımlar

### 1. Dokümantasyonu İnceleyin
- **[01-giris.md](01-giris.md)**: Airflow kavramları detaylı
- **[02-kurulum.md](02-kurulum.md)**: Production kurulum
- **[03-dag-gelistirme.md](03-dag-gelistirme.md)**: DAG best practices

### 2. Örnek DAG'leri İnceleyin
```bash
# Example DAG'leri aktif et (docker-compose.yaml'de)
AIRFLOW__CORE__LOAD_EXAMPLES: 'true'
```

### 3. Provider Packages Ekleyin
```bash
# Google Cloud için
_PIP_ADDITIONAL_REQUIREMENTS: apache-airflow-providers-google

# AWS için
_PIP_ADDITIONAL_REQUIREMENTS: apache-airflow-providers-amazon
```

### 4. Gerçek Veri ile ETL Yapın
- BigQuery entegrasyonu: [07-bigquery-entegrasyonu.md](07-bigquery-entegrasyonu.md)
- Sales Datamart demo: [08-sales-datamart-demo.md](08-sales-datamart-demo.md)

### 5. Production'a Geçiş
- Deployment: [06-deployment-cicd.md](06-deployment-cicd.md)
- Cloud Composer (GCP) veya AWS MWAA kullanın

---

## Faydalı Linkler

### Resmi Kaynaklar
- [Apache Airflow Official Docs](https://airflow.apache.org/docs/)
- [Airflow GitHub](https://github.com/apache/airflow)
- [Provider Packages](https://airflow.apache.org/docs/apache-airflow-providers/index.html)

### Community
- [Airflow Slack](https://apache-airflow.slack.com/)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/airflow)
- [Astronomer Guides](https://docs.astronomer.io/learn)

### Tools
- [Crontab Guru](https://crontab.guru/) - Cron expression tester
- [Airflow Summit Videos](https://airflowsummit.org/)

---

## Cheat Sheet'e Geçin

Detaylı referans için: **[cheatsheet.md](cheatsheet.md)**

---

**Tebrikler!** 🎉

İlk Airflow DAG'inizi çalıştırdınız. Şimdi [cheatsheet.md](cheatsheet.md) ile devam edin veya [03-dag-gelistirme.md](03-dag-gelistirme.md) ile DAG geliştirmeyi derinleştirin.
