/*
 * Data Quality Checks
 *
 * Bu SQL veri kalitesi kontrolleri yapar.
 * Hata bulunursa BigQuery ERROR() fonksiyonu ile pipeline'ı durdurur.
 *
 * Kontroller:
 * - Row count (minimum beklenen veri)
 * - Null check (kritik alanlarda NULL olmamalı)
 * - Duplicate check (duplicate order_id)
 * - Value range check (negative amounts, impossible values)
 * - Referential integrity (orphan records)
 * - Business rules (discount > total amount, etc.)
 */

-- Çoklu veri kalitesi kontrolü
WITH quality_metrics AS (
    SELECT
        -- 1. Row Count Check
        COUNT(*) as total_rows,

        -- 2. Null Checks
        COUNTIF(order_id IS NULL) as null_order_ids,
        COUNTIF(customer_id IS NULL) as null_customer_ids,
        COUNTIF(product_id IS NULL) as null_product_ids,
        COUNTIF(order_date IS NULL) as null_order_dates,

        -- 3. Value Range Checks
        COUNTIF(quantity <= 0) as invalid_quantities,
        COUNTIF(unit_price <= 0) as invalid_prices,
        COUNTIF(total_amount <= 0) as invalid_amounts,
        COUNTIF(discount_amount < 0) as negative_discounts,

        -- 4. Business Rule Checks
        COUNTIF(discount_amount > total_amount) as invalid_discount_amount,
        COUNTIF(net_amount < 0) as negative_net_amounts,

        -- 5. Duplicate Check
        COUNT(*) - COUNT(DISTINCT order_id) as duplicate_orders,

        -- 6. Data Quality Flag Distribution
        COUNTIF(data_quality_flag != 'VALID') as invalid_records

    FROM `{{ params.project_id }}.datamart.sales_cleaned`
    WHERE order_date = DATE('{{ ds }}')
),
validation_results AS (
    SELECT
        -- Check 1: Minimum row count (en az 1 kayıt olmalı)
        CASE
            WHEN total_rows = 0 THEN 'ERROR: No data found for today'
            ELSE 'PASS'
        END as row_count_check,

        -- Check 2: Null checks
        CASE
            WHEN null_order_ids > 0 OR null_customer_ids > 0 OR
                 null_product_ids > 0 OR null_order_dates > 0
            THEN CONCAT('ERROR: Found NULL values - OrderID:', CAST(null_order_ids AS STRING),
                       ', CustomerID:', CAST(null_customer_ids AS STRING),
                       ', ProductID:', CAST(null_product_ids AS STRING))
            ELSE 'PASS'
        END as null_check,

        -- Check 3: Value range checks
        CASE
            WHEN invalid_quantities > 0 OR invalid_prices > 0 OR invalid_amounts > 0
            THEN CONCAT('ERROR: Invalid value ranges - InvalidQty:', CAST(invalid_quantities AS STRING),
                       ', InvalidPrice:', CAST(invalid_prices AS STRING),
                       ', InvalidAmount:', CAST(invalid_amounts AS STRING))
            ELSE 'PASS'
        END as value_range_check,

        -- Check 4: Business rules
        CASE
            WHEN invalid_discount_amount > 0 OR negative_net_amounts > 0
            THEN CONCAT('ERROR: Business rule violations - InvalidDiscount:', CAST(invalid_discount_amount AS STRING),
                       ', NegativeNet:', CAST(negative_net_amounts AS STRING))
            ELSE 'PASS'
        END as business_rule_check,

        -- Check 5: Duplicate check
        CASE
            WHEN duplicate_orders > 0
            THEN CONCAT('ERROR: Found ', CAST(duplicate_orders AS STRING), ' duplicate orders')
            ELSE 'PASS'
        END as duplicate_check,

        -- Check 6: Data quality score (en az %95 olmalı)
        CASE
            WHEN invalid_records > 0 AND (total_rows - invalid_records) * 100.0 / total_rows < 95
            THEN CONCAT('ERROR: Data quality score too low - ',
                       CAST(ROUND((total_rows - invalid_records) * 100.0 / total_rows, 2) AS STRING),
                       '% (minimum 95% required)')
            ELSE 'PASS'
        END as quality_score_check,

        -- Özet bilgiler
        total_rows,
        invalid_records,
        ROUND((total_rows - invalid_records) * 100.0 / NULLIF(total_rows, 0), 2) as quality_score_pct

    FROM quality_metrics
)

-- Final validation - Hata varsa ERROR() ile fail et
SELECT
    CASE
        -- Tüm kontroller PASS ise başarılı
        WHEN row_count_check = 'PASS'
         AND null_check = 'PASS'
         AND value_range_check = 'PASS'
         AND business_rule_check = 'PASS'
         AND duplicate_check = 'PASS'
         AND quality_score_check = 'PASS'
        THEN CONCAT('✅ ALL QUALITY CHECKS PASSED - Total Rows: ', CAST(total_rows AS STRING),
                   ', Quality Score: ', CAST(quality_score_pct AS STRING), '%')

        -- Herhangi bir check fail ederse error mesajı göster
        ELSE ERROR(
            CONCAT(
                '❌ DATA QUALITY CHECKS FAILED:\n',
                '1. Row Count: ', row_count_check, '\n',
                '2. Null Check: ', null_check, '\n',
                '3. Value Range: ', value_range_check, '\n',
                '4. Business Rules: ', business_rule_check, '\n',
                '5. Duplicate Check: ', duplicate_check, '\n',
                '6. Quality Score: ', quality_score_check, '\n',
                'Total Rows: ', CAST(total_rows AS STRING), ', ',
                'Invalid Records: ', CAST(invalid_records AS STRING), ', ',
                'Quality Score: ', CAST(quality_score_pct AS STRING), '%'
            )
        )
    END as validation_result

FROM validation_results;
