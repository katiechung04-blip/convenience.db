import sqlite3

DB_NAME = "convenience.db"

def build_and_fill_db():
    # 1. 데이터베이스 파일 연결 및 외래키 활성화
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    
    print("1. 테이블 구조(Schema) 생성 중...")
    
    # 2. 작성하신 main.py의 SQL문과 일치하는 테이블들 생성
    cur.execute("CREATE TABLE IF NOT EXISTS Store (store_id TEXT PRIMARY KEY, city TEXT);")
    cur.execute("CREATE TABLE IF NOT EXISTS Brand (brand_id TEXT PRIMARY KEY, brand_name TEXT);")
    cur.execute("CREATE TABLE IF NOT EXISTS Product (barcode_number TEXT PRIMARY KEY, product_name TEXT, specification TEXT, packaging TEXT, brand_id TEXT, FOREIGN KEY(brand_id) REFERENCES Brand(brand_id));")
    cur.execute("CREATE TABLE IF NOT EXISTS StoreInventory (store_id TEXT, barcode_number TEXT, stock_quantity INTEGER, selling_price INTEGER, PRIMARY KEY(store_id, barcode_number));")
    cur.execute("CREATE TABLE IF NOT EXISTS Supplier (supplier_id TEXT PRIMARY KEY, supplier_name TEXT, phone_number TEXT);")
    cur.execute("CREATE TABLE IF NOT EXISTS PurchaseOrder (order_id TEXT PRIMARY KEY, store_id TEXT, supplier_id TEXT, order_date TEXT);")
    cur.execute("CREATE TABLE IF NOT EXISTS PurchaseOrderDetail (order_id TEXT, barcode_number TEXT, order_quantity INTEGER, PRIMARY KEY(order_id, barcode_number));")
    cur.execute("CREATE TABLE IF NOT EXISTS ProductSupplier (supplier_id TEXT, barcode_number TEXT, supply_price INTEGER, PRIMARY KEY(supplier_id, barcode_number));")
    cur.execute("CREATE TABLE IF NOT EXISTS Customer (customer_id TEXT PRIMARY KEY, phone_number TEXT);")
    cur.execute("CREATE TABLE IF NOT EXISTS Member (customer_id TEXT PRIMARY KEY, member_name TEXT, point INTEGER, FOREIGN KEY(customer_id) REFERENCES Customer(customer_id));")
    cur.execute("CREATE TABLE IF NOT EXISTS Sale (sale_id TEXT PRIMARY KEY, store_id TEXT, customer_id TEXT, sale_date TEXT, total_amount INTEGER);")
    cur.execute("CREATE TABLE IF NOT EXISTS SaleDetail (sale_id TEXT, barcode_number TEXT, quantity INTEGER, unit_price INTEGER, PRIMARY KEY(sale_id, barcode_number));")

    print("2. 기능 평가용 샘플 데이터 적재 중...")
    
    # 3. main.py의 각 통계 및 조회 메뉴에서 에러 없이 데이터가 출력되도록 샘플 데이터 삽입
    cur.executemany("INSERT OR IGNORE INTO Store VALUES (?, ?);", [('S01', '서울시'), ('S02', '부산시')])
    cur.executemany("INSERT OR IGNORE INTO Brand VALUES (?, ?);", [('B01', '칠성'), ('B02', '농심')])
    
    cur.executemany("INSERT OR IGNORE INTO Product VALUES (?, ?, ?, ?, ?);", [
        ('P001', '칠성사이다', '500ml', '페트병', 'B01'),
        ('P002', '신라면 블랙', '134g', '컵라면', 'B02')
    ])
    
    # 전체 재고 및 재고 부족(5개 이하) 테스트용 데이터
    cur.executemany("INSERT OR IGNORE INTO StoreInventory VALUES (?, ?, ?, ?);", [
        ('S01', 'P001', 3, 2000),  # 재고가 3개라 '재고 부족 상품'에 걸림
        ('S01', 'P002', 15, 1600),
        ('S02', 'P001', 20, 2100)
    ])
    
    cur.executemany("INSERT OR IGNORE INTO Supplier VALUES (?, ?, ?);", [
        ('SUP01', '대형유통네트웍스', '02-123-4567'),
        ('SUP02', '백산물류', '031-987-6543')
    ])
    
    cur.executemany("INSERT OR IGNORE INTO ProductSupplier VALUES (?, ?, ?);", [
        ('SUP01', 'P001', 1200),
        ('SUP02', 'P002', 900)
    ])
    
    cur.executemany("INSERT OR IGNORE INTO PurchaseOrder VALUES (?, ?, ?, ?);", [('O001', 'S01', 'SUP01', '2026-06-18')])
    cur.executemany("INSERT OR IGNORE INTO PurchaseOrderDetail VALUES (?, ?, ?);", [('O001', 'P001', 100)])
    
    # 고객 및 회원 데이터 (Supertype/Subtype 관계 반영)
    cur.executemany("INSERT OR IGNORE INTO Customer VALUES (?, ?);", [('C001', '010-1111-2222'), ('C002', '010-3333-4444')])
    cur.executemany("INSERT OR IGNORE INTO Member VALUES (?, ?, ?);", [('C001', '이영희', 1500)])
    
    # 통계 쿼리(SUM, GROUP BY)용 판매 내역 데이터
    cur.executemany("INSERT OR IGNORE INTO Sale VALUES (?, ?, ?, ?, ?);", [
        ('SALE01', 'S01', 'C001', '2026-06-18', 4000),
        ('SALE02', 'S02', 'C002', '2026-06-18', 1600)
    ])
    cur.executemany("INSERT OR IGNORE INTO SaleDetail VALUES (?, ?, ?, ?);", [
        ('SALE01', 'P001', 2, 2000),
        ('SALE02', 'P002', 1, 1600)
    ])

    conn.commit()
    conn.close()
    print("🎉 convenience.db 파일이 성공적으로 만들어졌습니다!")

if __name__ == "__main__":
    build_and_fill_db()
