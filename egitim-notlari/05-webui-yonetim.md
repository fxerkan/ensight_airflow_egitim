# Airflow Web UI ve Yönetim

> **Bu Bölümde Öğrenecekleriniz:**
> - Airflow WebUI'ı etkin kullanma
> - DAG'leri görselleştirme ve yönetme
> - Task'ları izleme ve debug etme
> - Connection ve variable yönetimi
> - Scheduling ve backfill işlemleri
> - Keyboard shortcuts ve power user özellikleri

## İçindekiler
1. [Web UI Genel Bakış](#webui-genel-bakis)
2. [DAG View'ları](#dag-viewlari)
3. [DAG Çalıştırma](#dag-calistirma)
4. [Scheduling ve Cron](#scheduling-cron)
5. [Backfill İşlemleri](#backfill-islemleri)
6. [Hata Ayıklama](#hata-ayiklama)
7. [Connection ve Variable Yönetimi](#connection-variable-yonetimi)
8. [Keyboard Shortcuts](#keyboard-shortcuts)
9. [Advanced Features](#advanced-features)
10. [Pratik Alıştırmalar](#pratik-alıştırmalar)
11. [Sık Sorulan Sorular](#sik-sorulan-sorular)
12. [Referanslar](#referanslar)

---

## WebUI Genel Bakış

Airflow Web UI'ya erişim: **http://localhost:8080**

### Ana Sayfalar

| Sayfa | Açıklama | URL |
|-------|----------|-----|
| **DAGs** | DAG listesi ve durum | `/dags` |
| **Grid** | DAG run'ları grid görünümü | `/dags/<dag_id>/grid` |
| **Graph** | DAG grafiği | `/dags/<dag_id>/graph` |
| **Calendar** | DAG run takvimi | `/dags/<dag_id>/calendar` |
| **Task Duration** | Task süreleri | `/dags/<dag_id>/duration` |
| **Gantt** | Gantt chart | `/dags/<dag_id>/gantt` |
| **Code** | DAG kaynak kodu | `/dags/<dag_id>/code` |
| **Audit Log** | Değişiklik logları | `/dags/<dag_id>/audit-log` |

### DAGs List View

Airflow WebUI'ın ana sayfasında tüm DAG'lerinizi görebilir ve yönetebilirsiniz.

![Airflow DAGs List View](../assets/dags-list-view.png)
*Kaynak: [Airflow Official UI Documentation](https://airflow.apache.org/docs/apache-airflow/stable/ui.html)*

**Görüntülenen Bilgiler:**
- DAG ID ve açıklama
- Schedule interval
- Owner
- Recent runs (son çalıştırmalar)
- Last run duration
- Next run time
- Tags

**Filtreler:**
- Search (arama)
- Tags
- Owner
- Status (Active/Paused)

---

## DAG View'ları

### 1. Grid View (Ana Görünüm)

Grid View, DAG run'larınızın tüm task instance'larını grid formatında gösterir. Her sütun bir DAG run, her satır bir task'ı temsil eder.

![Airflow Grid View](../assets/grid-view.png)
*Kaynak: [Airflow Official UI Documentation](https://airflow.apache.org/docs/apache-airflow/stable/ui.html)*

**Navigasyon**: DAG detay sayfasında varsayılan view. Hızlı geçiş için **`g` tuşuna** basın.

**Özellikler:**
- Tüm DAG run'larının task durumları
- Zaman çizelgesi (timeline)
- Task renk kodları:
  - 🟢 **Yeşil**: Success
  - 🔴 **Kırmızı**: Failed
  - 🟡 **Sarı**: Running
  - ⚪ **Gri**: Queued
  - 🔵 **Mavi**: Up for retry
  - 🟤 **Turuncu**: Up for reschedule
  - ⚫ **Siyah**: Skipped

**Kullanım:**
- Task'a tıklayarak detayları görüntüleme
- Run'a tıklayarak tüm run bilgilerini görme
- Filter/sort ile arama

### 2. Graph View

Graph View, DAG'inizin task'larını ve aralarındaki bağımlılıkları node-based graph olarak gösterir.

![Airflow Graph View](../assets/graph-view.png)
*Kaynak: [Airflow Official UI Documentation](https://airflow.apache.org/docs/apache-airflow/stable/ui.html)*

**Hızlı Geçiş**: Grid View'dayken **`g` tuşuna** basarak Graph View'a geçiş yapabilirsiniz.

**Özellikler:**
- Task dependency grafiği
- Task grupları (Task Groups)
- Akış yönü
- Task durumları renk kodlu

**Etkileşimler:**
- Task'a tıklama → Task details
- Zoom in/out
- Pan (kaydırma)
- Auto-layout

**Ne Zaman Kullan:**
- DAG yapısını anlamak için
- Dependency problemlerini görmek için
- Pipeline akışını görselleştirmek için

### 3. Calendar View

**Calendar View:** DAG run'larını takvim formatında gösterir (WebUI'da 'c' tuşu ile erişilebilir)

**Özellikler:**
- Aylık takvim görünümü
- Her günün run durumu
- Success/failure pattern'leri

**Kullanım:**
- Geçmiş run pattern'lerini analiz
- Sorunlu günleri tespit
- SLA ihlallerini görme

### 4. Gantt Chart

**Gantt View:** Task execution timeline'ını gösterir (WebUI'da 't' tuşu ile erişilebilir)

**Özellikler:**
- Task başlangıç ve bitiş zamanları
- Paralel çalışan task'lar
- Task süreleri
- Bottleneck tespiti

**Kullanım:**
- Performance optimizasyonu
- Parallelization fırsatları
- Uzun süren task'ları bulma

### 5. Task Duration

**Özellikler:**
- Task'ların ortalama süreleri
- Trend analizi
- Outlier (aykırı) değerler

### 6. Code View

**Özellikler:**
- DAG kaynak kodu görüntüleme
- Syntax highlighting
- Read-only view

---

## DAG Çalıştırma

### 1. Manual Trigger (Manuel Tetikleme)

**Trigger DAG:** DAG satırındaki ▶️ (play) butonuna tıklayın ve "Trigger DAG" butonuna basın

**Adımlar:**
1. DAGs listesinde DAG'i bul
2. ▶️ **Play** butonuna tıkla
3. (Opsiyonel) Configuration ekle
4. "Trigger" butonuna bas

**Configuration ile Tetikleme:**
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "environment": "production"
}
```

**DAG içinde kullanım:**
```python
@task
def process_data(**kwargs):
    conf = kwargs['dag_run'].conf or {}
    start_date = conf.get('start_date', '2024-01-01')
    print(f"Processing from {start_date}")
```

### 2. Pause/Unpause DAG

**Pause:**
- DAG schedule'u durdurur
- Manuel trigger hala çalışır
- Mevcut run'lar tamamlanır

**Toggle:**
- DAGs listesinde toggle switch

### 3. Clear/Rerun Tasks

**Task'ları Temizle ve Yeniden Çalıştır:**

1. Grid view'da task'a tıkla
2. **Clear** butonuna bas
3. Seçenekler:
   - ✅ **Past**: Önceki task'ları da clear et
   - ✅ **Future**: Sonraki task'ları da clear et
   - ✅ **Upstream**: Upstream task'ları da clear et
   - ✅ **Downstream**: Downstream task'ları da clear et
   - ✅ **Failed**: Sadece failed task'ları clear et

**Kullanım Senaryoları:**
- Task failed → Data düzelt → Clear → Retry
- Upstream veri değişti → Clear downstream tasks
- Tüm pipeline'ı yeniden çalıştır

### 4. Mark Success/Failed

**Task'ı başarılı/başarısız olarak işaretle:**

1. Task'a tıkla
2. **Mark Success** veya **Mark Failed**

**⚠️ DİKKAT:**
- Task gerçekten çalışmaz, sadece işaretlenir
- Downstream task'lar bu duruma göre çalışır
- Loglarda görünür

**Kullanım Senaryoları:**
- Test amacıyla downstream'i tetiklemek
- Bilinen bir hatayı geçici bypass etmek
- Emergency fix sonrası manuel onay

---

## Scheduling ve Cron

### Schedule Interval Belirleme

**WebUI'da Görüntüleme:**
- DAGs listesinde "Schedule" sütunu
- DAG detayında "Schedule Interval" bilgisi

### Cron Expression Örnekleri

```python
# Her gün saat 02:00
schedule_interval='0 2 * * *'

# Her Pazartesi 09:00
schedule_interval='0 9 * * 1'

# Her ayın 1'i ve 15'i saat 12:00
schedule_interval='0 12 1,15 * *'

# Her 4 saatte bir
schedule_interval='0 */4 * * *'

# İş günleri 08:00 (Pazartesi-Cuma)
schedule_interval='0 8 * * 1-5'

# Her ay sonu (son gün 23:59)
schedule_interval='59 23 28-31 * *'
```

**Cron Tester:** [crontab.guru](https://crontab.guru/)

### Next Run Time

**WebUI'da Görüntüleme:**
- DAGs listesinde "Next Run" sütunu
- Last run + schedule_interval

**Örnek:**
```
Last Run: 2024-02-27 02:00:00
Schedule: @daily (0 0 * * *)
Next Run: 2024-02-28 00:00:00
```

### Catchup Davranışı

**catchup=True:**
```python
# start_date'ten bugüne kadar her gün için run oluştur
with DAG(
    dag_id='backfill_dag',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=True  # 1 Ocak'tan bugüne tüm günler
):
    pass
```

**catchup=False (önerilen):**
```python
# Sadece şimdiden itibaren çalıştır
with DAG(
    dag_id='my_dag',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False  # Geçmiş günleri atla
):
    pass
```

---

## Backfill İşlemleri

Backfill, geçmiş tarihler için DAG run'larını çalıştırmaktır.

### CLI ile Backfill

```bash
# Belirli tarih aralığı için backfill
docker exec airflow-webserver-1 \
  airflow dags backfill \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  my_dag

# Sadece başarısız task'ları yeniden çalıştır
docker exec airflow-webserver-1 \
  airflow dags backfill \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --rerun-failed-tasks \
  my_dag

# Specific tasks
docker exec airflow-webserver-1 \
  airflow dags backfill \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --task-regex 'extract.*' \
  my_dag
```

### Backfill Best Practices

1. **Küçük aralıklarla test et:**
   ```bash
   # İlk 1 gün test et
   airflow dags backfill -s 2024-01-01 -e 2024-01-01 my_dag
   # Sonra tüm ay
   airflow dags backfill -s 2024-01-01 -e 2024-01-31 my_dag
   ```

2. **Resource limitleri koy:**
   ```python
   with DAG(
       max_active_runs=1,  # Aynı anda 1 run
       max_active_tasks_per_dag=16  # Max parallelism
   ):
       pass
   ```

3. **Dry-run kullan:**
   ```bash
   airflow dags backfill --dry-run -s 2024-01-01 -e 2024-01-31 my_dag
   ```

---

## Hata Ayıklama

### 1. Task Logs

**Log Görüntüleme:**
1. Grid view'da task'a tıkla
2. "Log" butonuna bas
3. Log stream açılır

**Log Seviyeleri:**
- INFO: Genel bilgi
- WARNING: Uyarılar
- ERROR: Hatalar
- DEBUG: Detaylı debug bilgisi

**CLI ile Log:**
```bash
docker exec airflow-webserver-1 \
  airflow tasks logs my_dag my_task 2024-01-01
```

### 2. Task Instance Details

**Bilgiler:**
- Start time / End time
- Duration
- Try number (retry count)
- Hostname (hangi worker'da çalıştı)
- Rendered template (Jinja template render edilmiş hali)
- XCom values

### 3. Import Errors

**DAG import hatalarını görüntüleme:**

WebUI:
- Admin → Import Errors

CLI:
```bash
docker exec airflow-webserver-1 \
  airflow dags list-import-errors
```

**Yaygın Import Hataları:**
- Syntax error
- Missing imports
- Invalid DAG parameters
- Circular dependencies

### 4. Test Tasks

**CLI ile task test:**
```bash
# Task'ı test et (database'e yazmaz)
docker exec airflow-webserver-1 \
  airflow tasks test my_dag my_task 2024-01-01

# DAG'i test et (tüm task'ları)
docker exec airflow-webserver-1 \
  airflow dags test my_dag 2024-01-01
```

### 5. Rendered Templates

**Jinja template'lerin render edilmiş halini görme:**

1. Task'a tıkla
2. "Rendered Template" tab'ına git
3. Template değişkenleri görüntüle

**Örnek:**
```python
bash_command='echo "Date: {{ ds }}"'
# Rendered: echo "Date: 2024-01-01"
```

---

## Connection ve Variable Yönetimi

### Connections

**Connection Nedir:**
Dış sistemlere (database, API, cloud) bağlantı bilgileri.

**Connection Ekleme:**
1. Admin → Connections
2. "+" butonuna bas
3. Connection bilgilerini gir:
   - **Connection Id**: `google_cloud_default`
   - **Connection Type**: Google Cloud
   - **Keyfile Path**: `/path/to/keyfile.json`

**Connection Types:**
- Google Cloud Platform
- Amazon Web Services
- PostgreSQL
- MySQL
- HTTP
- SSH
- FTP/SFTP

**CLI ile Connection:**
```bash
# Connection ekle
docker exec airflow-webserver-1 \
  airflow connections add 'my_postgres' \
  --conn-type 'postgres' \
  --conn-host 'localhost' \
  --conn-login 'airflow' \
  --conn-password 'airflow' \
  --conn-port 5432

# Connection listele
docker exec airflow-webserver-1 \
  airflow connections list

# Connection test et
docker exec airflow-webserver-1 \
  airflow connections test my_postgres
```

**DAG'de Kullanım:**
```python
from airflow.providers.postgres.hooks.postgres import PostgresHook

@task
def query_database():
    hook = PostgresHook(postgres_conn_id='my_postgres')
    records = hook.get_records("SELECT * FROM table")
    return records
```

### Variables

**Variable Nedir:**
DAG'ler arası paylaşılan global değişkenler.

**Variable Ekleme:**
1. Admin → Variables
2. "+" butonuna bas
3. Key-Value gir:
   - **Key**: `gcp_project_id`
   - **Value**: `my-gcp-project`

**CLI ile Variable:**
```bash
# Variable ekle
docker exec airflow-webserver-1 \
  airflow variables set gcp_project_id my-gcp-project

# Variable listele
docker exec airflow-webserver-1 \
  airflow variables list

# Variable al
docker exec airflow-webserver-1 \
  airflow variables get gcp_project_id
```

**DAG'de Kullanım:**
```python
from airflow.models import Variable

# DAG tanımında (parse zamanında)
GCP_PROJECT = Variable.get("gcp_project_id", default_var="default-project")

# Task içinde (runtime'da, önerilen)
@task
def process_data():
    project_id = Variable.get("gcp_project_id")
    print(f"Project: {project_id}")
```

**⚠️ DİKKAT:**
- Variable.get() DAG parse zamanında çalışır → Her parse'da database hit
- Runtime'da kullanmak daha performanslı

**Secrets Backend:**
Production'da variable'ları secret manager'da sakla:
- Google Cloud Secret Manager
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault

---

## Keyboard Shortcuts

Airflow WebUI, hızlı navigasyon için keyboard shortcuts destekler.

### DAG Details Sayfası

| Shortcut | Açıklama |
|----------|----------|
| **`g`** | Grid View ↔ Graph View toggle |
| **`r`** | Sayfayı refresh et (Auto-refresh açmadan manuel refresh) |
| **`/`** | Search/filter bar'a odaklan |
| **`Esc`** | Modal/dialog'u kapat |

### DAG List Sayfası

| Shortcut | Açıklama |
|----------|----------|
| **`/`** | DAG arama kutusuna odaklan |
| **`Ctrl/Cmd + K`** | Quick search (bazı versiyonlarda) |

### Task Instance Details

| Shortcut | Açıklama |
|----------|----------|
| **`l`** | Task log'larını aç |
| **`x`** | XCom values göster |
| **`t`** | Task details modal'ı aç |

### Power User İpuçları

```bash
# 🚀 Hızlı DAG arama
1. Ana sayfada "/" tuşuna bas
2. DAG adını yaz
3. Enter ile DAG'e git

# 🔄 Auto-refresh
1. DAG details sayfasında sağ üstteki "Auto-refresh" toggle'ı aktif et
2. Her 10 saniyede bir otomatik refresh olur

# 📊 View switching
1. Grid View'dayken "g" tuşuna bas → Graph View
2. Graph View'dayken "g" tuşuna bas → Grid View geri
```

---

## Advanced Features

### 1. Filtering ve Search

**DAG Listesinde Gelişmiş Filtreleme:**

```
# Tag ile filtre
tag:production
tag:etl

# Owner ile filtre
owner:data-team

# Status ile filtre
status:active
status:paused

# Kombinasyon
tag:production AND owner:data-team
```

**Task Instance Filtering:**
- State (Success, Failed, Running, Queued vb.)
- Task ID pattern
- Execution date range

### 2. Task State Colors (Renk Kodları Tablosu)

| Renk | State | Açıklama |
|------|-------|----------|
| 🟢 **Success (Yeşil)** | `success` | Task başarıyla tamamlandı |
| 🔴 **Failed (Kırmızı)** | `failed` | Task başarısız oldu |
| 🟡 **Running (Sarı)** | `running` | Task şu an çalışıyor |
| ⚪ **Queued (Gri)** | `queued` | Task kuyruğa alındı, çalışmayı bekliyor |
| 🔵 **Up for Retry (Mavi)** | `up_for_retry` | Retry bekliyor |
| 🟠 **Up for Reschedule (Turuncu)** | `up_for_reschedule` | Sensor reschedule modunda bekliyor |
| ⚫ **Skipped (Siyah)** | `skipped` | Task atlandı (branching) |
| 🟣 **Upstream Failed (Mor)** | `upstream_failed` | Upstream task failed olduğu için çalışmadı |
| 🟤 **Deferred (Kahverengi)** | `deferred` | Async deferred mode (Airflow 2.2+) |
| ⬜ **No Status (Beyaz)** | `no_status` | Henüz çalışmadı / scheduled değil |

### 3. DAG Dependencies View

**Cross-DAG Dependencies:** Admin menüsünden "DAG Dependencies" sayfası DAG'ler arası bağımlılıkları gösterir.

```python
# Örnek: DAG2, DAG1'e bağımlı
from airflow.sensors.external_task import ExternalTaskSensor

wait_for_dag1 = ExternalTaskSensor(
    task_id='wait_for_dag1_completion',
    external_dag_id='dag1',
    external_task_id='final_task'
)
```

**Dependencies Graph:** Tüm DAG'lerinizin birbirlerine nasıl bağlı olduğunu görselleştirir.

### 4. Audit Log

**Audit Log Sayfası:** Admin → Audit Logs

Her değişiklik loglanır:
- DAG pause/unpause
- Task clear
- Variable create/update/delete
- Connection create/update/delete
- User actions

**Log Bilgileri:**
- User (kim yaptı)
- Timestamp (ne zaman)
- Action (ne yapıldı)
- DAG ID / Task ID
- Extra (detaylar)

### 5. Browse Menu

| Sayfa | Kullanım |
|-------|----------|
| **DAG Runs** | Tüm DAG run'ları listele ve filtrele |
| **Task Instances** | Tüm task instance'ları göster |
| **Jobs** | Scheduler, webserver job'larını görüntüle |
| **Logs** | Airflow component logları |
| **Pools** | Task pool'larını yönet (concurrency limit) |
| **XComs** | XCom değerlerini görüntüle ve debug et |
| **Variables** | Global variables |
| **Connections** | External system connections |
| **Plugins** | Yüklü plugin'leri göster |

### 6. Pools (Concurrency Control)

**Pool Oluşturma:**
1. Admin → Pools
2. "+" butonu
3. Pool name: `bigquery_pool`
4. Slots: `5` (Aynı anda max 5 task çalışabilir)

**DAG'de Kullanım:**
```python
task = BigQueryInsertJobOperator(
    task_id='query_bigquery',
    pool='bigquery_pool',  # Bu pool'u kullan
    ...
)
```

**Kullanım Senaryoları:**
- API rate limiting
- Database connection limiting
- Resource (CPU/Memory) control

### 7. Datasets (Airflow 2.4+)

**Dataset-based Scheduling:** DAG'ler veri değişikliklerine göre trigger olabilir.

```python
from airflow import Dataset

# DAG 1: Dataset'i update eder
with DAG('producer_dag', ...) as dag:
    update_data = BashOperator(
        task_id='update',
        bash_command='...',
        outlets=[Dataset('s3://bucket/data.csv')]  # Dataset güncellendi
    )

# DAG 2: Dataset değişince trigger olur
with DAG(
    'consumer_dag',
    schedule=[Dataset('s3://bucket/data.csv')],  # Dataset'e bağlı
    ...
) as dag:
    process_data = BashOperator(...)
```

### 8. Cron Expression Tester

**WebUI'da Cron Test:**
- DAG oluştururken/düzenlerken schedule interval'e tıklayın
- Cron expression girin
- Next run times preview görebilirsiniz

**Harici Tool:** [crontab.guru](https://crontab.guru/)

```
# Örnekler
0 2 * * * → Her gün 02:00
0 */4 * * * → Her 4 saatte
0 9 * * 1-5 → İş günleri 09:00
0 12 1,15 * * → Her ayın 1 ve 15'i 12:00
```

---

## Monitoring ve Alerting

### SLA (Service Level Agreement)

**SLA Tanımlama:**
```python
from datetime import timedelta

default_args = {
    'sla': timedelta(hours=2)  # Task 2 saat içinde tamamlanmalı
}

with DAG(
    default_args=default_args,
    sla_miss_callback=alert_sla_miss
):
    pass
```

### Email Alerting

```python
default_args = {
    'email': ['team@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'email_on_success': False
}
```

### Custom Callbacks

```python
def slack_alert(context):
    """Slack'e bildirim gönder"""
    ti = context['task_instance']
    message = f"Task {ti.task_id} failed in {ti.dag_id}"
    # Slack webhook call
    send_to_slack(message)

task = BashOperator(
    task_id='critical_task',
    bash_command='...',
    on_failure_callback=slack_alert
)
```

---

## Pratik Alıştırmalar

### Alıştırma 1: WebUI Navigation (Kolay)
**Zorluk**: ⭐ Kolay
**Süre**: 10 dakika

**Görev**: Airflow WebUI'da aşağıdaki sayfaları bulun ve açın:

1. DAGs listesi
2. Specific bir DAG'in Grid View'ı
3. Graph View'a geçiş (keyboard shortcut ile)
4. Task log'larını görüntüleme
5. Connections sayfası
6. Variables sayfası
7. Audit Log
8. DAG Dependencies

**İpuçları**: Keyboard shortcuts kullanın (`g`, `/` vb.)

---

### Alıştırma 2: DAG Trigger ve Monitoring (Orta)
**Zorluk**: ⭐⭐ Orta
**Süre**: 20 dakika

**Görev**: `01_hello_world` DAG'ini manuel trigger edin ve izleyin:

**Adımlar**:
1. DAG'i pause durumundaysa unpause edin
2. Configuration ile trigger edin:
   ```json
   {"test_mode": true, "user": "your_name"}
   ```
3. Grid View'da task durumlarını izleyin
4. Failed bir task varsa log'larını inceleyin
5. Task'ı clear edip yeniden çalıştırın
6. Rendered template'leri görüntüleyin

**Beklenen Çıktı**: Screenshot'lar ve gözlemleriniz

---

### Alıştırma 3: Backfill İşlemi (Orta)
**Zorluk**: ⭐⭐ Orta
**Süre**: 25 dakika

**Görev**: Bir DAG için geçmiş tarih backfill yapın:

**Senaryo**: `sales_etl` DAG'i için 1-7 Ocak 2024 arasında backfill yapmanız gerekiyor.

**Adımlar**:
1. CLI ile backfill komutu oluşturun
2. İlk 1 gün test edin (dry-run)
3. Tüm haftayı backfill edin
4. WebUI'dan progress takip edin
5. Failed task'ları temizleyip yeniden çalıştırın

**Komutlar**:
```bash
# Dry-run
airflow dags backfill --dry-run -s 2024-01-01 -e 2024-01-07 sales_etl

# Gerçek backfill
airflow dags backfill -s 2024-01-01 -e 2024-01-07 sales_etl
```

---

### Alıştırma 4: Connection ve Variable Yönetimi (Orta)
**Zorluk**: ⭐⭐ Orta
**Süre**: 20 dakika

**Görev**: WebUI ve CLI kullanarak connection ve variable yönetin:

**Connection Ekleyin**:
1. WebUI'dan PostgreSQL connection
   - ID: `my_postgres`
   - Host: `localhost`
   - Port: `5432`

2. CLI'dan BigQuery connection
   ```bash
   airflow connections add google_cloud_default \
     --conn-type google_cloud_platform \
     --conn-extra '{"project":"my-project"}'
   ```

**Variable Ekleyin**:
1. WebUI'dan: `env=development`
2. CLI'dan: `gcp_project_id=my-gcp-project`
3. DAG'de kullanın:
   ```python
   from airflow.models import Variable
   env = Variable.get("env")
   ```

**Test Edin**: DAG içinde connection ve variable kullanın

---

### Alıştırma 5: Debugging Senaryosu (Zor)
**Zorluk**: ⭐⭐⭐ Zor
**Süre**: 30 dakika

**Görev**: Aşağıdaki failed DAG'i debug edin:

**Senaryo**: `sales_pipeline` DAG'i failed durumda. Nedeni bulun ve düzeltin.

**Debug Adımları**:
1. **Grid View** → Failed task'ı bulun (kırmızı)
2. **Task Details** → Log'ları inceleyin
3. **Rendered Template** → Jinja template'in render edilmiş halini kontrol edin
4. **XCom Values** → Upstream task'lardan gelen veriyi kontrol edin
5. **Import Errors** → Admin → Import Errors'u kontrol edin
6. **CLI Test** → Task'ı manuel test edin:
   ```bash
   airflow tasks test sales_pipeline transform_data 2024-01-01
   ```

**Yaygın Hatalar**:
- Connection eksik/yanlış
- Variable undefined
- Python syntax error
- Resource unavailable (API down, file missing)
- Timeout

**Beklenen Çıktı**: Hatanın root cause'u ve çözümü

---

## Sık Sorulan Sorular (FAQ)

### WebUI Kullanımı

**S1: WebUI'a erişemiyorum, ne yapmalıyım?**
**C**: Şu adımları izleyin:
```bash
# 1. Webserver container çalışıyor mu?
docker ps | grep webserver

# 2. Port 8080 açık mı?
curl http://localhost:8080/health

# 3. Webserver log'larını kontrol et
docker logs airflow-webserver-1

# 4. Restart webserver
docker compose restart airflow-webserver
```

**S2: DAG listede görünmüyor, neden?**
**C**: Olası nedenler:
1. **Import Error**: Admin → Import Errors kontrol edin
2. **DAG Folder**: DAG dosyası `dags/` klasöründe mi?
3. **Parse Error**: Syntax hatası var mı?
4. **Scheduler**: Scheduler çalışıyor mu?

Debug:
```bash
# Import errors
airflow dags list-import-errors

# DAG'i manuel parse et
python dags/my_dag.py

# DAG listesi
airflow dags list
```

**S3: Task log'larını görüntüleyemiyorum?**
**C**:
- Log dosyaları oluştu mu? `logs/` klasörünü kontrol edin
- Docker volume mount doğru mu?
- Task gerçekten çalıştı mı? (Queued state'de olabilir)

**S4: Grid View çok yavaş yükleniyor?**
**C**:
- Çok fazla DAG run var. Auto-delete eski run'ları:
  ```python
  # airflow.cfg veya DAG params
  max_active_runs_per_dag = 3
  ```
- Database performance problemi olabilir
- Browser cache'i temizleyin

### DAG Yönetimi

**S5: DAG'i pause etmek ne işe yarar?**
**C**:
- Schedule'u durdurur (yeni run oluşmaz)
- Manuel trigger hala çalışır
- Mevcut running task'lar devam eder

**S6: Clear vs Delete farkı nedir?**
**C**:
- **Clear**: Task instance'ı siler ve yeniden çalıştırır (retry)
- **Delete**: DAG run'ı tamamen siler (geri getirilemez)

**S7: Mark Success ne zaman kullanmalıyım?**
**C**:
- Test/development için downstream'i tetiklemek
- Bilinen bir hatayı bypass etmek
- Emergency fix sonrası manuel onay

⚠️ **DİKKAT**: Production'da dikkatli kullanın, task gerçekten çalışmaz!

**S8: Backfill sırasında DAG pause olmalı mı?**
**C**: Tavsiye edilir:
- Pause edin → Scheduled run'lar oluşmasın
- Backfill yapın
- Bitince unpause edin

### Performance

**S9: WebUI çok yavaş, ne yapabilirim?**
**C**: Optimizasyon ipuçları:
```python
# 1. Eski task instance'ları temizle
airflow db clean --clean-before-timestamp 2024-01-01 --yes

# 2. DAG parse sıklığını azalt
# airflow.cfg
dag_dir_list_interval = 600  # 10 dakika

# 3. Auto-refresh'i kapat
# WebUI'da toggle'ı disable et
```

**S10: Çok fazla DAG var, nasıl organize ederim?**
**C**:
- **Tags kullan**: production, staging, etl, ml vb.
- **Owner belirle**: Takımlara göre filtrele
- **Klasör organize et**: `dags/etl/`, `dags/ml/`
- **Search**: `/` tuşu ile hızlı arama

### Troubleshooting

**S11: "Broken DAG" hatası alıyorum?**
**C**: DAG'de syntax veya import hatası var:
```bash
# Import errors listele
airflow dags list-import-errors

# DAG'i Python olarak çalıştır
python dags/my_dag.py
```

**S12: Task stuck in "queued" state?**
**C**:
- Worker çalışmıyor olabilir: `docker ps | grep worker`
- Pool limit dolmuş olabilir: Admin → Pools
- Max active tasks limit: `parallelism` arttırın

**S13: XCom data göremiyorum?**
**C**:
- Task return value var mı?
- Metadata database erişilebilir mi?
- Browse → XComs sayfasından kontrol edin

---

## İpuçları ve Püf Noktaları

### 💡 İpucu 1: Auto-refresh ile Live Monitoring
```
Grid View'da sağ üstteki "Auto-refresh" toggle'ı aktif edin.
Her 10 saniyede otomatik güncellenir. Long-running DAG'leri izlerken kullanışlı.
```

### 💡 İpucu 2: Bulk Operations
```
Grid View'da multiple task'ları seçip toplu clear/mark success yapabilirsiniz.
Shift tuşu ile range selection.
```

### 💡 İpucu 3: Quick Search
```
DAG listesinde "/" tuşu ile hızlıca arama yapın.
Tag, owner, DAG ID ile filtreleyin.
```

### 💡 İpucu 4: Rendered Template Debug
```
Task'a tıklayın → "Rendered Template" tab
Jinja variables'ın gerçek değerlerini görürsünüz:
{{ ds }} → 2024-01-01
{{ dag.dag_id }} → my_dag
```

### 💡 İpucu 5: Browser DevTools ile Debug
```
F12 → Network tab → XHR
API call'ları görebilirsiniz. Hata durumunda faydalı.
```

### 💡 İpucu 6: Task Duration Analysis
```
DAG Details → Task Duration view
Hangi task'ların ne kadar sürdüğünü görün.
Performance bottleneck'leri tespit edin.
```

### 💡 İpucu 7: Calendar View ile Pattern Analysis
```
DAG Details → Calendar view
Haftalık/aylık başarı/başarısızlık pattern'lerini görün.
Recurring issues'ları tespit edin.
```

---

## Referanslar

### Resmi Dokümantasyon
- [Airflow UI Guide](https://airflow.apache.org/docs/apache-airflow/stable/ui.html)
- [Managing Connections](https://airflow.apache.org/docs/apache-airflow/stable/howto/connection.html)
- [Using Variables](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/variables.html)

### Best Practices
- [Monitoring and Alerting](https://airflow.apache.org/docs/apache-airflow/stable/logging-monitoring/index.html)

---

## Sonraki Adımlar

- **[06-deployment-cicd.md](06-deployment-cicd.md)**: Deployment ve CI/CD
- **[07-bigquery-entegrasyonu.md](07-bigquery-entegrasyonu.md)**: BigQuery entegrasyonu
