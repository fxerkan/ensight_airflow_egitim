# Airflow Cheat Sheet - Hızlı Referans

> **Hızlı Erişim**: Bu dosya Airflow ile çalışırken sık ihtiyaç duyacağınız komut, parametre ve pattern'leri içerir.

## İçindekiler
1. [CLI Commands](#cli-commands)
2. [DAG Parameters](#dag-parameters)
3. [Operator Reference](#operator-reference)
4. [Jinja Templates](#jinja-templates)
5. [Cron Expressions](#cron-expressions)
6. [Task States](#task-states)
7. [Best Practices Checklist](#best-practices-checklist)
8. [Troubleshooting Guide](#troubleshooting-guide)

---

## CLI Commands

### DAG Management

```bash
# List all DAGs
airflow dags list

# List DAGs with tag
airflow dags list --tags production

# Trigger a DAG
airflow dags trigger my_dag

# Trigger with config
airflow dags trigger my_dag --conf '{"key":"value"}'

# Pause/Unpause DAG
airflow dags pause my_dag
airflow dags unpause my_dag

# Test DAG (doesn't save state)
airflow dags test my_dag 2024-01-01

# Backfill
airflow dags backfill my_dag \
  --start-date 2024-01-01 \
  --end-date 2024-01-31

# Delete DAG
airflow dags delete my_dag
```

### Task Management

```bash
# List tasks in DAG
airflow tasks list my_dag

# Show task hierarchy (tree)
airflow tasks list my_dag --tree

# Test a task
airflow tasks test my_dag my_task 2024-01-01

# View task logs
airflow tasks logs my_dag my_task 2024-01-01

# Clear tasks (rerun)
airflow tasks clear my_dag --task-regex "extract.*"
airflow tasks clear my_dag --start-date 2024-01-01

# Render task template
airflow tasks render my_dag my_task 2024-01-01
```

### Debug & Info

```bash
# List import errors
airflow dags list-import-errors

# Show DAG structure
airflow dags show my_dag

# Export DAG to image
airflow dags show my_dag --save dag.png

# Check scheduler health
airflow jobs check

# Version info
airflow version

# Config values
airflow config get-value core executor
airflow config list
```

### Variables & Connections

```bash
# Variables
airflow variables set my_var my_value
airflow variables get my_var
airflow variables list
airflow variables delete my_var
airflow variables export variables.json
airflow variables import variables.json

# Connections
airflow connections add my_conn \
  --conn-type postgres \
  --conn-host localhost \
  --conn-login airflow \
  --conn-password airflow \
  --conn-port 5432

airflow connections list
airflow connections get my_conn
airflow connections delete my_conn
airflow connections test my_conn
```

### Database

```bash
# Initialize database
airflow db init

# Upgrade database
airflow db upgrade

# Reset database (⚠️ DANGER)
airflow db reset

# Clean old data
airflow db clean \
  --clean-before-timestamp 2024-01-01 \
  --yes
```

### Users (RBAC)

```bash
# Create admin user
airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com \
  --password admin

# List users
airflow users list

# Delete user
airflow users delete --username admin
```

---

## DAG Parameters

### Essential DAG Parameters

```python
from airflow import DAG
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-team',                    # Task sahibi
    'depends_on_past': False,                # Önceki run'a bağımlı mı?
    'email': ['alerts@company.com'],         # Alert email
    'email_on_failure': True,                # Hata durumunda email
    'email_on_retry': False,                 # Retry'da email
    'retries': 3,                            # Hata durumunda retry sayısı
    'retry_delay': timedelta(minutes=5),     # Retry arası bekleme
    'execution_timeout': timedelta(hours=2), # Maksimum çalışma süresi
    'sla': timedelta(hours=1),               # SLA (Service Level Agreement)
}

with DAG(
    dag_id='my_dag',                         # ✅ Required: Benzersiz DAG ID
    description='DAG açıklaması',            # DAG açıklaması

    # Scheduling
    start_date=datetime(2024, 1, 1),         # ✅ Required: Başlangıç tarihi (static!)
    end_date=datetime(2024, 12, 31),         # Bitiş tarihi (opsiyonel)
    schedule_interval='@daily',              # Çalışma sıklığı (cron veya preset)
    catchup=False,                           # Geçmiş run'ları çalıştırma

    # Concurrency
    max_active_runs=1,                       # Aynı anda çalışan max run sayısı
    max_active_tasks=16,                     # DAG'de aynı anda çalışan max task

    # UI & Organization
    tags=['production', 'etl', 'daily'],     # Filtreleme için tag'ler
    doc_md="""# DAG Documentation""",        # Markdown dokümantasyon

    # Defaults
    default_args=default_args,               # Tüm task'lara uygulanır

    # Advanced
    dagrun_timeout=timedelta(hours=4),       # DAG run timeout
    sla_miss_callback=alert_sla_miss,        # SLA ihlal callback
    on_failure_callback=send_alert,          # DAG failure callback
    on_success_callback=log_success,         # DAG success callback

    # Rendering
    render_template_as_native_obj=True,      # Template rendering optimization
) as dag:
    pass
```

### Schedule Intervals

```python
# Preset schedules
schedule_interval='@once'       # Bir kez
schedule_interval='@hourly'     # Her saat başı (0 * * * *)
schedule_interval='@daily'      # Gece yarısı (0 0 * * *)
schedule_interval='@weekly'     # Pazar gece yarısı (0 0 * * 0)
schedule_interval='@monthly'    # Her ayın 1'i (0 0 1 * *)
schedule_interval='@yearly'     # Yıl başı (0 0 1 1 *)
schedule_interval=None          # Manuel trigger only

# Timedelta
from datetime import timedelta
schedule_interval=timedelta(minutes=30)
schedule_interval=timedelta(hours=6)
schedule_interval=timedelta(days=2)

# Cron expressions
schedule_interval='0 2 * * *'       # Her gün 02:00
schedule_interval='*/15 * * * *'    # Her 15 dakika
schedule_interval='0 9 * * 1-5'     # İş günleri 09:00
schedule_interval='0 12 1,15 * *'   # Ayın 1 ve 15'i 12:00
```

---

## Operator Reference

### Core Operators

```python
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.email import EmailOperator

# BashOperator
bash_task = BashOperator(
    task_id='run_script',
    bash_command='echo "Hello {{ ds }}"',
    env={'VAR': 'value'},
    append_env=True,
    cwd='/tmp'
)

# PythonOperator
def my_function(**kwargs):
    print(kwargs['ds'])
    return 'result'

python_task = PythonOperator(
    task_id='run_python',
    python_callable=my_function,
    op_kwargs={'arg1': 'value1'},
    provide_context=True
)

# DummyOperator (placeholder)
start = DummyOperator(task_id='start')
end = DummyOperator(task_id='end')

# EmailOperator
email = EmailOperator(
    task_id='send_email',
    to=['team@example.com'],
    subject='Report {{ ds }}',
    html_content='<h1>Report</h1>',
    files=['/tmp/report.pdf']
)
```

### TaskFlow API (Airflow 2.0+)

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id='taskflow_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def my_etl():

    @task
    def extract() -> dict:
        return {'data': [1, 2, 3]}

    @task
    def transform(data: dict) -> dict:
        data['sum'] = sum(data['data'])
        return data

    @task
    def load(data: dict):
        print(f"Sum: {data['sum']}")

    # Pipeline
    data = extract()
    transformed = transform(data)
    load(transformed)

dag = my_etl()
```

### BigQuery Operators

```python
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryInsertJobOperator,
    BigQueryCheckOperator,
    BigQueryValueCheckOperator
)
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import (
    GCSToBigQueryOperator
)

# Query execution
query_task = BigQueryInsertJobOperator(
    task_id='run_query',
    configuration={
        "query": {
            "query": "SELECT * FROM `project.dataset.table`",
            "useLegacySql": False
        }
    },
    location='US'
)

# GCS to BigQuery
load_task = GCSToBigQueryOperator(
    task_id='load_data',
    bucket='my-bucket',
    source_objects=['data/*.csv'],
    destination_project_dataset_table='project.dataset.table',
    write_disposition='WRITE_TRUNCATE',
    autodetect=True
)

# Data quality check
check_task = BigQueryCheckOperator(
    task_id='check_data',
    sql="SELECT COUNT(*) > 0 FROM `project.dataset.table`"
)
```

### Sensors

```python
from airflow.sensors.filesystem import FileSensor
from airflow.sensors.time_sensor import TimeSensor
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor

# File sensor
file_sensor = FileSensor(
    task_id='wait_for_file',
    filepath='/data/file.csv',
    poke_interval=60,
    timeout=600,
    mode='poke'  # or 'reschedule'
)

# GCS object sensor
gcs_sensor = GCSObjectExistenceSensor(
    task_id='wait_for_gcs_file',
    bucket='my-bucket',
    object='data/{{ ds }}.csv',
    timeout=600
)

# External task sensor
external_sensor = ExternalTaskSensor(
    task_id='wait_for_upstream_dag',
    external_dag_id='upstream_dag',
    external_task_id='final_task',
    timeout=3600
)

# Time sensor
time_sensor = TimeSensor(
    task_id='wait_until_2am',
    target_time=time(2, 0, 0)
)
```

---

## Jinja Templates

### Execution Date Variables

```python
# Bash command içinde
bash_command='echo "Date: {{ ds }}"'

# SQL query içinde
sql=f"""
    SELECT * FROM table
    WHERE date = '{{{{ ds }}}}'  # Double braces in f-string
"""

# Available variables:
{{ ds }}                    # 2024-01-01 (YYYY-MM-DD)
{{ ds_nodash }}             # 20240101 (YYYYMMDD)
{{ ts }}                    # 2024-01-01T00:00:00+00:00 (ISO timestamp)
{{ ts_nodash }}             # 20240101T000000
{{ prev_ds }}               # Previous execution date
{{ next_ds }}               # Next execution date
{{ yesterday_ds }}          # Yesterday
{{ tomorrow_ds }}           # Tomorrow

# Datetime objects
{{ execution_date }}        # Airflow datetime object
{{ prev_execution_date }}   # Previous
{{ next_execution_date }}   # Next

# DAG & Task info
{{ dag }}                   # DAG object
{{ dag.dag_id }}            # DAG ID string
{{ task }}                  # Task object
{{ task.task_id }}          # Task ID string
{{ task_instance }}         # TaskInstance object
{{ run_id }}                # DAG run ID

# Config & params
{{ params }}                # DAG params
{{ var.value.my_var }}      # Airflow Variable
{{ var.json.my_json_var }}  # JSON Variable

# Macros
{{ macros.datetime.now() }}
{{ macros.timedelta(days=1) }}
{{ macros.ds_add(ds, 7) }}  # Add 7 days to ds
```

### Template Filters

```python
# String operations
{{ ds | replace('-', '') }}         # Remove dashes
{{ ds | upper }}                    # Uppercase
{{ task_id | default('unknown') }}  # Default value

# Date operations
{{ execution_date.strftime('%Y%m%d') }}
{{ (execution_date - macros.timedelta(days=1)).strftime('%Y-%m-%d') }}

# Conditional
{% if params.mode == 'full' %}
    SELECT * FROM table
{% else %}
    SELECT * FROM table WHERE date = '{{ ds }}'
{% endif %}

# Loops
{% for i in range(5) %}
    UNION ALL SELECT {{ i }}
{% endfor %}
```

---

## Cron Expressions

### Format
```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of Week (0-7, 0=Sunday, 7=Sunday)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of Month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

### Common Patterns

```bash
# Every minute
* * * * *

# Every 5 minutes
*/5 * * * *

# Every 15 minutes
*/15 * * * *

# Every hour
0 * * * *

# Every day at midnight
0 0 * * *

# Every day at 2 AM
0 2 * * *

# Every day at 9:30 AM
30 9 * * *

# Every Monday at 9 AM
0 9 * * 1

# Every weekday at 8 AM (Mon-Fri)
0 8 * * 1-5

# First day of month at noon
0 12 1 * *

# 1st and 15th at noon
0 12 1,15 * *

# Every quarter (Jan, Apr, Jul, Oct) 1st at midnight
0 0 1 1,4,7,10 *

# Last day of month (not directly supported, use workaround)
0 0 28-31 * * # Check if tomorrow is 1st in script
```

### Test Cron

**Online**: https://crontab.guru/

**CLI**:
```bash
# Install croniter
pip install croniter

# Python script
from croniter import croniter
from datetime import datetime

cron = croniter('0 2 * * *', datetime.now())
for _ in range(5):
    print(cron.get_next(datetime))
```

---

## Task States

### State Diagram

```
          ┌─────────┐
          │  None   │ (Not scheduled yet)
          └────┬────┘
               │
          ┌────▼────┐
          │ Queued  │ (Scheduled, waiting for worker)
          └────┬────┘
               │
          ┌────▼────┐
          │ Running │
          └────┬────┘
               │
        ┌──────┼──────┐
        │      │      │
    ┌───▼─┐ ┌─▼──┐ ┌─▼────────┐
    │Success Failed Upstream │
    │     │ │    │ │ Failed   │
    └─────┘ └──┬─┘ └──────────┘
               │
          ┌────▼────────┐
          │ Up for Retry│
          └──────┬──────┘
                 │
          (retry_delay)
                 │
          ┌──────▼──────┐
          │   Queued    │
          └─────────────┘
```

### State Colors & Meanings

| State | Color | Symbol | Meaning |
|-------|-------|--------|---------|
| **success** | 🟢 Green | ✓ | Task completed successfully |
| **running** | 🟡 Yellow | ↻ | Task is currently running |
| **failed** | 🔴 Red | ✗ | Task failed |
| **queued** | ⚪ Gray | ⧗ | Task is queued, waiting for worker |
| **up_for_retry** | 🔵 Blue | ⟲ | Task failed, waiting for retry |
| **up_for_reschedule** | 🟠 Orange | ⏰ | Sensor in reschedule mode |
| **skipped** | ⚫ Black | ⤳ | Task was skipped (branching) |
| **upstream_failed** | 🟣 Purple | ⇅ | Upstream task failed |
| **deferred** | 🟤 Brown | ⏸ | Async task deferred (2.2+) |
| **removed** | ⬜ White | ∅ | Task removed from DAG |

### State Transitions

```python
# Normal flow
None → Queued → Running → Success

# Failure with retry
None → Queued → Running → Failed → Up for Retry → Queued → Running → Success

# Upstream failure
None → Queued → Upstream Failed (if upstream task failed)

# Skipped (Branching)
None → Queued → Skipped (by BranchPythonOperator)

# Deferred (Async)
None → Queued → Running → Deferred → Running → Success
```

---

## Best Practices Checklist

### DAG Design

- [ ] **Idempotent tasks**: Her çalıştırmada aynı sonuç
- [ ] **Static start_date**: `datetime(2024, 1, 1)` ✅ | `datetime.now()` ❌
- [ ] **catchup=False**: Yeni DAG'ler için (geçmişi çalıştırma)
- [ ] **Meaningful dag_id**: `daily_sales_etl` ✅ | `dag1` ❌
- [ ] **Tags**: Filtreleme için tag'ler ekle
- [ ] **Documentation**: DAG ve task doc_md ekle
- [ ] **Owner**: Sorumlu takımı belirt
- [ ] **Default args**: Retry, timeout, email ayarları
- [ ] **SLA**: Critical pipeline'lar için SLA tanımla

### Task Design

- [ ] **Small, focused tasks**: Her task bir iş yapsın
- [ ] **Meaningful task_id**: `extract_sales_data` ✅ | `task1` ❌
- [ ] **Proper dependencies**: `task1 >> task2 >> task3`
- [ ] **Retry strategy**: `retries=3, retry_delay=timedelta(minutes=5)`
- [ ] **Timeout**: `execution_timeout=timedelta(hours=2)`
- [ ] **Avoid top-level code**: DAG parse her 30 saniyede çalışır!

### Performance

- [ ] **Pool usage**: Rate limiting için pool kullan
- [ ] **Sensor mode**: Long wait için `mode='reschedule'`
- [ ] **XCom limit**: Küçük data için (<1MB), büyük data GCS/S3'te
- [ ] **Parallelism**: `max_active_tasks_per_dag` ayarla
- [ ] **Partitioning**: Incremental load yap (full load değil)

### Security

- [ ] **Secrets**: Variable değil, Secret Manager kullan
- [ ] **Connections**: Credential'ları WebUI'da sakla
- [ ] **RBAC**: Role-based access control aktif
- [ ] **Audit logs**: Değişiklikleri logla

### Testing

- [ ] **Unit tests**: DAG import edilebilir mi?
- [ ] **Integration tests**: Task'lar çalışıyor mu?
- [ ] **Test before deploy**: Staging'de test et
- [ ] **CI/CD**: Automated testing pipeline

---

## Troubleshooting Guide

### DAG Issues

#### DAG Not Appearing

```bash
# 1. Check import errors
airflow dags list-import-errors

# 2. Check scheduler logs
docker logs airflow-scheduler-1 --tail 100

# 3. Manually import
python dags/my_dag.py

# 4. Check file location
ls dags/my_dag.py
```

#### DAG Not Scheduling

**Checklist:**
- [ ] DAG paused? → Unpause it
- [ ] start_date in future? → Set to past
- [ ] schedule_interval=None? → Change schedule
- [ ] catchup=False and start_date old? → Trigger manually

```bash
# Unpause
airflow dags unpause my_dag

# Manual trigger
airflow dags trigger my_dag
```

### Task Issues

#### Task Stuck in Queued

```bash
# Check scheduler
docker ps | grep scheduler

# Check parallelism
airflow config get-value core parallelism
airflow config get-value core max_active_tasks_per_dag

# Check pools
airflow pools list

# Restart scheduler
docker compose restart airflow-scheduler
```

#### Task Failed

```bash
# View logs
airflow tasks logs my_dag my_task 2024-01-01

# Test task
airflow tasks test my_dag my_task 2024-01-01

# Check dependencies
airflow tasks list my_dag --tree
```

#### Task Timeout

```python
# Increase timeout
task = BashOperator(
    task_id='long_task',
    execution_timeout=timedelta(hours=4)  # Increase
)
```

### Connection Issues

#### Connection Test Failed

```bash
# Test connection
airflow connections test my_conn

# List connections
airflow connections list

# Re-create connection
airflow connections delete my_conn
airflow connections add my_conn --conn-type postgres ...
```

### Performance Issues

#### Slow WebUI

```bash
# Clean old data
airflow db clean --clean-before-timestamp 2024-01-01 --yes

# Optimize database
# PostgreSQL
VACUUM ANALYZE;

# Check database size
SELECT pg_size_pretty(pg_database_size('airflow'));
```

#### High Memory Usage

```yaml
# Reduce workers (docker-compose.yaml)
AIRFLOW__CORE__PARALLELISM: 16  # Reduce from 32
AIRFLOW__CORE__MAX_ACTIVE_TASKS_PER_DAG: 8

# Limit DAG runs
AIRFLOW__CORE__MAX_ACTIVE_RUNS_PER_DAG: 1
```

---

## Quick Commands Summary

```bash
# DAG lifecycle
airflow dags list
airflow dags trigger my_dag
airflow dags pause my_dag
airflow dags test my_dag 2024-01-01

# Task lifecycle
airflow tasks test my_dag my_task 2024-01-01
airflow tasks logs my_dag my_task 2024-01-01
airflow tasks clear my_dag

# Debug
airflow dags list-import-errors
docker logs airflow-scheduler-1

# Variables & Connections
airflow variables set key value
airflow connections add conn_id --conn-type type

# Database
airflow db clean --clean-before-timestamp 2024-01-01 --yes

# Scheduler
docker compose restart airflow-scheduler
```

---

## Faydalı Linkler

- **Official Docs**: https://airflow.apache.org/docs/
- **GitHub**: https://github.com/apache/airflow
- **Crontab Guru**: https://crontab.guru/
- **Astronomer Guides**: https://docs.astronomer.io/learn
- **Slack Community**: https://apache-airflow.slack.com/

---

**Referanslarımız:**
- [quickstart.md](quickstart.md) - Hızlı başlangıç
- [01-giris.md](01-giris.md) - Detaylı giriş
- [03-dag-gelistirme.md](03-dag-gelistirme.md) - DAG development
- [04-operatorler.md](04-operatorler.md) - Operators guide
