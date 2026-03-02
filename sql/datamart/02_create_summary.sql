/*
 * Daily Sales Summary Report
 *
 * Bu SQL günlük satış özet raporunu oluşturur.
 *
 * Kaynak: datamart.sales_cleaned
 * Hedef: datamart.daily_sales_summary
 *
 * Metrikler:
 * - Toplam satış, sipariş sayısı, ortalama sipariş değeri
 * - Kategori bazlı dağılım
 * - Müşteri ve ürün çeşitliliği
 * - İndirim analizi
 */

-- Günlük satış özet tablosu oluştur
CREATE TABLE IF NOT EXISTS `{{ params.project_id }}.datamart.daily_sales_summary` (
    report_date DATE,
    total_orders INT64,
    unique_customers INT64,
    unique_products INT64,
    total_quantity INT64,
    gross_sales FLOAT64,
    total_discounts FLOAT64,
    net_sales FLOAT64,
    avg_order_value FLOAT64,
    avg_discount_percentage FLOAT64,
    -- Kategori breakdown
    electronics_sales FLOAT64,
    fashion_sales FLOAT64,
    home_sales FLOAT64,
    -- Sipariş büyüklüğü dağılımı
    small_orders_count INT64,
    medium_orders_count INT64,
    large_orders_count INT64,
    extra_large_orders_count INT64,
    -- Veri kalitesi
    valid_records_count INT64,
    invalid_records_count INT64,
    data_quality_score FLOAT64,
    -- Metadata
    generated_at TIMESTAMP
)
PARTITION BY report_date
OPTIONS(
    description="Günlük satış özet raporu - KPI'lar ve metrikler",
    labels=[("layer", "reporting"), ("type", "summary")]
);

-- Günlük özet raporunu oluştur (MERGE ile upsert)
MERGE `{{ params.project_id }}.datamart.daily_sales_summary` T
USING (
    SELECT
        order_date as report_date,

        -- Temel metrikler
        COUNT(DISTINCT order_id) as total_orders,
        COUNT(DISTINCT customer_id) as unique_customers,
        COUNT(DISTINCT product_id) as unique_products,
        SUM(quantity) as total_quantity,
        SUM(total_amount) as gross_sales,
        SUM(discount_amount) as total_discounts,
        SUM(net_amount) as net_sales,
        AVG(net_amount) as avg_order_value,
        AVG(discount_percentage) as avg_discount_percentage,

        -- Kategori bazlı satışlar
        SUM(CASE WHEN category = 'Electronics' THEN net_amount ELSE 0 END) as electronics_sales,
        SUM(CASE WHEN category = 'Fashion' THEN net_amount ELSE 0 END) as fashion_sales,
        SUM(CASE WHEN category = 'Home' THEN net_amount ELSE 0 END) as home_sales,

        -- Sipariş büyüklüğü dağılımı
        COUNTIF(order_size_category = 'Small') as small_orders_count,
        COUNTIF(order_size_category = 'Medium') as medium_orders_count,
        COUNTIF(order_size_category = 'Large') as large_orders_count,
        COUNTIF(order_size_category = 'Extra Large') as extra_large_orders_count,

        -- Veri kalitesi metrikleri
        COUNTIF(data_quality_flag = 'VALID') as valid_records_count,
        COUNTIF(data_quality_flag != 'VALID') as invalid_records_count,
        ROUND(
            COUNTIF(data_quality_flag = 'VALID') * 100.0 / COUNT(*),
            2
        ) as data_quality_score,

        -- Metadata
        CURRENT_TIMESTAMP() as generated_at

    FROM `{{ params.project_id }}.datamart.sales_cleaned`
    WHERE order_date = DATE('{{ ds }}')
    GROUP BY order_date
) S
ON T.report_date = S.report_date
WHEN MATCHED THEN
    UPDATE SET
        total_orders = S.total_orders,
        unique_customers = S.unique_customers,
        unique_products = S.unique_products,
        total_quantity = S.total_quantity,
        gross_sales = S.gross_sales,
        total_discounts = S.total_discounts,
        net_sales = S.net_sales,
        avg_order_value = S.avg_order_value,
        avg_discount_percentage = S.avg_discount_percentage,
        electronics_sales = S.electronics_sales,
        fashion_sales = S.fashion_sales,
        home_sales = S.home_sales,
        small_orders_count = S.small_orders_count,
        medium_orders_count = S.medium_orders_count,
        large_orders_count = S.large_orders_count,
        extra_large_orders_count = S.extra_large_orders_count,
        valid_records_count = S.valid_records_count,
        invalid_records_count = S.invalid_records_count,
        data_quality_score = S.data_quality_score,
        generated_at = S.generated_at
WHEN NOT MATCHED THEN
    INSERT (
        report_date, total_orders, unique_customers, unique_products,
        total_quantity, gross_sales, total_discounts, net_sales,
        avg_order_value, avg_discount_percentage,
        electronics_sales, fashion_sales, home_sales,
        small_orders_count, medium_orders_count, large_orders_count, extra_large_orders_count,
        valid_records_count, invalid_records_count, data_quality_score,
        generated_at
    )
    VALUES (
        S.report_date, S.total_orders, S.unique_customers, S.unique_products,
        S.total_quantity, S.gross_sales, S.total_discounts, S.net_sales,
        S.avg_order_value, S.avg_discount_percentage,
        S.electronics_sales, S.fashion_sales, S.home_sales,
        S.small_orders_count, S.medium_orders_count, S.large_orders_count, S.extra_large_orders_count,
        S.valid_records_count, S.invalid_records_count, S.data_quality_score,
        S.generated_at
    );
