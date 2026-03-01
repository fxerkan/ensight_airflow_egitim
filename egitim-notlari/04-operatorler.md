# Airflow Operators

## İçindekiler
1. [Operator Nedir](#operator-nedir)
2. [Temel Operator'ler](#temel-operatorler)
3. [TaskFlow API](#taskflow-api)
4. [Sensor Operators](#sensor-operators)
5. [Best Practices](#best-practices)
6. [Referanslar](#referanslar)

---

## Operator Nedir

**Operator**, Airflow'da tek bir iş birimi (task) tanımlar. Her operator bir görev gerçekleştirir.

### Operator Hierarchy

```
BaseOperator
├── BashOperator       # Bash komutları
├── PythonOperator     # Python fonksiyonları
├── EmailOperator      # Email gönderme
├── Sensor             # Koşul bekleme
│   ├── FileSensor
│   ├── TimeSensor
│   └── ExternalTaskSensor
└── Transfer Operators
    ├── S3ToRedshiftOperator
    └── GCSToBigQueryOperator
```

### Operator vs Hook vs Sensor

| Kavram | Açıklama | Örnek |
|--------|----------|-------|
| **Operator** | Bir task tanımlar ve çalıştırır | `BashOperator`, `PythonOperator` |
| **Hook** | Dış sistemlere bağlantı sağlar | `PostgresHook`, `GCSHook` |
| **Sensor** | Bir koşulun gerçekleşmesini bekler | `FileSensor`, `HttpSensor` |

---

## Temel Operator'ler

### 1. BashOperator

Bash komutları çalıştırır.

```python
from airflow.operators.bash import BashOperator

# Basit komut
task1 = BashOperator(
    task_id='print_date',
    bash_command='date'
)

# Çoklu komut
task2 = BashOperator(
    task_id='multiple_commands',
    bash_command='''
        echo "Starting..."
        ls -la
        pwd
        echo "Done!"
    '''
)

# Environment variables
task3 = BashOperator(
    task_id='with_env',
    bash_command='echo "Hello $NAME"',
    env={'NAME': 'Airflow'}
)

# Template kullanımı
task4 = BashOperator(
    task_id='templated',
    bash_command='echo "Execution date: {{ ds }}"'
)
```

**Jinja Templates:**
- `{{ ds }}`: Execution date (YYYY-MM-DD)
- `{{ ds_nodash }}`: YYYYMMDD format
- `{{ execution_date }}`: Tam timestamp
- `{{ dag }}`: DAG objesi
- `{{ task }}`: Task objesi

### 2. PythonOperator

Python fonksiyonları çalıştırır.

```python
from airflow.operators.python import PythonOperator

def my_function(name, **kwargs):
    """Python task fonksiyonu"""
    execution_date = kwargs['execution_date']
    print(f"Hello {name}!")
    print(f"Execution Date: {execution_date}")
    return f"Result: {name}"

# Basit kullanım
task1 = PythonOperator(
    task_id='python_task',
    python_callable=my_function,
    op_kwargs={'name': 'Airflow'}  # Fonksiyona argüman
)

# Context kullanımı
def process_data(**kwargs):
    """Context'ten veri al"""
    ti = kwargs['ti']  # Task Instance
    dag_run = kwargs['dag_run']
    conf = kwargs['conf']

    # Önceki task'tan veri al (XCom)
    previous_result = ti.xcom_pull(task_ids='previous_task')

    print(f"Previous result: {previous_result}")
    return "processed"

task2 = PythonOperator(
    task_id='process',
    python_callable=process_data
)
```

**Context Variables:**
- `ti` (TaskInstance): Task instance objesi
- `dag_run`: DAG run objesi
- `execution_date`: Çalıştırma tarihi
- `conf`: DAG run configuration
- `params`: DAG parametreleri

### 3. EmailOperator

Email gönderir.

```python
from airflow.operators.email import EmailOperator

send_email = EmailOperator(
    task_id='send_report',
    to=['team@example.com'],
    subject='Daily Sales Report - {{ ds }}',
    html_content='''
        <h3>Daily Sales Report</h3>
        <p>Date: {{ ds }}</p>
        <p>Total Sales: ${{ params.total_sales }}</p>
    ''',
    params={'total_sales': 12500},
    files=['/tmp/report.pdf']  # Attachment
)
```

### 4. DummyOperator

Hiçbir iş yapmaz, sadece placeholder.

```python
from airflow.operators.dummy import DummyOperator

start = DummyOperator(task_id='start')
end = DummyOperator(task_id='end')

start >> [task1, task2, task3] >> end
```

**Kullanım Senaryoları:**
- Pipeline başlangıç/bitiş marker'ı
- Branching sonrası birleştirme noktası
- Task gruplarını organize etme

---

## TaskFlow API

### @task Decorator (Airflow 2.0+)

Modern Python-first yaklaşım.

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id='taskflow_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def my_etl_pipeline():
    """Modern TaskFlow API ile ETL"""

    @task
    def extract() -> dict:
        """Veri çek"""
        data = {'sales': [100, 200, 300]}
        return data  # Otomatik XCom push

    @task
    def transform(data: dict) -> dict:
        """Veri dönüştür"""
        total = sum(data['sales'])
        return {'total_sales': total}

    @task
    def load(summary: dict):
        """Veri yükle"""
        print(f"Total Sales: {summary['total_sales']}")

    # Pipeline tanımla
    extracted_data = extract()
    transformed_data = transform(extracted_data)
    load(transformed_data)

# DAG instance oluştur
dag_instance = my_etl_pipeline()
```

### TaskFlow API Avantajları

| Özellik | Geleneksel | TaskFlow API |
|---------|------------|--------------|
| **Kod Miktarı** | Fazla boilerplate | Minimal kod |
| **XCom Yönetimi** | Manuel push/pull | Otomatik |
| **Type Hints** | Yok | Destekleniyor |
| **Dependency** | Manuel (>>) | Fonksiyon çağrısı ile otomatik |
| **Okunabilirlik** | Düşük | Yüksek |

### TaskFlow Örnekleri

#### Örnek 1: ETL Pipeline

Dosya: `dags/04_taskflow_api_dag.py`

```python
@dag(
    dag_id='04_taskflow_api_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['egitim', 'taskflow', 'modern'],
)
def taskflow_etl_pipeline():
    """Modern Airflow TaskFlow API ile ETL Pipeline"""

    @task
    def extract_data() -> dict:
        """Extract: Veri kaynağından veri çek"""
        print("Veri çekiliyor...")

        data = {
            'customers': [
                {'id': 1, 'name': 'Ahmet Yılmaz', 'city': 'Istanbul'},
                {'id': 2, 'name': 'Ayşe Demir', 'city': 'Ankara'},
            ],
            'orders': [
                {'order_id': 101, 'customer_id': 1, 'amount': 250.50},
                {'order_id': 102, 'customer_id': 2, 'amount': 175.00},
            ]
        }
        return data

    @task
    def transform_data(data: dict) -> dict:
        """Transform: Veriyi dönüştür ve zenginleştir"""
        print("Veri dönüştürülüyor...")

        customer_totals = {}
        for order in data['orders']:
            customer_id = order['customer_id']
            amount = order['amount']
            customer_totals[customer_id] = customer_totals.get(customer_id, 0) + amount

        enriched_customers = []
        for customer in data['customers']:
            customer_id = customer['id']
            enriched_customers.append({
                'customer_id': customer_id,
                'customer_name': customer['name'],
                'total_orders': customer_totals.get(customer_id, 0),
                'segment': 'VIP' if customer_totals.get(customer_id, 0) > 200 else 'Standard'
            })

        return {
            'customers': enriched_customers,
            'summary': {
                'total_customers': len(enriched_customers),
                'total_revenue': sum(customer_totals.values())
            }
        }

    @task
    def load_data(data: dict) -> str:
        """Load: Dönüştürülmüş veriyi yükle"""
        print("Veri yükleniyor...")
        print(f"Total Customers: {data['summary']['total_customers']}")
        print(f"Total Revenue: {data['summary']['total_revenue']}")
        return "success"

    # Pipeline
    extracted_data = extract_data()
    transformed_data = transform_data(extracted_data)
    load_data(transformed_data)

dag_instance = taskflow_etl_pipeline()
```

#### Örnek 2: Paralel İşlem

```python
@dag(...)
def parallel_processing():

    @task
    def fetch_data():
        return {'data': [1, 2, 3, 4, 5]}

    @task
    def process_chunk(data: list, chunk_id: int):
        """Veriyi parçala ve işle"""
        print(f"Processing chunk {chunk_id}: {data}")
        return sum(data)

    @task
    def combine_results(results: list):
        """Sonuçları birleştir"""
        total = sum(results)
        print(f"Total: {total}")

    # Paralel işlem
    data = fetch_data()
    chunk1 = process_chunk(data[0:2], 1)
    chunk2 = process_chunk(data[2:4], 2)
    chunk3 = process_chunk(data[4:5], 3)

    combine_results([chunk1, chunk2, chunk3])
```

---

## Sensor Operators

Sensor'lar bir koşulun gerçekleşmesini bekler (polling).

### FileSensor

Dosyanın oluşmasını bekler.

```python
from airflow.sensors.filesystem import FileSensor

wait_for_file = FileSensor(
    task_id='wait_for_data',
    filepath='/data/sales_{{ ds }}.csv',
    poke_interval=60,  # 60 saniyede bir kontrol et
    timeout=600,  # 10 dakika timeout
    mode='poke'  # 'poke' veya 'reschedule'
)
```

### TimeSensor

Belirli bir zamana kadar bekler.

```python
from airflow.sensors.time_sensor import TimeSensor

wait_until_2am = TimeSensor(
    task_id='wait_until_2am',
    target_time=time(2, 0, 0)  # Saat 02:00:00
)
```

### ExternalTaskSensor

Başka bir DAG'in task'ının tamamlanmasını bekler.

```python
from airflow.sensors.external_task import ExternalTaskSensor

wait_for_upstream_dag = ExternalTaskSensor(
    task_id='wait_for_upstream',
    external_dag_id='upstream_dag',
    external_task_id='final_task',
    timeout=3600
)
```

### HttpSensor

HTTP endpoint'in hazır olmasını bekler.

```python
from airflow.sensors.http_sensor import HttpSensor

wait_for_api = HttpSensor(
    task_id='wait_for_api',
    http_conn_id='my_api',
    endpoint='/health',
    response_check=lambda response: response.status_code == 200,
    poke_interval=30
)
```

### Sensor Mode: Poke vs Reschedule

```python
# POKE MODE (default)
# Worker slot'u tutar, sürekli kontrol eder
sensor1 = FileSensor(
    task_id='sensor1',
    filepath='/data/file.csv',
    mode='poke',
    poke_interval=60
)

# RESCHEDULE MODE
# Worker slot'u serbest bırakır, periyodik reschedule olur
sensor2 = FileSensor(
    task_id='sensor2',
    filepath='/data/file.csv',
    mode='reschedule',  # Resource-efficient
    poke_interval=300
)
```

**Ne Zaman Reschedule:**
- Uzun bekleme süreleri (>5 dakika)
- Worker slot'u sınırlı
- Çok sayıda sensor var

---

## Best Practices

### 1. Operator Seçimi

```python
# ✅ DOĞRU - Doğru operator kullan
BigQueryInsertJobOperator(...)  # BigQuery işlemi için

# ❌ YANLIŞ - Generic operator ile custom kod
PythonOperator(
    python_callable=run_bigquery_query  # Avoid!
)
```

### 2. Idempotency

```python
# ✅ DOĞRU - Idempotent task
@task
def load_data():
    """Aynı datayı tekrar yüklerse overwrite eder"""
    query = """
        MERGE INTO table USING source
        WHEN MATCHED THEN UPDATE
        WHEN NOT MATCHED THEN INSERT
    """

# ❌ YANLIŞ - Non-idempotent
@task
def append_data():
    """Her çalışmada duplicate oluşturur"""
    query = "INSERT INTO table SELECT * FROM source"
```

### 3. Resource Management

```python
# ✅ DOĞRU - Connection pooling
@task
def query_database():
    hook = PostgresHook(postgres_conn_id='my_db')
    # Hook connection pool'u yönetir
    result = hook.get_records("SELECT * FROM table")

# ❌ YANLIŞ - Her defasında yeni connection
@task
def query_database():
    import psycopg2
    conn = psycopg2.connect(...)  # Manual connection
```

### 4. Task Size

```python
# ✅ DOĞRU - Küçük atomik task'lar
extract_sales = PythonOperator(...)
extract_customers = PythonOperator(...)
transform_sales = PythonOperator(...)
load_data = PythonOperator(...)

# ❌ YANLIŞ - Monolithic task
do_everything = PythonOperator(
    python_callable=extract_transform_load_all
)
```

### 5. Error Handling

```python
@task(retries=3, retry_delay=timedelta(minutes=5))
def fragile_task():
    """Hata olursa 3 kez dene, 5 dakika ara ile"""
    try:
        # risky operation
        result = external_api_call()
        return result
    except SpecificError as e:
        # Log ve re-raise
        logging.error(f"API call failed: {e}")
        raise

@task(on_failure_callback=send_slack_alert)
def critical_task():
    """Hata olursa Slack'e bildir"""
    pass
```

---

## Provider Packages

Airflow, farklı sistemlerle entegrasyon için provider package'lar sunar.

### Popüler Provider'lar

```bash
# Google Cloud Provider
pip install apache-airflow-providers-google

# AWS Provider
pip install apache-airflow-providers-amazon

# Azure Provider
pip install apache-airflow-providers-microsoft-azure

# Snowflake Provider
pip install apache-airflow-providers-snowflake

# dbt Provider
pip install apache-airflow-providers-dbt-cloud
```

### Provider Operator Örnekleri

```python
# Google Cloud
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator

# AWS
from airflow.providers.amazon.aws.operators.s3 import S3CreateBucketOperator
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator

# dbt
from airflow.providers.dbt.cloud.operators.dbt import DbtCloudRunJobOperator
```

---

## Referanslar

### Resmi Dokümantasyon
- [Operators Guide](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/operators.html)
- [TaskFlow API](https://airflow.apache.org/docs/apache-airflow/stable/tutorial/taskflow.html)
- [Provider Packages](https://airflow.apache.org/docs/apache-airflow-providers/index.html)

### Operator Listesi
- [Core Operators](https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/operators/index.html)
- [Sensor Operators](https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/sensors/index.html)

---

## Provider Packages Detaylı Tablo (20+ Provider)

| Provider Package | Operatörler | Use Case | Kurulum |
|------------------|-------------|----------|---------|
| **apache-airflow-providers-google** | BigQueryInsertJobOperator, GCSToBigQueryOperator, DataprocSubmitJobOperator, DataflowTemplatedJobStartOperator | GCP servisleri (BigQuery, GCS, Dataproc, Dataflow, Cloud Functions) | `pip install apache-airflow-providers-google` |
| **apache-airflow-providers-amazon** | S3CreateBucketOperator, S3ToRedshiftOperator, GlueCrawlerOperator, AthenaOperator, EMRCreateJobFlowOperator | AWS servisleri (S3, Redshift, Glue, Athena, EMR, Lambda) | `pip install apache-airflow-providers-amazon` |
| **apache-airflow-providers-microsoft-azure** | AzureBlobStorageCreateContainerOperator, AzureDataFactoryRunPipelineOperator, AzureDataLakeStorageListOperator | Azure servisleri (Blob Storage, Data Factory, Data Lake) | `pip install apache-airflow-providers-microsoft-azure` |
| **apache-airflow-providers-snowflake** | SnowflakeOperator, S3ToSnowflakeOperator | Snowflake warehouse | `pip install apache-airflow-providers-snowflake` |
| **apache-airflow-providers-databricks** | DatabricksSubmitRunOperator, DatabricksRunNowOperator | Databricks jobs | `pip install apache-airflow-providers-databricks` |
| **apache-airflow-providers-postgres** | PostgresOperator, PostgresHook | PostgreSQL | `pip install apache-airflow-providers-postgres` |
| **apache-airflow-providers-mysql** | MySqlOperator, MySqlHook | MySQL/MariaDB | `pip install apache-airflow-providers-mysql` |
| **apache-airflow-providers-http** | SimpleHttpOperator, HttpSensor | REST API calls | `pip install apache-airflow-providers-http` |
| **apache-airflow-providers-ssh** | SSHOperator, SFTPOperator | Remote execution, file transfer | `pip install apache-airflow-providers-ssh` |
| **apache-airflow-providers-ftp** | FTPOperator, FTPSensor | FTP operations | `pip install apache-airflow-providers-ftp` |
| **apache-airflow-providers-slack** | SlackWebhookOperator, SlackAPIPostOperator | Slack notifications | `pip install apache-airflow-providers-slack` |
| **apache-airflow-providers-email** | EmailOperator | Email notifications | Built-in |
| **apache-airflow-providers-docker** | DockerOperator | Run containers | `pip install apache-airflow-providers-docker` |
| **apache-airflow-providers-kubernetes** | KubernetesPodOperator | K8s pod execution | `pip install apache-airflow-providers-kubernetes` |
| **apache-airflow-providers-elasticsearch** | ElasticsearchSQLOperator | Elasticsearch | `pip install apache-airflow-providers-elasticsearch` |
| **apache-airflow-providers-mongo** | MongoOperator, MongoHook | MongoDB | `pip install apache-airflow-providers-mongo` |
| **apache-airflow-providers-redis** | RedisPublishOperator | Redis pub/sub | `pip install apache-airflow-providers-redis` |
| **apache-airflow-providers-dbt-cloud** | DbtCloudRunJobOperator | dbt Cloud jobs | `pip install apache-airflow-providers-dbt-cloud` |
| **apache-airflow-providers-apache-spark** | SparkSubmitOperator, SparkSqlOperator | Spark jobs | `pip install apache-airflow-providers-apache-spark` |
| **apache-airflow-providers-apache-kafka** | KafkaProducerOperator, KafkaConsumerOperator | Kafka messaging | `pip install apache-airflow-providers-apache-kafka` |

---

## Operator Selection Decision Tree

```
START: Neyi yapmak istiyorsunuz?

┌─ Script çalıştırma
│  ├─ Bash script → BashOperator
│  ├─ Python function → PythonOperator / @task
│  ├─ SQL query → PostgresOperator / MySqlOperator
│  └─ Remote script → SSHOperator

┌─ Data Transfer
│  ├─ GCS → BigQuery → GCSToBigQueryOperator
│  ├─ S3 → Redshift → S3ToRedshiftOperator
│  ├─ Local → GCS → LocalFilesystemToGCSOperator
│  └─ BigQuery → GCS → BigQueryToGCSOperator

┌─ Waiting / Sensing
│  ├─ File exists → FileSensor / GCSObjectExistenceSensor
│  ├─ Time → TimeSensor
│  ├─ External DAG → ExternalTaskSensor
│  ├─ HTTP endpoint → HttpSensor
│  └─ SQL condition → SqlSensor

┌─ Cloud Platform
│  ├─ GCP
│  │  ├─ BigQuery query → BigQueryInsertJobOperator
│  │  ├─ Dataproc job → DataprocSubmitJobOperator
│  │  └─ Cloud Function → CloudFunctionInvokeFunctionOperator
│  ├─ AWS
│  │  ├─ EMR job → EMRCreateJobFlowOperator
│  │  ├─ Lambda → LambdaInvokeFunctionOperator
│  │  └─ Glue → GlueCrawlerOperator
│  └─ Azure
│     ├─ Data Factory → AzureDataFactoryRunPipelineOperator
│     └─ Blob Storage → AzureBlobStorageListOperator

┌─ Orchestration
│  ├─ Branching → BranchPythonOperator
│  ├─ Trigger another DAG → TriggerDagRunOperator
│  ├─ Placeholder → DummyOperator (EmptyOperator in 2.4+)
│  └─ Dynamic tasks → @task + .expand()

┌─ Notifications
│  ├─ Email → EmailOperator
│  ├─ Slack → SlackWebhookOperator
│  └─ Custom → PythonOperator with callback
```

---

## Custom Operator Oluşturma (Step-by-Step)

### Neden Custom Operator?

- Tekrar eden logic'i encapsulate etmek
- Complex API client wrapper
- Custom validation logic
- Team-specific business logic

### Örnek: CustomEmailOperator

**Adım 1: BaseOperator'dan inherit et**

```python
# plugins/operators/custom_email_operator.py

from airflow.models.baseoperator import BaseOperator
from airflow.utils.decorators import apply_defaults
from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class CustomEmailOperator(BaseOperator):
    """
    Custom Email Operator with template support and retry logic.

    :param to: Recipient email address
    :param subject: Email subject (supports Jinja)
    :param body: Email body (supports Jinja)
    :param cc: CC recipients
    :param smtp_host: SMTP server host
    :param smtp_port: SMTP server port
    """

    # Template fields (Jinja support)
    template_fields = ('subject', 'body', 'to')
    template_ext = ('.html', '.txt')

    # UI color
    ui_color = '#e6f7ff'
    ui_fgcolor = '#000'

    @apply_defaults
    def __init__(
        self,
        *,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        smtp_host: str = 'smtp.gmail.com',
        smtp_port: int = 587,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.to = to
        self.subject = subject
        self.body = body
        self.cc = cc
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

    def execute(self, context):
        """
        Main execution method.

        :param context: Airflow context (ds, execution_date, task_instance, etc.)
        :return: Email sent status
        """
        self.log.info(f"Sending email to {self.to}")
        self.log.info(f"Subject: {self.subject}")

        # Create message
        msg = MIMEMultipart()
        msg['From'] = 'airflow@company.com'
        msg['To'] = self.to
        msg['Subject'] = self.subject

        if self.cc:
            msg['Cc'] = self.cc

        # Attach body
        msg.attach(MIMEText(self.body, 'html'))

        # Send email
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            # In production, use Airflow connection
            # connection = self.get_connection('smtp_default')
            # server.login(connection.login, connection.password)
            server.send_message(msg)
            server.quit()

            self.log.info("Email sent successfully")
            return "Email sent"

        except Exception as e:
            self.log.error(f"Failed to send email: {e}")
            raise
```

**Adım 2: Operator'ü kullan**

```python
# dags/email_example_dag.py

from operators.custom_email_operator import CustomEmailOperator

with DAG('email_example', ...) as dag:

    send_report = CustomEmailOperator(
        task_id='send_daily_report',
        to='manager@company.com',
        subject='Daily Sales Report - {{ ds }}',
        body="""
        <h2>Daily Sales Report</h2>
        <p>Date: {{ ds }}</p>
        <p>Total Sales: ${{ params.total_sales }}</p>
        """,
        cc='team@company.com',
        params={'total_sales': 12500}
    )
```

### Örnek 2: Custom API Operator

```python
# plugins/operators/custom_api_operator.py

from airflow.models.baseoperator import BaseOperator
from airflow.hooks.http_hook import HttpHook
import json

class CustomAPIOperator(BaseOperator):
    """
    Operator to call custom API with retry logic.
    """

    template_fields = ('endpoint', 'data')

    @apply_defaults
    def __init__(
        self,
        *,
        endpoint: str,
        method: str = 'POST',
        data: dict = None,
        http_conn_id: str = 'api_default',
        **kwargs
    ):
        super().__init__(**kwargs)
        self.endpoint = endpoint
        self.method = method
        self.data = data or {}
        self.http_conn_id = http_conn_id

    def execute(self, context):
        """Make API call with Hook"""
        hook = HttpHook(http_conn_id=self.http_conn_id, method=self.method)

        self.log.info(f"Calling API: {self.endpoint}")
        self.log.info(f"Data: {self.data}")

        response = hook.run(
            endpoint=self.endpoint,
            data=json.dumps(self.data),
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code != 200:
            raise ValueError(f"API call failed: {response.text}")

        result = response.json()
        self.log.info(f"API response: {result}")

        # Push to XCom
        context['task_instance'].xcom_push(key='api_result', value=result)

        return result
```

---

## Sensor Deep Dive

### Sensor Modes: Poke vs Reschedule

#### Poke Mode

```python
sensor = FileSensor(
    task_id='wait_for_file',
    filepath='/data/file.csv',
    mode='poke',           # Default
    poke_interval=60,      # 60 saniyede bir kontrol et
    timeout=3600           # 1 saat timeout
)
```

**Davranış:**
- Worker slot'u **tutar**
- Sürekli kontrol eder (poke_interval kadar bekleyip tekrar)
- Kısa bekleme süreleri için uygundur (<5 dakika)

**Pros:**
- Düşük gecikme (hemen tepki verir)
- Basit

**Cons:**
- Worker slot'u boşa harcar
- Çok sensor olursa worker'lar tükenebilir

#### Reschedule Mode

```python
sensor = FileSensor(
    task_id='wait_for_file',
    filepath='/data/file.csv',
    mode='reschedule',     # Resource-friendly
    poke_interval=300,     # 5 dakikada bir
    timeout=7200           # 2 saat timeout
)
```

**Davranış:**
- Worker slot'u **serbest bırakır**
- Scheduler tarafından periodic olarak reschedule edilir
- Uzun bekleme süreleri için uygundur (>5 dakika)

**Pros:**
- Worker slot'u verimli kullanır
- Çok sensor olsa bile scalable

**Cons:**
-약간 delay olabilir (poke_interval + scheduler delay)
- Metadata database'de çok entry oluşturur

### Timeout ve Poke Interval

```python
# Örnek: File sensor (max 2 saat bekle, 5 dakikada bir kontrol et)
sensor = FileSensor(
    task_id='wait_for_file',
    filepath='/data/file.csv',
    poke_interval=300,     # 5 dakika
    timeout=7200,          # 2 saat (7200 saniye)
    mode='reschedule'
)

# Timeout olursa AirflowSensorTimeout hatası verir
```

### Smart Sensors (Airflow 2.0+, Deprecated in 2.2)

Smart sensor'lar centralized sensor scheduler kullanırdı, ancak scalability sorunları nedeniyle deprecated edildi. Bunun yerine **reschedule mode** kullanın.

### Custom Sensor Örneği

```python
# plugins/sensors/custom_api_sensor.py

from airflow.sensors.base import BaseSensorOperator
from airflow.hooks.http_hook import HttpHook

class CustomAPISensor(BaseSensorOperator):
    """
    Wait until API returns expected status.
    """

    template_fields = ('endpoint',)

    def __init__(
        self,
        *,
        endpoint: str,
        expected_status: str = 'completed',
        http_conn_id: str = 'api_default',
        **kwargs
    ):
        super().__init__(**kwargs)
        self.endpoint = endpoint
        self.expected_status = expected_status
        self.http_conn_id = http_conn_id

    def poke(self, context) -> bool:
        """
        Check condition.

        :return: True if condition met, False otherwise
        """
        hook = HttpHook(http_conn_id=self.http_conn_id, method='GET')

        self.log.info(f"Checking API: {self.endpoint}")
        response = hook.run(endpoint=self.endpoint)

        if response.status_code != 200:
            self.log.warning(f"API returned {response.status_code}")
            return False

        data = response.json()
        status = data.get('status')

        self.log.info(f"Current status: {status}")

        if status == self.expected_status:
            self.log.info(f"Status is {self.expected_status}, continuing...")
            return True
        else:
            self.log.info(f"Waiting for status {self.expected_status}...")
            return False
```

**Kullanım:**

```python
wait_for_job = CustomAPISensor(
    task_id='wait_for_processing',
    endpoint='/api/jobs/{{ job_id }}',
    expected_status='completed',
    poke_interval=60,
    timeout=3600,
    mode='reschedule'
)
```

---

## TaskFlow API Advanced

### Multiple Outputs

```python
@task(multiple_outputs=True)
def extract_data() -> dict:
    """Return multiple outputs as dict"""
    return {
        'customer_count': 100,
        'order_count': 500,
        'total_revenue': 12500.50
    }

@task
def process_customers(count: int):
    print(f"Processing {count} customers")

@task
def process_orders(count: int):
    print(f"Processing {count} orders")

# Usage
data = extract_data()
process_customers(data['customer_count'])
process_orders(data['order_count'])
```

### Task Groups

```python
from airflow.utils.task_group import TaskGroup

@dag(...)
def etl_with_task_groups():

    @task
    def start():
        return "Started"

    # Task Group for Extract phase
    with TaskGroup(group_id='extract') as extract_group:
        @task
        def extract_customers():
            return {'customers': [...]}

        @task
        def extract_products():
            return {'products': [...]}

        customers = extract_customers()
        products = extract_products()

    # Task Group for Transform phase
    with TaskGroup(group_id='transform') as transform_group:
        @task
        def transform_customers(data):
            return data

        @task
        def transform_products(data):
            return data

        transform_customers(customers)
        transform_products(products)

    start() >> extract_group >> transform_group

dag = etl_with_task_groups()
```

### Dynamic Task Mapping

```python
@dag(...)
def dynamic_processing():

    @task
    def get_items():
        """Return list of items to process"""
        return [
            {'id': 1, 'name': 'Item1'},
            {'id': 2, 'name': 'Item2'},
            {'id': 3, 'name': 'Item3'},
        ]

    @task
    def process_item(item: dict):
        """Process each item"""
        print(f"Processing {item['name']}")
        return f"Processed {item['id']}"

    @task
    def combine_results(results: list):
        """Combine all results"""
        print(f"Total processed: {len(results)}")

    # Dynamic expansion
    items = get_items()
    processed = process_item.expand(item=items)
    combine_results(processed)

dag = dynamic_processing()
```

### Virtualenv Decorator

```python
@task.virtualenv(
    task_id='process_with_pandas',
    requirements=['pandas==1.5.0', 'numpy==1.23.0'],
    system_site_packages=False
)
def analyze_data():
    """Task runs in isolated virtualenv"""
    import pandas as pd
    import numpy as np

    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    result = df.sum().to_dict()
    return result
```

---

## Pratik Alıştırmalar

### Alıştırma 1: Custom Operator

**Görev:** BigQuery row count check yapan custom operator oluşturun.

```python
# plugins/operators/bigquery_row_count_operator.py

from airflow.models.baseoperator import BaseOperator
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook

class BigQueryRowCountOperator(BaseOperator):
    """Check if table has minimum row count."""

    template_fields = ('table', 'min_rows')

    def __init__(self, *, table: str, min_rows: int, **kwargs):
        super().__init__(**kwargs)
        self.table = table
        self.min_rows = min_rows

    def execute(self, context):
        hook = BigQueryHook(gcp_conn_id='google_cloud_default')
        sql = f"SELECT COUNT(*) as cnt FROM `{self.table}`"

        result = hook.get_first(sql)
        count = result[0]

        self.log.info(f"Table {self.table} has {count} rows")

        if count < self.min_rows:
            raise ValueError(f"Row count {count} < minimum {self.min_rows}")

        return count
```

### Alıştırma 2: Custom Sensor

**Görev:** GCS'de multiple files'ın var olduğunu kontrol eden sensor.

```python
# plugins/sensors/gcs_multiple_files_sensor.py

from airflow.sensors.base import BaseSensorOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook

class GCSMultipleFilesSensor(BaseSensorOperator):
    """Wait for multiple files to exist in GCS."""

    def __init__(self, *, bucket: str, prefixes: list, **kwargs):
        super().__init__(**kwargs)
        self.bucket = bucket
        self.prefixes = prefixes

    def poke(self, context) -> bool:
        hook = GCSHook(gcp_conn_id='google_cloud_default')

        for prefix in self.prefixes:
            if not hook.exists(bucket_name=self.bucket, object_name=prefix):
                self.log.info(f"File not found: gs://{self.bucket}/{prefix}")
                return False

        self.log.info("All files exist")
        return True

# Usage
wait_for_files = GCSMultipleFilesSensor(
    task_id='wait_for_all_files',
    bucket='my-bucket',
    prefixes=['raw/customers.csv', 'raw/products.csv', 'raw/orders.csv'],
    poke_interval=60,
    timeout=3600,
    mode='reschedule'
)
```

### Alıştırma 3: TaskFlow with Dynamic Mapping

**Görev:** CSV dosyalarını BigQuery'e parallel load eden DAG.

```python
@dag(dag_id='parallel_csv_load', ...)
def load_csv_files():

    @task
    def list_csv_files():
        """List all CSV files in GCS"""
        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket('my-bucket')
        blobs = bucket.list_blobs(prefix='raw/')
        return [blob.name for blob in blobs if blob.name.endswith('.csv')]

    @task
    def load_file_to_bigquery(file_path: str):
        """Load single CSV to BigQuery"""
        from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator

        table_name = file_path.split('/')[-1].replace('.csv', '')

        load_op = GCSToBigQueryOperator(
            task_id=f'load_{table_name}',
            bucket='my-bucket',
            source_objects=[file_path],
            destination_project_dataset_table=f'project.dataset.{table_name}',
            write_disposition='WRITE_TRUNCATE',
            autodetect=True
        )
        load_op.execute(context={})
        return f"Loaded {file_path}"

    files = list_csv_files()
    load_file_to_bigquery.expand(file_path=files)

dag = load_csv_files()
```

### Alıştırma 4: Operator Comparison

**Görev:** BashOperator vs PythonOperator vs TaskFlow karşılaştırması.

```python
# Scenario: BigQuery'den veri çek, process et, GCS'e yaz

# Option 1: BashOperator
bash_extract = BashOperator(
    task_id='bash_extract',
    bash_command='bq query --format=csv "SELECT * FROM table" > /tmp/data.csv'
)

# Option 2: PythonOperator
def extract_data(**kwargs):
    from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
    hook = BigQueryHook(gcp_conn_id='google_cloud_default')
    df = hook.get_pandas_df("SELECT * FROM table")
    df.to_csv('/tmp/data.csv', index=False)

python_extract = PythonOperator(
    task_id='python_extract',
    python_callable=extract_data
)

# Option 3: TaskFlow (BEST)
@task
def extract_and_process():
    from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
    from google.cloud import storage

    # Extract
    hook = BigQueryHook(gcp_conn_id='google_cloud_default')
    df = hook.get_pandas_df("SELECT * FROM table")

    # Process
    df_processed = df[df['amount'] > 100]

    # Load to GCS
    df_processed.to_csv('gs://bucket/processed_data.csv', index=False)

    return f"Processed {len(df_processed)} rows"
```

### Alıştırma 5: Sensor Best Practices

**Görev:** File sensor'u optimize edin.

```python
# ❌ BAD: Poke mode with long timeout
bad_sensor = FileSensor(
    task_id='wait_for_file_bad',
    filepath='/data/large_file.csv',
    mode='poke',
    poke_interval=10,    # Too frequent
    timeout=86400        # 24 hours! Worker slot blocked
)

# ✅ GOOD: Reschedule mode
good_sensor = FileSensor(
    task_id='wait_for_file_good',
    filepath='/data/large_file.csv',
    mode='reschedule',   # Frees worker slot
    poke_interval=300,   # 5 minutes
    timeout=3600,        # 1 hour reasonable timeout
    soft_fail=False      # Fail loudly if timeout
)

# ✅ BETTER: Use sensor with ExponentialBackoff
from airflow.sensors.base import PokeReturnValue

@task.sensor(poke_interval=60, timeout=3600, mode='reschedule')
def smart_file_sensor(filepath: str):
    """Custom sensor with exponential backoff"""
    import os
    import time

    if os.path.exists(filepath):
        return PokeReturnValue(is_done=True, xcom_value=filepath)
    else:
        return PokeReturnValue(is_done=False)
```

### Alıştırma 6: Provider Package Integration

**Görev:** Multiple provider'ları entegre edin.

```python
# Scenario: S3 → BigQuery → Slack notification

from airflow.providers.amazon.aws.transfers.s3_to_gcs import S3ToGCSOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator

with DAG('multi_provider_pipeline', ...) as dag:

    # AWS S3 → GCS
    s3_to_gcs = S3ToGCSOperator(
        task_id='s3_to_gcs',
        bucket='my-s3-bucket',
        prefix='data/',
        dest_gcs='gs://my-gcs-bucket/data/'
    )

    # GCS → BigQuery
    gcs_to_bq = GCSToBigQueryOperator(
        task_id='gcs_to_bigquery',
        bucket='my-gcs-bucket',
        source_objects=['data/*.csv'],
        destination_project_dataset_table='project.dataset.table',
        write_disposition='WRITE_TRUNCATE'
    )

    # Slack notification
    notify = SlackWebhookOperator(
        task_id='notify_slack',
        http_conn_id='slack_webhook',
        message='Data pipeline completed successfully!',
        channel='#data-alerts'
    )

    s3_to_gcs >> gcs_to_bq >> notify
```

---

## Sık Sorulan Sorular (FAQ)

**S1: Operator vs Hook farkı nedir?**

A:
- **Operator**: Task tanımlar, scheduling ve retry logic ile
- **Hook**: Dış sistemlere low-level connection sağlar
- Örnek: `BigQueryInsertJobOperator` (operator) içinde `BigQueryHook` (hook) kullanır

**S2: Custom operator ne zaman yazılmalı?**

A:
- Tekrar eden logic varsa
- Complex business logic encapsulate etmek için
- Mevcut operator yeterli değilse
- Team-specific pattern'ler için

**S3: Sensor timeout olursa ne olur?**

A: `AirflowSensorTimeout` exception fırlatır ve task fail olur. `soft_fail=True` ile skip yapabilirsiniz.

**S4: Poke vs Reschedule mode ne zaman kullanılır?**

A:
- **Poke**: <5 dakika bekleme, low latency gerekli
- **Reschedule**: >5 dakika bekleme, çok sensor var

**S5: XCom boyutu sınırı var mı?**

A: Evet, database row size'a bağlı (~1MB PostgreSQL). Büyük veri için GCS/S3 kullanın, path'i XCom'a push edin.

**S6: TaskFlow API eski PythonOperator'den ne fark eder?**

A:
- Daha temiz syntax
- Otomatik XCom handling
- Type hints desteği
- Functional programming style

**S7: Provider package version uyumsuzluğu olursa?**

A:
```bash
# Tüm provider'ları listele
pip list | grep apache-airflow-providers

# Specific version kur
pip install apache-airflow-providers-google==10.13.1
```

**S8: Operator içinde başka operator çağırabilir miyim?**

A: Evet ama önerilmez. Bunun yerine SubDAG veya TaskGroup kullanın.

**S9: Sensor'da external sistem credential nasıl yönetilir?**

A: Airflow Connection kullanın:
```python
sensor = HttpSensor(
    task_id='wait_for_api',
    http_conn_id='api_connection',  # Admin → Connections'dan tanımlı
    endpoint='/status'
)
```

**S10: TaskFlow API ile BashOperator karıştırılabilir mi?**

A: Evet:
```python
@dag(...)
def mixed_dag():
    @task
    def python_task():
        return "done"

    bash_task = BashOperator(
        task_id='bash',
        bash_command='echo "Hello"'
    )

    python_task() >> bash_task
```

**S11: Dynamic task mapping max task limit var mı?**

A: Evet, `max_map_length` parametresi (default 1024). Ayarlanabilir:
```python
@task
def process_items():
    ...

process_items.expand(item=items).set_max_map_length(5000)
```

**S12: Operator retry logic nasıl çalışır?**

A:
```python
task = MyOperator(
    task_id='task',
    retries=3,                        # 3 kez dene
    retry_delay=timedelta(minutes=5), # 5 dakika ara ile
    retry_exponential_backoff=True,   # Exponential backoff
    max_retry_delay=timedelta(hours=1) # Max 1 saat backoff
)
```

**S13: Sensor soft_fail ne işe yarar?**

A:
```python
sensor = FileSensor(
    task_id='wait_file',
    filepath='/data/file.csv',
    timeout=3600,
    soft_fail=True  # Timeout olursa FAIL yerine SKIP
)
```
Downstream task'lar `trigger_rule='none_failed'` ile çalışabilir.

**S14: Multiple provider aynı anda kullanılabilir mi?**

A: Evet:
```python
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.amazon.aws.operators.s3 import S3CreateBucketOperator
from airflow.providers.slack.operators.slack import SlackAPIPostOperator

# Hepsi aynı DAG'de kullanılabilir
```

**S15: Operator template_fields nedir?**

A: Jinja templating destekleyen field'lar:
```python
class MyOperator(BaseOperator):
    template_fields = ('query', 'output_path')  # Bu field'lar {{ ds }} gibi template kullanabilir

    def __init__(self, query, output_path, **kwargs):
        self.query = query
        self.output_path = output_path
```

---

## Sonraki Adımlar

- **[05-webui-yonetim.md](05-webui-yonetim.md)**: WebUI detaylı kullanım
- **[07-bigquery-entegrasyonu.md](07-bigquery-entegrasyonu.md)**: BigQuery operatörleri
