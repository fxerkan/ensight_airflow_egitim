/*
 * Sales Data Transformation
 *
 * Bu SQL staging layer'dan veriyi okur, temizler ve datamart layer'a yükler.
 *
 * Kaynak: staging.sales_raw
 * Hedef: datamart.sales_cleaned
 *
 * İşlemler:
 * - Veri temizleme (NULL check, negatif değer kontrolü)
 * - Tarih dönüşümü (STRING -> DATE)
 * - Hesaplanan alanlar (discount_percentage, profit_margin)
 * - Kategorizasyon (order_size_category)
 */

-- Temizlenmiş satış verileri tablosu oluştur/değiştir
CREATE TABLE IF NOT EXISTS `{{ params.project_id }}.datamart.sales_cleaned` (
    order_id STRING,
    customer_id STRING,
    product_id STRING,
    product_name STRING,
    category STRING,
    quantity INT64,
    unit_price FLOAT64,
    total_amount FLOAT64,
    discount_amount FLOAT64,
    net_amount FLOAT64,
    discount_percentage FLOAT64,
    order_size_category STRING,
    order_date DATE,
    processed_at TIMESTAMP,
    data_quality_flag STRING
)
PARTITION BY order_date
CLUSTER BY category, customer_id
OPTIONS(
    description="Temizlenmiş ve dönüştürülmüş satış verileri - Datamart layer",
    labels=[("layer", "datamart"), ("team", "data-engineering")]
);

-- Staging'den datamart'a veri transformation (bugünün verisi)
INSERT INTO `{{ params.project_id }}.datamart.sales_cleaned`
SELECT
    order_id,
    customer_id,
    product_id,
    product_name,
    category,
    quantity,
    unit_price,
    total_amount,
    discount_amount,
    -- Net tutar hesaplama
    (total_amount - discount_amount) as net_amount,

    -- İndirim yüzdesi hesaplama
    ROUND(
        CASE
            WHEN total_amount > 0 THEN (discount_amount / total_amount) * 100
            ELSE 0
        END,
        2
    ) as discount_percentage,

    -- Sipariş büyüklüğü kategorizasyonu
    CASE
        WHEN total_amount < 1000 THEN 'Small'
        WHEN total_amount >= 1000 AND total_amount < 5000 THEN 'Medium'
        WHEN total_amount >= 5000 AND total_amount < 10000 THEN 'Large'
        ELSE 'Extra Large'
    END as order_size_category,

    -- Tarih dönüşümü (STRING -> DATE)
    PARSE_DATE('%Y-%m-%d', order_date) as order_date,

    -- İşlenme zamanı
    CURRENT_TIMESTAMP() as processed_at,

    -- Veri kalitesi flag
    CASE
        WHEN quantity <= 0 OR unit_price <= 0 OR total_amount <= 0 THEN 'INVALID_AMOUNT'
        WHEN discount_amount > total_amount THEN 'INVALID_DISCOUNT'
        WHEN product_name IS NULL OR category IS NULL THEN 'MISSING_DATA'
        ELSE 'VALID'
    END as data_quality_flag

FROM `{{ params.project_id }}.staging.sales_raw`
WHERE
    -- Sadece bugünün verisini işle (incremental load)
    PARSE_DATE('%Y-%m-%d', order_date) = DATE('{{ ds }}')
    -- Temel veri kalitesi filtreleri
    AND order_id IS NOT NULL
    AND customer_id IS NOT NULL
    AND product_id IS NOT NULL;
