import sqlite3
import os

DB_NAME = "convenience.db"


def connect_db():
    if not os.path.exists(DB_NAME):
        print(f"[오류] {DB_NAME} 파일이 없습니다.")
        print("Google Drive 링크에서 convenience.db를 다운로드한 뒤 main.py와 같은 폴더에 넣어주세요.")
        return None

    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def print_rows(rows):
    if not rows:
        print("조회된 데이터가 없습니다.")
    else:
        for row in rows:
            print(row)


def sale_management():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    print("\n[판매 관리]")
    print("1. 판매 내역 조회")
    print("2. 판매 상세 조회")
    print("3. 뒤로가기")
    choice = input("선택: ")

    if choice == "1":
        cur.execute("""
        SELECT sale_id, store_id, customer_id, sale_date, total_amount
        FROM Sale
        ORDER BY sale_id
        """)
        print_rows(cur.fetchall())

    elif choice == "2":
        sale_id = input("조회할 sale_id 입력: ")
        cur.execute("""
        SELECT sd.sale_id, p.product_name, sd.quantity, sd.unit_price
        FROM SaleDetail sd
        JOIN Product p ON sd.barcode_number = p.barcode_number
        WHERE sd.sale_id = ?
        """, (sale_id,))
        print_rows(cur.fetchall())

    conn.close()


def inventory_management():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    print("\n[재고 관리]")
    print("1. 전체 재고 조회")
    print("2. 매장별 재고 조회")
    print("3. 재고 부족 상품 조회")
    print("4. 뒤로가기")
    choice = input("선택: ")

    if choice == "1":
        cur.execute("""
        SELECT si.store_id, p.product_name, si.stock_quantity, si.selling_price
        FROM StoreInventory si
        JOIN Product p ON si.barcode_number = p.barcode_number
        ORDER BY si.store_id, p.product_name
        """)
        print_rows(cur.fetchall())

    elif choice == "2":
        store_id = input("매장 ID 입력: ")
        cur.execute("""
        SELECT si.store_id, p.product_name, si.stock_quantity, si.selling_price
        FROM StoreInventory si
        JOIN Product p ON si.barcode_number = p.barcode_number
        WHERE si.store_id = ?
        ORDER BY p.product_name
        """, (store_id,))
        print_rows(cur.fetchall())

    elif choice == "3":
        cur.execute("""
        SELECT si.store_id, p.product_name, si.stock_quantity
        FROM StoreInventory si
        JOIN Product p ON si.barcode_number = p.barcode_number
        WHERE si.stock_quantity <= 5
        ORDER BY si.stock_quantity
        """)
        print_rows(cur.fetchall())

    conn.close()


def order_management():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    print("\n[발주 관리]")
    print("1. 발주 내역 조회")
    print("2. 발주 상세 조회")
    print("3. 뒤로가기")
    choice = input("선택: ")

    if choice == "1":
        cur.execute("""
        SELECT po.order_id, po.store_id, s.supplier_name, po.order_date
        FROM PurchaseOrder po
        JOIN Supplier s ON po.supplier_id = s.supplier_id
        ORDER BY po.order_id
        """)
        print_rows(cur.fetchall())

    elif choice == "2":
        order_id = input("조회할 order_id 입력: ")
        cur.execute("""
        SELECT pod.order_id, p.product_name, pod.order_quantity
        FROM PurchaseOrderDetail pod
        JOIN Product p ON pod.barcode_number = p.barcode_number
        WHERE pod.order_id = ?
        """, (order_id,))
        print_rows(cur.fetchall())

    conn.close()


def product_supplier_management():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    print("\n[상품/공급업체 관리]")
    print("1. 전체 상품 조회")
    print("2. 브랜드별 상품 조회")
    print("3. 공급업체 조회")
    print("4. 공급업체별 공급 가능 상품 조회")
    print("5. 뒤로가기")
    choice = input("선택: ")

    if choice == "1":
        cur.execute("""
        SELECT p.barcode_number, p.product_name, p.specification, p.packaging, b.brand_name
        FROM Product p
        JOIN Brand b ON p.brand_id = b.brand_id
        ORDER BY p.product_name
        """)
        print_rows(cur.fetchall())

    elif choice == "2":
        brand_name = input("브랜드명 입력: ")
        cur.execute("""
        SELECT p.barcode_number, p.product_name, p.specification, p.packaging, b.brand_name
        FROM Product p
        JOIN Brand b ON p.brand_id = b.brand_id
        WHERE b.brand_name LIKE ?
        ORDER BY p.product_name
        """, (f"%{brand_name}%",))
        print_rows(cur.fetchall())

    elif choice == "3":
        cur.execute("""
        SELECT supplier_id, supplier_name, phone_number
        FROM Supplier
        ORDER BY supplier_id
        """)
        print_rows(cur.fetchall())

    elif choice == "4":
        supplier_id = input("공급업체 ID 입력: ")
        cur.execute("""
        SELECT s.supplier_name, p.product_name, ps.supply_price
        FROM ProductSupplier ps
        JOIN Supplier s ON ps.supplier_id = s.supplier_id
        JOIN Product p ON ps.barcode_number = p.barcode_number
        WHERE s.supplier_id = ?
        ORDER BY p.product_name
        """, (supplier_id,))
        print_rows(cur.fetchall())

    conn.close()


def customer_management():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    print("\n[고객 관리]")
    print("1. 회원 조회")
    print("2. 전화번호로 고객 조회")
    print("3. 회원 구매 내역 조회")
    print("4. 뒤로가기")
    choice = input("선택: ")

    if choice == "1":
        cur.execute("""
        SELECT c.customer_id, c.phone_number, m.member_name, m.point
        FROM Customer c
        JOIN Member m ON c.customer_id = m.customer_id
        ORDER BY c.customer_id
        """)
        print_rows(cur.fetchall())

    elif choice == "2":
        phone = input("전화번호 입력: ")
        cur.execute("""
        SELECT customer_id, phone_number
        FROM Customer
        WHERE phone_number LIKE ?
        """, (f"%{phone}%",))
        print_rows(cur.fetchall())

    elif choice == "3":
        customer_id = input("customer_id 입력: ")
        cur.execute("""
        SELECT s.sale_id, s.store_id, s.sale_date, s.total_amount
        FROM Sale s
        WHERE s.customer_id = ?
        ORDER BY s.sale_date DESC
        """, (customer_id,))
        print_rows(cur.fetchall())

    conn.close()


def statistics_menu():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    print("\n[통계 조회]")
    print("1. 매장별 총매출 조회")
    print("2. 제품별 판매량 조회")
    print("3. 회원별 구매 금액 조회")
    print("4. 뒤로가기")
    choice = input("선택: ")

    if choice == "1":
        cur.execute("""
        SELECT st.store_id, st.city, SUM(s.total_amount) AS total_sales
        FROM Sale s
        JOIN Store st ON s.store_id = st.store_id
        GROUP BY st.store_id, st.city
        ORDER BY total_sales DESC
        """)
        print_rows(cur.fetchall())

    elif choice == "2":
        cur.execute("""
        SELECT p.product_name, SUM(sd.quantity) AS total_quantity
        FROM SaleDetail sd
        JOIN Product p ON sd.barcode_number = p.barcode_number
        GROUP BY p.product_name
        ORDER BY total_quantity DESC
        """)
        print_rows(cur.fetchall())

    elif choice == "3":
        cur.execute("""
        SELECT c.customer_id, c.phone_number, m.member_name, SUM(s.total_amount) AS total_purchase
        FROM Customer c
        JOIN Member m ON c.customer_id = m.customer_id
        JOIN Sale s ON c.customer_id = s.customer_id
        GROUP BY c.customer_id, c.phone_number, m.member_name
        ORDER BY total_purchase DESC
        """)
        print_rows(cur.fetchall())

    conn.close()


def main():
    while True:
        print("\n=== 편의점 DB 시스템 ===")
        print("1. 판매 관리")
        print("2. 재고 관리")
        print("3. 발주 관리")
        print("4. 상품/공급업체 관리")
        print("5. 고객 관리")
        print("6. 통계 조회")
        print("7. 종료")

        choice = input("메뉴 선택: ")

        if choice == "1":
            sale_management()
        elif choice == "2":
            inventory_management()
        elif choice == "3":
            order_management()
        elif choice == "4":
            product_supplier_management()
        elif choice == "5":
            customer_management()
        elif choice == "6":
            statistics_menu()
        elif choice == "7":
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 입력입니다.")


if __name__ == "__main__":
    main()