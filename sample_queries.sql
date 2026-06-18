-- =================================================================
-- 편의점 데이터베이스 기능 평가용 필수 5대 샘플 쿼리문 (최종 보정본)
-- =================================================================

-- [쿼리 1] 각 매장별 판매 상위 20개 제품
-- 명세서 요구사항: 각 매장별 가장 많이 판매된 상위 20개 제품 [cite: 51]
SELECT 
    store_id,
    barcode_number,
    product_name,
    total_qty,
    rank_in_store
FROM (
    SELECT
        s.store_id,
        sd.barcode_number,
        p.product_name,
        SUM(sd.quantity) AS total_qty,
        ROW_NUMBER() OVER (
            PARTITION BY s.store_id
            ORDER BY SUM(sd.quantity) DESC
        ) AS rank_in_store
    FROM Sale s
    JOIN SaleDetail sd ON s.sale_id = sd.sale_id
    JOIN Product p ON sd.barcode_number = p.barcode_number
    GROUP BY s.store_id, sd.barcode_number
)
WHERE rank_in_store <= 20
ORDER BY store_id, rank_in_store;


-- [쿼리 2] 시·도별 판매 상위 20개 제품
-- 명세서 요구사항: 시·도별로 가장 많이 판매된 상위 20개 제품 (state를 테이블 내 컬럼명인 city로 보정) [cite: 34, 52]
SELECT 
    city,
    barcode_number,
    product_name,
    total_qty,
    rank_in_city
FROM (
    SELECT
        st.city,
        sd.barcode_number,
        p.product_name,
        SUM(sd.quantity) AS total_qty,
        ROW_NUMBER() OVER (
            PARTITION BY st.city
            ORDER BY SUM(sd.quantity) DESC
        ) AS rank_in_city
    FROM Sale s
    JOIN Store st ON s.store_id = st.store_id
    JOIN SaleDetail sd ON s.sale_id = sd.sale_id
    JOIN Product p ON sd.barcode_number = p.barcode_number
    GROUP BY st.city, sd.barcode_number
)
WHERE rank_in_city <= 20
ORDER BY city, rank_in_city;


-- [쿼리 3] 판매 실적 상위 5개 매장
-- 명세서 요구사항: 판매 실적이 우수한 상위 5개 매장 [cite: 53]
SELECT 
    s.store_id,
    st.city,
    SUM(s.total_amount) AS total_sales
FROM Sale s
JOIN Store st ON s.store_id = st.store_id
GROUP BY s.store_id
ORDER BY total_sales DESC
LIMIT 5;


-- [쿼리 4] 특정 제품 A가 제품 B보다 많이 팔린 매장 수 (예: 펩시 > 코카콜라)
-- 명세서 요구사항: 코카콜라보다 펩시콜라가 더 많이 판매된 매장의 수 [cite: 54]
-- (조교님 데이터셋의 키워드인 '%펩시%'와 '%코카콜라%'를 완벽하게 반영)
SELECT COUNT(*) AS store_count
FROM (
    SELECT
        s.store_id,
        SUM(CASE WHEN p.product_name LIKE '%펩시%' THEN sd.quantity ELSE 0 END) AS pepsi_qty,
        SUM(CASE WHEN p.product_name LIKE '%코카콜라%' THEN sd.quantity ELSE 0 END) AS coca_qty
    FROM Sale s
    JOIN SaleDetail sd ON s.sale_id = sd.sale_id
    JOIN Product p ON sd.barcode_number = p.barcode_number
    GROUP BY s.store_id
)
WHERE pepsi_qty > coca_qty;


-- [쿼리 5] 특정 제품과 함께 가장 많이 구매된 상위 3개 제품 (예: 우유와 함께)
-- 명세서 요구사항: 소비자가 우유와 함께 가장 많이 구매한 제품 상위 3개 [cite: 55]
SELECT 
    p2.barcode_number,
    p2.product_name,
    COUNT(*) AS co_purchase_count
FROM SaleDetail sd1
JOIN SaleDetail sd2 ON sd1.sale_id = sd2.sale_id
                   AND sd1.barcode_number <> sd2.barcode_number
JOIN Product p1 ON sd1.barcode_number = p1.barcode_number
JOIN Product p2 ON sd2.barcode_number = p2.barcode_number
WHERE p1.product_name LIKE '%우유%'
GROUP BY p2.barcode_number
ORDER BY co_purchase_count DESC
LIMIT 3;
