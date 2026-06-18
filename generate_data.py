import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_NAME = "convenience.db"

random.seed(42)


def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def reset_db():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print("기존 convenience.db 삭제 완료")


def create_tables():
    conn = connect_db()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE Store (
        store_id INTEGER PRIMARY KEY,
        state TEXT NOT NULL,
        city TEXT NOT NULL,
        street_name TEXT NOT NULL,
        street_number TEXT NOT NULL,
        open_time TEXT NOT NULL,
        close_time TEXT NOT NULL
    );

    CREATE TABLE Brand (
        brand_id INTEGER PRIMARY KEY,
        brand_name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE Product (
        barcode_number TEXT PRIMARY KEY,
        product_name TEXT NOT NULL,
        specification TEXT,
        packaging TEXT,
        brand_id INTEGER NOT NULL,
        FOREIGN KEY (brand_id) REFERENCES Brand(brand_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    );

    CREATE TABLE ProductType (
        type_id INTEGER PRIMARY KEY,
        type_name TEXT NOT NULL,
        parent_type_id INTEGER,
        FOREIGN KEY (parent_type_id) REFERENCES ProductType(type_id)
            ON UPDATE CASCADE
            ON DELETE SET NULL
    );

    CREATE TABLE ProductTypeAssignment (
        barcode_number TEXT NOT NULL,
        type_id INTEGER NOT NULL,
        PRIMARY KEY (barcode_number, type_id),
        FOREIGN KEY (barcode_number) REFERENCES Product(barcode_number)
            ON UPDATE CASCADE
            ON DELETE CASCADE,
        FOREIGN KEY (type_id) REFERENCES ProductType(type_id)
            ON UPDATE CASCADE
            ON DELETE CASCADE
    );

    CREATE TABLE StoreInventory (
        store_id INTEGER NOT NULL,
        barcode_number TEXT NOT NULL,
        stock_quantity INTEGER NOT NULL CHECK(stock_quantity >= 0),
        selling_price INTEGER NOT NULL CHECK(selling_price >= 0),
        PRIMARY KEY (store_id, barcode_number),
        FOREIGN KEY (store_id) REFERENCES Store(store_id)
            ON UPDATE CASCADE
            ON DELETE CASCADE,
        FOREIGN KEY (barcode_number) REFERENCES Product(barcode_number)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    );

    CREATE TABLE Customer (
        customer_id INTEGER PRIMARY KEY,
        phone_number TEXT NOT NULL UNIQUE
    );

    CREATE TABLE Member (
        customer_id INTEGER PRIMARY KEY,
        member_name TEXT NOT NULL,
        point INTEGER NOT NULL DEFAULT 0 CHECK(point >= 0),
        FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
            ON UPDATE CASCADE
            ON DELETE CASCADE
    );

    CREATE TABLE NonMember (
        customer_id INTEGER PRIMARY KEY,
        FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
            ON UPDATE CASCADE
            ON DELETE CASCADE
    );

    CREATE TABLE Sale (
        sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_id INTEGER NOT NULL,
        customer_id INTEGER,
        sale_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        total_amount INTEGER NOT NULL DEFAULT 0 CHECK(total_amount >= 0),
        FOREIGN KEY (store_id) REFERENCES Store(store_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,
        FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
            ON UPDATE CASCADE
            ON DELETE SET NULL
    );

    CREATE TABLE SaleDetail (
        sale_id INTEGER NOT NULL,
        barcode_number TEXT NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        unit_price INTEGER NOT NULL CHECK(unit_price >= 0),
        PRIMARY KEY (sale_id, barcode_number),
        FOREIGN KEY (sale_id) REFERENCES Sale(sale_id)
            ON UPDATE CASCADE
            ON DELETE CASCADE,
        FOREIGN KEY (barcode_number) REFERENCES Product(barcode_number)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    );

    CREATE TABLE Supplier (
        supplier_id INTEGER PRIMARY KEY,
        supplier_name TEXT NOT NULL,
        phone_number TEXT
    );

    CREATE TABLE ProductSupplier (
        supplier_id INTEGER NOT NULL,
        barcode_number TEXT NOT NULL,
        supply_price INTEGER NOT NULL CHECK(supply_price >= 0),
        PRIMARY KEY (supplier_id, barcode_number),
        FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id)
            ON UPDATE CASCADE
            ON DELETE CASCADE,
        FOREIGN KEY (barcode_number) REFERENCES Product(barcode_number)
            ON UPDATE CASCADE
            ON DELETE CASCADE
    );

    CREATE TABLE PurchaseOrder (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_id INTEGER NOT NULL,
        supplier_id INTEGER NOT NULL,
        order_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (store_id) REFERENCES Store(store_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,
        FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    );

    CREATE TABLE PurchaseOrderDetail (
        order_id INTEGER NOT NULL,
        barcode_number TEXT NOT NULL,
        order_quantity INTEGER NOT NULL CHECK(order_quantity > 0),
        PRIMARY KEY (order_id, barcode_number),
        FOREIGN KEY (order_id) REFERENCES PurchaseOrder(order_id)
            ON UPDATE CASCADE
            ON DELETE CASCADE,
        FOREIGN KEY (barcode_number) REFERENCES Product(barcode_number)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    );
    """)

    conn.commit()
    conn.close()
    print("테이블 생성 완료")


def insert_stores(cur):
    stores = [
        (1, "서울특별시", "강남구", "테헤란로", "101", "00:00", "23:59"),
        (2, "서울특별시", "마포구", "양화로", "25", "00:00", "23:59"),
        (3, "경기도", "남양주시", "경춘로", "88", "07:00", "23:00"),
        (4, "경기도", "수원시", "권선로", "45", "06:00", "24:00"),
        (5, "인천광역시", "부평구", "부평대로", "13", "00:00", "23:59")
    ]

    cur.executemany("""
    INSERT INTO Store
    (store_id, state, city, street_name, street_number, open_time, close_time)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, stores)


def insert_brands_and_products(cur):
    brands = [
        (1, "농심"),
        (2, "삼양"),
        (3, "오뚜기"),
        (4, "롯데"),
        (5, "빙그레"),
        (6, "코카콜라"),
        (7, "동원"),
        (8, "CJ"),
        (9, "해태"),
        (10, "유한킴벌리")
    ]

    products = [
        ("880100000001", "신라면", "120g", "봉지", 1),
        ("880100000002", "짜파게티", "140g", "봉지", 1),
        ("880100000003", "새우깡", "90g", "봉지", 1),
        ("880100000004", "삼양라면", "120g", "봉지", 2),
        ("880100000005", "불닭볶음면", "140g", "봉지", 2),
        ("880100000006", "진라면 매운맛", "120g", "봉지", 3),
        ("880100000007", "오뚜기밥", "210g", "용기", 3),
        ("880100000008", "초코파이", "12개입", "박스", 4),
        ("880100000009", "몽쉘", "12개입", "박스", 4),
        ("880100000010", "바나나맛우유", "240ml", "병", 5),
        ("880100000011", "요플레", "85g", "컵", 5),
        ("880100000012", "코카콜라", "500ml", "페트병", 6),
        ("880100000013", "스프라이트", "500ml", "페트병", 6),
        ("880100000014", "동원참치", "100g", "캔", 7),
        ("880100000015", "양반김", "10봉", "봉지", 7),
        ("880100000016", "햇반", "210g", "용기", 8),
        ("880100000017", "비비고 만두", "400g", "봉지", 8),
        ("880100000018", "에이스", "121g", "박스", 9),
        ("880100000019", "홈런볼", "146g", "봉지", 9),
        ("880100000020", "크리넥스 티슈", "250매", "박스", 10),
        ("880100000021", "물티슈", "100매", "팩", 10),
        ("880100000022", "삼다수", "500ml", "페트병", 6),
        ("880100000023", "컵누들", "38g", "컵", 3),
        ("880100000024", "사리곰탕면", "110g", "봉지", 1),
        ("880100000025", "포카칩", "66g", "봉지", 4)
    ]

    cur.executemany("""
    INSERT INTO Brand (brand_id, brand_name)
    VALUES (?, ?)
    """, brands)

    cur.executemany("""
    INSERT INTO Product
    (barcode_number, product_name, specification, packaging, brand_id)
    VALUES (?, ?, ?, ?, ?)
    """, products)

    return products


def insert_product_types(cur):
    product_types = [
        (1, "식품", None),
        (2, "생활용품", None),
        (3, "라면", 1),
        (4, "과자", 1),
        (5, "음료", 1),
        (6, "즉석식품", 1),
        (7, "유제품", 1),
        (8, "통조림", 1),
        (9, "위생용품", 2)
    ]

    assignments = [
        ("880100000001", 3),
        ("880100000002", 3),
        ("880100000003", 4),
        ("880100000004", 3),
        ("880100000005", 3),
        ("880100000006", 3),
        ("880100000007", 6),
        ("880100000008", 4),
        ("880100000009", 4),
        ("880100000010", 7),
        ("880100000011", 7),
        ("880100000012", 5),
        ("880100000013", 5),
        ("880100000014", 8),
        ("880100000015", 6),
        ("880100000016", 6),
        ("880100000017", 6),
        ("880100000018", 4),
        ("880100000019", 4),
        ("880100000020", 9),
        ("880100000021", 9),
        ("880100000022", 5),
        ("880100000023", 3),
        ("880100000024", 3),
        ("880100000025", 4)
    ]

    cur.executemany("""
    INSERT INTO ProductType (type_id, type_name, parent_type_id)
    VALUES (?, ?, ?)
    """, product_types)

    cur.executemany("""
    INSERT INTO ProductTypeAssignment (barcode_number, type_id)
    VALUES (?, ?)
    """, assignments)


def insert_suppliers(cur, products):
    suppliers = [
        (1, "대한식품물류", "02-1111-2222"),
        (2, "서울음료유통", "02-3333-4444"),
        (3, "편의점종합물류", "031-555-6666"),
        (4, "생활용품유통", "032-777-8888")
    ]

    cur.executemany("""
    INSERT INTO Supplier (supplier_id, supplier_name, phone_number)
    VALUES (?, ?, ?)
    """, suppliers)

    for product in products:
        barcode = product[0]
        product_name = product[1]

        if "코카콜라" in product_name or "스프라이트" in product_name or "삼다수" in product_name:
            supplier_ids = [2, 3]
        elif "티슈" in product_name or "물티슈" in product_name:
            supplier_ids = [4, 3]
        else:
            supplier_ids = [1, 3]

        for supplier_id in supplier_ids:
            supply_price = random.randint(600, 2600)

            cur.execute("""
            INSERT INTO ProductSupplier (supplier_id, barcode_number, supply_price)
            VALUES (?, ?, ?)
            """, (supplier_id, barcode, supply_price))


def insert_inventory(cur, products):
    for store_id in range(1, 6):
        for product in products:
            barcode = product[0]
            stock_quantity = random.randint(20, 80)
            selling_price = random.randrange(1200, 4500, 100)

            cur.execute("""
            INSERT INTO StoreInventory
            (store_id, barcode_number, stock_quantity, selling_price)
            VALUES (?, ?, ?, ?)
            """, (store_id, barcode, stock_quantity, selling_price))


def insert_customers(cur):
    customers = [
        (1, "010-1111-1111"),
        (2, "010-2222-2222"),
        (3, "010-3333-3333"),
        (4, "010-4444-4444"),
        (5, "010-5555-5555"),
        (6, "010-6666-6666"),
        (7, "010-7777-7777"),
        (8, "010-8888-8888"),
        (9, "010-9999-9999"),
        (10, "010-0000-0000")
    ]

    members = [
        (1, "김민수", 1200),
        (2, "이서연", 850),
        (3, "박지훈", 300),
        (4, "최유진", 2150),
        (5, "정하늘", 640),
        (6, "강도윤", 430)
    ]

    non_members = [
        (7,),
        (8,),
        (9,),
        (10,)
    ]

    cur.executemany("""
    INSERT INTO Customer (customer_id, phone_number)
    VALUES (?, ?)
    """, customers)

    cur.executemany("""
    INSERT INTO Member (customer_id, member_name, point)
    VALUES (?, ?, ?)
    """, members)

    cur.executemany("""
    INSERT INTO NonMember (customer_id)
    VALUES (?)
    """, non_members)


def insert_sales(cur):
    for _ in range(45):
        store_id = random.randint(1, 5)
        customer_id = random.randint(1, 10)
        sale_date = datetime.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))

        cur.execute("""
        INSERT INTO Sale (store_id, customer_id, sale_date, total_amount)
        VALUES (?, ?, ?, 0)
        """, (
            store_id,
            customer_id,
            sale_date.strftime("%Y-%m-%d %H:%M:%S")
        ))

        sale_id = cur.lastrowid
        total_amount = 0

        cur.execute("""
        SELECT barcode_number, stock_quantity, selling_price
        FROM StoreInventory
        WHERE store_id = ?
          AND stock_quantity > 0
        """, (store_id,))

        available_items = cur.fetchall()

        if not available_items:
            continue

        selected_items = random.sample(
            available_items,
            min(random.randint(1, 4), len(available_items))
        )

        for barcode, stock_quantity, selling_price in selected_items:
            quantity = random.randint(1, min(3, stock_quantity))
            subtotal = quantity * selling_price
            total_amount += subtotal

            cur.execute("""
            INSERT INTO SaleDetail
            (sale_id, barcode_number, quantity, unit_price)
            VALUES (?, ?, ?, ?)
            """, (
                sale_id,
                barcode,
                quantity,
                selling_price
            ))

            cur.execute("""
            UPDATE StoreInventory
            SET stock_quantity = stock_quantity - ?
            WHERE store_id = ?
              AND barcode_number = ?
            """, (
                quantity,
                store_id,
                barcode
            ))

        cur.execute("""
        UPDATE Sale
        SET total_amount = ?
        WHERE sale_id = ?
        """, (
            total_amount,
            sale_id
        ))

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
            """, (
                earned_point,
                customer_id
            ))


def insert_purchase_orders(cur):
    for _ in range(20):
        store_id = random.randint(1, 5)
        supplier_id = random.randint(1, 4)
        order_date = datetime.now() - timedelta(days=random.randint(0, 20))

        cur.execute("""
        INSERT INTO PurchaseOrder (store_id, supplier_id, order_date)
        VALUES (?, ?, ?)
        """, (
            store_id,
            supplier_id,
            order_date.strftime("%Y-%m-%d %H:%M:%S")
        ))

        order_id = cur.lastrowid

        cur.execute("""
        SELECT barcode_number
        FROM ProductSupplier
        WHERE supplier_id = ?
        """, (supplier_id,))

        supplier_products = [row[0] for row in cur.fetchall()]

        selected_products = random.sample(
            supplier_products,
            min(random.randint(1, 4), len(supplier_products))
        )

        for barcode in selected_products:
            order_quantity = random.randint(5, 40)

            cur.execute("""
            INSERT INTO PurchaseOrderDetail
            (order_id, barcode_number, order_quantity)
            VALUES (?, ?, ?)
            """, (
                order_id,
                barcode,
                order_quantity
            ))


def verify_data():
    conn = connect_db()
    cur = conn.cursor()

    tables = [
        "Store",
        "Brand",
        "Product",
        "ProductType",
        "ProductTypeAssignment",
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

    print("\n=== 생성된 데이터 개수 확인 ===")

    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"{table}: {count}개")

    print("\n=== 테스트용 주요 ID ===")
    print("매장 ID: 1 ~ 5")
    print("공급업체 ID: 1 ~ 4")
    print("고객 ID: 1 ~ 10")
    print("상품 바코드 예시:")
    print("880100000001 신라면")
    print("880100000012 코카콜라")
    print("880100000020 크리넥스 티슈")

    conn.close()


def main():
    reset_db()
    create_tables()

    conn = connect_db()
    cur = conn.cursor()

    products = None

    try:
        insert_stores(cur)
        products = insert_brands_and_products(cur)
        insert_product_types(cur)
        insert_suppliers(cur, products)
        insert_inventory(cur, products)
        insert_customers(cur)
        insert_sales(cur)
        insert_purchase_orders(cur)

        conn.commit()
        print("\nconvenience.db 데이터 생성 완료!")

    except Exception as e:
        conn.rollback()
        print("\n데이터 생성 중 오류가 발생했습니다.")
        print(e)

    finally:
        conn.close()

    verify_data()


if __name__ == "__main__":
    main()