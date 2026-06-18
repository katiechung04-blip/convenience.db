#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
유통업체 데이터베이스 관리 시스템 - 최종 통합본
- DBA 인터페이스
- OLAP 쿼리 인터페이스 (필수 5대 쿼리 완벽 내장)
- 소비자 인터페이스
- 자동 재주문 시스템
- 공급업체 인터페이스
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional

DB_NAME = "convenience.db"

# ============================================================
# 데이터베이스 연결 및 유효성 검증
# ============================================================

def get_connection() -> Optional[sqlite3.Connection]:
    """데이터베이스 연결을 반환합니다."""
    if not os.path.exists(DB_NAME):
        print(f"\n[오류] {DB_NAME} 파일이 없습니다. 경로를 다시 확인해주세요.")
        return None
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def print_rows(cursor: sqlite3.Cursor, headers: Optional[list] = None):
    """쿼리 결과를 테이블 형태로 출력합니다."""
    rows = cursor.fetchall()
    if not rows:
        print("  (조회된 데이터가 없습니다)")
        return
    
    if headers is None:
        headers = [desc[0] for desc in cursor.description]
    
    # 컬럼 너비 계산
    widths = [len(str(h)) for h in headers]
    str_rows = []
    for row in rows:
        str_row = [str(v) if v is not None else "NULL" for v in row]
        str_rows.append(str_row)
        for i, v in enumerate(str_row):
            widths[i] = max(widths[i], len(v))
    
    print("-" * (sum(widths) + (len(widths) * 3)))
    header_line = " | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers))
    print(f"  {header_line}")
    print("-" * (sum(widths) + (len(widths) * 3)))
    
    for str_row in str_rows:
        line = " | ".join(str_row[i].ljust(widths[i]) for i in range(len(str_row)))
        print(f"  {line}")
    
    print("-" * (sum(widths) + (len(widths) * 3)))
    print(f"  총 {len(rows)}건의 데이터가 조회되었습니다.\n")


# ============================================================
# 1. DBA 인터페이스 - SQL 직접 실행
# ============================================================

def dba_interface():
    """DBA가 SQL을 직접 입력하여 실행할 수 있는 인터페이스"""
    print("\n" + "="*60)
    print(" DBA 관리자 인터페이스 - SQL 직접 실행 쉘")
    print(" 종료하려면 'exit' 또는 'quit' 입력")
    print("="*60)
    
    conn = get_connection()
    if not conn: return
    
    while True:
        sql = input("SQL> ").strip()
        
        if sql.lower() in ('exit', 'quit', ''):
            break
        
        try:
            cursor = conn.execute(sql)
            if sql.strip().upper().startswith("SELECT"):
                print_rows(cursor)
            else:
                conn.commit()
                print(f"  실행 완료. 영향받은 행: {cursor.rowcount}개")
        except sqlite3.Error as e:
            print(f"  [SQL 구문오류]: {e}")
    
    conn.close()


# ============================================================
# 2. OLAP 쿼리 인터페이스 (교수님 필수 5대 쿼리)
# ============================================================

def olap_interface():
    """OLAP성 분석 쿼리를 실행하는 인터페이스"""
    conn = get_connection()
    if not conn: return
    
    while True:
        print("\n" + "="*60)
        print(" 유통업체 OLAP 경영 분석 통계 인터페이스")
        print("="*60)
        print("1. 각 매장별 판매 상위 20개 제품 조회")
        print("2. 시·도별 판매 상위 20개 제품 조회")
        print("3. 판매 실적 상위 5개 매장 조회")
        print("4. 특정 제품 판매량 비교 우위 매장 수 (펩시 > 코카콜라)")
        print("5. 특정 제품과 함께 가장 많이 구매된 상위 3개 제품 (우유와 함께)")
        print("0. 돌아가기")
        
        choice = input("선택> ").strip()
        
        if choice == "0":
            break
        
        elif choice == "1":
            sql = """
            SELECT store_id, barcode_number, product_name, total_qty, rank_in_store
            FROM (
                SELECT s.store_id, sd.barcode_number, p.product_name, SUM(sd.quantity) AS total_qty,
                       ROW_NUMBER() OVER (PARTITION BY s.store_id ORDER BY SUM(sd.quantity) DESC) AS rank_in_store
                FROM Sale s
                JOIN SaleDetail sd ON s.sale_id = sd.sale_id
                JOIN Product p ON sd.barcode_number = p.barcode_number
                GROUP BY s.store_id, sd.barcode_number
            ) WHERE rank_in_store <= 20 ORDER BY store_id, rank_in_store;
            """
            print_rows(conn.execute(sql), ["매장ID", "바코드", "상품명", "총판매량", "매장내순위"])
        
        elif choice == "2":
            sql = """
            SELECT city, barcode_number, product_name, total_qty, rank_in_city
            FROM (
                SELECT st.city, sd.barcode_number, p.product_name, SUM(sd.quantity) AS total_qty,
                       ROW_NUMBER() OVER (PARTITION BY st.city ORDER BY SUM(sd.quantity) DESC) AS rank_in_city
                FROM Sale s
                JOIN Store st ON s.store_id = st.store_id
                JOIN SaleDetail sd ON s.sale_id = sd.sale_id
                JOIN Product p ON sd.barcode_number = p.barcode_number
                GROUP BY st.city, sd.barcode_number
            ) WHERE rank_in_city <= 20 ORDER BY city, rank_in_city;
            """
            print_rows(conn.execute(sql), ["시·도(지역)", "바코드", "상품명", "총판매량", "지역내순위"])
        
        elif choice == "3":
            sql = """
            SELECT s.store_id, st.city, SUM(s.total_amount) AS total_sales
            FROM Sale s
            JOIN Store st ON s.store_id = st.store_id
            GROUP BY s.store_id
            ORDER BY total_sales DESC
            LIMIT 5;
            """
            print_rows(conn.execute(sql), ["매장ID", "지역", "총매출액"])
        
        elif choice == "4":
            sql = """
            SELECT COUNT(*) AS store_count
            FROM (
                SELECT s.store_id,
                       SUM(CASE WHEN p.product_name LIKE '%펩시%' THEN sd.quantity ELSE 0 END) AS pepsi_qty,
                       SUM(CASE WHEN p.product_name LIKE '%코카콜라%' THEN sd.quantity ELSE 0 END) AS coca_qty
                FROM Sale s
                JOIN SaleDetail sd ON s.sale_id = sd.sale_id
                JOIN Product p ON sd.barcode_number = p.barcode_number
                GROUP BY s.store_id
            ) WHERE pepsi_qty > coca_qty;
            """
            res = conn.execute(sql).fetchone()
            print(f"\n▶ 코카콜라보다 펩시가 더 많이 팔린 매장 수: {res['store_count']}개 매장")
        
        elif choice == "5":
            target = input("기준 제품명 입력 (기본값: 우유)> ").strip()
            if not target: target = "우유"
            sql = """
            SELECT p2.barcode_number, p2.product_name, COUNT(*) AS co_purchase_count
            FROM SaleDetail sd1
            JOIN SaleDetail sd2 ON sd1.sale_id = sd2.sale_id AND sd1.barcode_number <> sd2.barcode_number
            JOIN Product p1 ON sd1.barcode_number = p1.barcode_number
            JOIN Product p2 ON sd2.barcode_number = p2.barcode_number
            WHERE p1.product_name LIKE ?
            GROUP BY p2.barcode_number
            ORDER BY co_purchase_count DESC
            LIMIT 3;
            """
            print_rows(conn.execute(sql, (f"%{target}%",)), ["바코드", "연관 상품명", "동시 구매 횟수"])
            
    conn.close()


# ============================================================
# 3. 소비자 인터페이스 (통합 POS 및 상품 명세 매칭 검색)
# ============================================================

def customer_interface():
    """소비자용 인터페이스 - 상품 검색 및 POS 실시간 구매 결제"""
    conn = get_connection()
    if not conn: return
    
    while True:
        print("\n" + "="*60)
        print(" 소비자 / 실시간 POS 결제 인터페이스")
        print("="*60)
        print("1. 상품 통합 검색 (브랜드명/상품명 패턴 매칭)")
        print("2. 실시간 가맹점 상품 구매 (POS 트랜잭션 및 재고 차감)")
        print("0. 돌아가기")
        
        choice = input("선택> ").strip()
        
        if choice == "0":
            break
        
        elif choice == "1":
            keyword = input("검색할 상품명 또는 브랜드명 입력: ").strip()
            sql = """
            SELECT p.barcode_number, p.product_name, b.brand_name, p.specification, p.packaging
            FROM Product p
            JOIN Brand b ON p.brand_id = b.brand_id
            WHERE p.product_name LIKE ? OR b.brand_name LIKE ?
            """
            print_rows(conn.execute(sql, (f"%{keyword}%", f"%{keyword}%")), ["바코드", "상품명", "브랜드명", "규격", "포장단위"])
        
        elif choice == "2":
            print("\n--- POS 결제 시뮬레이션 프로세스 구동 ---")
            store_id = input("매장 ID 입력 (예: S01): ").strip()
            barcode = input("상품 바코드 입력 (예: P001): ").strip()
            qty = int(input("구매 수량 입력: ").strip())
            
            cursor = conn.execute(
                "SELECT stock_quantity, selling_price FROM StoreInventory WHERE store_id = ? AND barcode_number = ?", 
                (store_id, barcode)
            )
            inv = cursor.fetchone()
            if not inv or inv['stock_quantity'] < qty:
                print("🚨 [결제 실패]: 가맹점에 해당 상품의 자재 재고가 없거나 부족합니다.")
                continue
            
            total_price = inv['selling_price'] * qty
            try:
                # 판매 영수증 트랜잭션 기록 및 실시간 재고 연동 차감
                cursor = conn.execute("INSERT INTO Sale (store_id, customer_id, sale_date, total_amount) VALUES (?, 'C001', ?, ?)", 
                             (store_id, datetime.now().strftime("%Y-%m-%d"), total_price))
                sale_id = cursor.lastrowid
                conn.execute("INSERT INTO SaleDetail (sale_id, barcode_number, quantity, unit_price) VALUES (?, ?, ?, ?)", 
                             (sale_id, barcode, qty, inv['selling_price']))
                conn.execute("UPDATE StoreInventory SET stock_quantity = stock_quantity - ? WHERE store_id = ? AND barcode_number = ?", 
                             (qty, store_id, barcode))
                conn.commit()
                print(f"🍏 [결제 성공] 영수증 번호 #{sale_id} 발급 완료 / 총액 {total_price}원 실시간 마이너스 차감 반영!")
            except sqlite3.Error as e:
                conn.rollback()
                print(f"🚨 트랜잭션 오류 발생으로 승인이 취소되었습니다: {e}")
                
    conn.close()


# ============================================================
# 4. 자동 재주문 시스템 (안전재고 확보 수량 미달 시 스크립트 가동)
# ============================================================

def auto_reorder_system():
    """재고가 기준 이하인 제품을 자동으로 발주서 테이블에 등록하는 시스템"""
    print("\n" + "="*60)
    print(" 시스템 안전 재고 확보 정기 자동 발주 프로그램")
    print("="*60)
    
    conn = get_connection()
    if not conn: return
    
    limit_qty = input("자동 긴급 발주를 가동할 임계 기준 수량 설정 (기본값: 10)> ").strip()
    limit_qty = int(limit_qty) if limit_qty else 10
    
    # 가맹점 인벤토리 전수 조사
    cursor = conn.execute(
        "SELECT store_id, barcode_number, stock_quantity FROM StoreInventory WHERE stock_quantity <= ?", 
        (limit_qty,)
    )
    low_stocks = cursor.fetchall()
    
    if not low_stocks:
        print(f" 현재 모든 가맹점의 상품 재고가 안전 기준 수량({limit_qty}개)을 충족하고 있습니다.")
        conn.close()
        return
        
    print(f"\n🚨 [재고 부족 경보] 기준치 미달 항목 총 {len(low_stocks)}건 포착. 자동 발주 트랜잭션을 구동합니다.\n")
    
    for item in low_stocks:
        store_id = item['store_id']
        barcode = item['barcode_number']
        current_qty = item['stock_quantity']
        
        # 벤더업체 매핑 정보 추적
        sup_cursor = conn.execute("SELECT supplier_id FROM ProductSupplier WHERE barcode_number = ? LIMIT 1", (barcode,))
        sup = sup_cursor.fetchone()
        
        if sup:
            supplier_id = sup['supplier_id']
            # 발주서 헤더 및 디테일 밀어넣기
            cursor = conn.execute("INSERT INTO PurchaseOrder (store_id, supplier_id, order_date) VALUES (?, ?, ?)", 
                         (store_id, supplier_id, datetime.now().strftime("%Y-%m-%d")))
            order_id = cursor.lastrowid
            conn.execute("INSERT INTO PurchaseOrderDetail (order_id, barcode_number, order_quantity) VALUES (?, ?, 50)", 
                         (order_id, barcode))
            print(f" 📦 [자동 발주 송신] 매장:{store_id} -> 공급업체:{supplier_id} | 품목:{barcode} (현재고:{current_qty}개) ➡️ 긴급 물류 50개 자동 발주 처리 완료!")
            
    conn.commit()
    conn.close()
    print("\n 모든 재고 부족 품목에 대한 신규 발주 명세서가 성공적으로 적재되었습니다.")


# ============================================================
# 5. 공급업체 인터페이스 (발주 확인 후 공급 승인 및 자재 적재)
# ============================================================

def supplier_interface():
    """공급업체가 발주를 확인하고 공급 처리하여 실시간 가맹점 자재를 증가시키는 인터페이스"""
    print("\n" + "="*60)
    print(" 공급업체 연동 물류 관리 인터페이스")
    print("="*60)
    
    conn = get_connection()
    if not conn: return
    
    print("\n[현재 전국 물류 허브에 접수된 미처리 가맹점 발주 요청 내역]")
    sql = """
    SELECT po.order_id, po.store_id, pod.barcode_number, pod.order_quantity 
    FROM PurchaseOrder po 
    JOIN PurchaseOrderDetail pod ON po.order_id = pod.order_id
    """
    print_rows(conn.execute(sql), ["발주ID(order_id)", "요청가맹점ID", "요청바코드", "발주수량"])
    
    order_id = input("납품 공급 처리를 승인할 발주 ID(order_id)를 입력하세요: ").strip()
    if not order_id: 
        conn.close()
        return
    
    cursor = conn.execute(
        "SELECT po.store_id, pod.barcode_number, pod.order_quantity FROM PurchaseOrder po JOIN PurchaseOrderDetail pod ON po.order_id = pod.order_id WHERE po.order_id = ?", 
        (order_id,)
    )
    order_data = cursor.fetchone()
    
    if order_data:
        store_id = order_data['store_id']
        barcode = order_data['barcode_number']
        qty = order_data['order_quantity']
        
        try:
            # 실시간 자재 납품 입고 완료 처리 (재고 증가 및 발주 명세 해제)
            conn.execute("UPDATE StoreInventory SET stock_quantity = stock_quantity + ? WHERE store_id = ? AND barcode_number = ?", 
                         (qty, store_id, barcode))
            conn.execute("DELETE FROM PurchaseOrderDetail WHERE order_id = ?", (order_id,))
            conn.execute("DELETE FROM PurchaseOrder WHERE order_id = ?", (order_id,))
            conn.commit()
            print(f"\n🚚 [물류 수송 완료] 가맹점 {store_id}에 자재 {qty}개가 안전하게 적재되었습니다. 발주가 마감되었습니다.")
        except sqlite3.Error as e:
            conn.rollback()
            print(f"🚨 물류 입고 처리 중 데이터베이스 락 오류 발생: {e}")
    else:
        print("❌ 입력하신 발주서 식별 ID 코드를 찾을 수 없습니다.")
        
    conn.close()


# ============================================================
# 메인 메뉴 제어 루프
# ============================================================

def main():
    """시스템 메인 엔트리 구조"""
    while True:
        print("\n" + "■"*30)
        print("   대형 유통 가맹점 통합 데이터베이스 제어 제어 인터페이스")
        print("■"*30)
        print(" 1. DBA 관리자 인터페이스 (SQL 직접 실행 쉘)")
        print(" 2. 유통 가맹점 OLAP 경영 분석 통계 (필수 5대 조회)")
        print(" 3. 소비자 / 실시간 POS 결제 시스템 인터페이스")
        print(" 4. 시스템 정기 안전 재고 확보 자동 발주 프로그램")
        print(" 5. 공급업체 연동 물류 관리 시스템 인터페이스")
        print(" 0. 시스템 안전 종료")
        print("■"*30)
        
        choice = input("원하시는 시스템 메뉴 번호를 선택해 주세요: ").strip()
        
        if choice == "0":
            print("프로그램을 안전하게 종료하고 모든 DB 데이터 세션을 해제합니다.")
            break
        elif choice == "1":
            dba_interface()
        elif choice == "2":
            olap_interface()
        elif choice == "3":
            customer_interface()
        elif choice == "4":
            auto_order_interface() if 'auto_order_interface' in locals() else auto_reorder_system()
        elif choice == "5":
            supplier_interface()
        else:
            print("❌ 올바르지 않은 제어 제어 코드 명령입니다. 다시 입력해 주십시오.")


if __name__ == "__main__":
    main()
