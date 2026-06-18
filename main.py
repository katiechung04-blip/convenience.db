import sqlite3
import os
from datetime import datetime

DB_NAME = "convenience.db"


# =========================
# 공통 함수
# =========================

def connect_db():
    if not os.path.exists(DB_NAME):
        print(f"\n[오류] {DB_NAME} 파일이 없습니다.")
        print("Google Drive에서 convenience.db를 다운로드한 뒤 main.py와 같은 폴더에 넣어주세요.")
        return None

    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def check_database_ready():
    conn = connect_db()
    if conn is None:
        return False

    required_tables = [
        "Store",
        "Brand",
        "Product",
        "StoreInventory",
        "Customer",
        "Member",
        "NonMember",
        "Sale",
        "SaleDetail",
        "Supplier",
        "ProductSupplier",
        "PurchaseOrder",
        "PurchaseOrderDetail"
    ]

    cur = conn.cursor()
    cur.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    """)

    existing_tables = {row[0] for row in cur.fetchall()}
    conn.close()

    missing_tables = []

    for table in required_tables:
        if table not in existing_tables:
            missing_tables.append(table)

    if missing_tables:
        print("\n[오류] DB에 필요한 테이블이 없습니다.")
        print("누락된 테이블:", ", ".join(missing_tables))
        return False

    return True


def print_rows(rows, headers=None):
    if not rows:
        print("조회된 데이터가 없습니다.")
        return

    if headers:
        print("-" * 80)
        print(" | ".join(headers))
        print("-" * 80)

    for row in rows:
        print(row)

    print("-" * 80)


def input_int(message):
    while True:
        value = input(message).strip()

        try:
            return int(value)
        except ValueError:
            print("숫자로 입력해주세요.")


def input_positive_int(message):
    while True:
        value = input_int(message)

        if value > 0:
            return value

        print("1 이상의 숫자를 입력해주세요.")


# =========================
# 1. 판매 관리
# =========================

def sale_management():
    while True:
        print("\n[판매 관리]")
        print("1. 판매 내역 조회")
        print("2. 판매 상세 조회")
        print("3. POS 판매 처리")
        print("4. 뒤로가기")

        choice = input("선택: ").strip()

        if choice == "1":
            show_sales()
        elif choice == "2":
            show_sale_detail()
        elif choice == "3":
            process_sale()
        elif choice == "4":
            break
        else:
            print("잘못된 입력입니다.")


def show_sales():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    cur.execute("""
    SELECT sale_id, store_id, customer_id, sale_date, total_amount
    FROM Sale
    ORDER BY sale_id
    """)

    rows = cur.fetchall()
    print_rows(rows, ["sale_id", "store_id", "customer_id", "sale_date", "total_amount"])

    conn.close()


def show_sale_detail():
    conn = connect_db()
    if conn is None:
        return

    sale_id = input("조회할 sale_id 입력: ").strip()
    cur = conn.cursor()

    cur.execute("""
    SELECT sd.sale_id,
           p.product_name,
           sd.quantity,
           sd.unit_price,
           sd.quantity * sd.unit_price AS subtotal
    FROM SaleDetail sd
    JOIN Product p ON sd.barcode_number = p.barcode_number
    WHERE sd.sale_id = ?
    ORDER BY p.product_name
    """, (sale_id,))

    rows = cur.fetchall()
    print_rows(rows, ["sale_id", "product_name", "quantity", "unit_price", "subtotal"])

    conn.close()


def process_sale():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    try:
        print("\n[POS 판매 처리]")

        store_id = input("매장 ID 입력: ").strip()

        cur.execute("""
        SELECT store_id
        FROM Store
        WHERE store_id = ?
        """, (store_id,))

        if cur.fetchone() is None:
            print("존재하지 않는 매장입니다.")
            conn.close()
            return

        phone = input("고객 전화번호 입력, 미입력 시 비회원 판매 처리: ").strip()
        customer_id = None

        if phone:
            customer_id = get_or_create_customer(cur, phone)

        items = {}

        while True:
            barcode = input("\n상품 바코드 입력, 상품 입력 종료는 Enter: ").strip()

            if barcode == "":
                break

            cur.execute("""
            SELECT p.product_name,
                   si.stock_quantity,
                   si.selling_price
            FROM StoreInventory si
            JOIN Product p ON si.barcode_number = p.barcode_number
            WHERE si.store_id = ?
              AND si.barcode_number = ?
            """, (store_id, barcode))

            row = cur.fetchone()

            if row is None:
                print("해당 매장에 존재하지 않는 상품입니다.")
                continue

            product_name, stock_quantity, selling_price = row

            print(f"상품명: {product_name}")
            print(f"현재 재고: {stock_quantity}")
            print(f"판매가: {selling_price}")

            quantity = input_positive_int("구매 수량 입력: ")

            already_quantity = 0
            if barcode in items:
                already_quantity = items[barcode]["quantity"]

            if already_quantity + quantity > stock_quantity:
                print("재고가 부족하여 판매할 수 없습니다.")
                continue

            if barcode in items:
                items[barcode]["quantity"] += quantity
            else:
                items[barcode] = {
                    "product_name": product_name,
                    "quantity": quantity,
                    "unit_price": selling_price
                }

            print("장바구니에 상품이 추가되었습니다.")

        if not items:
            print("판매할 상품이 없습니다.")
            conn.close()
            return

        total_amount = 0

        for barcode, item in items.items():
            total_amount += item["quantity"] * item["unit_price"]

        cur.execute("""
        INSERT INTO Sale (store_id, customer_id, sale_date, total_amount)
        VALUES (?, ?, ?, ?)
        """, (
            store_id,
            customer_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_amount
        ))

        sale_id = cur.lastrowid

        for barcode, item in items.items():
            cur.execute("""
            INSERT INTO SaleDetail (sale_id, barcode_number, quantity, unit_price)
            VALUES (?, ?, ?, ?)
            """, (
                sale_id,
                barcode,
                item["quantity"],
                item["unit_price"]
            ))

            cur.execute("""
            UPDATE StoreInventory
            SET stock_quantity = stock_quantity - ?
            WHERE store_id = ?
              AND barcode_number = ?
            """, (
                item["quantity"],
                store_id,
                barcode
            ))

        if customer_id is not None:
            cur.execute("""
            SELECT customer_id
            FROM Member
            WHERE customer_id = ?
            """, (customer_id,))

            if cur.fetchone() is not None:
                earned_point = int(total_amount * 0.01)

                cur.execute("""
                UPDATE Member
                SET point = point + ?
                WHERE customer_id = ?
                """, (earned_point, customer_id))

                print(f"회원 포인트 {earned_point}점이 적립되었습니다.")

        conn.commit()

        print("\n판매 처리가 완료되었습니다.")
        print(f"sale_id: {sale_id}")
        print(f"총 판매 금액: {total_amount}원")

    except Exception as e:
        conn.rollback()
        print("\n판매 처리 중 오류가 발생했습니다.")
        print(e)

    finally:
        conn.close()


def get_or_create_customer(cur, phone):
    cur.execute("""
    SELECT customer_id
    FROM Customer
    WHERE phone_number = ?
    """, (phone,))

    row = cur.fetchone()

    if row is not None:
        customer_id = row[0]
        print(f"기존 고객입니다. customer_id = {customer_id}")
        return customer_id

    print("등록되지 않은 고객입니다.")
    choice = input("회원으로 등록하시겠습니까? (y/n): ").strip().lower()

    cur.execute("""
    INSERT INTO Customer (phone_number)
    VALUES (?)
    """, (phone,))

    customer_id = cur.lastrowid

    if choice == "y":
        name = input("회원 이름 입력: ").strip()

        cur.execute("""
        INSERT INTO Member (customer_id, member_name, point)
        VALUES (?, ?, 0)
        """, (customer_id, name))

        print("신규 회원으로 등록되었습니다.")

    else:
        cur.execute("""
        INSERT INTO NonMember (customer_id)
        VALUES (?)
        """, (customer_id,))

        print("비회원 고객으로 등록되었습니다.")

    return customer_id


# =========================
# 2. 재고 관리
# =========================

def inventory_management():
    while True:
        print("\n[재고 관리]")
        print("1. 전체 재고 조회")
        print("2. 매장별 재고 조회")
        print("3. 재고 부족 상품 조회")
        print("4. 뒤로가기")

        choice = input("선택: ").strip()

        if choice == "1":
            show_all_inventory()
        elif choice == "2":
            show_inventory_by_store()
        elif choice == "3":
            show_low_stock()
        elif choice == "4":
            break
        else:
            print("잘못된 입력입니다.")


def show_all_inventory():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    cur.execute("""
    SELECT si.store_id,
           st.city,
           p.product_name,
           si.stock_quantity,
           si.selling_price
    FROM StoreInventory si
    JOIN Store st ON si.store_id = st.store_id
    JOIN Product p ON si.barcode_number = p.barcode_number
    ORDER BY si.store_id, p.product_name
    """)

    rows = cur.fetchall()
    print_rows(rows, ["store_id", "city", "product_name", "stock_quantity", "selling_price"])

    conn.close()


def show_inventory_by_store():
    conn = connect_db()
    if conn is None:
        return

    store_id = input("매장 ID 입력: ").strip()
    cur = conn.cursor()

    cur.execute("""
    SELECT si.store_id,
           p.barcode_number,
           p.product_name,
           si.stock_quantity,
           si.selling_price
    FROM StoreInventory si
    JOIN Product p ON si.barcode_number = p.barcode_number
    WHERE si.store_id = ?
    ORDER BY p.product_name
    """, (store_id,))

    rows = cur.fetchall()
    print_rows(rows, ["store_id", "barcode_number", "product_name", "stock_quantity", "selling_price"])

    conn.close()


def show_low_stock():
    conn = connect_db()
    if conn is None:
        return

    standard = input_int("재고 부족 기준 수량 입력: ")
    cur = conn.cursor()

    cur.execute("""
    SELECT si.store_id,
           st.city,
           p.product_name,
           si.stock_quantity
    FROM StoreInventory si
    JOIN Store st ON si.store_id = st.store_id
    JOIN Product p ON si.barcode_number = p.barcode_number
    WHERE si.stock_quantity <= ?
    ORDER BY si.stock_quantity
    """, (standard,))

    rows = cur.fetchall()
    print_rows(rows, ["store_id", "city", "product_name", "stock_quantity"])

    conn.close()


# =========================
# 3. 발주 관리
# =========================

def order_management():
    while True:
        print("\n[발주 관리]")
        print("1. 발주 내역 조회")
        print("2. 발주 상세 조회")
        print("3. 신규 발주 등록")
        print("4. 뒤로가기")

        choice = input("선택: ").strip()

        if choice == "1":
            show_purchase_orders()
        elif choice == "2":
            show_purchase_order_detail()
        elif choice == "3":
            create_purchase_order()
        elif choice == "4":
            break
        else:
            print("잘못된 입력입니다.")


def show_purchase_orders():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    cur.execute("""
    SELECT po.order_id,
           po.store_id,
           st.city,
           po.supplier_id,
           sp.supplier_name,
           po.order_date
    FROM PurchaseOrder po
    JOIN Store st ON po.store_id = st.store_id
    JOIN Supplier sp ON po.supplier_id = sp.supplier_id
    ORDER BY po.order_id
    """)

    rows = cur.fetchall()
    print_rows(rows, ["order_id", "store_id", "city", "supplier_id", "supplier_name", "order_date"])

    conn.close()


def show_purchase_order_detail():
    conn = connect_db()
    if conn is None:
        return

    order_id = input("조회할 order_id 입력: ").strip()
    cur = conn.cursor()

    cur.execute("""
    SELECT pod.order_id,
           p.product_name,
           pod.order_quantity
    FROM PurchaseOrderDetail pod
    JOIN Product p ON pod.barcode_number = p.barcode_number
    WHERE pod.order_id = ?
    ORDER BY p.product_name
    """, (order_id,))

    rows = cur.fetchall()
    print_rows(rows, ["order_id", "product_name", "order_quantity"])

    conn.close()


def create_purchase_order():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    try:
        print("\n[신규 발주 등록]")

        store_id = input("발주 매장 ID 입력: ").strip()
        supplier_id = input("공급업체 ID 입력: ").strip()

        cur.execute("""
        SELECT store_id
        FROM Store
        WHERE store_id = ?
        """, (store_id,))

        if cur.fetchone() is None:
            print("존재하지 않는 매장입니다.")
            conn.close()
            return

        cur.execute("""
        SELECT supplier_id
        FROM Supplier
        WHERE supplier_id = ?
        """, (supplier_id,))

        if cur.fetchone() is None:
            print("존재하지 않는 공급업체입니다.")
            conn.close()
            return

        items = {}

        while True:
            barcode = input("\n발주할 상품 바코드 입력, 상품 입력 종료는 Enter: ").strip()

            if barcode == "":
                break

            cur.execute("""
            SELECT p.product_name,
                   ps.supply_price
            FROM ProductSupplier ps
            JOIN Product p ON ps.barcode_number = p.barcode_number
            WHERE ps.supplier_id = ?
              AND ps.barcode_number = ?
            """, (supplier_id, barcode))

            row = cur.fetchone()

            if row is None:
                print("해당 공급업체가 공급하지 않는 상품입니다.")
                continue

            product_name, supply_price = row

            print(f"상품명: {product_name}")
            print(f"공급가: {supply_price}")

            quantity = input_positive_int("발주 수량 입력: ")

            if barcode in items:
                items[barcode]["quantity"] += quantity
            else:
                items[barcode] = {
                    "product_name": product_name,
                    "quantity": quantity
                }

            print("발주 목록에 상품이 추가되었습니다.")

        if not items:
            print("발주할 상품이 없습니다.")
            conn.close()
            return

        cur.execute("""
        INSERT INTO PurchaseOrder (store_id, supplier_id, order_date)
        VALUES (?, ?, ?)
        """, (
            store_id,
            supplier_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        order_id = cur.lastrowid

        for barcode, item in items.items():
            cur.execute("""
            INSERT INTO PurchaseOrderDetail (order_id, barcode_number, order_quantity)
            VALUES (?, ?, ?)
            """, (
                order_id,
                barcode,
                item["quantity"]
            ))

        conn.commit()

        print("\n발주 등록이 완료되었습니다.")
        print(f"order_id: {order_id}")

    except Exception as e:
        conn.rollback()
        print("\n발주 등록 중 오류가 발생했습니다.")
        print(e)

    finally:
        conn.close()


# =========================
# 4. 상품/공급업체 관리
# =========================

def product_supplier_management():
    while True:
        print("\n[상품/공급업체 관리]")
        print("1. 전체 상품 조회")
        print("2. 바코드로 상품 조회")
        print("3. 브랜드별 상품 조회")
        print("4. 공급업체 조회")
        print("5. 공급업체별 공급 가능 상품 조회")
        print("6. 뒤로가기")

        choice = input("선택: ").strip()

        if choice == "1":
            show_all_products()
        elif choice == "2":
            search_product_by_barcode()
        elif choice == "3":
            search_products_by_brand()
        elif choice == "4":
            show_suppliers()
        elif choice == "5":
            show_products_by_supplier()
        elif choice == "6":
            break
        else:
            print("잘못된 입력입니다.")


def show_all_products():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    cur.execute("""
    SELECT p.barcode_number,
           p.product_name,
           p.specification,
           p.packaging,
           b.brand_name
    FROM Product p
    JOIN Brand b ON p.brand_id = b.brand_id
    ORDER BY p.product_name
    """)

    rows = cur.fetchall()
    print_rows(rows, ["barcode_number", "product_name", "specification", "packaging", "brand_name"])

    conn.close()


def search_product_by_barcode():
    conn = connect_db()
    if conn is None:
        return

    barcode = input("상품 바코드 입력: ").strip()
    cur = conn.cursor()

    cur.execute("""
    SELECT p.barcode_number,
           p.product_name,
           p.specification,
           p.packaging,
           b.brand_name
    FROM Product p
    JOIN Brand b ON p.brand_id = b.brand_id
    WHERE p.barcode_number = ?
    """, (barcode,))

    rows = cur.fetchall()
    print_rows(rows, ["barcode_number", "product_name", "specification", "packaging", "brand_name"])

    conn.close()


def search_products_by_brand():
    conn = connect_db()
    if conn is None:
        return

    brand_name = input("브랜드명 입력: ").strip()
    cur = conn.cursor()

    cur.execute("""
    SELECT p.barcode_number,
           p.product_name,
           p.specification,
           p.packaging,
           b.brand_name
    FROM Product p
    JOIN Brand b ON p.brand_id = b.brand_id
    WHERE b.brand_name LIKE ?
    ORDER BY p.product_name
    """, (f"%{brand_name}%",))

    rows = cur.fetchall()
    print_rows(rows, ["barcode_number", "product_name", "specification", "packaging", "brand_name"])

    conn.close()


def show_suppliers():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    cur.execute("""
    SELECT supplier_id,
           supplier_name,
           phone_number
    FROM Supplier
    ORDER BY supplier_id
    """)

    rows = cur.fetchall()
    print_rows(rows, ["supplier_id", "supplier_name", "phone_number"])

    conn.close()


def show_products_by_supplier():
    conn = connect_db()
    if conn is None:
        return

    supplier_id = input("공급업체 ID 입력: ").strip()
    cur = conn.cursor()

    cur.execute("""
    SELECT sp.supplier_name,
           p.barcode_number,
           p.product_name,
           ps.supply_price
    FROM ProductSupplier ps
    JOIN Supplier sp ON ps.supplier_id = sp.supplier_id
    JOIN Product p ON ps.barcode_number = p.barcode_number
    WHERE sp.supplier_id = ?
    ORDER BY p.product_name
    """, (supplier_id,))

    rows = cur.fetchall()
    print_rows(rows, ["supplier_name", "barcode_number", "product_name", "supply_price"])

    conn.close()


# =========================
# 5. 고객 관리
# =========================

def customer_management():
    while True:
        print("\n[고객 관리]")
        print("1. 전체 회원 조회")
        print("2. 전화번호로 고객 조회")
        print("3. 신규 회원 등록")
        print("4. 고객 구매 내역 조회")
        print("5. 뒤로가기")

        choice = input("선택: ").strip()

        if choice == "1":
            show_members()
        elif choice == "2":
            search_customer_by_phone()
        elif choice == "3":
            register_member()
        elif choice == "4":
            show_customer_purchase_history()
        elif choice == "5":
            break
        else:
            print("잘못된 입력입니다.")


def show_members():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    cur.execute("""
    SELECT c.customer_id,
           c.phone_number,
           m.member_name,
           m.point
    FROM Customer c
    JOIN Member m ON c.customer_id = m.customer_id
    ORDER BY c.customer_id
    """)

    rows = cur.fetchall()
    print_rows(rows, ["customer_id", "phone_number", "member_name", "point"])

    conn.close()


def search_customer_by_phone():
    conn = connect_db()
    if conn is None:
        return

    phone = input("전화번호 입력: ").strip()
    cur = conn.cursor()

    cur.execute("""
    SELECT c.customer_id,
           c.phone_number,
           CASE
               WHEN m.customer_id IS NOT NULL THEN 'Member'
               WHEN nm.customer_id IS NOT NULL THEN 'NonMember'
               ELSE 'Unknown'
           END AS customer_type
    FROM Customer c
    LEFT JOIN Member m ON c.customer_id = m.customer_id
    LEFT JOIN NonMember nm ON c.customer_id = nm.customer_id
    WHERE c.phone_number LIKE ?
    ORDER BY c.customer_id
    """, (f"%{phone}%",))

    rows = cur.fetchall()
    print_rows(rows, ["customer_id", "phone_number", "customer_type"])

    conn.close()


def register_member():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    try:
        phone = input("전화번호 입력: ").strip()
        name = input("회원 이름 입력: ").strip()

        cur.execute("""
        SELECT customer_id
        FROM Customer
        WHERE phone_number = ?
        """, (phone,))

        row = cur.fetchone()

        if row is not None:
            customer_id = row[0]

            cur.execute("""
            SELECT customer_id
            FROM Member
            WHERE customer_id = ?
            """, (customer_id,))

            if cur.fetchone() is not None:
                print("이미 회원으로 등록된 고객입니다.")
                conn.close()
                return

            cur.execute("""
            DELETE FROM NonMember
            WHERE customer_id = ?
            """, (customer_id,))

            cur.execute("""
            INSERT INTO Member (customer_id, member_name, point)
            VALUES (?, ?, 0)
            """, (customer_id, name))

            print("기존 비회원 고객이 회원으로 전환되었습니다.")

        else:
            cur.execute("""
            INSERT INTO Customer (phone_number)
            VALUES (?)
            """, (phone,))

            customer_id = cur.lastrowid

            cur.execute("""
            INSERT INTO Member (customer_id, member_name, point)
            VALUES (?, ?, 0)
            """, (customer_id, name))

            print("신규 회원이 등록되었습니다.")

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("회원 등록 중 오류가 발생했습니다.")
        print(e)

    finally:
        conn.close()


def show_customer_purchase_history():
    conn = connect_db()
    if conn is None:
        return

    customer_id = input("customer_id 입력: ").strip()
    cur = conn.cursor()

    cur.execute("""
    SELECT s.sale_id,
           s.store_id,
           s.sale_date,
           s.total_amount
    FROM Sale s
    WHERE s.customer_id = ?
    ORDER BY s.sale_date DESC
    """, (customer_id,))

    rows = cur.fetchall()
    print_rows(rows, ["sale_id", "store_id", "sale_date", "total_amount"])

    conn.close()


# =========================
# 6. 통계 조회
# =========================

def statistics_menu():
    while True:
        print("\n[통계 조회]")
        print("1. 매장별 총매출 조회")
        print("2. 제품별 판매량 조회")
        print("3. 회원별 구매 금액 조회")
        print("4. 재고 금액 조회")
        print("5. 뒤로가기")

        choice = input("선택: ").strip()

        if choice == "1":
            show_sales_by_store()
        elif choice == "2":
            show_sales_quantity_by_product()
        elif choice == "3":
            show_purchase_amount_by_member()
        elif choice == "4":
            show_inventory_value()
        elif choice == "5":
            break
        else:
            print("잘못된 입력입니다.")


def show_sales_by_store():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    cur.execute("""
    SELECT st.store_id,
           st.city,
           SUM(s.total_amount) AS total_sales
    FROM Sale s
    JOIN Store st ON s.store_id = st.store_id
    GROUP BY st.store_id, st.city
    ORDER BY total_sales DESC
    """)

    rows = cur.fetchall()
    print_rows(rows, ["store_id", "city", "total_sales"])

    conn.close()


def show_sales_quantity_by_product():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    cur.execute("""
    SELECT p.product_name,
           SUM(sd.quantity) AS total_quantity,
           SUM(sd.quantity * sd.unit_price) AS total_sales
    FROM SaleDetail sd
    JOIN Product p ON sd.barcode_number = p.barcode_number
    GROUP BY p.product_name
    ORDER BY total_quantity DESC
    """)

    rows = cur.fetchall()
    print_rows(rows, ["product_name", "total_quantity", "total_sales"])

    conn.close()


def show_purchase_amount_by_member():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    cur.execute("""
    SELECT c.customer_id,
           c.phone_number,
           m.member_name,
           SUM(s.total_amount) AS total_purchase
    FROM Customer c
    JOIN Member m ON c.customer_id = m.customer_id
    JOIN Sale s ON c.customer_id = s.customer_id
    GROUP BY c.customer_id, c.phone_number, m.member_name
    ORDER BY total_purchase DESC
    """)

    rows = cur.fetchall()
    print_rows(rows, ["customer_id", "phone_number", "member_name", "total_purchase"])

    conn.close()


def show_inventory_value():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    cur.execute("""
    SELECT si.store_id,
           st.city,
           SUM(si.stock_quantity * si.selling_price) AS inventory_value
    FROM StoreInventory si
    JOIN Store st ON si.store_id = st.store_id
    GROUP BY si.store_id, st.city
    ORDER BY inventory_value DESC
    """)

    rows = cur.fetchall()
    print_rows(rows, ["store_id", "city", "inventory_value"])

    conn.close()


# =========================
# 메인 메뉴
# =========================

def main():
    if not check_database_ready():
        return

    while True:
        print("\n=== 편의점 DB 시스템 ===")
        print("1. 판매 관리")
        print("2. 재고 관리")
        print("3. 발주 관리")
        print("4. 상품/공급업체 관리")
        print("5. 고객 관리")
        print("6. 통계 조회")
        print("7. 종료")

        choice = input("메뉴 선택: ").strip()

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
