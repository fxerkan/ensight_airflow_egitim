# Google Cloud Credentials Kurulum Kılavuzu

## 1. Service Account Key Dosyası Oluşturma

### Google Cloud Console'da:

1. **Google Cloud Console**'a gidin: https://console.cloud.google.com
2. Projenizi seçin: `my-project-id`
3. **IAM & Admin** > **Service Accounts**'a gidin
4. **CREATE SERVICE ACCOUNT** butonuna tıklayın
5. Servis hesabı bilgilerini girin:
   - Name: `airflow-bigquery-sa`
   - Description: `Airflow BigQuery Service Account`
6. **CREATE AND CONTINUE** butonuna tıklayın
7. Gerekli rolleri ekleyin:
   - `BigQuery Admin` veya
   - `BigQuery Data Editor` + `BigQuery Job User`
8. **CONTINUE** ve **DONE** butonlarına tıklayın

### Service Account Key İndirme:

1. Oluşturduğunuz service account'a tıklayın
2. **KEYS** sekmesine gidin
3. **ADD KEY** > **Create new key** seçin
4. **JSON** formatını seçin
5. **CREATE** butonuna tıklayın
6. İndirilen JSON dosyasını şu klasöre kopyalayın:
   ```
   ../repo_local/ensight_airflow_egitim/credentials/gcp-key.json
   ```

## 2. Airflow'u Yeniden Başlatma

```bash
cd ../repo_local/ensight_airflow_egitim
docker-compose down
docker-compose up -d
```

## 3. Airflow UI'da Connection Oluşturma

### Yöntem 1: UI Üzerinden (Ekran görüntünüzdeki gibi)

1. Airflow UI'a gidin: http://localhost:8080
2. **Admin** > **Connections** menüsüne gidin
3. **+ (Add)** butonuna tıklayın
4. Formu şu şekilde doldurun:

**Connection Id:** `google_cloud_default`

**Connection Type:** `Google Bigquery`

**Description:** `Google BigQuery connection for my-project-id project`

**Extra:** (aşağıdaki JSON'u yapıştırın)

```json
{
  "extra__google_cloud_platform__project": "my-project-id",
  "extra__google_cloud_platform__key_path": "/opt/airflow/credentials/gcp-key.json",
  "extra__google_cloud_platform__scope": "https://www.googleapis.com/auth/cloud-platform",
  "extra__google_cloud_platform__num_retries": 5
}
```

5. **Save** butonuna tıklayın
6. **Test** butonuna tıklayarak connection'ı test edin

### Yöntem 2: Airflow CLI ile

Docker container içinde:

```bash
docker-compose exec airflow-webserver airflow connections add 'google_cloud_default' \
    --conn-type 'google_cloud_platform' \
    --conn-extra '{
        "extra__google_cloud_platform__project": "my-project-id",
        "extra__google_cloud_platform__key_path": "/opt/airflow/credentials/gcp-key.json",
        "extra__google_cloud_platform__scope": "https://www.googleapis.com/auth/cloud-platform",
        "extra__google_cloud_platform__num_retries": 5
    }'
```

### Yöntem 3: Python ile (DAG içinde)

```python
from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryExecuteQueryOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'bigquery_test_dag',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
) as dag:

    test_query = BigQueryExecuteQueryOperator(
        task_id='test_bigquery_connection',
        sql='''
            SELECT
                COUNT(*) as row_count
            FROM
                `{GCP_PROJECT_ID}.{GCP_DATASET_ID}.customers`
            LIMIT 1
        ''',
        use_legacy_sql=False,
        gcp_conn_id='google_cloud_default',
    )
```

## 4. Connection Test

Connection'ı test etmek için basit bir DAG oluşturun ve çalıştırın.

## Güvenlik Notları

⚠️ **ÖNEMLİ:**

- `gcp-key.json` dosyası hassas bilgiler içerir
- Bu dosyayı asla Git'e eklemeyin
- `.gitignore` dosyası zaten eklenmiştir
- Production ortamında Secret Manager kullanın

## Alternatif: Environment Variable ile

Eğer JSON dosyası yerine environment variable kullanmak isterseniz:

1. `.env` dosyasına ekleyin:

```bash
GCP_KEYFILE_DICT='{"type":"service_account","project_id":"my-project-id",...}'
```

2. Extra alanında:

```json
{
  "extra__google_cloud_platform__keyfile_dict": "${GCP_KEYFILE_DICT}"
}
```

## Sorun Giderme

### Connection Test Başarısız Olursa:

1. JSON dosyasının doğru yerde olduğunu kontrol edin:

   ```bash
   docker-compose exec airflow-webserver ls -la /opt/airflow/credentials/
   ```
2. JSON dosyasının geçerli olduğunu kontrol edin:

   ```bash
   docker-compose exec airflow-webserver cat /opt/airflow/credentials/gcp-key.json | python -m json.tool
   ```
3. Service Account'un gerekli izinlere sahip olduğunu kontrol edin
4. Airflow logs'u kontrol edin:

   ```bash
   docker-compose logs airflow-webserver
   ```
