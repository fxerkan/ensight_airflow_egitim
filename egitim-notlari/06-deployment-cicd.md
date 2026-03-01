# Deployment ve CI/CD

## İçindekiler
1. [Deployment Stratejisi](#deployment-stratejisi)
2. [Git Workflow](#git-workflow)
3. [Azure DevOps Pipeline](#azure-devops-pipeline)
4. [GitHub Actions](#github-actions)
5. [Cloud Composer Deployment](#cloud-composer-deployment)
6. [Best Practices](#best-practices)
7. [Referanslar](#referanslar)

---

## Deployment Stratejisi

### Environment'lar

```
Development → Testing → Staging → Production
```

| Environment | Amaç | Özellikler |
|-------------|------|------------|
| **Development** | Geliştirme ve test | Local Docker, catchup=False, küçük veri |
| **Testing** | Automated tests | CI/CD pipeline, test data |
| **Staging** | Pre-production test | Production benzeri, gerçek data subset |
| **Production** | Canlı sistem | Full scale, monitoring, alerting |

### Environment Konfigürasyonu

```python
import os

ENV = os.getenv('AIRFLOW_ENV', 'development')

if ENV == 'production':
    DATASET = 'prod_sales_datamart'
    SCHEDULE = '0 2 * * *'  # Daily 02:00
    CATCHUP = False
    RETRIES = 3
elif ENV == 'staging':
    DATASET = 'staging_sales_datamart'
    SCHEDULE = '0 4 * * *'  # Daily 04:00
    CATCHUP = False
    RETRIES = 2
else:  # development
    DATASET = 'dev_sales_datamart'
    SCHEDULE = None  # Manuel trigger only
    CATCHUP = False
    RETRIES = 1

with DAG(
    dag_id=f'sales_etl_{ENV}',
    schedule_interval=SCHEDULE,
    default_args={
        'retries': RETRIES,
        ...
    }
):
    pass
```

---

## Git Workflow

### Branch Stratejisi (GitFlow)

```
main (production)
  ↑
develop
  ↑
feature/new-dag
feature/fix-bug
```

**Branches:**
- `main`: Production code
- `develop`: Development integration
- `feature/*`: Yeni özellikler
- `hotfix/*`: Acil production fix'leri
- `release/*`: Release hazırlığı

### Commit Mesajları

```bash
# ✅ DOĞRU
git commit -m "feat: Add customer dimension to sales datamart"
git commit -m "fix: Resolve BigQuery schema mismatch in sales_etl"
git commit -m "docs: Update README with deployment instructions"

# ❌ YANLIŞ
git commit -m "updates"
git commit -m "fix"
git commit -m "changes"
```

**Conventional Commits:**
- `feat`: Yeni özellik
- `fix`: Bug fix
- `docs`: Dokümantasyon
- `refactor`: Code refactoring
- `test`: Test ekleme
- `chore`: Bakım işleri

### Pull Request Process

1. Feature branch oluştur
   ```bash
   git checkout -b feature/new-sales-report
   ```

2. Değişiklikleri yap ve commit et
   ```bash
   git add dags/new_sales_report.py
   git commit -m "feat: Add daily sales summary report DAG"
   ```

3. Push to remote
   ```bash
   git push origin feature/new-sales-report
   ```

4. Pull Request oluştur
   - Title: `feat: Add daily sales summary report`
   - Description: Detaylı açıklama, test sonuçları

5. Code Review
   - En az 1 reviewer approval

6. Merge to develop
   ```bash
   git checkout develop
   git merge feature/new-sales-report
   ```

---

## Azure DevOps Pipeline

### azure-pipelines.yml

```yaml
trigger:
  branches:
    include:
      - main
      - develop
  paths:
    include:
      - dags/*
      - plugins/*
      - requirements.txt

pool:
  vmImage: 'ubuntu-latest'

variables:
  - group: airflow-variables  # Variable group

stages:
  - stage: Test
    jobs:
      - job: UnitTests
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '3.10'

          - script: |
              pip install -r requirements.txt
              pip install pytest pytest-cov
            displayName: 'Install dependencies'

          - script: |
              pytest tests/ --cov=dags --cov-report=xml
            displayName: 'Run unit tests'

          - task: PublishCodeCoverageResults@1
            inputs:
              codeCoverageTool: 'Cobertura'
              summaryFileLocation: 'coverage.xml'

      - job: DAGValidation
        steps:
          - script: |
              pip install apache-airflow==2.8.1
              python -m py_compile dags/*.py
            displayName: 'Validate DAG syntax'

          - script: |
              python scripts/validate_dags.py
            displayName: 'Validate DAG structure'

  - stage: DeployStaging
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/develop'))
    jobs:
      - deployment: DeployToStaging
        environment: 'airflow-staging'
        strategy:
          runOnce:
            deploy:
              steps:
                - task: gcloud@2
                  inputs:
                    command: 'composer'
                    arguments: 'environments storage dags import
                      --environment=airflow-staging
                      --location=us-central1
                      --source=dags/'

  - stage: DeployProduction
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: DeployToProduction
        environment: 'airflow-production'
        strategy:
          runOnce:
            deploy:
              steps:
                - task: gcloud@2
                  inputs:
                    command: 'composer'
                    arguments: 'environments storage dags import
                      --environment=airflow-prod
                      --location=us-central1
                      --source=dags/'

                - script: |
                    # Notify team
                    curl -X POST $(SLACK_WEBHOOK_URL) \
                      -H 'Content-Type: application/json' \
                      -d '{"text":"Airflow DAGs deployed to production"}'
                  displayName: 'Send Slack notification'
```

### DAG Validation Script

`scripts/validate_dags.py`:

```python
"""DAG validation script for CI/CD"""
import os
import sys
from airflow.models import DagBag

def validate_dags():
    """Validate all DAGs"""
    dag_bag = DagBag(dag_folder='dags/', include_examples=False)

    if dag_bag.import_errors:
        print("❌ DAG Import Errors:")
        for filename, error in dag_bag.import_errors.items():
            print(f"\n{filename}:")
            print(error)
        sys.exit(1)

    print(f"✅ {len(dag_bag.dags)} DAG(s) validated successfully")

    # Check for circular dependencies
    for dag_id, dag in dag_bag.dags.items():
        try:
            dag.test_cycle()
        except Exception as e:
            print(f"❌ Circular dependency in {dag_id}: {e}")
            sys.exit(1)

    print("✅ No circular dependencies found")
    return 0

if __name__ == '__main__':
    sys.exit(validate_dags())
```

---

## GitHub Actions

### .github/workflows/airflow-ci.yml

```yaml
name: Airflow CI/CD

on:
  push:
    branches: [main, develop]
    paths:
      - 'dags/**'
      - 'plugins/**'
      - 'requirements.txt'
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov flake8

      - name: Lint with flake8
        run: |
          flake8 dags/ --max-line-length=120

      - name: Test DAG syntax
        run: |
          python -m py_compile dags/*.py

      - name: Run unit tests
        run: |
          pytest tests/ --cov=dags --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  deploy-staging:
    needs: test
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}

      - name: Deploy to Staging
        run: |
          gsutil -m rsync -r -d dags/ \
            gs://us-central1-airflow-staging-*/dags/

  deploy-production:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://airflow-prod.example.com
    steps:
      - uses: actions/checkout@v3

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}

      - name: Deploy to Production
        run: |
          gsutil -m rsync -r -d dags/ \
            gs://us-central1-airflow-prod-*/dags/

      - name: Notify Slack
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Airflow DAGs deployed to production'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## Cloud Composer Deployment

### GCS Sync ile Deployment

```bash
# Development → Staging
gsutil -m rsync -r -d dags/ \
  gs://us-central1-airflow-staging-abc123/dags/

# Staging → Production
gsutil -m rsync -r -d dags/ \
  gs://us-central1-airflow-prod-xyz789/dags/
```

**Flags:**
- `-m`: Multithread (paralel upload)
- `-r`: Recursive
- `-d`: Delete removed files

### Environment Variables

```bash
# Staging environment variables güncelle
gcloud composer environments update airflow-staging \
  --location us-central1 \
  --update-env-variables \
    ENV=staging,\
    GCP_PROJECT_ID=my-project-staging

# Production
gcloud composer environments update airflow-prod \
  --location us-central1 \
  --update-env-variables \
    ENV=production,\
    GCP_PROJECT_ID=my-project-prod
```

### Python Packages

```bash
# requirements.txt'den package'ları kur
gcloud composer environments update airflow-prod \
  --location us-central1 \
  --update-pypi-packages-from-file requirements.txt
```

### Airflow Config Override

```bash
# Airflow config güncelle
gcloud composer environments update airflow-prod \
  --location us-central1 \
  --update-airflow-configs \
    core-parallelism=64,\
    core-max_active_runs_per_dag=3
```

---

## Best Practices

### 1. Environment Separation

```python
# ✅ DOĞRU - Environment variables
GCP_PROJECT = os.getenv('GCP_PROJECT_ID')
DATASET = os.getenv('DATASET_NAME')

# ❌ YANLIŞ - Hardcoded
GCP_PROJECT = 'my-prod-project'
DATASET = 'prod_dataset'
```

### 2. Secrets Management

```bash
# Google Secret Manager kullan
gcloud composer environments update airflow-prod \
  --location us-central1 \
  --update-env-variables \
    AIRFLOW__SECRETS__BACKEND=airflow.providers.google.cloud.secrets.secret_manager.CloudSecretManagerBackend,\
    AIRFLOW__SECRETS__BACKEND_KWARGS='{"project_id":"my-project"}'
```

**Secret'ları sakla:**
```bash
echo -n "my-api-key" | gcloud secrets create api-key --data-file=-
```

**DAG'de kullan:**
```python
from airflow.models import Variable

api_key = Variable.get("api-key")  # Secret Manager'dan gelir
```

### 3. DAG Versioning

```python
# ✅ DOĞRU - Version in DAG ID
with DAG(
    dag_id='sales_etl_v2',  # Version suffix
    ...
):
    pass

# Veya Git commit hash
DAG_VERSION = os.getenv('GIT_COMMIT_SHA', 'local')[:7]

with DAG(
    dag_id=f'sales_etl_{DAG_VERSION}',
    ...
):
    pass
```

### 4. Backward Compatibility

```python
# Schema evolution destekli
load_data = GCSToBigQueryOperator(
    task_id='load',
    schema_update_options=[
        'ALLOW_FIELD_ADDITION',      # Yeni field eklenebilir
        'ALLOW_FIELD_RELAXATION'     # REQUIRED → NULLABLE
    ],
    write_disposition='WRITE_APPEND'
)
```

### 5. Rollback Stratejisi

```bash
# Eski versiyonu geri yükle
git checkout v1.2.3
gsutil -m rsync -r -d dags/ gs://airflow-prod/dags/

# Veya specific DAG'i geri al
git show v1.2.3:dags/sales_etl.py > dags/sales_etl.py
gsutil cp dags/sales_etl.py gs://airflow-prod/dags/
```

### 6. Monitoring Post-Deployment

**Deployment sonrası kontroller:**

```bash
# 1. DAG import errors
gcloud composer environments run airflow-prod \
  --location us-central1 \
  dags list-import-errors

# 2. DAG listesi
gcloud composer environments run airflow-prod \
  --location us-central1 \
  dags list

# 3. DAG pause durumu
gcloud composer environments run airflow-prod \
  --location us-central1 \
  dags unpause sales_etl
```

### 7. Automated Testing

**tests/test_dags.py:**

```python
import pytest
from airflow.models import DagBag

def test_no_import_errors():
    """Test that all DAGs can be imported"""
    dag_bag = DagBag(include_examples=False)
    assert len(dag_bag.import_errors) == 0

def test_dag_has_tags():
    """Test that all DAGs have tags"""
    dag_bag = DagBag(include_examples=False)
    for dag_id, dag in dag_bag.dags.items():
        assert len(dag.tags) > 0, f"{dag_id} has no tags"

def test_dag_has_owner():
    """Test that all DAGs have owner"""
    dag_bag = DagBag(include_examples=False)
    for dag_id, dag in dag_bag.dags.items():
        assert dag.default_args.get('owner') is not None

def test_sales_etl_tasks():
    """Test sales_etl DAG structure"""
    dag_bag = DagBag(include_examples=False)
    dag = dag_bag.get_dag('sales_etl')

    assert dag is not None
    assert len(dag.tasks) >= 10
    assert 'extract' in [t.task_id for t in dag.tasks]
```

### 8. Blue-Green Deployment

```python
# V1 (eski) ve V2 (yeni) paralel çalışır
with DAG(
    dag_id='sales_etl_v1',
    schedule_interval='0 2 * * *',
    ...
):
    # Eski logic

with DAG(
    dag_id='sales_etl_v2',
    schedule_interval='0 3 * * *',  # 1 saat sonra
    ...
):
    # Yeni logic

# V2 test edildikten sonra V1'i pause et
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Tüm testler pass ediyor
- [ ] Code review yapıldı
- [ ] DAG syntax validate edildi
- [ ] Environment variables kontrol edildi
- [ ] Secrets yapılandırıldı
- [ ] Dokümantasyon güncellendi
- [ ] Rollback planı hazır

### Deployment

- [ ] Staging'e deploy et
- [ ] Staging'de test et
- [ ] Production'a deploy et
- [ ] DAG import errors kontrol et
- [ ] İlk run'ı izle

### Post-Deployment

- [ ] Monitoring dashboard'u kontrol et
- [ ] Log'ları incele
- [ ] SLA'ları kontrol et
- [ ] Stakeholder'lara bildir
- [ ] Deployment dokümante et

---

## Referanslar

### CI/CD
- [Astronomer - CI/CD for Airflow](https://docs.astronomer.io/learn/ci-cd)
- [GitHub Actions for Airflow](https://github.com/apache/airflow/tree/main/.github/workflows)

### Cloud Composer
- [Deploying DAGs to Cloud Composer](https://cloud.google.com/composer/docs/how-to/using/managing-dags)
- [Environment Variables](https://cloud.google.com/composer/docs/how-to/managing/environment-variables)

### Best Practices
- [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)

---

## Environment Separation Architecture

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        DEVELOPMENT                               │
│  ┌────────────┐   ┌────────────┐   ┌─────────────┐            │
│  │ Developer  │──▶│ Local      │──▶│ Feature     │            │
│  │ Machine    │   │ Docker     │   │ Branch      │            │
│  └────────────┘   └────────────┘   └─────────────┘            │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        CI/CD PIPELINE                            │
│  ┌────────────┐   ┌────────────┐   ┌─────────────┐            │
│  │ Unit       │──▶│ Integration│──▶│ DAG         │            │
│  │ Tests      │   │ Tests      │   │ Validation  │            │
│  └────────────┘   └────────────┘   └─────────────┘            │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                   ┌───────────┴───────────┐
                   │                       │
                   ▼                       ▼
    ┌──────────────────────┐   ┌──────────────────────┐
    │     STAGING          │   │    PRODUCTION        │
    │                      │   │                      │
    │ • Test data          │   │ • Real data          │
    │ • Manual testing     │   │ • Auto-scaling       │
    │ • QA approval        │   │ • HA setup           │
    │ • Performance test   │   │ • 24/7 monitoring    │
    └──────────────────────┘   └──────────────────────┘
```

### Resource Allocation

| Environment | CPU | RAM | Storage | Database | Executors |
|-------------|-----|-----|---------|----------|-----------|
| **Development** | 2-4 cores | 4-8 GB | 20 GB | SQLite/Postgres (local) | LocalExecutor |
| **Staging** | 4-8 cores | 8-16 GB | 100 GB | Postgres (managed) | CeleryExecutor (2-4 workers) |
| **Production** | 16+ cores | 32+ GB | 500+ GB | Postgres HA cluster | CeleryExecutor (10+ workers) |

---

## Secrets Management Deep Dive

### HashiCorp Vault Integration

**Setup:**

```yaml
# docker-compose.yaml
environment:
  AIRFLOW__SECRETS__BACKEND: airflow.providers.hashicorp.secrets.vault.VaultBackend
  AIRFLOW__SECRETS__BACKEND_KWARGS: |
    {
      "connections_path": "airflow/connections",
      "variables_path": "airflow/variables",
      "url": "http://vault:8200",
      "token": "${VAULT_TOKEN}"
    }
```

**Store secrets:**

```bash
# Vault'a secret ekle
vault kv put airflow/connections/google_cloud_default \
  conn_type=google_cloud_platform \
  keyfile_path=/path/to/keyfile.json

# DAG'de kullan (otomatik Vault'tan çeker)
from airflow.hooks.base import BaseHook
conn = BaseHook.get_connection('google_cloud_default')
```

### AWS Secrets Manager

```yaml
environment:
  AIRFLOW__SECRETS__BACKEND: airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend
  AIRFLOW__SECRETS__BACKEND_KWARGS: |
    {
      "connections_prefix": "airflow/connections",
      "variables_prefix": "airflow/variables",
      "profile_name": "default"
    }
```

```bash
# AWS CLI ile secret ekle
aws secretsmanager create-secret \
  --name airflow/connections/my_db \
  --secret-string '{"conn_type":"postgres","host":"db.example.com","login":"user","password":"pass"}'
```

### GCP Secret Manager

```yaml
environment:
  AIRFLOW__SECRETS__BACKEND: airflow.providers.google.cloud.secrets.secret_manager.CloudSecretManagerBackend
  AIRFLOW__SECRETS__BACKEND_KWARGS: |
    {
      "connections_prefix": "airflow-connections",
      "variables_prefix": "airflow-variables",
      "project_id": "my-gcp-project"
    }
```

```bash
# gcloud ile secret ekle
echo -n "my-api-key" | gcloud secrets create airflow-variables-api-key --data-file=-

# DAG'de kullan
from airflow.models import Variable
api_key = Variable.get("api-key")  # Otomatik Secret Manager'dan gelir
```

---

## Blue-Green Deployment

### Strategy Açıklaması

**Blue-Green deployment:** Yeni version (green) hazırlanırken eski version (blue) çalışmaya devam eder. Test edildikten sonra traffic green'e geçer.

```
BEFORE:
┌─────────┐
│  BLUE   │ ◀── 100% traffic
│ (v1.0)  │
└─────────┘

DURING:
┌─────────┐
│  BLUE   │ ◀── 100% traffic
│ (v1.0)  │
└─────────┘
┌─────────┐
│  GREEN  │ ◀── Testing
│ (v2.0)  │
└─────────┘

AFTER:
┌─────────┐
│  BLUE   │     (Standby for rollback)
│ (v1.0)  │
└─────────┘
┌─────────┐
│  GREEN  │ ◀── 100% traffic
│ (v2.0)  │
└─────────┘
```

### Implementation (Cloud Composer)

```bash
# 1. Create green environment
gcloud composer environments create airflow-green \
  --location us-central1 \
  --airflow-version 2.8.1 \
  --node-count 3

# 2. Deploy DAGs to green
gsutil -m rsync -r -d dags/ gs://us-central1-airflow-green-*/dags/

# 3. Test green environment
gcloud composer environments run airflow-green \
  --location us-central1 \
  dags test my_dag 2024-01-01

# 4. Switch traffic (update DNS or load balancer)
# Point airflow.company.com → green environment

# 5. Monitor for 24-48 hours

# 6. Delete blue if successful
gcloud composer environments delete airflow-blue --location us-central1
```

---

## Canary Deployment

### Gradual Rollout

```
Phase 1: 5% traffic to new version
┌─────────┐
│  OLD    │ ◀── 95%
│ (v1.0)  │
└─────────┘
┌─────────┐
│  NEW    │ ◀── 5%
│ (v2.0)  │
└─────────┘

Phase 2: 25% traffic
OLD: 75%, NEW: 25%

Phase 3: 50% traffic
OLD: 50%, NEW: 50%

Phase 4: 100% traffic (rollout complete)
┌─────────┐
│  NEW    │ ◀── 100%
│ (v2.0)  │
└─────────┘
```

### Automated Rollback

```python
# canary_rollout.py

import time
from monitoring import get_error_rate

def canary_rollout():
    phases = [5, 25, 50, 100]

    for traffic_percent in phases:
        print(f"Rolling out to {traffic_percent}%...")

        # Update load balancer
        update_traffic_split(new_version_percent=traffic_percent)

        # Monitor for 30 minutes
        time.sleep(1800)

        error_rate = get_error_rate()

        if error_rate > 0.05:  # >5% error rate
            print(f"Error rate {error_rate:.2%} too high! Rolling back...")
            update_traffic_split(new_version_percent=0)
            return False

        print(f"Phase {traffic_percent}% successful")

    print("Canary rollout completed successfully!")
    return True
```

---

## Docker Image Management

### Custom Airflow Image

**Dockerfile:**

```dockerfile
FROM apache/airflow:2.8.1-python3.10

# Install system dependencies
USER root
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Copy requirements
COPY requirements.txt /requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /requirements.txt

# Copy DAGs, plugins
COPY --chown=airflow:root dags/ /opt/airflow/dags/
COPY --chown=airflow:root plugins/ /opt/airflow/plugins/

# Copy config
COPY --chown=airflow:root config/airflow.cfg /opt/airflow/airflow.cfg
```

**requirements.txt:**

```
apache-airflow-providers-google==10.13.1
apache-airflow-providers-amazon==8.15.0
apache-airflow-providers-snowflake==5.1.0
pandas==2.1.4
numpy==1.26.2
```

**Build and Push:**

```bash
# Build image
docker build -t mycompany/airflow:2.8.1 .

# Tag for registry
docker tag mycompany/airflow:2.8.1 gcr.io/my-project/airflow:2.8.1

# Push to GCR
docker push gcr.io/my-project/airflow:2.8.1

# Or ECR (AWS)
docker tag mycompany/airflow:2.8.1 123456789.dkr.ecr.us-east-1.amazonaws.com/airflow:2.8.1
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/airflow:2.8.1
```

### Image Scanning

```bash
# Scan with Trivy
trivy image mycompany/airflow:2.8.1

# Scan with Snyk
snyk container test mycompany/airflow:2.8.1

# Scan with Clair
clair-scanner --ip $(hostname -i) mycompany/airflow:2.8.1
```

---

## DAG Testing Strategy

### Unit Tests

**tests/test_dag_structure.py:**

```python
import pytest
from airflow.models import DagBag

@pytest.fixture
def dagbag():
    return DagBag(dag_folder='dags/', include_examples=False)

def test_no_import_errors(dagbag):
    """Test that all DAGs load without errors"""
    assert len(dagbag.import_errors) == 0, f"Import errors: {dagbag.import_errors}"

def test_all_dags_have_tags(dagbag):
    """Test that all DAGs have tags"""
    for dag_id, dag in dagbag.dags.items():
        assert len(dag.tags) > 0, f"{dag_id} has no tags"

def test_all_dags_have_owner(dagbag):
    """Test that all DAGs have owner"""
    for dag_id, dag in dagbag.dags.items():
        owner = dag.default_args.get('owner')
        assert owner is not None, f"{dag_id} has no owner"
        assert owner != 'airflow', f"{dag_id} uses default owner"

def test_specific_dag_structure(dagbag):
    """Test sales_etl DAG structure"""
    dag = dagbag.get_dag('sales_etl')
    assert dag is not None
    assert len(dag.tasks) >= 5

    task_ids = [t.task_id for t in dag.tasks]
    assert 'extract' in task_ids
    assert 'transform' in task_ids
    assert 'load' in task_ids
```

### Integration Tests

**tests/test_bigquery_integration.py:**

```python
import pytest
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator

def test_bigquery_connection():
    """Test BigQuery connection works"""
    from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook

    hook = BigQueryHook(gcp_conn_id='google_cloud_default')
    result = hook.get_first("SELECT 1 as test")

    assert result[0] == 1

@pytest.mark.integration
def test_bigquery_query_execution():
    """Test BigQuery query execution"""
    from datetime import datetime

    operator = BigQueryInsertJobOperator(
        task_id='test_query',
        configuration={
            "query": {
                "query": "SELECT COUNT(*) as cnt FROM `project.dataset.table` LIMIT 1",
                "useLegacySql": False
            }
        }
    )

    # Mock context
    context = {'execution_date': datetime(2024, 1, 1)}

    result = operator.execute(context)
    assert result is not None
```

### pytest Fixtures

**tests/conftest.py:**

```python
import pytest
from airflow.models import DagBag, Connection
from airflow import settings

@pytest.fixture(scope='session')
def dagbag():
    return DagBag(dag_folder='dags/', include_examples=False)

@pytest.fixture
def test_connection():
    """Create test connection"""
    conn = Connection(
        conn_id='test_connection',
        conn_type='postgres',
        host='localhost',
        schema='testdb',
        login='testuser',
        password='testpass'
    )

    session = settings.Session()
    session.add(conn)
    session.commit()

    yield conn

    # Cleanup
    session.delete(conn)
    session.commit()
```

---

## Monitoring ve Observability

### Key Metrics

| Category | Metric | Description | Threshold |
|----------|--------|-------------|-----------|
| **Scheduler** | `scheduler.heartbeat` | Scheduler alive | < 30s |
| | `dag.processing.total_parse_time` | DAG parse time | < 60s |
| | `dag_file_refresh_error` | DAG parse errors | = 0 |
| **Tasks** | `task_instance.duration.<dag_id>.<task_id>` | Task execution time | Baseline + 50% |
| | `task_instance.failures` | Failed tasks | < 5/hour |
| | `zombies_killed` | Zombie tasks | = 0 |
| **Executor** | `executor.open_slots` | Available slots | > 2 |
| | `executor.queued_tasks` | Queued tasks | < 100 |
| **Database** | `dag_processing.last_duration` | DB query time | < 1s |
| **System** | CPU usage | CPU utilization | < 80% |
| | Memory usage | RAM utilization | < 85% |
| | Disk usage | Disk space | < 80% |

### Alerting Rules

**prometheus/alert_rules.yml:**

```yaml
groups:
  - name: airflow_alerts
    interval: 30s
    rules:
      - alert: SchedulerDown
        expr: up{job="airflow-scheduler"} == 0
        for: 5m
        annotations:
          summary: "Airflow scheduler is down"
          description: "Scheduler has been down for 5 minutes"

      - alert: HighTaskFailureRate
        expr: rate(airflow_task_instance_failures[5m]) > 0.1
        for: 10m
        annotations:
          summary: "High task failure rate"
          description: "Task failure rate > 10% for 10 minutes"

      - alert: DiskSpaceLow
        expr: node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.2
        for: 5m
        annotations:
          summary: "Low disk space"
          description: "Less than 20% disk space remaining"
```

### Dashboard Setup

**Grafana dashboard example queries:**

```promql
# Task duration (p95)
histogram_quantile(0.95,
  rate(airflow_task_duration_bucket{dag_id="sales_etl"}[5m])
)

# Task success rate
sum(rate(airflow_task_instance_success[5m])) /
sum(rate(airflow_task_instance_total[5m]))

# Scheduler lag
airflow_scheduler_lag_seconds

# Queue size
airflow_executor_queued_tasks
```

---

## Deployment Checklist (50+ Items)

### Pre-Deployment

#### Code Quality
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Code coverage > 80%
- [ ] Linting passed (flake8, black)
- [ ] Type checking passed (mypy)
- [ ] Security scan passed (bandit)
- [ ] Dependency vulnerability scan passed

#### Code Review
- [ ] PR approved by 2+ reviewers
- [ ] Architecture review completed
- [ ] Performance impact assessed
- [ ] Breaking changes documented
- [ ] Migration script prepared (if schema changes)

#### Configuration
- [ ] Environment variables documented
- [ ] Secrets migrated to secret backend
- [ ] Connection IDs documented
- [ ] DAG parameters validated
- [ ] airflow.cfg reviewed
- [ ] Resource limits set (CPU, memory)

#### Documentation
- [ ] README updated
- [ ] CHANGELOG updated
- [ ] DAG documentation (doc_md) written
- [ ] Runbook created for new DAGs
- [ ] Alert runbook updated

### Deployment

#### Backup
- [ ] Database backup taken
- [ ] DAG files backed up (Git tagged)
- [ ] Configuration backed up
- [ ] Connections exported

#### Staging Deployment
- [ ] Deployed to staging environment
- [ ] Smoke tests passed
- [ ] Performance tests passed
- [ ] Load tests passed
- [ ] DAGs triggered manually
- [ ] Logs reviewed
- [ ] Metrics reviewed

#### Production Deployment
- [ ] Maintenance window scheduled
- [ ] Stakeholders notified
- [ ] Rollback plan prepared
- [ ] Database migration executed (if needed)
- [ ] DAG files deployed
- [ ] Configuration updated
- [ ] Connections updated
- [ ] Services restarted (scheduler, webserver)
- [ ] Health check passed

### Post-Deployment

#### Validation
- [ ] All DAGs visible in UI
- [ ] No import errors
- [ ] Connections tested
- [ ] Variables tested
- [ ] First DAG run triggered
- [ ] Logs accessible
- [ ] Metrics flowing to monitoring

#### Monitoring (24h)
- [ ] Error rate normal
- [ ] Task duration normal
- [ ] Queue size normal
- [ ] Scheduler lag normal
- [ ] Database performance normal
- [ ] No memory leaks
- [ ] No disk space issues

#### Communication
- [ ] Deployment announced (Slack/Email)
- [ ] Stakeholders notified
- [ ] Documentation published
- [ ] Postmortem scheduled (if issues)
- [ ] Lessons learned documented

---

## Pratik Alıştırmalar

### Alıştırma 1: Environment Variables

**Görev:** Environment-aware DAG yazın.

```python
import os

ENV = os.getenv('AIRFLOW_ENV', 'development')

if ENV == 'production':
    PROJECT = 'prod-project'
    DATASET = 'prod_dataset'
    SCHEDULE = '@daily'
    RETRIES = 3
elif ENV == 'staging':
    PROJECT = 'staging-project'
    DATASET = 'staging_dataset'
    SCHEDULE = '@hourly'
    RETRIES = 2
else:
    PROJECT = 'dev-project'
    DATASET = 'dev_dataset'
    SCHEDULE = None
    RETRIES = 1

with DAG(
    dag_id=f'sales_etl_{ENV}',
    schedule_interval=SCHEDULE,
    default_args={'retries': RETRIES},
    tags=[ENV, 'sales']
) as dag:
    # Tasks...
    pass
```

### Alıştırma 2: Unit Test

**Görev:** DAG structure test yazın.

```python
# tests/test_sales_etl.py

def test_sales_etl_dag(dagbag):
    dag = dagbag.get_dag('sales_etl')

    assert dag is not None
    assert dag.schedule_interval == '@daily'
    assert dag.catchup == False

    # Task count
    assert len(dag.tasks) >= 10

    # Required tasks exist
    task_ids = [t.task_id for t in dag.tasks]
    assert 'extract_customers' in task_ids
    assert 'upsert_dim_customer' in task_ids
    assert 'insert_fact_sales' in task_ids

    # Dependencies
    extract_task = dag.get_task('extract_customers')
    downstream_ids = [t.task_id for t in extract_task.downstream_list]
    assert 'load_customers_staging' in downstream_ids
```

### Alıştırma 3: CI/CD Pipeline

**Görev:** GitHub Actions workflow oluşturun.

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov=dags
      - run: flake8 dags/
      - run: python scripts/validate_dags.py
```

### Alıştırma 4: Secret Backend

**Görev:** GCP Secret Manager entegrasyonu.

```yaml
# docker-compose.yaml
environment:
  AIRFLOW__SECRETS__BACKEND: airflow.providers.google.cloud.secrets.secret_manager.CloudSecretManagerBackend
  AIRFLOW__SECRETS__BACKEND_KWARGS: '{"project_id": "my-project"}'
```

```bash
# Secret ekle
gcloud secrets create airflow-variables-api-key \
  --data-file=- <<< "my-secret-key"

# DAG'de kullan
from airflow.models import Variable
api_key = Variable.get("api-key")
```

### Alıştırma 5: Blue-Green Deployment

**Görev:** Blue-green deployment script yazın.

```bash
#!/bin/bash
# deploy_blue_green.sh

GREEN_ENV="airflow-green"
BLUE_ENV="airflow-blue"

# Deploy to green
echo "Deploying to green environment..."
gsutil -m rsync -r -d dags/ gs://green-bucket/dags/

# Test green
echo "Testing green environment..."
gcloud composer environments run $GREEN_ENV \
  --location us-central1 \
  dags test sales_etl 2024-01-01

# Switch traffic
echo "Switching traffic to green..."
# Update load balancer or DNS

echo "Monitoring for 1 hour..."
sleep 3600

# Check error rate
ERROR_RATE=$(get_error_rate $GREEN_ENV)
if [ $ERROR_RATE > 0.05 ]; then
  echo "Error rate too high! Rolling back..."
  # Switch back to blue
  exit 1
fi

echo "Deployment successful!"
```

---

## Sık Sorulan Sorular (FAQ)

**S1: DAG'leri Git'te nasıl yönetmeliyim?**

A: Ayrı dags repo veya monorepo içinde `/dags` folder. CI/CD ile automatic deploy.

**S2: Environment variable vs Airflow Variable?**

A:
- **Environment variable**: Static config, restart gerektirir
- **Airflow Variable**: Dynamic, UI'dan değiştirilebilir

**S3: Secret rotation nasıl yapılır?**

A: Secret backend (Vault/Secret Manager) otomatik rotation destekler. Airflow connection'lar her task'ta fetch edilir.

**S4: Blue-green vs Canary?**

A:
- **Blue-green**: All-or-nothing switch, fast rollback
- **Canary**: Gradual rollout, lower risk

**S5: DAG deployment sırasında downtime olur mu?**

A: Hayır, Airflow DAG'leri hot reload eder (default 300 saniyede bir).

**S6: Docker image versioning stratejisi?**

A:
- Semantic versioning (2.8.1)
- Git commit SHA (abc1234)
- Environment tag (prod, staging)

**S7: Rollback ne kadar sürer?**

A:
- DAG rollback: Anında (Git revert + deploy)
- Infrastructure rollback: 5-10 dakika

**S8: Multiple region deployment?**

A: Active-active veya active-passive setup. GCS/S3 replication + database replication gerekir.

**S9: DAG CI/CD için best practice?**

A:
- Feature branch → PR → Tests → Staging → Production
- Automated testing (unit + integration)
- Manual QA approval for prod

**S10: Monitoring hangi tool'lar?**

A:
- Prometheus + Grafana (metrics)
- ELK Stack / CloudWatch (logs)
- PagerDuty / Opsgenie (alerting)

---

## Sonraki Adımlar

- Production monitoring setup
- Alerting ve incident response
- Performance tuning
- Cost optimization
