
import sqlite3
import os
from datetime import datetime

# main.py와 같은 폴더에 convenience.db를 두는 것을 기본으로 합니다.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = "convenience.db"
DB_PATH = os.path.join(BASE_DIR, DB_NAME)


# =========================================================
# 공통 함수
# =========================================================

def connect_db():
    """
    convenience.db 파일을 연결합니다.
    DB 파일은 main.py와 같은 폴더에 있어야 합니다.
    """
    if not os.path.exists(DB_PATH):
        print(f"\n[오류] {DB_NAME} 파일이 없습니다.")
        print("Google Drive에서 convenience.db를 다운로드한 뒤 main.py와 같은 폴더에 넣어주세요.")
        print(f"현재 main.py 위치: {BASE_DIR}")
        return None

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    except sqlite3.DatabaseError:
        print(f"\n[오류] {DB_NAME} 파일이 올바른 SQLite 데이터베이스가 아닙니다.")
        print("올바른 convenience.db 파일을 다시 다운로드하여 main.py와 같은 폴더에 넣어주세요.")
        return None


def check_database_ready():
    """
    기본 DB 테이블이 존재하는지 확인합니다.
    SupplyRecord 관련 테이블은 main.py에서 자동 생성하므로 여기서는 검사하지 않습니다.
    """
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

    try:
        cur = conn.cursor()
        cur.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """)

        existing_tables = {row[0] for row in cur.fetchall()}

    except sqlite3.DatabaseError:
        print(f"\n[오류] {DB_NAME} 파일을 읽을 수 없습니다.")
        print("DB 파일이 올바른 SQLite 데이터베이스인지 확인해주세요.")
        conn.close()
        return False

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


def ensure_supply_tables():
    """
    명세서의 공급업체 처리 요구사항을 위해 공급 기록 테이블을 보장합니다.
    - SupplyRecord: 어떤 발주가 언제 어느 공급업체에 의해 처리되었는지 기록
    - SupplyRecordDetail: 실제 공급된 상품과 수량 기록
    """
    conn = connect_db()
    if conn is None:
        return False

    cur = conn.cursor()

    try:
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS SupplyRecord (
            receipt_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            supplier_id INTEGER NOT NULL,
            supplied_at TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES PurchaseOrder(order_id)
                ON UPDATE CASCADE
                ON DELETE CASCADE,
            FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id)
                ON UPDATE CASCADE
                ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS SupplyRecordDetail (
            receipt_id INTEGER NOT NULL,
            barcode_number TEXT NOT NULL,
            supplied_quantity INTEGER NOT NULL CHECK(supplied_quantity > 0),
            PRIMARY KEY (receipt_id, barcode_number),
            FOREIGN KEY (receipt_id) REFERENCES SupplyRecord(receipt_id)
                ON UPDATE CASCADE
                ON DELETE CASCADE,
            FOREIGN KEY (barcode_number) REFERENCES Product(barcode_number)
                ON UPDATE CASCADE
                ON DELETE RESTRICT
        );
        """)

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        print("\n[오류] 공급 기록 테이블 생성 중 문제가 발생했습니다.")
        print(e)
        return False

    finally:
        conn.close()


def print_rows(rows, headers=None):
    if not rows:
        print("조회된 데이터가 없습니다.")
        return

    if headers:
        print("-" * 100)
        print(" | ".join(headers))
        print("-" * 100)

    for row in rows:
        print(row)

    print("-" * 100)


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


# =========================================================
# 1. 판매 관리
# =========================================================

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
    """
    POS 판매 처리
    - Customer 확인 또는 생성
    - Sale 생성
    - SaleDetail 생성
    - StoreInventory 재고 감소
    - Member 포인트 적립
    """
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
            return

        phone = input("고객 전화번호 입력, 미입력 시 익명 비회원 판매 처리: ").strip()
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
            return

        total_amount = 0

        for item in items.values():
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


# =========================================================
# 2. 재고 관리
# =========================================================

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
           st.state,
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
    print_rows(rows, ["store_id", "state", "city", "product_name", "stock_quantity", "selling_price"])

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
           p.barcode_number,
           p.product_name,
           si.stock_quantity
    FROM StoreInventory si
    JOIN Store st ON si.store_id = st.store_id
    JOIN Product p ON si.barcode_number = p.barcode_number
    WHERE si.stock_quantity <= ?
    ORDER BY si.stock_quantity
    """, (standard,))

    rows = cur.fetchall()
    print_rows(rows, ["store_id", "city", "barcode_number", "product_name", "stock_quantity"])

    conn.close()


# =========================================================
# 3. 발주/공급 관리
# =========================================================

def order_management():
    while True:
        print("\n[발주/공급 관리]")
        print("1. 발주 내역 조회")
        print("2. 발주 상세 조회")
        print("3. 신규 발주 등록")
        print("4. 자동 재주문 발주 생성")
        print("5. 공급업체 발주 처리")
        print("6. 공급 처리 기록 조회")
        print("7. 뒤로가기")

        choice = input("선택: ").strip()

        if choice == "1":
            show_purchase_orders()
        elif choice == "2":
            show_purchase_order_detail()
        elif choice == "3":
            create_purchase_order()
        elif choice == "4":
            auto_reorder()
        elif choice == "5":
            supplier_process_order()
        elif choice == "6":
            show_supply_records()
        elif choice == "7":
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
           po.order_date,
           CASE
               WHEN sr.receipt_id IS NULL THEN 'Pending'
               ELSE 'Supplied'
           END AS supply_status
    FROM PurchaseOrder po
    JOIN Store st ON po.store_id = st.store_id
    JOIN Supplier sp ON po.supplier_id = sp.supplier_id
    LEFT JOIN SupplyRecord sr ON po.order_id = sr.order_id
    ORDER BY po.order_id
    """)

    rows = cur.fetchall()
    print_rows(rows, ["order_id", "store_id", "city", "supplier_id", "supplier_name", "order_date", "supply_status"])

    conn.close()


def show_purchase_order_detail():
    conn = connect_db()
    if conn is None:
        return

    order_id = input("조회할 order_id 입력: ").strip()
    cur = conn.cursor()

    cur.execute("""
    SELECT pod.order_id,
           p.barcode_number,
           p.product_name,
           pod.order_quantity
    FROM PurchaseOrderDetail pod
    JOIN Product p ON pod.barcode_number = p.barcode_number
    WHERE pod.order_id = ?
    ORDER BY p.product_name
    """, (order_id,))

    rows = cur.fetchall()
    print_rows(rows, ["order_id", "barcode_number", "product_name", "order_quantity"])

    conn.close()


def create_purchase_order():
    """
    매장이 공급업체에 신규 발주를 등록합니다.
    - PurchaseOrder 생성
    - PurchaseOrderDetail 생성
    """
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
            return

        cur.execute("""
        SELECT supplier_id
        FROM Supplier
        WHERE supplier_id = ?
        """, (supplier_id,))

        if cur.fetchone() is None:
            print("존재하지 않는 공급업체입니다.")
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


def auto_reorder():
    """
    자동 재주문 발주 생성
    - 재고가 기준 이하인 상품을 찾음
    - 해당 상품을 가장 낮은 공급가로 공급하는 업체 선택
    - PurchaseOrder, PurchaseOrderDetail 자동 생성
    """
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    try:
        print("\n[자동 재주문 발주 생성]")

        threshold = input_int("재고 부족 기준 수량 입력: ")
        target_stock = input_positive_int("목표 재고 수량 입력: ")

        if target_stock <= threshold:
            print("목표 재고 수량은 재고 부족 기준보다 커야 합니다.")
            return

        cur.execute("""
        SELECT si.store_id,
               si.barcode_number,
               p.product_name,
               si.stock_quantity
        FROM StoreInventory si
        JOIN Product p ON si.barcode_number = p.barcode_number
        WHERE si.stock_quantity <= ?
          AND NOT EXISTS (
              SELECT 1
              FROM PurchaseOrder po
              JOIN PurchaseOrderDetail pod ON po.order_id = pod.order_id
              LEFT JOIN SupplyRecord sr ON po.order_id = sr.order_id
              WHERE po.store_id = si.store_id
                AND pod.barcode_number = si.barcode_number
                AND sr.receipt_id IS NULL
          )
        ORDER BY si.store_id, si.stock_quantity
        """, (threshold,))

        low_stock_items = cur.fetchall()

        if not low_stock_items:
            print("자동 발주 대상 상품이 없습니다.")
            return

        order_groups = {}

        for store_id, barcode, product_name, stock_quantity in low_stock_items:
            cur.execute("""
            SELECT supplier_id
            FROM ProductSupplier
            WHERE barcode_number = ?
            ORDER BY supply_price ASC
            LIMIT 1
            """, (barcode,))

            supplier_row = cur.fetchone()

            if supplier_row is None:
                print(f"{product_name}은 공급 가능한 업체가 없어 자동 발주에서 제외되었습니다.")
                continue

            supplier_id = supplier_row[0]
            order_quantity = target_stock - stock_quantity

            key = (store_id, supplier_id)

            if key not in order_groups:
                order_groups[key] = []

            order_groups[key].append((barcode, product_name, order_quantity))

        if not order_groups:
            print("생성 가능한 자동 발주가 없습니다.")
            return

        created_order_count = 0

        for (store_id, supplier_id), items in order_groups.items():
            cur.execute("""
            INSERT INTO PurchaseOrder (store_id, supplier_id, order_date)
            VALUES (?, ?, ?)
            """, (
                store_id,
                supplier_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            order_id = cur.lastrowid

            for barcode, product_name, order_quantity in items:
                cur.execute("""
                INSERT INTO PurchaseOrderDetail (order_id, barcode_number, order_quantity)
                VALUES (?, ?, ?)
                """, (
                    order_id,
                    barcode,
                    order_quantity
                ))

            created_order_count += 1

        conn.commit()

        print("\n자동 재주문 발주가 완료되었습니다.")
        print(f"생성된 발주 건수: {created_order_count}")

    except Exception as e:
        conn.rollback()
        print("자동 재주문 발주 중 오류가 발생했습니다.")
        print(e)

    finally:
        conn.close()


def supplier_process_order():
    """
    공급업체 발주 처리
    - 공급업체가 미처리 발주를 확인
    - 공급 처리 기록 생성
    - 실제 공급 수량 기록
    - StoreInventory 재고 증가
    """
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    try:
        print("\n[공급업체 발주 처리]")

        supplier_id = input("공급업체 ID 입력: ").strip()

        cur.execute("""
        SELECT supplier_id, supplier_name
        FROM Supplier
        WHERE supplier_id = ?
        """, (supplier_id,))

        supplier = cur.fetchone()

        if supplier is None:
            print("존재하지 않는 공급업체입니다.")
            return

        print(f"공급업체: {supplier[1]}")

        cur.execute("""
        SELECT po.order_id,
               po.store_id,
               st.city,
               po.order_date,
               COUNT(pod.barcode_number) AS item_count
        FROM PurchaseOrder po
        JOIN PurchaseOrderDetail pod ON po.order_id = pod.order_id
        JOIN Store st ON po.store_id = st.store_id
        WHERE po.supplier_id = ?
          AND NOT EXISTS (
              SELECT 1
              FROM SupplyRecord sr
              WHERE sr.order_id = po.order_id
          )
        GROUP BY po.order_id, po.store_id, st.city, po.order_date
        ORDER BY po.order_date
        """, (supplier_id,))

        pending_orders = cur.fetchall()

        if not pending_orders:
            print("처리할 미공급 발주가 없습니다.")
            return

        print("\n[미공급 발주 목록]")
        print_rows(pending_orders, ["order_id", "store_id", "city", "order_date", "item_count"])

        order_id = input("처리할 order_id 입력: ").strip()

        cur.execute("""
        SELECT po.order_id, po.store_id
        FROM PurchaseOrder po
        WHERE po.order_id = ?
          AND po.supplier_id = ?
          AND NOT EXISTS (
              SELECT 1
              FROM SupplyRecord sr
              WHERE sr.order_id = po.order_id
          )
        """, (order_id, supplier_id))

        order = cur.fetchone()

        if order is None:
            print("처리할 수 없는 발주입니다.")
            return

        store_id = order[1]

        cur.execute("""
        SELECT pod.barcode_number,
               p.product_name,
               pod.order_quantity
        FROM PurchaseOrderDetail pod
        JOIN Product p ON pod.barcode_number = p.barcode_number
        WHERE pod.order_id = ?
        ORDER BY p.product_name
        """, (order_id,))

        order_items = cur.fetchall()

        if not order_items:
            print("발주 상세 내역이 없습니다.")
            return

        cur.execute("""
        INSERT INTO SupplyRecord (order_id, supplier_id, supplied_at)
        VALUES (?, ?, ?)
        """, (
            order_id,
            supplier_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        receipt_id = cur.lastrowid

        for barcode, product_name, order_quantity in order_items:
            print(f"\n상품명: {product_name}")
            print(f"발주 수량: {order_quantity}")

            supplied_input = input("실제 공급 수량 입력, Enter 시 발주 수량과 동일: ").strip()

            if supplied_input == "":
                supplied_quantity = order_quantity
            else:
                try:
                    supplied_quantity = int(supplied_input)
                except ValueError:
                    print("잘못된 수량입니다. 해당 상품은 발주 수량과 동일하게 처리합니다.")
                    supplied_quantity = order_quantity

            if supplied_quantity <= 0:
                print("공급 수량은 1 이상이어야 하므로 발주 수량과 동일하게 처리합니다.")
                supplied_quantity = order_quantity

            cur.execute("""
            INSERT INTO SupplyRecordDetail (receipt_id, barcode_number, supplied_quantity)
            VALUES (?, ?, ?)
            """, (
                receipt_id,
                barcode,
                supplied_quantity
            ))

            cur.execute("""
            UPDATE StoreInventory
            SET stock_quantity = stock_quantity + ?
            WHERE store_id = ?
              AND barcode_number = ?
            """, (
                supplied_quantity,
                store_id,
                barcode
            ))

        conn.commit()

        print("\n공급 처리가 완료되었습니다.")
        print(f"receipt_id: {receipt_id}")
        print(f"처리된 order_id: {order_id}")

    except Exception as e:
        conn.rollback()
        print("공급 처리 중 오류가 발생했습니다.")
        print(e)

    finally:
        conn.close()


def show_supply_records():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    cur.execute("""
    SELECT sr.receipt_id,
           sr.order_id,
           sr.supplier_id,
           sp.supplier_name,
           sr.supplied_at
    FROM SupplyRecord sr
    JOIN Supplier sp ON sr.supplier_id = sp.supplier_id
    ORDER BY sr.receipt_id
    """)

    rows = cur.fetchall()
    print_rows(rows, ["receipt_id", "order_id", "supplier_id", "supplier_name", "supplied_at"])

    conn.close()


# =========================================================
# 4. 상품/공급업체 관리
# =========================================================

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


# =========================================================
# 5. 고객 관리
# =========================================================

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


# =========================================================
# 6. 통계/테스트 쿼리
# =========================================================

def statistics_menu():
    while True:
        print("\n[통계/테스트 쿼리/DBA 조회]")
        print("1. 각 매장별 가장 많이 판매된 상위 20개 제품")
        print("2. 시·도별 가장 많이 판매된 상위 20개 제품")
        print("3. 판매 실적이 우수한 상위 5개 매장")
        print("4. 특정 제품 B가 제품 A보다 더 많이 판매된 매장 수")
        print("5. 특정 제품과 함께 가장 많이 구매된 제품 상위 3개")
        print("6. DBA SQL 조회")
        print("7. 뒤로가기")

        choice = input("선택: ").strip()

        if choice == "1":
            query_top20_products_by_store()
        elif choice == "2":
            query_top20_products_by_state()
        elif choice == "3":
            query_top5_stores_by_sales()
        elif choice == "4":
            query_compare_two_products_by_store()
        elif choice == "5":
            query_products_bought_together()
        elif choice == "6":
            dba_sql_menu()
        elif choice == "7":
            break
        else:
            print("잘못된 입력입니다.")


def query_top20_products_by_store():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    cur.execute("""
    WITH product_sales AS (
        SELECT s.store_id,
               st.city,
               p.product_name,
               SUM(sd.quantity) AS total_quantity,
               SUM(sd.quantity * sd.unit_price) AS total_sales
        FROM Sale s
        JOIN Store st ON s.store_id = st.store_id
        JOIN SaleDetail sd ON s.sale_id = sd.sale_id
        JOIN Product p ON sd.barcode_number = p.barcode_number
        GROUP BY s.store_id, st.city, p.product_name
    ),
    ranked AS (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY store_id
                   ORDER BY total_quantity DESC, total_sales DESC
               ) AS ranking
        FROM product_sales
    )
    SELECT store_id, city, ranking, product_name, total_quantity, total_sales
    FROM ranked
    WHERE ranking <= 20
    ORDER BY store_id, ranking
    """)

    rows = cur.fetchall()
    print_rows(rows, ["store_id", "city", "ranking", "product_name", "total_quantity", "total_sales"])

    conn.close()


def query_top20_products_by_state():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    cur.execute("""
    WITH product_sales AS (
        SELECT st.state,
               p.product_name,
               SUM(sd.quantity) AS total_quantity,
               SUM(sd.quantity * sd.unit_price) AS total_sales
        FROM Sale s
        JOIN Store st ON s.store_id = st.store_id
        JOIN SaleDetail sd ON s.sale_id = sd.sale_id
        JOIN Product p ON sd.barcode_number = p.barcode_number
        GROUP BY st.state, p.product_name
    ),
    ranked AS (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY state
                   ORDER BY total_quantity DESC, total_sales DESC
               ) AS ranking
        FROM product_sales
    )
    SELECT state, ranking, product_name, total_quantity, total_sales
    FROM ranked
    WHERE ranking <= 20
    ORDER BY state, ranking
    """)

    rows = cur.fetchall()
    print_rows(rows, ["state", "ranking", "product_name", "total_quantity", "total_sales"])

    conn.close()


def query_top5_stores_by_sales():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    cur.execute("""
    SELECT st.store_id,
           st.state,
           st.city,
           SUM(s.total_amount) AS total_sales,
           COUNT(s.sale_id) AS sale_count
    FROM Sale s
    JOIN Store st ON s.store_id = st.store_id
    GROUP BY st.store_id, st.state, st.city
    ORDER BY total_sales DESC
    LIMIT 5
    """)

    rows = cur.fetchall()
    print_rows(rows, ["store_id", "state", "city", "total_sales", "sale_count"])

    conn.close()


def query_compare_two_products_by_store():
    """
    명세서 예시:
    코카콜라보다 펩시콜라가 더 많이 판매된 매장의 수

    DB에 펩시콜라가 없을 수도 있으므로 제품명을 직접 입력할 수 있게 구현했습니다.
    예: 제품 A = 코카콜라, 제품 B = 스프라이트
    """
    conn = connect_db()
    if conn is None:
        return

    product_a = input("제품 A 입력, 기본값 코카콜라: ").strip()
    product_b = input("제품 B 입력, 기본값 펩시콜라: ").strip()

    if product_a == "":
        product_a = "코카콜라"

    if product_b == "":
        product_b = "펩시콜라"

    cur = conn.cursor()

    cur.execute("""
    WITH product_sales AS (
        SELECT s.store_id,
               p.product_name,
               SUM(sd.quantity) AS total_quantity
        FROM Sale s
        JOIN SaleDetail sd ON s.sale_id = sd.sale_id
        JOIN Product p ON sd.barcode_number = p.barcode_number
        WHERE p.product_name LIKE ?
           OR p.product_name LIKE ?
        GROUP BY s.store_id, p.product_name
    ),
    store_compare AS (
        SELECT store_id,
               SUM(CASE WHEN product_name LIKE ? THEN total_quantity ELSE 0 END) AS product_a_quantity,
               SUM(CASE WHEN product_name LIKE ? THEN total_quantity ELSE 0 END) AS product_b_quantity
        FROM product_sales
        GROUP BY store_id
    )
    SELECT COUNT(*) AS store_count
    FROM store_compare
    WHERE product_b_quantity > product_a_quantity
    """, (
        f"%{product_a}%",
        f"%{product_b}%",
        f"%{product_a}%",
        f"%{product_b}%"
    ))

    rows = cur.fetchall()
    print(f"\n'{product_b}'가 '{product_a}'보다 더 많이 판매된 매장 수")
    print_rows(rows, ["store_count"])

    conn.close()


def query_products_bought_together():
    """
    명세서 예시:
    소비자가 우유와 함께 가장 많이 구매한 제품 상위 3개

    DB의 상품명이 '바나나맛우유'처럼 저장되어 있어도 LIKE 검색으로 동작합니다.
    """
    conn = connect_db()
    if conn is None:
        return

    base_product = input("기준 제품 입력, 기본값 우유: ").strip()

    if base_product == "":
        base_product = "우유"

    cur = conn.cursor()

    cur.execute("""
    WITH base_sales AS (
        SELECT DISTINCT sd.sale_id
        FROM SaleDetail sd
        JOIN Product p ON sd.barcode_number = p.barcode_number
        WHERE p.product_name LIKE ?
    )
    SELECT p.product_name,
           COUNT(DISTINCT sd.sale_id) AS together_sale_count,
           SUM(sd.quantity) AS total_quantity
    FROM SaleDetail sd
    JOIN Product p ON sd.barcode_number = p.barcode_number
    WHERE sd.sale_id IN (
        SELECT sale_id FROM base_sales
    )
      AND p.product_name NOT LIKE ?
    GROUP BY p.product_name
    ORDER BY together_sale_count DESC, total_quantity DESC
    LIMIT 3
    """, (
        f"%{base_product}%",
        f"%{base_product}%"
    ))

    rows = cur.fetchall()
    print(f"\n'{base_product}'와 함께 가장 많이 구매된 제품 상위 3개")
    print_rows(rows, ["product_name", "together_sale_count", "total_quantity"])

    conn.close()


def show_inventory_value():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    cur.execute("""
    SELECT si.store_id,
           st.state,
           st.city,
           SUM(si.stock_quantity * si.selling_price) AS inventory_value
    FROM StoreInventory si
    JOIN Store st ON si.store_id = st.store_id
    GROUP BY si.store_id, st.state, st.city
    ORDER BY inventory_value DESC
    """)

    rows = cur.fetchall()
    print_rows(rows, ["store_id", "state", "city", "inventory_value"])

    conn.close()


# =========================================================
# 7. DBA용 SQL 실행 메뉴
# =========================================================

def dba_sql_menu():
    """
    DBA 사용자를 위한 간단한 SQL 실행 기능입니다.
    SELECT 계열 조회 쿼리만 허용합니다.
    데이터 변경은 다른 기능 메뉴를 통해 수행하도록 제한했습니다.
    """
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    print("\n[DBA SQL 조회]")
    print("SELECT/WITH/PRAGMA로 시작하는 조회 쿼리만 실행 가능합니다.")
    print("종료하려면 Enter만 입력하세요.")

    while True:
        sql = input("\nSQL> ").strip()

        if sql == "":
            break

        allowed = (
            sql.lower().startswith("select")
            or sql.lower().startswith("with")
            or sql.lower().startswith("pragma")
        )

        if not allowed:
            print("안전을 위해 SELECT, WITH, PRAGMA 조회 쿼리만 허용합니다.")
            continue

        try:
            cur.execute(sql)
            rows = cur.fetchall()
            print_rows(rows)

        except Exception as e:
            print("SQL 실행 중 오류가 발생했습니다.")
            print(e)

    conn.close()


# =========================================================
# 메인 메뉴
# =========================================================

def main():
    if not check_database_ready():
        return

    if not ensure_supply_tables():
        return

    while True:
        print("\n=== 편의점 DB 시스템 ===")
        print("1. 판매 관리")
        print("2. 재고 관리")
        print("3. 발주/공급 관리")
        print("4. 상품/공급업체 관리")
        print("5. 고객 관리")
        print("6. 통계/테스트 쿼리/DBA 조회")
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
