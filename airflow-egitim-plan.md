# AIRFLOW 101 EĞİTİM PLANI

## 📋 EĞİTİM GENEL BAKIŞ

**Süre:** 2 Gün (16 saat)
**Seviye:** Başlangıç
**Hedef Kitle:** Python bilen, Airflow'a yeni başlayan Data Engineer'lar
**Ortam:** Docker Compose (Local) + GCP Cloud Composer (Production)

---

## 🎯 EĞİTİM HEDEFLERİ

Eğitim sonunda katılımcılar:
- ✅ Airflow mimarisini ve bileşenlerini anlayacak
- ✅ Sıfırdan DAG geliştirebilecek
- ✅ Farklı Operator tiplerini kullanabilecek
- ✅ DAG'leri Test ve Production ortamlarına deploy edebilecek
- ✅ CI/CD sürecini Azure DevOps veya GitHub ile kuracak
- ✅ Airflow WebUI'ı etkin kullanacak
- ✅ BigQuery ile entegre DAG'ler geliştirebilecek
- ✅ Dataform joblarını Airflow ile tetikleyebilecek
- ✅ Uçtan uca bir Sales Datamart pipeline'ı oluşturabilecek

---

## 📚 EĞİTİM İÇERİĞİ (Sunum Yapısı)

### **BÖLÜM 1: GİRİŞ VE TEMELLERİ (6-8 slayt)**

#### 1.1 Airflow Nedir?
- **İçerik:**
  - Workflow orchestration nedir?
  - Airflow'un tarihçesi (Airbnb, Apache)
  - Airflow vs diğer araçlar (Luigi, Prefect, Dagster)
  - Kullanım senaryoları
- **Görsel:**
  - Airflow logo ve timeline
  - Workflow orchestration konsept diyagramı
  - Kullanım senaryoları infografiği

#### 1.2 Airflow Mimarisi ve Bileşenleri
- **İçerik:**
  - **Web Server:** WebUI arayüzü
  - **Scheduler:** DAG'leri planlar ve görev atar
  - **Executor:** Görevleri çalıştırır (SequentialExecutor, LocalExecutor, CeleryExecutor, KubernetesExecutor)
  - **Metadata Database:** PostgreSQL/MySQL - DAG state, run history
  - **Workers:** Görevleri çalıştıran süreçler
  - **Triggerer:** Async görevler için (Airflow 2.2+)
- **Görsel:**
  - Mimari diyagram (Scheduler → Executor → Workers → Metadata DB)
  - Executor türleri karşılaştırma tablosu
  - Airflow 2.x architecture diagram
- **Notlar:** https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html

#### 1.3 DAG Nedir?
- **İçerik:**
  - Directed Acyclic Graph (Yönsüz Döngüsel Olmayan Graf)
  - DAG'in anatomisi: Tasks, Dependencies, Schedule
  - Task vs Operator farkı
  - DAG parametreleri: `dag_id`, `schedule_interval`, `start_date`, `catchup`, `tags`, `default_args`
- **Görsel:**
  - DAG graf örneği (A → B → C → D, branch yapısı)
  - Task lifecycle diagram
  - DAG parametreleri infografiği
- **Kod Örneği:**
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email': ['team@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='ilk_dag_ornegimiz',
    default_args=default_args,
    description='İlk basit DAG örneği',
    schedule_interval='0 8 * * *',  # Her gün saat 08:00
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['ornek', 'egitim'],
) as dag:

    def merhaba_dunya():
        print("Merhaba Airflow!")
        return "Başarılı!"

    task1 = PythonOperator(
        task_id='merhaba_task',
        python_callable=merhaba_dunya
    )
```

---

### **BÖLÜM 2: KURULUM VE KONFIGÜRASYON (8-10 slayt)**

#### 2.1 Docker Compose ile Local Kurulum
- **İçerik:**
  - Docker Desktop kurulumu (Windows/Mac)
  - Official Airflow Docker Compose dosyası
  - Dizin yapısı: `dags/`, `logs/`, `plugins/`, `config/`
  - Container'ları başlatma: `docker-compose up`
  - Servisler: webserver, scheduler, postgres, redis
- **Kod Örneği:**
```bash
# Docker Compose dosyasını indir
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.8.1/docker-compose.yaml'

# Dizinleri oluştur
mkdir -p ./dags ./logs ./plugins ./config

# Airflow user ID ayarla
echo -e "AIRFLOW_UID=$(id -u)" > .env

# Başlat
docker-compose up airflow-init
docker-compose up -d

# UI: http://localhost:8080
# Username: airflow
# Password: airflow
```
- **Görsel:**
  - Docker Desktop ekran görüntüsü
  - Dizin yapısı ağaç diyagramı
  - Docker containers listesi (docker ps)
  - Airflow login ekranı

#### 2.2 Airflow Konfigürasyonu (airflow.cfg)
- **İçerik:**
  - Önemli konfigürasyon parametreleri:
    - `executor`: LocalExecutor, CeleryExecutor
    - `sql_alchemy_conn`: Database connection
    - `dags_folder`: DAG dosyalarının yolu
    - `load_examples`: Example DAG'leri göster/gizle
    - `parallelism`: Max paralel task sayısı
    - `max_active_runs_per_dag`: DAG başına max aktif run
  - Environment variables ile override
- **Kod Örneği:**
```ini
[core]
executor = LocalExecutor
dags_folder = /opt/airflow/dags
load_examples = False
parallelism = 32
max_active_runs_per_dag = 16

[database]
sql_alchemy_conn = postgresql+psycopg2://airflow:airflow@postgres/airflow

[webserver]
expose_config = True
rbac = True
```
- **Görsel:**
  - airflow.cfg dosya içeriği
  - Environment variables listesi

#### 2.3 GCP Cloud Composer Kurulumu
- **İçerik:**
  - Cloud Composer nedir? (Managed Airflow)
  - GCP Console'dan environment oluşturma
  - Composer versiyonu seçimi (Airflow 2.x)
  - Machine type, node count, disk size
  - Fiyatlandırma modeli
- **Görsel:**
  - GCP Console - Cloud Composer ekran görüntüleri
  - Environment creation adımları
  - Composer architecture diagram
- **Notlar:** https://cloud.google.com/composer/docs/concepts/overview

---

### **BÖLÜM 3: İLK DAG GELİŞTİRME (10-12 slayt)**

#### 3.1 Çok Basit Bir DAG Geliştirme
- **İçerik:**
  - Adım 1: DAG dosyası oluştur (`dags/ilk_dag.py`)
  - Adım 2: Import statements
  - Adım 3: DAG tanımla
  - Adım 4: Task'ları ekle
  - Adım 5: Dependencies tanımla
  - DAG'i Airflow'a yükle
- **Kod Örneği 1: Hello World DAG**
```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime

def print_context(**kwargs):
    print(f"Execution Date: {kwargs['execution_date']}")
    print(f"DAG Run ID: {kwargs['run_id']}")
    return "Tamamlandı!"

with DAG(
    'hello_world_dag',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['hello', 'beginner']
) as dag:

    # Task 1: Bash komutu çalıştır
    task_bash = BashOperator(
        task_id='print_date',
        bash_command='date'
    )

    # Task 2: Python fonksiyonu çalıştır
    task_python = PythonOperator(
        task_id='print_context',
        python_callable=print_context
    )

    # Task 3: Başka bir Bash komutu
    task_echo = BashOperator(
        task_id='echo_hello',
        bash_command='echo "Hello Airflow!"'
    )

    # Dependencies (Sıralama)
    task_bash >> task_python >> task_echo
```
- **Görsel:**
  - VS Code'da DAG dosyası
  - DAG folder structure
  - Graph view screenshot (Airflow UI)

#### 3.2 Task Dependencies (Bağımlılıklar)
- **İçerik:**
  - Bitshift operators: `>>` (downstream), `<<` (upstream)
  - Multiple dependencies: `[A, B] >> C`
  - Cross dependencies: `A >> [B, C, D] >> E`
  - `set_upstream()` ve `set_downstream()` metotları
- **Kod Örneği:**
```python
# Farklı dependency pattern'leri

# Linear
task_a >> task_b >> task_c

# Fan-out (Dallanma)
task_a >> [task_b, task_c, task_d]

# Fan-in (Birleşme)
[task_a, task_b, task_c] >> task_d

# Diamond pattern
task_start >> [task_branch1, task_branch2]
task_branch1 >> task_end
task_branch2 >> task_end

# Chain kullanımı
from airflow.models.baseoperator import chain
chain(task_a, [task_b, task_c], task_d)
```
- **Görsel:**
  - Dependency pattern diyagramları
  - Airflow Graph view örnekleri
  - Gantt chart screenshot

---

### **BÖLÜM 4: OPERATOR TİPLERİ (12-15 slayt)**

#### 4.1 Operator Nedir?
- **İçerik:**
  - Operator = Task template
  - Atomik işlerin yapı taşları
  - Idempotent olmalı
  - Operator kategorileri: Action, Transfer, Sensor
- **Görsel:**
  - Operator hierarchy diagram
  - Action vs Transfer vs Sensor karşılaştırması

#### 4.2 Temel Operatörler

##### A. BashOperator
- **Kullanım:** Shell komutları çalıştırma
- **Kod Örneği:**
```python
from airflow.operators.bash import BashOperator

run_script = BashOperator(
    task_id='run_etl_script',
    bash_command='python /scripts/etl.py --date {{ ds }}',
    env={'ENV': 'production'},
    append_env=True
)
```

##### B. PythonOperator
- **Kullanım:** Python fonksiyonları çalıştırma
- **Kod Örneği:**
```python
from airflow.operators.python import PythonOperator

def extract_data(**kwargs):
    execution_date = kwargs['execution_date']
    # Veri çekme işlemi
    data = fetch_from_api(execution_date)
    return data

extract_task = PythonOperator(
    task_id='extract_data',
    python_callable=extract_data,
    provide_context=True
)
```

##### C. EmailOperator
- **Kullanım:** Email gönderme
- **Kod Örneği:**
```python
from airflow.operators.email import EmailOperator

send_email = EmailOperator(
    task_id='send_report',
    to=['team@example.com'],
    subject='Daily Report - {{ ds }}',
    html_content='<h3>Report tamamlandı</h3>',
    files=['/tmp/report.csv']
)
```

##### D. Sensor Operators
- **Kullanım:** Koşul beklemek
- **Tipler:** FileSensor, S3KeySensor, TimeSensor, ExternalTaskSensor
- **Kod Örneği:**
```python
from airflow.sensors.filesystem import FileSensor

wait_for_file = FileSensor(
    task_id='wait_for_data',
    filepath='/data/input_{{ ds }}.csv',
    poke_interval=60,  # 60 saniyede bir kontrol
    timeout=3600  # 1 saat timeout
)
```

#### 4.3 Transfer Operatörler
- **İçerik:**
  - Sistemler arası veri aktarımı
  - S3ToRedshiftOperator, MySqlToGCSOperator, etc.
- **Görsel:**
  - Transfer operator flow diagram

#### 4.4 TaskFlow API (@task decorator) - Modern Yaklaşım
- **İçerik:**
  - Airflow 2.0+ özelliği
  - Python fonksiyonlarını otomatik task'a çevirme
  - XCom otomasyonu
- **Kod Örneği:**
```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def taskflow_example():

    @task
    def extract():
        return {'data': [1, 2, 3, 4, 5]}

    @task
    def transform(data: dict):
        values = data['data']
        return {'transformed': [x * 2 for x in values]}

    @task
    def load(data: dict):
        print(f"Loading: {data['transformed']}")

    # Otomatik dependency
    load(transform(extract()))

dag_instance = taskflow_example()
```
- **Görsel:**
  - Classic vs TaskFlow API karşılaştırması
  - TaskFlow graph view

---

### **BÖLÜM 5: DAG GELİŞTİRME ORTAMI (6-8 slayt)**

#### 5.1 IDE Kurulumu ve Eklentiler
- **İçerik:**
  - VS Code / PyCharm kullanımı
  - Apache Airflow extension
  - Python linting (pylint, black, flake8)
  - Airflow type hints ve auto-complete
- **Görsel:**
  - VS Code ekran görüntüsü + extensions
  - Auto-complete örneği

#### 5.2 Development Best Practices
- **İçerik:**
  - DAG dosya isimlendirme: `domain_process_dag.py`
  - Folder organization: `dags/finance/`, `dags/marketing/`
  - `requirements.txt` ve dependency management
  - `.airflowignore` kullanımı
  - Version control (Git)
- **Kod Örneği:**
```
dags/
├── common/
│   └── utils.py
├── finance/
│   ├── daily_sales_dag.py
│   └── monthly_revenue_dag.py
├── marketing/
│   └── campaign_analytics_dag.py
└── .airflowignore

# .airflowignore
tests/
README.md
*.pyc
__pycache__
```

#### 5.3 Local Testing
- **İçerik:**
  - `airflow dags test` komutu
  - `airflow tasks test` komutu
  - Unit testing DAG'ler
  - pytest kullanımı
- **Kod Örneği:**
```bash
# DAG syntax check
python dags/my_dag.py

# Tek bir task'ı test et
airflow tasks test my_dag my_task 2024-01-01

# Tüm DAG'i test et (gerçek run oluşturmadan)
airflow dags test my_dag 2024-01-01

# DAG parse check
airflow dags list

# Import errors kontrol
airflow dags list-import-errors
```

#### 5.4 Docker Compose Development Workflow
- **İçerik:**
  - Volume mounting: `./dags:/opt/airflow/dags`
  - Hot reload: DAG değişikliklerini otomatik algılama
  - Log izleme: `docker-compose logs -f webserver`
  - Container'a giriş: `docker exec -it airflow-webserver bash`
- **Kod Örneği:**
```bash
# DAG dosyasını kopyala
cp my_new_dag.py dags/

# Container'daki DAG'i kontrol et
docker exec airflow-webserver airflow dags list

# Scheduler loglarını izle
docker-compose logs -f scheduler

# Database reset (development)
docker-compose down -v
docker-compose up airflow-init
docker-compose up -d
```

---

### **BÖLÜM 6: DAG ÇALIŞTIRMA VE YÖNETİM (10-12 slayt)**

#### 6.1 Airflow WebUI Detaylı Anlatım
- **İçerik:**
  - **DAGs View:** Liste, search, filter, pause/unpause
  - **Graph View:** Task bağımlılıkları görselleştirme
  - **Tree View:** Geçmiş run'lar
  - **Gantt View:** Task execution timeline
  - **Code View:** DAG source kodu
  - **Task Instance Details:** Log, XCom, task duration
  - **Admin Panel:** Variables, Connections, Pools, Configuration
- **Görsel (Her bir view için screenshot):**
  - DAGs homepage
  - Graph view (colored tasks: success/failed/running)
  - Tree view (tarihsel run'lar)
  - Gantt chart
  - Task instance logs
  - Admin → Connections panel

#### 6.2 DAG Çalıştırma Yöntemleri
- **İçerik:**
  - **Manual trigger:** "Play" butonu
  - **Schedule-based:** cron expression veya preset
  - **Trigger with config:** Parametre ile çalıştırma
  - **CLI trigger:** `airflow dags trigger`
- **Kod Örneği:**
```bash
# Manual trigger via CLI
airflow dags trigger my_dag

# Trigger with config
airflow dags trigger my_dag --conf '{"param1": "value1"}'

# Trigger gelecek tarih için
airflow dags trigger my_dag --exec-date 2024-12-31
```

#### 6.3 Scheduling (Zamanlama)
- **İçerik:**
  - Cron expressions: `0 8 * * *` (Her gün 08:00)
  - Preset schedules: `@daily`, `@hourly`, `@weekly`, `@monthly`
  - `timedelta` kullanımı: `schedule_interval=timedelta(hours=6)`
  - `start_date`, `end_date`
  - `catchup=True/False`
- **Kod Örneği:**
```python
from datetime import datetime, timedelta

# Her 6 saatte bir
dag1 = DAG(
    'every_6_hours',
    schedule_interval=timedelta(hours=6),
    start_date=datetime(2024, 1, 1)
)

# Her pazartesi 09:00
dag2 = DAG(
    'weekly_monday',
    schedule_interval='0 9 * * 1',
    start_date=datetime(2024, 1, 1)
)

# Her ayın 1'i saat 00:00
dag3 = DAG(
    'monthly_first_day',
    schedule_interval='0 0 1 * *',
    start_date=datetime(2024, 1, 1)
)
```
- **Görsel:**
  - Cron expression cheat sheet
  - Schedule interval örnekleri tablosu

#### 6.4 Backfill (Geçmiş Tarih Çalıştırma)
- **İçerik:**
  - Backfill nedir? Neden gerekli?
  - `catchup=True` vs `False`
  - CLI ile backfill
  - Backfill stratejileri
- **Kod Örneği:**
```bash
# 2024-01-01 ile 2024-01-31 arası backfill
airflow dags backfill my_dag \
    --start-date 2024-01-01 \
    --end-date 2024-01-31

# Dry run (simülasyon)
airflow dags backfill my_dag \
    --start-date 2024-01-01 \
    --end-date 2024-01-31 \
    --dry-run

# Specific task backfill
airflow dags backfill my_dag \
    --start-date 2024-01-01 \
    --end-date 2024-01-31 \
    --task-regex 'transform_.*'
```

#### 6.5 Yeniden Çalıştırma ve Hata Ayıklama
- **İçerik:**
  - Failed task'ı clear et ve rerun
  - "Clear" vs "Mark Success"
  - Task retry mechanism
  - Task timeout ayarları
- **Kod Örneği:**
```python
# DAG seviyesinde retry ayarları
default_args = {
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=30),
    'execution_timeout': timedelta(hours=2)
}

# Task seviyesinde override
task = PythonOperator(
    task_id='critical_task',
    python_callable=my_function,
    retries=5,  # Override default
    retry_delay=timedelta(minutes=10)
)
```
- **Görsel:**
  - WebUI Clear task ekran görüntüsü
  - Task instance state transitions diagram
  - Retry mechanism flowchart

---

### **BÖLÜM 7: DAG'LER ARASI İLETİŞİM (8-10 slayt)**

#### 7.1 XCom (Cross-Communication)
- **İçerik:**
  - XCom nedir? Ne için kullanılır?
  - `xcom_push` ve `xcom_pull`
  - Limitation: Small data only (< 48KB önerilir)
  - XCom best practices
- **Kod Örneği:**
```python
from airflow.operators.python import PythonOperator

def push_data(**kwargs):
    # XCom'a veri yaz
    kwargs['ti'].xcom_push(key='customer_count', value=1250)
    # Return değeri otomatik push olur
    return {'sales_total': 45000.50}

def pull_data(**kwargs):
    ti = kwargs['ti']
    # Belirli key ile pull
    count = ti.xcom_pull(key='customer_count', task_ids='push_task')
    # Return value pull (default key: return_value)
    sales = ti.xcom_pull(task_ids='push_task')
    print(f"Customer Count: {count}")
    print(f"Sales Data: {sales}")

with DAG('xcom_example', ...) as dag:
    task1 = PythonOperator(task_id='push_task', python_callable=push_data)
    task2 = PythonOperator(task_id='pull_task', python_callable=pull_data)
    task1 >> task2
```
- **Görsel:**
  - XCom Admin panel screenshot
  - XCom flow diagram

#### 7.2 External Task Sensor
- **İçerik:**
  - Başka bir DAG'in tamamlanmasını bekleme
  - `ExternalTaskSensor` kullanımı
  - `execution_delta` ve `execution_date_fn`
- **Kod Örneği:**
```python
from airflow.sensors.external_task import ExternalTaskSensor

wait_for_upstream_dag = ExternalTaskSensor(
    task_id='wait_for_data_ingestion',
    external_dag_id='data_ingestion_dag',
    external_task_id='final_load_task',
    allowed_states=['success'],
    failed_states=['failed', 'skipped'],
    timeout=3600,
    poke_interval=60
)
```

#### 7.3 TriggerDagRunOperator
- **İçerik:**
  - Bir DAG'den başka bir DAG'i tetikleme
  - Parametre geçirme
- **Kod Örneği:**
```python
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

trigger_downstream = TriggerDagRunOperator(
    task_id='trigger_transform_dag',
    trigger_dag_id='transform_pipeline',
    conf={'source': 'api', 'date': '{{ ds }}'},
    wait_for_completion=True
)
```

#### 7.4 Variables ve Parametre Yönetimi
- **İçerik:**
  - Airflow Variables (Admin → Variables)
  - Environment variables
  - DAG run config
  - Templating (Jinja2)
- **Kod Örneği:**
```python
from airflow.models import Variable

# Variable set (UI veya CLI)
# airflow variables set my_var "value"

# Variable get
api_key = Variable.get("api_key")
db_conn = Variable.get("db_connection_string")

# JSON variable
config = Variable.get("etl_config", deserialize_json=True)

# Default value
timeout = Variable.get("timeout_seconds", default_var=300)

# Jinja template kullanımı
task = BashOperator(
    task_id='use_variable',
    bash_command='echo "Date: {{ ds }}, Env: {{ var.value.environment }}"'
)
```
- **Görsel:**
  - Variables panel screenshot
  - Template variables reference table

---

### **BÖLÜM 8: CONNECTIONS VE SECRETS (6-8 slayt)**

#### 8.1 Connections
- **İçerik:**
  - Connection nedir?
  - Connection types: Postgres, MySQL, HTTP, S3, GCS, BigQuery, Snowflake
  - Admin → Connections panel
  - Connection string format
- **Kod Örneği:**
```python
from airflow.providers.postgres.hooks.postgres import PostgresHook

# Connection kullanımı
hook = PostgresHook(postgres_conn_id='my_postgres_conn')
records = hook.get_records("SELECT * FROM customers LIMIT 10")

# BigQuery connection
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
bq_hook = BigQueryHook(gcp_conn_id='google_cloud_default')
```
- **Görsel:**
  - Connections panel screenshot
  - Connection creation form
  - Connection types listesi

#### 8.2 Secrets Backend
- **İçerik:**
  - Secrets management best practices
  - Google Secret Manager integration
  - Environment variables
  - HashiCorp Vault
- **Kod Örneği:**
```python
# airflow.cfg
[secrets]
backend = airflow.providers.google.cloud.secrets.secret_manager.CloudSecretManagerBackend
backend_kwargs = {"connections_prefix": "airflow-connections", "variables_prefix": "airflow-variables", "project_id": "my-gcp-project"}
```

---

### **BÖLÜM 9: NOTIFICATION VE ALERTING (5-6 slayt)**

#### 9.1 Email Notifications
- **İçerik:**
  - `email_on_failure`, `email_on_retry`, `email_on_success`
  - SMTP configuration
  - Custom email templates
- **Kod Örneği:**
```python
default_args = {
    'email': ['team@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
}

# Custom callback
def failure_callback(context):
    dag_id = context['dag'].dag_id
    task_id = context['task_instance'].task_id
    send_slack_message(f"DAG {dag_id} - Task {task_id} failed!")

task = PythonOperator(
    task_id='critical_task',
    python_callable=my_function,
    on_failure_callback=failure_callback
)
```

#### 9.2 Slack/Teams Integration
- **Kod Örneği:**
```python
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator

send_slack = SlackWebhookOperator(
    task_id='slack_notification',
    http_conn_id='slack_webhook',
    message='DAG {{ dag.dag_id }} tamamlandı!',
    channel='#data-alerts'
)
```
- **Görsel:**
  - Slack notification örneği
  - Email template örneği

---

### **BÖLÜM 10: DEPLOYMENT VE CI/CD (12-15 slayt)**

#### 10.1 Deployment Stratejileri
- **İçerik:**
  - Dev → Test → Prod workflow
  - Git branching strategy (feature, develop, main)
  - DAG versioning
  - Blue-Green deployment

#### 10.2 Azure DevOps ile CI/CD
- **İçerik:**
  - Azure Repos + Azure Pipelines
  - Build pipeline: linting, testing
  - Release pipeline: deploy to Composer
- **Kod Örneği: azure-pipelines.yml**
```yaml
trigger:
  branches:
    include:
      - main
      - develop

pool:
  vmImage: 'ubuntu-latest'

stages:
  - stage: Test
    jobs:
      - job: LintAndTest
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.9'

          - script: |
              pip install apache-airflow pylint pytest
              pylint dags/**/*.py
            displayName: 'Lint DAGs'

          - script: |
              pytest tests/
            displayName: 'Run Tests'

  - stage: Deploy
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - job: DeployToComposer
        steps:
          - task: gcloud@1
            inputs:
              command: 'composer'
              arguments: 'environments storage dags import --environment=$(COMPOSER_ENV) --location=$(COMPOSER_LOCATION) --source=dags/'
```

#### 10.3 GitHub Actions ile CI/CD
- **Kod Örneği: .github/workflows/deploy.yml**
```yaml
name: Deploy Airflow DAGs

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install apache-airflow pytest pylint black

      - name: Lint with pylint
        run: pylint dags/

      - name: Format check with black
        run: black --check dags/

      - name: Run tests
        run: pytest tests/

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Deploy to Cloud Composer
        run: |
          gcloud composer environments storage dags import \
            --environment ${{ secrets.COMPOSER_ENV }} \
            --location ${{ secrets.COMPOSER_LOCATION }} \
            --source dags/
```

#### 10.4 Cloud Composer'a Deployment
- **İçerik:**
  - `gcloud composer` CLI
  - GCS bucket sync
  - DAG deployment best practices
- **Kod Örneği:**
```bash
# DAG upload
gcloud composer environments storage dags import \
  --environment my-composer-env \
  --location us-central1 \
  --source dags/my_dag.py

# Plugins upload
gcloud composer environments storage plugins import \
  --environment my-composer-env \
  --location us-central1 \
  --source plugins/my_plugin.py

# Requirements install
gcloud composer environments update my-composer-env \
  --location us-central1 \
  --update-pypi-packages-from-file requirements.txt

# Environment variables set
gcloud composer environments update my-composer-env \
  --location us-central1 \
  --update-env-variables KEY=VALUE
```
- **Görsel:**
  - Azure DevOps pipeline screenshot
  - GitHub Actions workflow run
  - GCP Composer environment

---

### **BÖLÜM 11: BIGQUERY İLE AIRFLOW ENTEGRASYONU (15-18 slayt) ⭐**

#### 11.1 BigQuery Operatörleri Genel Bakış
- **İçerik:**
  - `BigQueryCreateEmptyTableOperator`
  - `BigQueryInsertJobOperator` (Query çalıştırma - EN ÖNEMLİ)
  - `BigQueryCheckOperator` (Data quality check)
  - `BigQueryGetDataOperator`
  - `BigQueryDeleteTableOperator`
  - `BigQueryToGCSOperator`
  - `GCSToBigQueryOperator`
- **Görsel:**
  - Operator türleri ve kullanım alanları tablosu
- **Notlar:** https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/bigquery.html

#### 11.2 BigQuery Connection Kurulumu
- **İçerik:**
  - Service Account oluşturma
  - JSON key download
  - Airflow connection ekle (Admin → Connections)
  - Connection ID: `google_cloud_default`
  - Keyfile JSON veya Keyfile Path
- **Kod Örneği:**
```bash
# gcloud ile service account oluştur
gcloud iam service-accounts create airflow-bq-sa \
    --display-name="Airflow BigQuery Service Account"

# Roller ata
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:airflow-bq-sa@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.admin"

# Key oluştur
gcloud iam service-accounts keys create key.json \
    --iam-account=airflow-bq-sa@PROJECT_ID.iam.gserviceaccount.com
```
- **Görsel:**
  - GCP IAM Service Account ekran görüntüsü
  - Airflow BigQuery connection form

#### 11.3 BigQuery'de SQL Sorgu Çalıştırma
- **Kod Örneği:**
```python
from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from datetime import datetime

with DAG(
    'bigquery_query_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
) as dag:

    # Query job
    run_query = BigQueryInsertJobOperator(
        task_id='run_query',
        configuration={
            "query": {
                "query": """
                    SELECT
                        DATE(order_date) as order_date,
                        COUNT(*) as order_count,
                        SUM(total_amount) as total_sales
                    FROM `{{ params.project }}.{{ params.dataset }}.orders`
                    WHERE DATE(order_date) = '{{ ds }}'
                    GROUP BY order_date
                """,
                "useLegacySql": False,
                "destinationTable": {
                    "projectId": "{{ params.project }}",
                    "datasetId": "{{ params.dataset }}",
                    "tableId": "daily_sales_summary"
                },
                "writeDisposition": "WRITE_APPEND",
                "createDisposition": "CREATE_IF_NEEDED"
            }
        },
        params={
            "project": "my-gcp-project",
            "dataset": "analytics"
        },
        location='US',
        gcp_conn_id='google_cloud_default'
    )
```

#### 11.4 GCS'den BigQuery'e Veri Yükleme
- **Kod Örneği:**
```python
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator

load_csv = GCSToBigQueryOperator(
    task_id='load_csv_to_bq',
    bucket='my-data-bucket',
    source_objects=['data/sales_{{ ds_nodash }}.csv'],
    destination_project_dataset_table='my-project.analytics.sales',
    schema_fields=[
        {'name': 'order_id', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'customer_id', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'product_id', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'quantity', 'type': 'INTEGER', 'mode': 'REQUIRED'},
        {'name': 'amount', 'type': 'FLOAT', 'mode': 'REQUIRED'},
        {'name': 'order_date', 'type': 'DATE', 'mode': 'REQUIRED'},
    ],
    write_disposition='WRITE_APPEND',
    skip_leading_rows=1,
    field_delimiter=',',
    autodetect=False
)
```

#### 11.5 BigQuery'den GCS'e Export
- **Kod Örneği:**
```python
from airflow.providers.google.cloud.transfers.bigquery_to_gcs import BigQueryToGCSOperator

export_to_gcs = BigQueryToGCSOperator(
    task_id='export_results',
    source_project_dataset_table='my-project.analytics.sales_summary',
    destination_cloud_storage_uris=['gs://my-bucket/exports/sales_{{ ds }}.csv'],
    export_format='CSV',
    print_header=True,
    gcp_conn_id='google_cloud_default'
)
```

#### 11.6 Data Quality Checks
- **Kod Örneği:**
```python
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryCheckOperator,
    BigQueryValueCheckOperator
)

# Row count check
check_row_count = BigQueryCheckOperator(
    task_id='check_row_count',
    sql="""
        SELECT COUNT(*) > 0
        FROM `my-project.analytics.sales`
        WHERE DATE(order_date) = '{{ ds }}'
    """,
    use_legacy_sql=False,
    gcp_conn_id='google_cloud_default'
)

# Value check
check_total_sales = BigQueryValueCheckOperator(
    task_id='check_total_sales',
    sql="""
        SELECT SUM(amount)
        FROM `my-project.analytics.sales`
        WHERE DATE(order_date) = '{{ ds }}'
    """,
    pass_value=1000.0,  # Minimum expected value
    use_legacy_sql=False,
    gcp_conn_id='google_cloud_default'
)
```

#### 11.7 BigQuery Sensors
- **Kod Örneği:**
```python
from airflow.providers.google.cloud.sensors.bigquery import BigQueryTableExistenceSensor

wait_for_table = BigQueryTableExistenceSensor(
    task_id='wait_for_source_table',
    project_id='my-project',
    dataset_id='raw_data',
    table_id='daily_events_{{ ds_nodash }}',
    gcp_conn_id='google_cloud_default',
    poke_interval=300,  # 5 dakika
    timeout=3600  # 1 saat
)
```

#### 11.8 Dataform Jobs ile Entegrasyon ⭐
- **İçerik:**
  - Dataform nedir?
  - Airflow ile Dataform workflow tetikleme
  - `DataformCreateWorkflowInvocationOperator`
- **Kod Örneği:**
```python
from airflow.providers.google.cloud.operators.dataform import (
    DataformCreateWorkflowInvocationOperator,
    DataformGetWorkflowInvocationOperator
)

# Dataform workflow tetikle
trigger_dataform = DataformCreateWorkflowInvocationOperator(
    task_id='trigger_dataform_workflow',
    project_id='my-gcp-project',
    region='us-central1',
    repository_id='my-dataform-repo',
    workflow_invocation={
        "compilation_result": "{{ task_instance.xcom_pull(task_ids='compile_dataform') }}"
    },
    gcp_conn_id='google_cloud_default'
)

# Dataform workflow durumunu kontrol et
check_dataform_status = DataformGetWorkflowInvocationOperator(
    task_id='check_dataform_status',
    project_id='my-gcp-project',
    region='us-central1',
    repository_id='my-dataform-repo',
    workflow_invocation_id='{{ task_instance.xcom_pull(task_ids="trigger_dataform_workflow")["name"].split("/")[-1] }}',
    gcp_conn_id='google_cloud_default'
)
```
- **Görsel:**
  - Dataform workflow diagram
  - Airflow + Dataform architecture

#### 11.9 BigQuery Best Practices
- **İçerik:**
  - Partitioned tables kullanımı
  - Query cost optimization
  - `use_legacy_sql=False` her zaman kullan
  - Table clustering
  - Incremental loads
- **Kod Örneği:**
```python
# Partitioned table oluşturma
create_partitioned_table = BigQueryInsertJobOperator(
    task_id='create_partitioned_table',
    configuration={
        "query": {
            "query": """
                CREATE TABLE IF NOT EXISTS `my-project.analytics.sales_partitioned`
                PARTITION BY DATE(order_date)
                CLUSTER BY customer_id, product_id
                AS
                SELECT * FROM `my-project.raw.sales`
                WHERE DATE(order_date) = '{{ ds }}'
            """,
            "useLegacySql": False
        }
    }
)
```

#### 11.10 Complete BigQuery Pipeline Örneği
- **Kod Örneği:**
```python
from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'email_on_failure': True,
    'email': ['team@example.com'],
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'bigquery_etl_pipeline',
    default_args=default_args,
    description='Complete ETL pipeline with BigQuery',
    schedule_interval='0 2 * * *',  # Her gün 02:00
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['bigquery', 'etl', 'production']
) as dag:

    # Step 1: GCS'de dosya var mı kontrol et
    check_file = GCSObjectExistenceSensor(
        task_id='check_source_file',
        bucket='my-data-bucket',
        object='raw/sales_{{ ds_nodash }}.csv',
        timeout=600
    )

    # Step 2: CSV'yi staging tabloya yükle
    load_to_staging = GCSToBigQueryOperator(
        task_id='load_to_staging',
        bucket='my-data-bucket',
        source_objects=['raw/sales_{{ ds_nodash }}.csv'],
        destination_project_dataset_table='my-project.staging.sales_raw',
        write_disposition='WRITE_TRUNCATE',
        skip_leading_rows=1,
        autodetect=True
    )

    # Step 3: Transform ve production tabloya yaz
    transform_and_load = BigQueryInsertJobOperator(
        task_id='transform_and_load',
        configuration={
            "query": {
                "query": """
                    INSERT INTO `my-project.analytics.sales`
                    SELECT
                        order_id,
                        customer_id,
                        product_id,
                        quantity,
                        amount,
                        PARSE_DATE('%Y%m%d', '{{ ds_nodash }}') as order_date,
                        CURRENT_TIMESTAMP() as ingestion_timestamp
                    FROM `my-project.staging.sales_raw`
                    WHERE amount > 0 AND quantity > 0
                """,
                "useLegacySql": False
            }
        }
    )

    # Step 4: Aggregate report oluştur
    create_daily_summary = BigQueryInsertJobOperator(
        task_id='create_daily_summary',
        configuration={
            "query": {
                "query": """
                    MERGE `my-project.analytics.daily_sales_summary` T
                    USING (
                        SELECT
                            order_date,
                            COUNT(*) as total_orders,
                            SUM(amount) as total_sales,
                            COUNT(DISTINCT customer_id) as unique_customers
                        FROM `my-project.analytics.sales`
                        WHERE order_date = '{{ ds }}'
                        GROUP BY order_date
                    ) S
                    ON T.order_date = S.order_date
                    WHEN MATCHED THEN
                        UPDATE SET
                            total_orders = S.total_orders,
                            total_sales = S.total_sales,
                            unique_customers = S.unique_customers
                    WHEN NOT MATCHED THEN
                        INSERT (order_date, total_orders, total_sales, unique_customers)
                        VALUES (S.order_date, S.total_orders, S.total_sales, S.unique_customers)
                """,
                "useLegacySql": False
            }
        }
    )

    # Dependencies
    check_file >> load_to_staging >> transform_and_load >> create_daily_summary
```
- **Görsel:**
  - Pipeline flow diagram
  - BigQuery tables ve data flow

---

### **BÖLÜM 12: UÇTAN UCA SALES DATAMART PIPELINE (12-15 slayt)**

#### 12.1 Proje Mimarisi
- **İçerik:**
  - Source: GCS CSV files
  - Staging: BigQuery raw tables
  - Dimensions: Customer, Product, Date
  - Fact: SalesTransaction
  - Star schema design
- **Görsel:**
  - Star schema ERD diagram
  - Data flow architecture

#### 12.2 Dimension Tables

**DimCustomer:**
```sql
CREATE TABLE IF NOT EXISTS `PROJECT_ID.sales_datamart.DimCustomer` (
    customer_key INT64,
    customer_id STRING,
    customer_name STRING,
    email STRING,
    city STRING,
    country STRING,
    created_date DATE,
    effective_date TIMESTAMP,
    is_current BOOL
)
PARTITION BY DATE(effective_date)
CLUSTER BY customer_id;
```

**DimProduct:**
```sql
CREATE TABLE IF NOT EXISTS `PROJECT_ID.sales_datamart.DimProduct` (
    product_key INT64,
    product_id STRING,
    product_name STRING,
    category STRING,
    subcategory STRING,
    unit_price FLOAT64,
    effective_date TIMESTAMP,
    is_current BOOL
)
PARTITION BY DATE(effective_date)
CLUSTER BY product_id;
```

**DimDate:**
```sql
CREATE TABLE IF NOT EXISTS `PROJECT_ID.sales_datamart.DimDate` (
    date_key INT64,
    full_date DATE,
    year INT64,
    quarter INT64,
    month INT64,
    month_name STRING,
    week INT64,
    day INT64,
    day_name STRING,
    is_weekend BOOL,
    is_holiday BOOL
);
```

**FactSalesTransaction:**
```sql
CREATE TABLE IF NOT EXISTS `PROJECT_ID.sales_datamart.FactSalesTransaction` (
    transaction_id STRING,
    date_key INT64,
    customer_key INT64,
    product_key INT64,
    quantity INT64,
    unit_price FLOAT64,
    total_amount FLOAT64,
    discount_amount FLOAT64,
    net_amount FLOAT64,
    transaction_timestamp TIMESTAMP
)
PARTITION BY DATE(transaction_timestamp)
CLUSTER BY customer_key, product_key;
```

#### 12.3 Sales Datamart DAG
- **Kod Örneği: `sales_datamart_pipeline.py`**
```python
from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

PROJECT_ID = "{{{{ params.project_id }}}}"
DATASET = "sales_datamart"
GCS_BUCKET = "{{{{ params.gcs_bucket }}}}"

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email': ['data-team@example.com'],
    'email_on_failure': True,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'sales_datamart_pipeline',
    default_args=default_args,
    description='Sales Datamart ETL Pipeline',
    schedule_interval='0 3 * * *',  # Her gün 03:00
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['sales', 'datamart', 'bigquery'],
    params={
        'project_id': 'MY_GCP_PROJECT_ID',  # Placeholder
        'gcs_bucket': 'my-sales-data-bucket'
    }
) as dag:

    # ==================== EXTRACT ====================

    # Check source files
    check_customers = GCSObjectExistenceSensor(
        task_id='check_customers_file',
        bucket=GCS_BUCKET,
        object='raw/customers_{{ ds_nodash }}.csv',
        timeout=600
    )

    check_products = GCSObjectExistenceSensor(
        task_id='check_products_file',
        bucket=GCS_BUCKET,
        object='raw/products_{{ ds_nodash }}.csv',
        timeout=600
    )

    check_transactions = GCSObjectExistenceSensor(
        task_id='check_transactions_file',
        bucket=GCS_BUCKET,
        object='raw/transactions_{{ ds_nodash }}.csv',
        timeout=600
    )

    # Load to staging
    load_customers_staging = GCSToBigQueryOperator(
        task_id='load_customers_staging',
        bucket=GCS_BUCKET,
        source_objects=['raw/customers_{{ ds_nodash }}.csv'],
        destination_project_dataset_table=f'{PROJECT_ID}.staging.customers_raw',
        write_disposition='WRITE_TRUNCATE',
        skip_leading_rows=1,
        autodetect=True
    )

    load_products_staging = GCSToBigQueryOperator(
        task_id='load_products_staging',
        bucket=GCS_BUCKET,
        source_objects=['raw/products_{{ ds_nodash }}.csv'],
        destination_project_dataset_table=f'{PROJECT_ID}.staging.products_raw',
        write_disposition='WRITE_TRUNCATE',
        skip_leading_rows=1,
        autodetect=True
    )

    load_transactions_staging = GCSToBigQueryOperator(
        task_id='load_transactions_staging',
        bucket=GCS_BUCKET,
        source_objects=['raw/transactions_{{ ds_nodash }}.csv'],
        destination_project_dataset_table=f'{PROJECT_ID}.staging.transactions_raw',
        write_disposition='WRITE_TRUNCATE',
        skip_leading_rows=1,
        autodetect=True
    )

    # ==================== TRANSFORM - DIMENSIONS ====================

    # DimDate (one-time population)
    populate_dim_date = BigQueryInsertJobOperator(
        task_id='populate_dim_date',
        configuration={
            "query": {
                "query": f"""
                    MERGE `{PROJECT_ID}.{DATASET}.DimDate` T
                    USING (
                        SELECT
                            CAST(FORMAT_DATE('%Y%m%d', date) AS INT64) as date_key,
                            date as full_date,
                            EXTRACT(YEAR FROM date) as year,
                            EXTRACT(QUARTER FROM date) as quarter,
                            EXTRACT(MONTH FROM date) as month,
                            FORMAT_DATE('%B', date) as month_name,
                            EXTRACT(WEEK FROM date) as week,
                            EXTRACT(DAY FROM date) as day,
                            FORMAT_DATE('%A', date) as day_name,
                            CASE WHEN EXTRACT(DAYOFWEEK FROM date) IN (1, 7) THEN TRUE ELSE FALSE END as is_weekend,
                            FALSE as is_holiday
                        FROM
                            UNNEST(GENERATE_DATE_ARRAY('2020-01-01', '2030-12-31')) as date
                    ) S
                    ON T.date_key = S.date_key
                    WHEN NOT MATCHED THEN
                        INSERT (date_key, full_date, year, quarter, month, month_name, week, day, day_name, is_weekend, is_holiday)
                        VALUES (S.date_key, S.full_date, S.year, S.quarter, S.month, S.month_name, S.week, S.day, S.day_name, S.is_weekend, S.is_holiday)
                """,
                "useLegacySql": False
            }
        }
    )

    # DimCustomer (SCD Type 1)
    upsert_dim_customer = BigQueryInsertJobOperator(
        task_id='upsert_dim_customer',
        configuration={
            "query": {
                "query": f"""
                    MERGE `{PROJECT_ID}.{DATASET}.DimCustomer` T
                    USING (
                        SELECT
                            FARM_FINGERPRINT(customer_id) as customer_key,
                            customer_id,
                            customer_name,
                            email,
                            city,
                            country,
                            PARSE_DATE('%Y-%m-%d', created_date) as created_date,
                            CURRENT_TIMESTAMP() as effective_date,
                            TRUE as is_current
                        FROM `{PROJECT_ID}.staging.customers_raw`
                    ) S
                    ON T.customer_id = S.customer_id
                    WHEN MATCHED THEN
                        UPDATE SET
                            customer_name = S.customer_name,
                            email = S.email,
                            city = S.city,
                            country = S.country,
                            effective_date = S.effective_date
                    WHEN NOT MATCHED THEN
                        INSERT (customer_key, customer_id, customer_name, email, city, country, created_date, effective_date, is_current)
                        VALUES (S.customer_key, S.customer_id, S.customer_name, S.email, S.city, S.country, S.created_date, S.effective_date, S.is_current)
                """,
                "useLegacySql": False
            }
        }
    )

    # DimProduct (SCD Type 1)
    upsert_dim_product = BigQueryInsertJobOperator(
        task_id='upsert_dim_product',
        configuration={
            "query": {
                "query": f"""
                    MERGE `{PROJECT_ID}.{DATASET}.DimProduct` T
                    USING (
                        SELECT
                            FARM_FINGERPRINT(product_id) as product_key,
                            product_id,
                            product_name,
                            category,
                            subcategory,
                            CAST(unit_price AS FLOAT64) as unit_price,
                            CURRENT_TIMESTAMP() as effective_date,
                            TRUE as is_current
                        FROM `{PROJECT_ID}.staging.products_raw`
                    ) S
                    ON T.product_id = S.product_id
                    WHEN MATCHED THEN
                        UPDATE SET
                            product_name = S.product_name,
                            category = S.category,
                            subcategory = S.subcategory,
                            unit_price = S.unit_price,
                            effective_date = S.effective_date
                    WHEN NOT MATCHED THEN
                        INSERT (product_key, product_id, product_name, category, subcategory, unit_price, effective_date, is_current)
                        VALUES (S.product_key, S.product_id, S.product_name, S.category, S.subcategory, S.unit_price, S.effective_date, S.is_current)
                """,
                "useLegacySql": False
            }
        }
    )

    # ==================== TRANSFORM - FACT ====================

    # FactSalesTransaction
    insert_fact_sales = BigQueryInsertJobOperator(
        task_id='insert_fact_sales',
        configuration={
            "query": {
                "query": f"""
                    INSERT INTO `{PROJECT_ID}.{DATASET}.FactSalesTransaction`
                    SELECT
                        t.transaction_id,
                        CAST(FORMAT_TIMESTAMP('%Y%m%d', t.transaction_timestamp) AS INT64) as date_key,
                        FARM_FINGERPRINT(t.customer_id) as customer_key,
                        FARM_FINGERPRINT(t.product_id) as product_key,
                        CAST(t.quantity AS INT64) as quantity,
                        CAST(t.unit_price AS FLOAT64) as unit_price,
                        CAST(t.total_amount AS FLOAT64) as total_amount,
                        CAST(t.discount_amount AS FLOAT64) as discount_amount,
                        CAST(t.total_amount - t.discount_amount AS FLOAT64) as net_amount,
                        PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', t.transaction_timestamp) as transaction_timestamp
                    FROM `{PROJECT_ID}.staging.transactions_raw` t
                    WHERE DATE(PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', t.transaction_timestamp)) = '{{{{ ds }}}}'
                """,
                "useLegacySql": False
            }
        }
    )

    # ==================== DATA QUALITY ====================

    # Check fact table row count
    validate_fact_count = BigQueryInsertJobOperator(
        task_id='validate_fact_count',
        configuration={
            "query": {
                "query": f"""
                    SELECT
                        CASE
                            WHEN COUNT(*) > 0 THEN 'PASS'
                            ELSE ERROR('No records inserted into Fact table')
                        END as validation
                    FROM `{PROJECT_ID}.{DATASET}.FactSalesTransaction`
                    WHERE DATE(transaction_timestamp) = '{{{{ ds }}}}'
                """,
                "useLegacySql": False
            }
        }
    )

    # ==================== REPORTING ====================

    # Create daily summary report
    create_daily_report = BigQueryInsertJobOperator(
        task_id='create_daily_report',
        configuration={
            "query": {
                "query": f"""
                    CREATE OR REPLACE TABLE `{PROJECT_ID}.{DATASET}.DailySalesReport` AS
                    SELECT
                        d.full_date,
                        d.day_name,
                        COUNT(DISTINCT f.transaction_id) as total_transactions,
                        COUNT(DISTINCT f.customer_key) as unique_customers,
                        COUNT(DISTINCT f.product_key) as unique_products,
                        SUM(f.quantity) as total_quantity,
                        SUM(f.total_amount) as total_sales,
                        SUM(f.discount_amount) as total_discounts,
                        SUM(f.net_amount) as net_sales,
                        AVG(f.net_amount) as avg_transaction_value
                    FROM `{PROJECT_ID}.{DATASET}.FactSalesTransaction` f
                    JOIN `{PROJECT_ID}.{DATASET}.DimDate` d ON f.date_key = d.date_key
                    WHERE d.full_date = '{{{{ ds }}}}'
                    GROUP BY d.full_date, d.day_name
                """,
                "useLegacySql": False
            }
        }
    )

    # ==================== DEPENDENCIES ====================

    # Extract
    check_customers >> load_customers_staging
    check_products >> load_products_staging
    check_transactions >> load_transactions_staging

    # Transform Dimensions
    load_customers_staging >> upsert_dim_customer
    load_products_staging >> upsert_dim_product
    load_transactions_staging >> populate_dim_date

    # Transform Fact (wait for all dimensions)
    [upsert_dim_customer, upsert_dim_product, populate_dim_date] >> insert_fact_sales

    # Validation
    insert_fact_sales >> validate_fact_count

    # Reporting
    validate_fact_count >> create_daily_report
```

- **Görsel:**
  - DAG graph view
  - Sample data screenshots
  - Sales report output

#### 12.4 Test Data Oluşturma
- **Python script: `generate_test_data.py`**
```python
import pandas as pd
import random
from datetime import datetime, timedelta

# Generate Customers
customers = pd.DataFrame({
    'customer_id': [f'CUST{i:05d}' for i in range(1, 101)],
    'customer_name': [f'Customer {i}' for i in range(1, 101)],
    'email': [f'customer{i}@example.com' for i in range(1, 101)],
    'city': random.choices(['Istanbul', 'Ankara', 'Izmir', 'Bursa', 'Antalya'], k=100),
    'country': ['Turkey'] * 100,
    'created_date': [(datetime.now() - timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d') for _ in range(100)]
})

# Generate Products
products = pd.DataFrame({
    'product_id': [f'PROD{i:04d}' for i in range(1, 51)],
    'product_name': [f'Product {i}' for i in range(1, 51)],
    'category': random.choices(['Electronics', 'Clothing', 'Food', 'Books'], k=50),
    'subcategory': random.choices(['Sub1', 'Sub2', 'Sub3'], k=50),
    'unit_price': [round(random.uniform(10, 500), 2) for _ in range(50)]
})

# Generate Transactions
transactions = []
for _ in range(500):
    transactions.append({
        'transaction_id': f'TXN{len(transactions):08d}',
        'customer_id': random.choice(customers['customer_id'].tolist()),
        'product_id': random.choice(products['product_id'].tolist()),
        'quantity': random.randint(1, 10),
        'unit_price': round(random.uniform(10, 500), 2),
        'total_amount': 0,  # Will calculate
        'discount_amount': round(random.uniform(0, 50), 2),
        'transaction_timestamp': (datetime.now() - timedelta(hours=random.randint(0, 24))).strftime('%Y-%m-%d %H:%M:%S')
    })

transactions_df = pd.DataFrame(transactions)
transactions_df['total_amount'] = transactions_df['unit_price'] * transactions_df['quantity']

# Save to CSV
today = datetime.now().strftime('%Y%m%d')
customers.to_csv(f'customers_{today}.csv', index=False)
products.to_csv(f'products_{today}.csv', index=False)
transactions_df.to_csv(f'transactions_{today}.csv', index=False)

print("Test data generated successfully!")
```

---

### **BÖLÜM 13: İLERİ SEVİYE KONULAR (6-8 slayt)**

#### 13.1 Dynamic DAGs
- **Kod Örneği:**
```python
# Birden fazla benzer DAG oluşturma
DATASETS = ['sales', 'marketing', 'finance']

for dataset in DATASETS:
    dag_id = f'{dataset}_daily_pipeline'

    with DAG(
        dag_id=dag_id,
        schedule_interval='@daily',
        start_date=datetime(2024, 1, 1),
        catchup=False
    ) as dag:
        task = BashOperator(
            task_id=f'process_{dataset}',
            bash_command=f'python process.py --dataset {dataset}'
        )

        globals()[dag_id] = dag
```

#### 13.2 Pools ve Resource Management
- **İçerik:**
  - Pools: Concurrent task limit
  - Priority weight
  - Task concurrency
- **Görsel:**
  - Pools admin panel

#### 13.3 DAG Callbacks
- **Kod Örneği:**
```python
def dag_success_callback(context):
    print(f"DAG {context['dag'].dag_id} succeeded!")

def dag_failure_callback(context):
    send_alert(f"DAG {context['dag'].dag_id} failed!")

dag = DAG(
    'my_dag',
    on_success_callback=dag_success_callback,
    on_failure_callback=dag_failure_callback,
    ...
)
```

---

### **BÖLÜM 14: TROUBLESHOOTING VE DEBUG (6-7 slayt)**

#### 14.1 Common Issues
- **İçerik:**
  - DAG görünmüyor: Parse errors, syntax errors
  - Task failed: Check logs
  - Scheduler delay: Executor kapasitesi
  - Zombie/Undead tasks

#### 14.2 Debugging Tools
- **İçerik:**
  - Airflow CLI commands
  - Log viewing (WebUI vs file system)
  - Database queries (metadata)
- **Kod Örneği:**
```bash
# DAG parse check
airflow dags list-import-errors

# Task logs
airflow tasks logs my_dag my_task 2024-01-01

# Database state
airflow db check

# Reset task
airflow tasks clear my_dag --start-date 2024-01-01 --end-date 2024-01-31
```

#### 14.3 Performance Optimization
- **İçerik:**
  - Executor selection (LocalExecutor vs CeleryExecutor)
  - Parallelism tuning
  - DAG file optimization
  - Database connection pooling

---

### **BÖLÜM 15: BEST PRACTICES VE ÖZET (5-6 slayt)**

#### 15.1 Best Practices
- ✅ Idempotent tasks yazın
- ✅ Catchup=False kullanın (gerekmedikçe)
- ✅ Default args kullanın
- ✅ Connections ve Variables kullanın, hard-code etmeyin
- ✅ Task'ları küçük ve atomik tutun
- ✅ Test edin (local test, CI/CD)
- ✅ Monitoring ve alerting kurun
- ✅ Documentation yazın

#### 15.2 Anti-Patterns (Yapılmaması Gerekenler)
- ❌ Top-level code (DAG dışında işlem yapmak)
- ❌ Variable.get() her task'ta çağırmak
- ❌ Büyük veri XCom ile taşımak
- ❌ DAG içinde API call yapmak (task içinde yapın)

#### 15.3 Eğitim Özeti
- Airflow mimarisi ve bileşenleri
- DAG geliştirme ve operatörler
- Deployment ve CI/CD
- BigQuery entegrasyonu
- Production-ready pipeline oluşturma

#### 15.4 Kaynaklar ve Daha Fazlası
- Apache Airflow Official Docs: https://airflow.apache.org/docs/
- Astronomer Academy: https://academy.astronomer.io
- GCP Airflow: https://cloud.google.com/composer/docs
- Community: Slack, Stack Overflow

---

## 📊 SUNUM İSTATİSTİKLERİ

- **Toplam Tahmini Slayt:** 120-140 slayt
- **Bölüm Sayısı:** 15 ana bölüm
- **Kod Örnekleri:** 30+ adet
- **Ekran Görüntüsü İhtiyacı:** 40+ adet
- **Demo Proje:** 1 adet (Sales Datamart)

---

## 🎨 GÖRSEL VE EKRAN GÖRÜNTÜLERİ İHTİYAÇ LİSTESİ

### Airflow WebUI Screenshots (alınacak):
1. Login screen
2. DAGs list view
3. Graph view (çeşitli DAG'ler için)
4. Tree view (historical runs)
5. Gantt chart
6. Task instance logs
7. Admin → Connections panel
8. Admin → Variables panel
9. Admin → Pools
10. XCom viewer
11. Code view

### GCP Screenshots:
1. BigQuery console
2. Cloud Composer environment
3. Service Account creation
4. IAM roles
5. GCS bucket
6. Dataform repository (if available)

### Development Environment:
1. VS Code with Airflow extension
2. Docker Desktop containers
3. Terminal - CLI commands
4. Git workflow

### Diagrams (oluşturulacak):
1. Airflow architecture
2. DAG lifecycle
3. Executor types comparison
4. Deployment pipeline
5. BigQuery ETL flow
6. Sales Datamart star schema
7. CI/CD workflow (Azure DevOps + GitHub)

---

## 📝 NOTLAR BÖLÜMÜ İÇİN İLAVE LİNKLER

Her slaytın notlar kısmına eklenecek:

**Genel Airflow:**
- https://airflow.apache.org/docs/apache-airflow/stable/
- https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html
- https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/

**Operators:**
- https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/operators.html
- https://registry.astronomer.io/

**BigQuery:**
- https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/bigquery.html
- https://cloud.google.com/bigquery/docs/orchestrate-dags
- https://cloud.google.com/composer/docs/how-to/using/using-bigquery-operator

**CI/CD:**
- https://cloud.google.com/composer/docs/dag-cicd-integration-guide
- https://docs.github.com/en/actions
- https://learn.microsoft.com/en-us/azure/devops/pipelines/

---

## ✅ SONRAKİ ADIMLAR

1. **Bu planı onaylayın**
2. **GCP bilgilerini sağlayın:**
   - Project ID
   - Airflow URL (Cloud Composer)
   - Dataset adları
3. **PPTX oluşturma için onay verin**

Bu plan üzerinde değişiklik yapmak ister misiniz?
