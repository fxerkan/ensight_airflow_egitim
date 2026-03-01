# Apache Airflow Kurulum

> Bu bölümde Apache Airflow'un farklı ortamlarda nasıl kurulacağını öğreneceksiniz.

## Bu Bölümde Öğrenecekleriniz

- Docker Compose ile local Airflow kurulumu
- Production-ready konfigürasyon ayarları
- Cloud Composer (GCP) kurulumu ve yönetimi
- Monitoring ve logging setup
- Performance tuning stratejileri
- Troubleshooting ve yaygın hatalar
- Production deployment checklist

## İçindekiler
1. [Docker Compose Kurulumu](#docker-compose-kurulumu)
2. [Dizin Yapısı](#dizin-yapisi)
3. [Airflow Konfigürasyon](#airflow-konfigurasyon)
4. [Cloud Composer Kurulumu](#cloud-composer-kurulumu)
5. [Production Kurulum](#production-kurulum)
6. [Monitoring ve Logging](#monitoring-ve-logging)
7. [Performance Tuning](#performance-tuning)
8. [Troubleshooting](#troubleshooting)
9. [Pratik Alıştırmalar](#pratik-alistirmalar)
10. [Sık Sorulan Sorular](#sik-sorulan-sorular)
11. [Referanslar](#referanslar)

---

## Docker Compose Kurulumu

### Gereksinimler

#### Sistem Gereksinimleri Detaylı Tablo

| Gereksinim | Minimum | Önerilen | Production | Not |
|------------|---------|----------|------------|-----|
| **RAM** | 4 GB | 8 GB | 16+ GB | Parallelism'e göre artırın |
| **CPU** | 2 Core | 4 Core | 8+ Core | Worker sayısına bağlı |
| **Disk** | 10 GB | 50 GB | 200+ GB | Log rotation gerekir |
| **Docker** | 20.10+ | 24.0+ | 24.0+ | Compose v2 built-in |
| **Python** | 3.8 | 3.10 | 3.10-3.11 | Airflow 2.8 uyumlu |
| **PostgreSQL** | 11 | 14 | 14-15 | Metadata database |
| **Network** | 1 Mbps | 10 Mbps | 100+ Mbps | GCP/AWS için |

> **💡 İpucu:** Production ortamında database ve Airflow'u ayrı makinalarda çalıştırın.

> **⚠️ Uyarı:** Docker Desktop macOS'te Memory limit ayarlaması gerektirir (Preferences → Resources).

#### Docker Deskto

### Adım 1: Proje Dizinini Oluşturma

```bash
# Proje dizini oluştur
mkdir airflow-project
cd airflow-project

# Alt dizinler
mkdir -p dags logs plugins config data scripts egitim-notlari
```

**Dizin Açıklamaları:**
- `dags/`: DAG Python dosyaları
- `logs/`: Airflow log dosyaları
- `plugins/`: Custom plugin'ler
- `config/`: Konfigürasyon dosyaları
- `data/`: Test verileri
- `scripts/`: Yardımcı script'ler
- `egitim-notlari/`: Eğitim dokümanları

### Adım 2: Docker Compose Dosyası

`docker-compose.yaml` dosyası oluşturun:

```yaml
version: '3.8'

x-airflow-common:
  &airflow-common
  image: apache/airflow:2.8.1
  environment:
    &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: LocalExecutor
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CORE__FERNET_KEY: ''
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
    AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
    AIRFLOW__API__AUTH_BACKENDS: 'airflow.api.auth.backend.basic_auth'
    AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK: 'true'
    _PIP_ADDITIONAL_REQUIREMENTS: ${_PIP_ADDITIONAL_REQUIREMENTS:- apache-airflow-providers-google==10.13.1}
  volumes:
    - ${AIRFLOW_PROJ_DIR:-.}/dags:/opt/airflow/dags
    - ${AIRFLOW_PROJ_DIR:-.}/logs:/opt/airflow/logs
    - ${AIRFLOW_PROJ_DIR:-.}/plugins:/opt/airflow/plugins
    - ${AIRFLOW_PROJ_DIR:-.}/config:/opt/airflow/config
  user: "${AIRFLOW_UID:-50000}:0"
  depends_on:
    &airflow-common-depends-on
    postgres:
      condition: service_healthy

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres-db-volume:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 10s
      retries: 5
      start_period: 5s
    restart: always

  airflow-webserver:
    <<: *airflow-common
    command: webserver
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-scheduler:
    <<: *airflow-common
    command: scheduler
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8974/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    restart: always
    depends_on:
      <<: *airflow-common-depends-on
      airflow-init:
        condition: service_completed_successfully

  airflow-init:
    <<: *airflow-common
    entrypoint: /bin/bash
    command:
      - -c
      - |
        mkdir -p /sources/logs /sources/dags /sources/plugins
        chown -R "${AIRFLOW_UID}:0" /sources/{logs,dags,plugins}
        exec /entrypoint airflow version
    environment:
      <<: *airflow-common-env
      _AIRFLOW_DB_UPGRADE: 'true'
      _AIRFLOW_WWW_USER_CREATE: 'true'
      _AIRFLOW_WWW_USER_USERNAME: ${_AIRFLOW_WWW_USER_USERNAME:-airflow}
      _AIRFLOW_WWW_USER_PASSWORD: ${_AIRFLOW_WWW_USER_PASSWORD:-airflow}
    user: "0:0"
    volumes:
      - ${AIRFLOW_PROJ_DIR:-.}:/sources

volumes:
  postgres-db-volume:
```

### Adım 3: Environment Variables (.env)

`.env` dosyası oluşturun:

```bash
# Airflow UID (Linux için)
AIRFLOW_UID=50000

# Airflow UI Credentials
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow

# GCP Configuration (opsiyonel)
GCP_PROJECT_ID=my-gcp-project
GCS_BUCKET=my-data-bucket
```

### Adım 4: Airflow'u Başlatma

```bash
# 1. Database initialization (ilk kez)
docker compose up airflow-init

# 2. Tüm servisleri başlat
docker compose up -d

# 3. Servislerin durumunu kontrol et
docker compose ps
```

**Beklenen Çıktı:**
```
NAME                                   STATUS    PORTS
airflow-project-airflow-scheduler-1    running
airflow-project-airflow-webserver-1    running   0.0.0.0:8080->8080/tcp
airflow-project-postgres-1             running   5432/tcp
```

### Adım 5: Web UI'ya Erişim

1. Tarayıcınızda açın: **http://localhost:8080**
2. Giriş yapın:
   - Username: `airflow`
   - Password: `airflow`

**Airflow Login Screen:** http://localhost:8080 adresinde username ve password alanları görünecektir

### Adım 6: İlk DAG'i Test Etme

**Hello World DAG oluşturun** (`dags/hello_world.py`):

```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id='hello_world',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
) as dag:

    hello = BashOperator(
        task_id='say_hello',
        bash_command='echo "Hello Airflow!"'
    )
```

**DAG'i kontrol edin:**
```bash
# DAG listesini görüntüle
docker exec airflow-project-airflow-webserver-1 airflow dags list

# DAG'i test et
docker exec airflow-project-airflow-webserver-1 \
  airflow dags test hello_world 2024-01-01
```

---

## Dizin Yapısı

### Standart Airflow Projesi

```
airflow-project/
│
├── dags/                          # DAG Python dosyaları
│   ├── 01_hello_world_dag.py
│   ├── 02_etl_pipeline_dag.py
│   └── 09_sales_datamart_pipeline.py
│
├── plugins/                       # Custom operator, sensor, hook
│   ├── operators/
│   │   └── custom_operator.py
│   └── hooks/
│       └── custom_hook.py
│
├── config/                        # Konfigürasyon dosyaları
│   ├── airflow.cfg
│   └── webserver_config.py
│
├── logs/                          # Airflow log dosyaları
│   ├── dag_id=hello_world/
│   │   └── run_id=.../
│   │       └── task_id=say_hello/
│   └── scheduler/
│
├── data/                          # Test/sample data
│   ├── customers.csv
│   └── products.csv
│
├── scripts/                       # Yardımcı script'ler
│   ├── generate_test_data.py
│   └── setup_connections.sh
│
├── tests/                         # Unit testler
│   ├── test_dags.py
│   └── test_operators.py
│
├── docker-compose.yaml            # Docker Compose config
├── .env                           # Environment variables
├── requirements.txt               # Python dependencies
└── README.md                      # Proje dokümantasyonu
```

### DAG Klasör Organizasyonu

**Tip: DAG'leri klasörlere ayırın**

```
dags/
├── etl/
│   ├── daily_sales_etl.py
│   └── customer_etl.py
├── ml/
│   ├── model_training.py
│   └── prediction_pipeline.py
├── reports/
│   ├── daily_report.py
│   └── weekly_summary.py
└── maintenance/
    ├── cleanup_logs.py
    └── backup_database.py
```

---

## Airflow Konfigürasyon

### airflow.cfg Dosyası

Airflow konfigürasyon dosyası: `/Users/erkan.ciftci/repo_local/airflow & bigquery eğitimi/config/airflow.cfg`

**Önemli Parametreler:**

#### 1. Core Ayarları

```ini
[core]
# DAG dosyalarının olduğu klasör
dags_folder = /opt/airflow/dags

# Executor tipi (LocalExecutor, CeleryExecutor, KubernetesExecutor)
executor = LocalExecutor

# Paralel çalışabilecek maksimum task sayısı
parallelism = 32

# Bir DAG için maksimum paralel task
max_active_tasks_per_dag = 16

# Maksimum aktif DAG run sayısı
max_active_runs_per_dag = 16

# Timezone
default_timezone = Europe/Istanbul
```

#### 2. Scheduler Ayarları

```ini
[scheduler]
# Scheduler'ın DAG klasörünü tarama sıklığı (saniye)
dag_dir_list_interval = 300

# Yeni DAG'leri başlangıçta duraklat
dags_are_paused_at_creation = True

# Task instance parallelism
max_tis_per_query = 512

# Scheduler'ın DAG parse periyodu
min_file_process_interval = 30
```

#### 3. Web Server Ayarları

```ini
[webserver]
# Web server portu
web_server_port = 8080

# Workers (gunicorn)
workers = 4

# Base URL
base_url = http://localhost:8080

# UI'da gösterilecek DAG sayısı
default_ui_timezone = Europe/Istanbul
```

#### 4. Database Ayarları

```ini
[database]
# Connection string
sql_alchemy_conn = postgresql+psycopg2://airflow:airflow@postgres/airflow

# Connection pool boyutu
sql_alchemy_pool_size = 5
sql_alchemy_max_overflow = 10
```

#### 5. Logging Ayarları

```ini
[logging]
# Log seviyesi (INFO, WARNING, ERROR)
logging_level = INFO

# Log klasörü
base_log_folder = /opt/airflow/logs

# Remote logging (GCS, S3)
remote_logging = False
remote_log_conn_id = google_cloud_default
remote_base_log_folder = gs://my-bucket/airflow-logs
```

### Konfigürasyonu Değiştirme

**1. Environment Variable ile:**
```bash
# Docker Compose'da
environment:
  AIRFLOW__CORE__PARALLELISM: 64
  AIRFLOW__WEBSERVER__WEB_SERVER_PORT: 8080
```

**2. airflow.cfg dosyası ile:**
```bash
# airflow.cfg dosyasını düzenle
vi config/airflow.cfg

# Servisleri yeniden başlat
docker compose restart
```

**3. CLI ile:**
```bash
# Konfigürasyon değerini görüntüle
docker exec airflow-webserver-1 \
  airflow config get-value core executor

# Değeri değiştir (geçici)
docker exec airflow-webserver-1 \
  airflow config set-value core parallelism 64
```

---

## Cloud Composer Kurulumu

**Google Cloud Composer**, Google Cloud Platform'da yönetilen Airflow servisidir.

### Avantajları

- ✅ Fully managed (güncelleme, bakım, monitoring)
- ✅ Auto-scaling
- ✅ GCP servisleriyle entegrasyon
- ✅ High availability
- ✅ Security ve IAM entegrasyonu

### Kurulum Adımları

#### 1. GCP Projesi Hazırlama

```bash
# GCloud CLI kurulumu
# https://cloud.google.com/sdk/docs/install

# Projeyi seç
gcloud config set project MY_PROJECT_ID

# API'leri etkinleştir
gcloud services enable composer.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable storage.googleapis.com
```

#### 2. Cloud Composer Environment Oluşturma

**Console üzerinden:**
1. Google Cloud Console → Composer → Create Environment
2. Environment ayarları:
   - Name: `airflow-prod`
   - Location: `us-central1`
   - Node count: `3`
   - Machine type: `n1-standard-4`
   - Disk size: `100GB`
   - Python version: `3.10`
   - Airflow version: `2.8.1`

**CLI ile:**
```bash
gcloud composer environments create airflow-prod \
    --location us-central1 \
    --node-count 3 \
    --machine-type n1-standard-4 \
    --disk-size 100 \
    --python-version 3.10 \
    --airflow-version 2.8.1 \
    --env-variables \
        GCP_PROJECT_ID=my-project-id
```

#### 3. DAG'leri Upload Etme

```bash
# DAG klasörünü al
gcloud composer environments describe airflow-prod \
    --location us-central1 \
    --format="get(config.dagGcsPrefix)"

# Çıktı: gs://us-central1-airflow-prod-xxxxx/dags

# DAG'leri upload et
gsutil cp dags/*.py gs://us-central1-airflow-prod-xxxxx/dags/
```

#### 4. Environment Variable Ekleme

```bash
# Environment variable ekle
gcloud composer environments update airflow-prod \
    --location us-central1 \
    --update-env-variables \
        GCS_BUCKET=my-data-bucket
```

#### 5. Python Package Kurulumu

```bash
# PyPI package kur
gcloud composer environments update airflow-prod \
    --location us-central1 \
    --update-pypi-packages-from-file requirements.txt
```

#### 6. Airflow UI'ya Erişim

```bash
# Airflow webserver URL'ini al
gcloud composer environments describe airflow-prod \
    --location us-central1 \
    --format="get(config.airflowUri)"

# Tarayıcıda aç
```

### Cloud Composer Best Practices

1. **Environment Sizing**: İş yüküne göre node count ve machine type ayarlayın
2. **Auto-scaling**: Workload peaks için auto-scaling aktif edin
3. **Monitoring**: Stackdriver ile monitoring kurun
4. **Cost Optimization**: Dev/Test için smaller environment kullanın
5. **Backup**: DAG'leri Git'te saklayın

---

## Troubleshooting

### 1. Airflow Servisleri Başlamıyor

**Problem:**
```bash
docker compose ps
# STATUS: restarting veya unhealthy
```

**Çözüm:**
```bash
# Log'ları kontrol et
docker compose logs airflow-webserver
docker compose logs airflow-scheduler

# Database initialization tekrar çalıştır
docker compose down -v
docker compose up airflow-init
docker compose up -d
```

### 2. DAG Import Hataları

**Problem:** DAG listede görünmüyor veya import error var

**Çözüm:**
```bash
# Import error kontrolü
docker exec airflow-webserver-1 airflow dags list-import-errors

# DAG dosyasını test et
docker exec airflow-webserver-1 python /opt/airflow/dags/my_dag.py

# Syntax check
docker exec airflow-webserver-1 \
  airflow dags list
```

### 3. Task Hataları

**Problem:** Task failed durumda

**Çözüm:**
```bash
# Task log'larını görüntüle
docker exec airflow-webserver-1 \
  airflow tasks logs my_dag my_task 2024-01-01

# Task'ı test et
docker exec airflow-webserver-1 \
  airflow tasks test my_dag my_task 2024-01-01
```

### 4. Yavaş Performans

**Çözüm:**
```bash
# Parallelism artır
# docker-compose.yaml içinde:
AIRFLOW__CORE__PARALLELISM: 64
AIRFLOW__CORE__MAX_ACTIVE_TASKS_PER_DAG: 32

# Database connection pool artır
AIRFLOW__DATABASE__SQL_ALCHEMY_POOL_SIZE: 10
```

### 5. Disk Dolması

**Çözüm:**
```bash
# Eski log'ları temizle
docker exec airflow-webserver-1 \
  airflow db clean --clean-before-timestamp "2024-01-01" --yes

# Volume'leri temizle
docker compose down
docker volume prune
```

---

## Referanslar

### Resmi Dokümantasyon
- [Airflow Docker Setup](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html)
- [Configuration Reference](https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html)
- [Cloud Composer Documentation](https://cloud.google.com/composer/docs)

### Best Practices
- [Astronomer - Airflow Setup](https://docs.astronomer.io/learn/airflow-setup)
- [Google Cloud - Composer Best Practices](https://cloud.google.com/composer/docs/best-practices)

### Troubleshooting
- [Common Issues and Solutions](https://airflow.apache.org/docs/apache-airflow/stable/howto/common-pitfalls.html)

---

## Production Kurulum

### Production Checklist (30+ Madde)

#### Pre-Production Hazırlık
- [ ] Resource planning tamamlandı (CPU, RAM, Disk)
- [ ] Network topology belirlendi
- [ ] Security politikaları tanımlandı
- [ ] Backup stratejisi oluşturuldu
- [ ] Disaster recovery planı hazırlandı
- [ ] Monitoring araçları seçildi
- [ ] Logging stratejisi tanımlandı
- [ ] Alert mekanizması kuruldu

#### Infrastructure
- [ ] Database cluster kuruldu (High Availability)
- [ ] Redis/Celery backend yapılandırıldı (CeleryExecutor için)
- [ ] Load balancer konfigüre edildi
- [ ] SSL sertifikaları yüklendi
- [ ] Firewall kuralları tanımlandı
- [ ] VPN/VPC konfigürasyonu tamamlandı
- [ ] DNS kayıtları oluşturuldu
- [ ] Storage/Volume konfigürasyonu yapıldı

#### Airflow Configuration
- [ ] Executor seçimi yapıldı (LocalExecutor/CeleryExecutor/KubernetesExecutor)
- [ ] Parallelism ayarları optimize edildi
- [ ] Connection pool sizing yapıldı
- [ ] Fernet key oluşturuldu ve saklandı
- [ ] Secret backend yapılandırıldı (Vault/Secret Manager)
- [ ] RBAC ve authentication aktif edildi
- [ ] Email/Slack alerting yapılandırıldı
- [ ] Log rotation aktif edildi

#### Security
- [ ] Service account'lar oluşturuldu (least privilege)
- [ ] API key'ler güvenli saklandı
- [ ] Database şifreleri rotasyona alındı
- [ ] HTTPS enforced edildi
- [ ] Rate limiting yapılandırıldı
- [ ] IP whitelist tanımlandı
- [ ] Audit logging aktif edildi
- [ ] Vulnerability scanning yapıldı

#### Testing & Validation
- [ ] DAG'ler test edildi
- [ ] Connection'lar doğrulandı
- [ ] Performance test yapıldı
- [ ] Failover test edildi
- [ ] Backup/restore test edildi
- [ ] Monitoring dashboard'ları oluşturuldu

---

## Monitoring ve Logging

### Prometheus + Grafana Setup

#### Prometheus Exporter Kurulumu

**docker-compose.yaml'a ekle:**

```yaml
# Prometheus StatsD Exporter
statsd-exporter:
  image: prom/statsd-exporter:v0.24.0
  ports:
    - "9102:9102"
    - "9125:9125/udp"
  command:
    - '--statsd.mapping-config=/tmp/statsd_mapping.yml'
  volumes:
    - ./config/statsd_mapping.yml:/tmp/statsd_mapping.yml

# Prometheus
prometheus:
  image: prom/prometheus:v2.40.0
  ports:
    - "9090:9090"
  volumes:
    - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus-data:/prometheus
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'

# Grafana
grafana:
  image: grafana/grafana:9.3.0
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
  volumes:
    - grafana-data:/var/lib/grafana
    - ./config/grafana-dashboards:/etc/grafana/provisioning/dashboards

volumes:
  prometheus-data:
  grafana-data:
```

#### Airflow StatsD Configuration

**Airflow environment variables:**

```yaml
environment:
  AIRFLOW__METRICS__STATSD_ON: 'true'
  AIRFLOW__METRICS__STATSD_HOST: 'statsd-exporter'
  AIRFLOW__METRICS__STATSD_PORT: 9125
  AIRFLOW__METRICS__STATSD_PREFIX: 'airflow'
```

#### Önemli Metrikler

| Metrik | Açıklama | Alert Threshold |
|--------|----------|-----------------|
| `airflow.scheduler.heartbeat` | Scheduler canlılığı | > 30s |
| `airflow.dag.processing.total_parse_time` | DAG parse süresi | > 60s |
| `airflow.task_instance.duration` | Task süresi | > 3600s |
| `airflow.task_instance.failures` | Task hataları | > 5/hour |
| `airflow.executor.open_slots` | Boş worker slot | < 2 |
| `airflow.pool.open_slots` | Pool slot'ları | < 1 |
| `airflow.dag_processing.import_errors` | DAG import hataları | > 0 |

### Elasticsearch + Kibana Setup

#### Elasticsearch Remote Logging

**docker-compose.yaml:**

```yaml
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.6.0
  environment:
    - discovery.type=single-node
    - xpack.security.enabled=false
  ports:
    - "9200:9200"
  volumes:
    - elasticsearch-data:/usr/share/elasticsearch/data

kibana:
  image: docker.elastic.co/kibana/kibana:8.6.0
  ports:
    - "5601:5601"
  environment:
    - ELASTICSEARCH_HOSTS=http://elasticsearch:9200

volumes:
  elasticsearch-data:
```

**Airflow Configuration:**

```yaml
environment:
  AIRFLOW__LOGGING__REMOTE_LOGGING: 'true'
  AIRFLOW__LOGGING__REMOTE_LOG_CONN_ID: 'elasticsearch_default'
  AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER: 'elasticsearch://airflow-logs'
  AIRFLOW__LOGGING__ELASTICSEARCH_HOST: 'http://elasticsearch:9200'
```

### CloudWatch Logs (AWS)

```yaml
environment:
  AIRFLOW__LOGGING__REMOTE_LOGGING: 'true'
  AIRFLOW__LOGGING__REMOTE_LOG_CONN_ID: 'aws_default'
  AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER: 'cloudwatch://airflow-logs'
```

---

## Performance Tuning

### Performance Tuning Tablosu

| Parametre | Default | Düşük Yük | Orta Yük | Yüksek Yük | Açıklama |
|-----------|---------|-----------|----------|------------|----------|
| **parallelism** | 32 | 16 | 64 | 128 | Toplam paralel task sayısı |
| **max_active_tasks_per_dag** | 16 | 8 | 32 | 64 | DAG başına paralel task |
| **max_active_runs_per_dag** | 16 | 4 | 16 | 32 | DAG başına aktif run |
| **dag_dir_list_interval** | 300 | 600 | 300 | 60 | DAG folder scan (saniye) |
| **min_file_process_interval** | 30 | 60 | 30 | 10 | DAG parse periyodu (saniye) |
| **sql_alchemy_pool_size** | 5 | 5 | 10 | 20 | Database connection pool |
| **sql_alchemy_max_overflow** | 10 | 5 | 20 | 40 | Pool overflow |
| **worker_concurrency** | 16 | 8 | 32 | 64 | Celery worker concurrency |

### Executor Comparison

| Executor | Use Case | Pros | Cons | Scalability |
|----------|----------|------|------|-------------|
| **SequentialExecutor** | Development, Testing | Basit, kolay debug | Çok yavaş, production'a uygun değil | ⭐ |
| **LocalExecutor** | Small-Medium prod | Kolay setup, iyi performans | Tek makina limiti | ⭐⭐⭐ |
| **CeleryExecutor** | Large production | Horizontal scaling, fault tolerant | Kompleks setup (Redis/RabbitMQ) | ⭐⭐⭐⭐⭐ |
| **KubernetesExecutor** | Cloud-native, dynamic | Auto-scaling, isolation | K8s gerektirir, overhead var | ⭐⭐⭐⭐⭐ |

### Database Performance

```sql
-- PostgreSQL indexes (metadata database)
CREATE INDEX idx_task_instance_dag_run ON task_instance(dag_id, run_id);
CREATE INDEX idx_task_instance_state ON task_instance(state);
CREATE INDEX idx_dag_run_state ON dag_run(state, dag_id);
CREATE INDEX idx_job_state ON job(state);
```

**PostgreSQL Tuning (postgresql.conf):**

```ini
# Connection
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
work_mem = 16MB

# Logging
log_min_duration_statement = 1000  # Log slow queries (>1s)
```

### Port Configuration

#### Gerekli Portlar

| Port | Servis | Açıklama | Firewall Kuralı |
|------|--------|----------|-----------------|
| **8080** | Airflow Webserver | UI erişimi | Public (HTTPS ile) |
| **8974** | Airflow Scheduler | Health check | Internal only |
| **5555** | Flower (Celery) | Worker monitoring | Internal only |
| **5432** | PostgreSQL | Metadata database | Internal only |
| **6379** | Redis | Celery broker | Internal only |
| **9090** | Prometheus | Metrics | Internal/VPN |
| **3000** | Grafana | Dashboard | Public (auth ile) |

**Firewall kuralları (iptables):**

```bash
# Webserver (HTTPS only)
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Internal services
iptables -A INPUT -p tcp --dport 5432 -s 10.0.0.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 6379 -s 10.0.0.0/24 -j ACCEPT

# Block everything else
iptables -A INPUT -p tcp --dport 8080 -j DROP
```

---

## Troubleshooting (Genişletilmiş)

### 1. Volume Permission Hatası

**Problem:**
```bash
PermissionError: [Errno 13] Permission denied: '/opt/airflow/logs'
```

**Çözüm:**
```bash
# Linux/macOS için UID ayarla
echo "AIRFLOW_UID=$(id -u)" >> .env

# Dizinleri doğru sahiplikte oluştur
sudo chown -R 50000:0 logs dags plugins

# Container içinde kontrol et
docker exec airflow-webserver-1 ls -la /opt/airflow/
```

### 2. Network Connectivity

**Problem:** Container'lar birbirini göremiyor

**Çözüm:**
```bash
# Network listesini kontrol et
docker network ls

# Container'ların network'ünü kontrol et
docker inspect airflow-webserver-1 | grep NetworkMode

# Manuel network oluştur
docker network create airflow-network

# docker-compose.yaml'a ekle
networks:
  default:
    external:
      name: airflow-network
```

### 3. Database Migration Hatası

**Problem:**
```bash
airflow.exceptions.AirflowException: Migration to version xxx failed
```

**Çözüm:**
```bash
# Database'i sıfırla (DEV ONLY!)
docker compose down -v
docker volume rm airflow-project_postgres-db-volume

# Migration'ı manuel çalıştır
docker exec airflow-webserver-1 airflow db upgrade

# Downgrade (son çare)
docker exec airflow-webserver-1 airflow db downgrade -y -r <version>
```

### 4. Memory Issues

**Problem:** Container sürekli restart oluyor (OOMKilled)

**Çözüm:**
```yaml
# docker-compose.yaml'da memory limit ekle
services:
  airflow-webserver:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

```bash
# Docker Desktop memory artır (macOS/Windows)
# Preferences → Resources → Memory: 8GB

# Linux için system memory kontrol et
free -h
```

### 5. Scheduler Lag

**Problem:** Task'lar zamanında çalışmıyor, queue'da bekliyor

**Tanı:**
```bash
# Scheduler log'larını kontrol et
docker logs airflow-scheduler-1 --tail 100

# DAG parse sürelerini ölç
docker exec airflow-webserver-1 airflow dags list-import-errors
```

**Çözüm:**
```yaml
# Parallelism artır
environment:
  AIRFLOW__CORE__PARALLELISM: 64
  AIRFLOW__CORE__MAX_ACTIVE_TASKS_PER_DAG: 32
  AIRFLOW__SCHEDULER__MAX_TIS_PER_QUERY: 512

# DAG parse interval'ini artır (DAG sayısı çoksa)
  AIRFLOW__SCHEDULER__MIN_FILE_PROCESS_INTERVAL: 60
```

### 6. DAG Import Errors

**Problem:** DAG listede görünmüyor veya import error var

**Tanı:**
```bash
# Import error listesi
docker exec airflow-webserver-1 airflow dags list-import-errors

# Specific DAG test et
docker exec airflow-webserver-1 python /opt/airflow/dags/my_dag.py

# Syntax check
docker exec airflow-webserver-1 python -m py_compile /opt/airflow/dags/my_dag.py
```

**Yaygın Hatalar:**
```python
# ❌ YANLIŞ - Circular import
from dags.my_other_dag import some_function  # Avoid!

# ✅ DOĞRU
from utils.helpers import some_function

# ❌ YANLIŞ - Top-level code
result = expensive_api_call()  # Her parse'da çalışır!

# ✅ DOĞRU
@task
def fetch_data():
    result = expensive_api_call()  # Sadece task çalışınca
```

### 7. Connection Issues

**Problem:** BigQuery/GCS connection çalışmıyor

**Tanı:**
```bash
# Connection test et
docker exec airflow-webserver-1 \
  airflow connections test google_cloud_default

# Environment variable kontrol et
docker exec airflow-webserver-1 env | grep GOOGLE

# Service account key dosyası var mı?
docker exec airflow-webserver-1 ls -la /opt/airflow/config/
```

**Çözüm:**
```bash
# Service account key'i mount et
volumes:
  - ./config/gcp-keyfile.json:/opt/airflow/config/gcp-keyfile.json:ro

# Environment variable ekle
environment:
  GOOGLE_APPLICATION_CREDENTIALS: /opt/airflow/config/gcp-keyfile.json
```

### 8. Task Stuck in Running State

**Problem:** Task running state'te takılı kaldı, ilerlemeiyor

**Tanı:**
```bash
# Task instance detayları
docker exec airflow-webserver-1 \
  airflow tasks state my_dag my_task 2024-01-01

# Logları kontrol et
docker exec airflow-webserver-1 \
  airflow tasks logs my_dag my_task 2024-01-01

# Process listesi
docker exec airflow-webserver-1 ps aux | grep my_task
```

**Çözüm:**
```bash
# Task'ı clear et (tekrar çalıştır)
docker exec airflow-webserver-1 \
  airflow tasks clear my_dag -t my_task -s 2024-01-01 -e 2024-01-01 -y

# Zombi task'ları temizle
docker exec airflow-webserver-1 \
  airflow tasks clear --only-failed my_dag
```

---

## Pratik Alıştırmalar

### Alıştırma 1: Kurulum Doğrulama

**Görev:** Tüm Airflow componentlerinin çalıştığını doğrulayın.

```bash
# 1. Container durumlarını kontrol et
docker compose ps

# 2. Webserver'a erişim test et
curl http://localhost:8080/health

# 3. Scheduler heartbeat kontrol et
docker logs airflow-scheduler-1 --tail 20 | grep "heartbeat"

# 4. Database connection test et
docker exec airflow-webserver-1 \
  airflow db check

# Beklenen çıktı: Tüm servisler "healthy" durumda
```

### Alıştırma 2: Config Değişikliği

**Görev:** Parallelism değerini değiştirin ve etkisini gözlemleyin.

```yaml
# docker-compose.yaml'da değiştir
environment:
  AIRFLOW__CORE__PARALLELISM: 64

# Servisleri yeniden başlat
docker compose restart airflow-scheduler airflow-webserver

# Config değerini doğrula
docker exec airflow-webserver-1 \
  airflow config get-value core parallelism

# Beklenen: 64
```

### Alıştırma 3: Custom Connection Ekleme

**Görev:** BigQuery connection'ı CLI ile ekleyin.

```bash
# Service account key'i kopyala
docker cp ~/Downloads/gcp-key.json airflow-webserver-1:/tmp/

# Connection ekle
docker exec airflow-webserver-1 \
  airflow connections add 'google_cloud_default' \
  --conn-type 'google_cloud_platform' \
  --conn-extra '{"keyfile_path": "/tmp/gcp-key.json", "project": "my-project"}'

# Connection test et
docker exec airflow-webserver-1 \
  airflow connections test google_cloud_default
```

### Alıştırma 4: DAG Deploy ve Test

**Görev:** Yeni bir DAG deploy edin ve test edin.

```bash
# 1. DAG dosyasını oluştur
cat > dags/test_dag.py << 'EOF'
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG('test_deployment', start_date=datetime(2024,1,1), schedule_interval='@daily') as dag:
    BashOperator(task_id='test', bash_command='echo "Deployment successful!"')
EOF

# 2. DAG'in yüklendiğini kontrol et (30 saniye bekle)
sleep 30
docker exec airflow-webserver-1 airflow dags list | grep test_deployment

# 3. DAG'i test et
docker exec airflow-webserver-1 \
  airflow dags test test_deployment 2024-01-01

# 4. Import error var mı kontrol et
docker exec airflow-webserver-1 airflow dags list-import-errors
```

### Alıştırma 5: Log Rotation Setup

**Görev:** Log rotation yapılandırın.

```yaml
# docker-compose.yaml'a ekle
environment:
  AIRFLOW__LOGGING__BASE_LOG_FOLDER: /opt/airflow/logs
  AIRFLOW__LOGGING__DAG_PROCESSOR_LOG_TARGET: file

# Eski log'ları temizle (>30 gün)
docker exec airflow-webserver-1 \
  find /opt/airflow/logs -name "*.log" -type f -mtime +30 -delete

# Cron job ekle (production'da)
# 0 2 * * * docker exec airflow-webserver airflow db clean --clean-before-timestamp $(date -d '30 days ago' +%Y-%m-%d) -y
```

---

## Sık Sorulan Sorular (FAQ)

### Genel Sorular

**S1: LocalExecutor vs CeleryExecutor ne zaman kullanılmalı?**

A:
- **LocalExecutor**: Küçük-orta projeler, tek sunucu yeterli, kolay setup
- **CeleryExecutor**: Büyük projeler, horizontal scaling gerekli, yüksek availability

**S2: Airflow 1.x'ten 2.x'e geçiş yapılabilir mi?**

A: Evet, ancak breaking changes var. Migration guide takip edin:
- TaskFlow API'ye geçiş (optional ama önerilen)
- RBAC default olarak açık
- Bazı operator'ler provider package'lara taşındı

**S3: Kaç DAG olması performansı etkiler?**

A: 1000+ DAG olunca scheduler lag başlar. Çözümler:
- `min_file_process_interval` artır
- DAG'leri klasörlere böl
- Kullanılmayan DAG'leri sil/pause et

**S4: DAG'ler Git'te nasıl yönetilmeli?**

A:
- Ayrı Git repo (dags-only)
- Veya monorepo içinde `/dags` folder
- CI/CD ile automatic deploy
- Git-sync sidecar (Kubernetes)

### Kurulum Soruları

**S5: Docker kullanmadan kurulum yapılabilir mi?**

A: Evet, pip ile:
```bash
pip install apache-airflow==2.8.1
airflow db init
airflow users create --username admin --role Admin
airflow webserver &
airflow scheduler &
```
Ancak Docker daha kolay ve taşınabilir.

**S6: macOS'te "Rosetta" hatası alıyorum?**

A: M1/M2 Mac kullanıyorsanız:
```yaml
platform: linux/amd64  # docker-compose.yaml'a ekle
```

**S7: Windows'ta path uzunluğu hatası?**

A: Windows long path'i enable edin:
```powershell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

### Performance Soruları

**S8: Scheduler çok CPU kullanıyor?**

A: DAG parse overhead azaltın:
```yaml
AIRFLOW__SCHEDULER__MIN_FILE_PROCESS_INTERVAL: 60  # Default 30
AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL: 300  # Default 300
```

**S9: Database connection pool hatası?**

A: Pool size artır:
```yaml
AIRFLOW__DATABASE__SQL_ALCHEMY_POOL_SIZE: 10
AIRFLOW__DATABASE__SQL_ALCHEMY_MAX_OVERFLOW: 20
```

**S10: Memory leak var gibi, RAM kullanımı artıyor?**

A:
- Scheduler/webserver restart schedule edin (weekly)
- XCom'da büyük veri saklamayın (>1MB)
- Eski DAG run'ları silin: `airflow db clean`

### Cloud Composer Soruları

**S11: Cloud Composer vs self-hosted maliyeti?**

A: Cloud Composer daha pahalı (~$300-500/month) ama:
- Fully managed
- Auto-scaling
- High availability
- No ops overhead

**S12: Cloud Composer environment upgrade nasıl yapılır?**

A:
```bash
gcloud composer environments update ENV_NAME \
  --location LOCATION \
  --airflow-version 2.8.1
```
Downtime olabilir, staging'de test edin.

### Security Soruları

**S13: Airflow'u internete açmak güvenli mi?**

A: Hayır, mutlaka:
- HTTPS enforce edin
- Strong authentication (LDAP/OAuth)
- RBAC aktif
- Rate limiting
- VPN/VPC arkasında tutun

**S14: API key'ler nerede saklanmalı?**

A:
- Airflow Variables (encrypted)
- Secret Backend (Vault, GCP Secret Manager)
- Kubernetes Secrets
- AWS Secrets Manager

**S15: Fernet key nedir ve nasıl oluşturulur?**

A: Airflow'un connection'ları encrypt ettiği key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# .env'ye ekle
AIRFLOW__CORE__FERNET_KEY=<generated-key>
```

---

## Sonraki Adımlar

- **[03-dag-gelistirme.md](03-dag-gelistirme.md)**: DAG yazma ve geliştirme
- **[04-operatorler.md](04-operatorler.md)**: Operator'ler ve kullanımları
