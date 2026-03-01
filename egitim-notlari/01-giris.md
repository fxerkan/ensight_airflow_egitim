# Apache Airflow Giriş

> **Bu Bölümde Öğrenecekleriniz:**
> - Apache Airflow'un ne olduğunu ve neden kullanıldığını
> - Workflow orchestration kavramını
> - Airflow mimarisini ve temel bileşenleri
> - DAG (Directed Acyclic Graph) yapısını
> - Gerçek dünya kullanım senaryolarını
> - Airflow'un alternatifleriyle karşılaştırmasını

## İçindekiler
1. [Airflow Nedir](#airflow-nedir)
2. [Workflow Orchestration](#workflow-orchestration)
3. [Airflow Mimarisi](#airflow-mimarisi)
4. [DAG Kavramı](#dag-kavrami)
5. [Airflow Kullanım Senaryoları](#kullanim-senaryolari)
6. [Airflow Timeline](#airflow-timeline)
7. [Airflow vs Alternatifleri](#airflow-vs-alternatifleri)
8. [Pratik Alıştırmalar](#pratik-alıştırmalar)
9. [Sık Sorulan Sorular (FAQ)](#sik-sorulan-sorular)
10. [Referanslar](#referanslar)

---

## Airflow Nedir

**Apache Airflow**, veri pipeline'larını programatik olarak yazmak, planlamak ve izlemek için kullanılan açık kaynaklı bir **workflow orchestration** platformudur.

### Temel Özellikler

- **Python ile Kodlanır**: DAG'ler (Directed Acyclic Graphs) Python kodu olarak yazılır
- **Dinamik Pipeline'lar**: Kodla oluşturulduğu için dinamik ve esnek pipeline'lar yaratabilirsiniz
- **Zengin UI**: Web tabanlı kullanıcı arayüzü ile görselleştirme ve yönetim
- **Ölçeklenebilir**: Kubernetes, Celery gibi executor'larla yatay ölçeklenebilir
- **Genişletilebilir**: Plugin sistemi ile özelleştirilebilir
- **Aktif Topluluk**: 2000+ katkıda bulunan, geniş provider ekosistemi

### Airflow Architecture Diagram

![Airflow Architecture](../assets/airflow-architecture-basic.png)
*Kaynak: [Apache Airflow Official Documentation](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html)*

### Airflow Ne Değildir?

- **Veri streaming aracı değil**: Airflow batch işler için tasarlanmıştır (Kafka, Flink değil)
- **Veri işleme motoru değil**: Airflow iş akışını orkestra eder, veriyi işlemez (Spark, dbt gibi araçları tetikler)
- **Gerçek zamanlı işlem aracı değil**: En kısa schedule interval 1 dakikadır

---

## Workflow Orchestration

### Workflow Orchestration Nedir?

**Workflow Orchestration**, birden fazla görevi (task) belirli bir sıraya göre çalıştırma, izleme ve yönetme sürecidir.

### Neden Workflow Orchestration'a İhtiyaç Var?

**Geleneksel Yaklaşım Sorunları:**
```bash
# Cron ile scheduled jobs
0 2 * * * /scripts/extract_data.sh
15 2 * * * /scripts/transform_data.sh
30 2 * * * /scripts/load_data.sh
```

**Sorunlar:**
- ❌ Bağımlılık yönetimi yok (bir iş başarısız olursa diğerleri yine çalışır)
- ❌ Hata yönetimi ve retry mekanizması yok
- ❌ Görselleştirme ve izleme zor
- ❌ Dinamik pipeline'lar oluşturamazsınız
- ❌ Logları merkezi bir yerde toplayamazsınız

**Airflow ile Çözüm:**
```python
extract >> transform >> load  # Bağımlılık net
# Retry, alerting, logging, monitoring hepsi built-in
```

### Orchestration vs Execution

| **Orchestration (Airflow)** | **Execution (Spark, dbt)** |
|------------------------------|----------------------------|
| İşleri zamanlar ve tetikler | Veriyi işler |
| Bağımlılıkları yönetir | Hesaplama yapar |
| Hata durumunda yeniden dener | Transformasyon uygular |
| Logları toplar ve izler | Aggregate hesaplar |

**Birlikte Çalışma:**
```
Airflow → Spark job başlat
       → Transformation tamamlandı mı kontrol et
       → dbt run tetikle
       → BigQuery'e veri yükle
       → Slack'e bildirim gönder
```

---

## Airflow Mimarisi

### Temel Bileşenler

![Airflow Architecture](../assets/airflow-architecture-basic.png)

#### 1. **Scheduler**
- DAG'leri sürekli izler ve çalıştırılması gereken task'ları belirler
- Task'ları Executor'a gönderir
- Heartbeat mekanizması ile sağlık kontrolü yapar

**Sorumluluğu:**
```
DAG klasörünü tara → Yeni DAG var mı?
                  → Schedule zamanı geldi mi?
                  → Task'ı kuyruğa al
                  → Executor'a gönder
```

#### 2. **Executor**
- Task'ların nasıl çalıştırılacağını belirler
- Farklı executor tipleri vardır

**Executor Tipleri:**

| Executor | Kullanım | Ölçeklenebilirlik |
|----------|----------|-------------------|
| **SequentialExecutor** | Development, test | Düşük (1 task seferde) |
| **LocalExecutor** | Küçük üretim | Orta (multiprocess) |
| **CeleryExecutor** | Büyük üretim | Yüksek (distributed) |
| **KubernetesExecutor** | Cloud-native | Çok yüksek (dynamic pods) |

#### 3. **Web Server**
- Flask tabanlı web UI
- DAG'leri görselleştirme
- Task log'larını görüntüleme
- Manuel tetikleme ve yönetim

**Özellikler:**
- DAG grafiği görselleştirme
- Task instance log'ları
- Connection ve variable yönetimi
- RBAC (Role-Based Access Control)

#### 4. **Metadata Database**
- DAG'ler, task'lar, run'lar hakkında tüm bilgiyi saklar
- PostgreSQL, MySQL, SQLite destekler

**Saklanan Bilgiler:**
- DAG tanımları ve schedule bilgileri
- Task instance durumları (success, failed, running)
- Connection ve variable'lar
- Kullanıcı ve yetki bilgileri
- XCom verileri (task'lar arası veri paylaşımı)

#### 5. **Workers**
- Task'ları çalıştırır
- CeleryExecutor veya KubernetesExecutor ile kullanılır
- Paralel çalışabilir

#### 6. **Triggerer** (Airflow 2.2+)
- Async task'ları yönetir
- Sensor'ları verimli çalıştırır
- Resource kullanımını azaltır

### Çalışma Akışı

```
┌─────────────┐
│   DAG File  │  (Python kodu)
└──────┬──────┘
       │
       ▼
┌─────────────┐    DAG'i parse et
│  Scheduler  │────────────────────┐
└──────┬──────┘                    │
       │                           ▼
       │ Task kuyruğa al    ┌─────────────┐
       │                    │  Metadata   │
       ▼                    │  Database   │
┌─────────────┐             └─────────────┘
│  Executor   │                    ▲
└──────┬──────┘                    │
       │                           │
       │ Task çalıştır             │ Durum kaydet
       ▼                           │
┌─────────────┐                    │
│   Worker    │────────────────────┘
└─────────────┘
       │
       ▼
    [Logs]
```

**Adımlar:**
1. **Scheduler**, DAG dosyalarını tarar
2. **Metadata DB**'ye DAG bilgilerini kaydeder
3. Schedule zamanı gelen task'ları belirler
4. **Executor**'a task'ları gönderir
5. **Worker**, task'ı çalıştırır
6. Sonuç **Metadata DB**'ye kaydedilir
7. **Web Server**, durumu kullanıcıya gösterir

---

## DAG Kavramı

### DAG Nedir?

**DAG (Directed Acyclic Graph)** = Yönlendirilmiş Döngüsel Olmayan Grafik

**Özellikleri:**
- **Directed (Yönlendirilmiş)**: Task'lar arasında yön var (A → B)
- **Acyclic (Döngüsel Değil)**: Döngü yok (A → B → A yasak)
- **Graph (Grafik)**: Task'lar ve aralarındaki bağlantılar

### Görsel Örnek

```
     ┌─────────┐
     │  Start  │
     └────┬────┘
          │
     ┌────▼─────┐
     │ Extract  │
     └────┬─────┘
          │
     ┌────▼────────┐
     │  Transform  │
     └────┬────────┘
          │
     ┌────▼─────┐
     │   Load   │
     └────┬─────┘
          │
     ┌────▼────┐
     │   End   │
     └─────────┘
```

### Basit DAG Örneği

```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id='simple_etl',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
) as dag:

    extract = BashOperator(
        task_id='extract_data',
        bash_command='echo "Extracting data..."'
    )

    transform = BashOperator(
        task_id='transform_data',
        bash_command='echo "Transforming data..."'
    )

    load = BashOperator(
        task_id='load_data',
        bash_command='echo "Loading data..."'
    )

    # Dependency tanımlama
    extract >> transform >> load
```

### DAG Neden Acyclic (Döngüsel Olmayan)?

**❌ YANLIŞ (Döngü var):**
```python
task_a >> task_b >> task_c >> task_a  # Sonsuz döngü!
```

**✅ DOĞRU:**
```python
task_a >> task_b >> task_c  # Linear flow
```

### Paralel Task'lar

```python
from airflow.models import dag

with DAG(...) as dag:
    start = BashOperator(task_id='start', ...)

    task_1 = BashOperator(task_id='task_1', ...)
    task_2 = BashOperator(task_id='task_2', ...)
    task_3 = BashOperator(task_id='task_3', ...)

    end = BashOperator(task_id='end', ...)

    # Paralel çalışma
    start >> [task_1, task_2, task_3] >> end
```

**Görsel:**
```
        start
          │
    ┌─────┼─────┐
    │     │     │
  task1 task2 task3
    │     │     │
    └─────┼─────┘
          │
         end
```

---

## Kullanım Senaryoları

### 1. ETL/ELT Pipeline'ları

**Kullanım:**
- Veri kaynağından veri çekme (Extract)
- Veriyi dönüştürme (Transform)
- Hedefe yükleme (Load)

**Örnek:**
```
CSV/API → Staging (GCS) → Transform (dbt) → BigQuery → BI Tool
```

**Airflow Rolü:**
- API'yi tetikle ve veri çek
- dbt run çalıştır
- BigQuery'e yükleme işlemini başlat
- Data quality check'leri çalıştır
- Hata durumunda Slack'e bildirim gönder

### 2. Machine Learning Pipeline'ları

**Kullanım:**
- Model eğitimi
- Feature engineering
- Model deployment
- Batch prediction

**Örnek Pipeline:**
```
Veri Toplama → Feature Engineering → Model Training →
Model Evaluation → Model Deployment → Prediction
```

### 3. Data Warehouse Bakımı

**Kullanım:**
- Incremental load
- Partisyon yönetimi
- Tablo optimizasyonu
- Snapshot alma

**Örnek:**
```python
check_new_data >> load_incremental >>
optimize_partitions >> create_snapshot >> send_report
```

### 4. Raporlama ve Analiz

**Kullanım:**
- Günlük/haftalık raporlar
- Dashboard güncelleme
- Email/Slack raporları

**Örnek:**
```
BigQuery Query → CSV Export → GCS Upload →
Email Attachment → Slack Notification
```

### 5. Sistem Bakımı

**Kullanım:**
- Backup işlemleri
- Log temizleme
- Database maintenance

**Örnek:**
```
Database Backup → Upload to GCS →
Delete Old Backups → Send Success Email
```

### 6. Multi-Cloud Orchestration

**Kullanım:**
- GCP ↔ AWS veri transferi
- Hybrid cloud workflows
- Cloud cost optimization

**Örnek:**
```
GCS → Transfer to S3 → Trigger Lambda →
Load to Redshift → Update Dashboard
```

---

## Airflow Timeline

### Airflow'un Evrimi

```
2014  🚀 Airbnb'de Maxime Beauchemin tarafından oluşturuldu
      - Veri pipeline'larını yönetmek için internal proje

2015  📖 Open source olarak yayınlandı
      - GitHub'da Apache incubator projesine katıldı

2016  🎓 Apache Foundation üst düzey projesi oldu
      - Apache Airflow 1.0 release

2018  📈 Hızlı büyüme ve popülerlik
      - Airflow Summit başladı
      - 100+ contributor

2020  🔥 Airflow 2.0 Major Release
      - TaskFlow API (@task decorator)
      - High Availability Scheduler
      - Full REST API
      - Improved UI (React tabanlı)

2022  ☁️ Cloud adoption yaygınlaştı
      - AWS MWAA (Managed Workflows for Apache Airflow)
      - GCP Cloud Composer 2
      - Astronomer platform

2024  🚀 Airflow 2.8+ Modern Features
      - Dataset-based scheduling
      - Dynamic Task Mapping improvements
      - Better observability
      - 3000+ contributors
```

### Airflow Benimseme İstatistikleri

| Metrik | Değer |
|--------|-------|
| **GitHub Stars** | 35,000+ |
| **Contributors** | 3,000+ |
| **Provider Packages** | 80+ (AWS, GCP, Azure, Snowflake vb.) |
| **Docker Pulls** | 1 Billion+ |
| **Companies Using** | 10,000+ (Airbnb, Adobe, Robinhood, Twitter vb.) |
| **Slack Community** | 15,000+ members |

---

## Airflow Avantajları

### Neden Airflow?

| Özellik | Açıklama |
|---------|----------|
| **Kod ile Tanımlama** | Python kodu = version control, code review |
| **Dinamik Pipeline'lar** | Loop'lar, conditional logic kullanabilirsiniz |
| **Zengin Ecosystem** | 1000+ provider (AWS, GCP, Azure, Snowflake, dbt...) |
| **Görselleştirme** | Web UI ile real-time monitoring |
| **Hata Yönetimi** | Retry, alerting, SLA tracking |
| **Ölçeklenebilirlik** | Kubernetes, Celery ile horizontal scaling |
| **Topluluk Desteği** | Aktif Apache projesi, geniş dokümantasyon |

### Airflow vs Alternatifleri

#### Detaylı Karşılaştırma Tablosu

| Özellik | Airflow | Prefect | Dagster | Luigi | Temporal | Cron |
|---------|---------|---------|---------|-------|----------|------|
| **Dil** | Python | Python | Python | Python | Go/Java/Python | Bash/Any |
| **UI** | ⭐⭐⭐⭐⭐ Rich Web UI | ⭐⭐⭐⭐ Modern UI | ⭐⭐⭐⭐ Good UI | ⭐⭐ Basic | ⭐⭐⭐ Good | ❌ None |
| **Ölçeklenebilirlik** | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐ Good | ⭐⭐⭐⭐ Good | ⭐⭐ Limited | ⭐⭐⭐⭐⭐ Excellent | ⭐ Very Limited |
| **Kurulum** | Orta (Docker ile kolay) | Kolay | Orta | Kolay | Orta | Çok Kolay |
| **Topluluk** | 🟢 Very Large (3000+) | 🟡 Medium (500+) | 🟡 Medium (400+) | 🟠 Small | 🟢 Large | 🟢 Universal |
| **Provider Ecosystem** | 🟢 80+ providers | 🟡 20+ | 🟡 30+ | 🟠 Limited | 🟡 Growing | ❌ None |
| **Learning Curve** | Orta | Düşük | Yüksek | Düşük | Orta | Çok Düşük |
| **Best For** | Data pipelines, ETL | Modern Python apps | Data engineering | Simple workflows | Microservices | Simple scheduled tasks |
| **Cloud Native** | ✅ Yes (Composer, MWAA) | ✅ Yes (Prefect Cloud) | ✅ Yes (Dagster+) | ❌ No | ✅ Yes (Temporal Cloud) | ❌ No |
| **Dynamic DAGs** | ✅ Yes | ✅ Yes | ✅ Yes | ⚠️ Limited | ✅ Yes | ❌ No |
| **Retry/Backoff** | ✅ Built-in | ✅ Built-in | ✅ Built-in | ✅ Basic | ✅ Advanced | ❌ Manual |
| **Monitoring** | ✅ Extensive | ✅ Good | ✅ Good | ⚠️ Basic | ✅ Excellent | ❌ None |
| **Cost** | 🆓 Free (OSS) | 🆓 Free / 💰 Cloud | 🆓 Free / 💰 Plus | 🆓 Free | 🆓 Free / 💰 Cloud | 🆓 Free |

#### Kullanım Senaryolarına Göre Seçim

```
ETL/ELT Pipelines          → Airflow ⭐⭐⭐⭐⭐
ML Training Pipelines      → Airflow ⭐⭐⭐⭐⭐ | Prefect ⭐⭐⭐⭐
Data Engineering           → Dagster ⭐⭐⭐⭐⭐ | Airflow ⭐⭐⭐⭐⭐
Simple Scheduled Jobs      → Cron ⭐⭐⭐⭐⭐
Modern Python Apps         → Prefect ⭐⭐⭐⭐⭐
Microservices Workflows    → Temporal ⭐⭐⭐⭐⭐
Asset-Centric Workflows    → Dagster ⭐⭐⭐⭐⭐
Legacy Systems             → Luigi ⭐⭐⭐
```

#### Neden Airflow?

✅ **Mature & Proven**: 10+ yıllık production kullanımı
✅ **Rich Ecosystem**: 80+ provider package (AWS, GCP, Azure, Snowflake, dbt...)
✅ **Extensive Documentation**: Kapsamlı dokümantasyon ve örnekler
✅ **Large Community**: Stack Overflow, Slack, forums'ta aktif destek
✅ **Cloud Support**: Google Cloud Composer, AWS MWAA gibi managed servisler
✅ **Enterprise Ready**: RBAC, audit logs, secret management
✅ **Flexible**: Çok çeşitli use case'lerde kullanılabilir

---

## Pratik Alıştırmalar

### Alıştırma 1: Workflow Orchestration Kavramını Anlama (Kolay)
**Zorluk**: ⭐ Kolay
**Süre**: 10 dakika

**Görev**: Aşağıdaki senaryoda neden workflow orchestration'a ihtiyaç olduğunu açıklayın:

```
Senaryo: E-ticaret şirketi günlük satış raporu oluşturmak istiyor
Adımlar:
1. PostgreSQL'den sipariş verileri çek (05:00)
2. Redis'ten ürün bilgileri çek (05:15)
3. İki veriyi birleştir ve analiz et (05:30)
4. Raporu Excel'e çıkar (05:45)
5. Raporu email ile gönder (06:00)

Soru: Bu işi cron ile yönetmeye çalışırsak ne sorunlar yaşarız?
```

**Beklenen Çıktı**: 3-5 madde halinde cron yaklaşımının sorunlarını listeleyin

**İpuçları**:
- Bağımlılık yönetimi düşünün
- Hata durumlarını düşünün
- Monitoring ve logging düşünün

---

### Alıştırma 2: DAG Tasarımı (Orta)
**Zorluk**: ⭐⭐ Orta
**Süre**: 20 dakika

**Görev**: Aşağıdaki senaryoya DAG diagram çizin:

```
Senaryo: ML Model Training Pipeline
1. Veriyi 3 farklı kaynaktan çek (paralel):
   - API'den customer data
   - Database'den transactions
   - CSV'den product catalog
2. Veriyi temizle ve birleştir
3. Feature engineering yap
4. 2 farklı model eğit (paralel):
   - Random Forest
   - XGBoost
5. Model performanslarını karşılaştır
6. En iyi modeli deploy et
7. Slack'e bildirim gönder
```

**Beklenen Çıktı**: ASCII diagram veya çizim

**İpuçları**:
- Hangi task'lar paralel çalışabilir?
- Hangi task'lar birbirine bağımlı?
- Start ve End dummy task'ları ekleyin

---

### Alıştırma 3: Airflow vs Alternatif Seçimi (Orta)
**Zorluk**: ⭐⭐ Orta
**Süre**: 15 dakika

**Görev**: Aşağıdaki senaryolarda hangi aracı seçersiniz ve neden?

**Senaryo A**: Startup şirketi, 5 kişilik data team, basit ETL pipeline'ları
- Araç seçiminiz: ____________
- Neden: ____________

**Senaryo B**: Enterprise şirket, 50+ data engineer, karmaşık veri ambarı
- Araç seçiminiz: ____________
- Neden: ____________

**Senaryo C**: Sadece haftalık bir backup script'i çalıştırmanız gerekiyor
- Araç seçiminiz: ____________
- Neden: ____________

**Senaryo D**: Modern Python microservices mimarisi, event-driven workflows
- Araç seçiminiz: ____________
- Neden: ____________

---

### Alıştırma 4: Airflow Architecture Kavramını Pekiştirin (Zor)
**Zorluk**: ⭐⭐⭐ Zor
**Süre**: 30 dakika

**Görev**: Aşağıdaki production senaryosunda nasıl bir Airflow mimarisi kurarsınız?

```
Requirements:
- 100+ DAG
- 1000+ task/gün
- High availability gerekli
- Multi-cloud (AWS + GCP)
- Cost optimization önemli
- Security critical (healthcare data)
```

**Sorular**:
1. Hangi Executor'ı seçersiniz? (Sequential/Local/Celery/Kubernetes)
2. Database için ne kullanırsınız?
3. Worker scaling nasıl olacak?
4. Secret management nasıl yaparsınız?
5. Disaster recovery planınız ne olur?

**Beklenen Çıktı**: Architecture diagram + açıklamalar

---

## Sık Sorulan Sorular (FAQ)

### Genel Sorular

**S1: Airflow veri işleme aracı mı, yoksa orkestrasyon aracı mı?**
**C**: Airflow bir **orkestrasyon** aracıdır, veri işleme motoru değildir. Airflow, Spark, dbt, BigQuery gibi araçları tetikler ve yönetir, ama verileri kendisi işlemez.

```python
# ❌ YANLIŞ - Airflow içinde heavy computation
@task
def process_millions_of_rows():
    df = pd.read_csv("huge_file.csv")  # Millions of rows
    # Heavy pandas operations...

# ✅ DOĞRU - Airflow sadece tetikler
@task
def trigger_spark_job():
    SparkSubmitOperator(
        application="process_data.py",
        ...
    )
```

**S2: Airflow real-time/streaming için uygun mu?**
**C**: **Hayır**. Airflow **batch processing** için tasarlanmıştır. Minimum schedule interval 1 dakikadır. Real-time için Apache Kafka, Apache Flink, Spark Streaming kullanın.

**S3: Airflow ücretsiz mi?**
**C**: **Evet**, Airflow açık kaynak ve ücretsizdir. Ancak managed servisler ücretlidir:
- Google Cloud Composer: $300-1000+/month
- AWS MWAA: $400-1500+/month
- Astronomer: $1000+/month

**S4: Airflow'u tek makinede çalıştırabilir miyim?**
**C**: **Evet**. Development için LocalExecutor ile çalıştırabilirsiniz. Production için distributed setup önerilir.

**S5: DAG dosyalarını nasıl version control yapmalıyım?**
**C**: Git kullanın. DAG'ler Python kodu olduğu için Git ile mükemmel çalışır:
```bash
git add dags/
git commit -m "feat: Add customer ETL pipeline"
git push origin main
```

### Teknik Sorular

**S6: DAG'lerin parse edilme sıklığı nedir?**
**C**: Default 30 saniyede bir. `dag_dir_list_interval` parametresi ile değiştirilebilir.

**S7: Task'lar arası veri nasıl paylaşılır?**
**C**: **XCom** (Cross-Communication) kullanarak. Ancak küçük veriler için uygundur (<1MB). Büyük veriler için GCS/S3 kullanın.

```python
# Task 1: XCom push
@task
def extract():
    data = {'count': 100}
    return data  # Otomatik XCom push

# Task 2: XCom pull
@task
def process(data: dict):
    count = data['count']  # Otomatik XCom pull
```

**S8: DAG çalışırken güncelleyebilir miyim?**
**C**: **Evet**, ancak dikkatli olun. Running task'lar eski kod ile devam eder, yeni trigger'lar yeni kodu kullanır.

**S9: Failed task'ı nasıl yeniden çalıştırırım?**
**C**: WebUI'da task'a tıklayıp "Clear" yapın veya CLI'dan:
```bash
airflow tasks clear my_dag my_task --start-date 2024-01-01
```

**S10: Airflow logları nerede saklanır?**
**C**: Default olarak `logs/` dizininde. Production'da GCS/S3'e remote logging yapılır.

### Best Practices

**S11: Kaç tane DAG oluşturmalıyım?**
**C**: İş mantığına göre ayrı DAG'ler oluşturun:
- ✅ 1 DAG per business process
- ❌ 1 giant DAG for everything
- ❌ 100+ mini DAGs for every small task

**S12: Task timeout nasıl belirlerim?**
**C**: `execution_timeout` parametresi:
```python
task = BashOperator(
    task_id='long_task',
    bash_command='...',
    execution_timeout=timedelta(hours=2)
)
```

**S13: Production'da hangi executor kullanmalıyım?**
**C**:
- Küçük/orta scale: **CeleryExecutor**
- Cloud-native: **KubernetesExecutor**
- Dev/test: **LocalExecutor**
- Asla: **SequentialExecutor** (sadece test için)

**S14: DAG schedule interval nasıl test ederim?**
**C**: [crontab.guru](https://crontab.guru/) kullanın:
```
0 2 * * * → Her gün 02:00
0 */4 * * * → Her 4 saatte bir
0 9 * * 1-5 → Pazartesi-Cuma 09:00
```

**S15: Airflow monitoring nasıl yaparım?**
**C**:
- WebUI dashboard
- StatsD + Grafana
- Airflow REST API
- SLA alerts
- Email notifications

---

## İpuçları ve Püf Noktaları

### 💡 İpucu 1: Idempotent Task'lar Yazın
Task'larınız her çalıştırıldığında aynı sonucu vermeli:
```python
# ✅ İdempotent
DELETE FROM table WHERE date = '{{ ds }}';
INSERT INTO table SELECT * FROM source WHERE date = '{{ ds }}';

# ❌ Non-idempotent
INSERT INTO table SELECT * FROM source;  # Duplicate oluşturur
```

### 💡 İpucu 2: start_date Static Yapın
```python
# ✅ Static
start_date=datetime(2024, 1, 1)

# ❌ Dynamic (her parse'da değişir)
start_date=datetime.now()
```

### 💡 İpucu 3: catchup=False Kullanın (Yeni DAG'ler için)
```python
with DAG(
    dag_id='new_dag',
    start_date=datetime(2020, 1, 1),
    catchup=False  # Geçmiş tarihler için çalıştırma
):
    pass
```

### 💡 İpucu 4: Tags Kullanın
```python
tags=['production', 'etl', 'bigquery', 'daily']
# WebUI'da filtreleme kolaylaşır
```

### 💡 İpucu 5: Dokumentasyon Ekleyin
```python
dag.doc_md = """
# Sales ETL Pipeline

Bu DAG günlük satış verilerini işler.

**Owner**: Data Engineering
**SLA**: 2 hours
**Dependencies**: None
"""
```

---

## Referanslar

### Resmi Dokümantasyon
- [Apache Airflow Official Docs](https://airflow.apache.org/docs/)
- [Airflow GitHub Repository](https://github.com/apache/airflow)
- [Airflow Architecture Guide](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html)

### Blog ve Makaleler
- [Airflow Best Practices by Google Cloud](https://cloud.google.com/composer/docs/best-practices)
- [Astronomer - Airflow Guides](https://docs.astronomer.io/learn)
- [Medium - Airflow Tutorials](https://medium.com/tag/apache-airflow)

### Video Kaynaklar
- [Airflow Summit](https://airflowsummit.org/)
- [YouTube - Official Airflow Channel](https://www.youtube.com/@ApacheAirflow)

### Topluluk
- [Airflow Slack](https://apache-airflow.slack.com/)
- [Stack Overflow - Airflow Tag](https://stackoverflow.com/questions/tagged/airflow)

---

## Sonraki Adımlar

- **[02-kurulum.md](02-kurulum.md)**: Docker Compose ile Airflow kurulumu
- **[03-dag-gelistirme.md](03-dag-gelistirme.md)**: DAG yazma ve geliştirme
- **[04-operatorler.md](04-operatorler.md)**: Operator'ler ve kullanımları
