"""Order Core Database Store for Sèo Trum Ops (Social Commerce Order System).

Manages:
- ops_orders
- ops_order_items
- ops_products
- ops_customer_addresses
- ops_shipments
- ops_shipping_events
- ops_order_audit_logs

Database file default: STATE_DIR / "ops_orders.sqlite3".
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Generator, List, Optional

import config

DEFAULT_DB_PATH = config.STATE_DIR / "ops_orders.sqlite3"

# Standard Default Product Catalog for Social Commerce
DEFAULT_PRODUCTS = [
    {
        "id": "prod_mos_01",
        "sku": "SKU-MOS-01",
        "name": "Khóa học Tin học Văn phòng MOS Thực chiến",
        "price": 590000,
        "category": "education",
        "stock": 999,
    },
    {
        "id": "prod_pbi_02",
        "sku": "SKU-PBI-02",
        "name": "Khóa học Phân tích Dữ liệu PowerBI & Tự động hóa Excel",
        "price": 1290000,
        "category": "education",
        "stock": 999,
    },
    {
        "id": "prod_book_03",
        "sku": "SKU-BOOK-03",
        "name": "Sách Giáo trình 100 Thủ thuật Excel & Dashboard Thực hành",
        "price": 199000,
        "category": "books",
        "stock": 150,
    },
    {
        "id": "prod_key_04",
        "sku": "SKU-KEY-04",
        "name": "Bàn phím cơ Silent Office Bluetooth 3-mode",
        "price": 850000,
        "category": "hardware",
        "stock": 45,
    },
    {
        "id": "prod_mou_05",
        "sku": "SKU-MOU-05",
        "name": "Chuột không dây công thái học Silent Click",
        "price": 320000,
        "category": "hardware",
        "stock": 80,
    },
]


def get_connection(db_path: Path | str | None = None) -> Generator[sqlite3.Connection, None, None]:
    p = Path(db_path or DEFAULT_DB_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _migrate_db(conn: sqlite3.Connection) -> None:
    """Tự động thêm các cột mới cho database đã tồn tại nếu chưa có."""
    cur = conn.execute("PRAGMA table_info(ops_products)")
    existing_cols = {row["name"] for row in cur.fetchall()}
    
    col_defs = [
        ("description", "TEXT DEFAULT ''"),
        ("sale_price", "INTEGER DEFAULT 0"),
        ("weight_gram", "INTEGER DEFAULT 500"),
        ("dimensions_json", "TEXT DEFAULT '{\"length\":20,\"width\":15,\"height\":10}'"),
        ("image_url", "TEXT DEFAULT ''"),
        ("auto_sell_enabled", "INTEGER DEFAULT 1"),
        ("updated_at", "REAL DEFAULT 0"),
    ]
    for col_name, col_type in col_defs:
        if col_name not in existing_cols:
            try:
                conn.execute(f"ALTER TABLE ops_products ADD COLUMN {col_name} {col_type};")
            except Exception:
                pass


def init_db(db_path: Path | str | None = None, seed_demo: bool = False) -> None:
    """Khởi tạo toàn bộ schema bảng Order Core, Product Catalog đa kênh và Automation Case Engine."""
    for conn in get_connection(db_path):
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS ops_orders (
            id TEXT PRIMARY KEY,
            crm_id TEXT,
            customer_name TEXT,
            customer_phone TEXT,
            page_id TEXT,
            thread_id TEXT,
            status TEXT NOT NULL DEFAULT 'draft',
            total_amount INTEGER DEFAULT 0,
            cod_amount INTEGER DEFAULT 0,
            shipping_fee INTEGER DEFAULT 0,
            payment_method TEXT DEFAULT 'cod',
            shipping_address TEXT,
            customer_notes TEXT,
            internal_notes TEXT,
            ai_confidence REAL DEFAULT 0.0,
            missing_fields TEXT,
            source TEXT DEFAULT 'inbox',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ops_order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            product_id TEXT,
            sku TEXT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            price INTEGER NOT NULL DEFAULT 0,
            total INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (order_id) REFERENCES ops_orders(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ops_products (
            id TEXT PRIMARY KEY,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            price INTEGER NOT NULL DEFAULT 0,
            sale_price INTEGER DEFAULT 0,
            category TEXT DEFAULT 'general',
            is_active INTEGER DEFAULT 1,
            auto_sell_enabled INTEGER DEFAULT 1,
            stock INTEGER DEFAULT 100,
            weight_gram INTEGER DEFAULT 500,
            dimensions_json TEXT DEFAULT '{"length":20,"width":15,"height":10}',
            image_url TEXT DEFAULT '',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS ops_product_variants (
            id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            sku TEXT NOT NULL,
            title TEXT NOT NULL,
            price INTEGER NOT NULL DEFAULT 0,
            stock INTEGER NOT NULL DEFAULT 0,
            attributes_json TEXT DEFAULT '{}',
            created_at REAL NOT NULL,
            FOREIGN KEY (product_id) REFERENCES ops_products(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ops_product_aliases (
            id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            alias TEXT NOT NULL,
            weight REAL DEFAULT 1.0,
            created_at REAL NOT NULL,
            FOREIGN KEY (product_id) REFERENCES ops_products(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ops_product_page_bindings (
            id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            page_id TEXT NOT NULL,
            channel TEXT NOT NULL DEFAULT '*',
            custom_price INTEGER,
            auto_sell_allowed INTEGER DEFAULT 1,
            created_at REAL NOT NULL,
            FOREIGN KEY (product_id) REFERENCES ops_products(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ops_inventory_movements (
            id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            variant_id TEXT,
            delta INTEGER NOT NULL,
            reason TEXT NOT NULL,
            order_id TEXT,
            created_at REAL NOT NULL,
            FOREIGN KEY (product_id) REFERENCES ops_products(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ops_price_books (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            page_id TEXT,
            channel TEXT,
            rules_json TEXT,
            created_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ops_automation_rules (
            id TEXT PRIMARY KEY,
            page_id TEXT NOT NULL DEFAULT '*',
            channel TEXT NOT NULL DEFAULT '*',
            case_type TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            level INTEGER NOT NULL DEFAULT 2,
            min_confidence REAL DEFAULT 0.85,
            require_product_match INTEGER DEFAULT 1,
            require_phone INTEGER DEFAULT 1,
            require_address INTEGER DEFAULT 1,
            max_cod_amount INTEGER DEFAULT 5000000,
            require_staff_approval INTEGER DEFAULT 0,
            message_template TEXT DEFAULT '',
            cooldown_seconds INTEGER DEFAULT 30,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ops_automation_runs (
            id TEXT PRIMARY KEY,
            case_type TEXT NOT NULL,
            thread_id TEXT,
            page_id TEXT,
            order_id TEXT,
            status TEXT NOT NULL,
            decision_reason TEXT NOT NULL,
            payload_json TEXT,
            created_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ops_outbox_messages (
            id TEXT PRIMARY KEY,
            thread_id TEXT,
            page_id TEXT,
            channel TEXT,
            recipient_id TEXT,
            body TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            error TEXT,
            created_at REAL NOT NULL,
            sent_at REAL
        );

        CREATE TABLE IF NOT EXISTS ops_customer_addresses (
            id TEXT PRIMARY KEY,
            crm_id TEXT,
            phone TEXT,
            receiver_name TEXT,
            province TEXT,
            district TEXT,
            ward TEXT,
            street_address TEXT,
            full_address TEXT NOT NULL,
            is_default INTEGER DEFAULT 1,
            created_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ops_shipments (
            id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            provider TEXT NOT NULL DEFAULT 'ghn',
            tracking_code TEXT,
            external_order_code TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            fee INTEGER DEFAULT 0,
            cod_amount INTEGER DEFAULT 0,
            expected_delivery_time TEXT,
            provider_response TEXT,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES ops_orders(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ops_shipping_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shipment_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            status TEXT NOT NULL,
            description TEXT,
            location TEXT,
            event_time REAL NOT NULL,
            raw_payload TEXT,
            FOREIGN KEY (shipment_id) REFERENCES ops_shipments(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ops_order_audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            action TEXT NOT NULL,
            actor TEXT NOT NULL,
            details TEXT,
            created_at REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES ops_orders(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_orders_status ON ops_orders(status);
        CREATE INDEX IF NOT EXISTS idx_orders_crm ON ops_orders(crm_id);
        CREATE INDEX IF NOT EXISTS idx_orders_thread ON ops_orders(thread_id);
        CREATE INDEX IF NOT EXISTS idx_order_items_order ON ops_order_items(order_id);
        CREATE INDEX IF NOT EXISTS idx_shipments_order ON ops_shipments(order_id);
        CREATE INDEX IF NOT EXISTS idx_shipments_tracking ON ops_shipments(tracking_code);
        CREATE INDEX IF NOT EXISTS idx_audit_order ON ops_order_audit_logs(order_id);
        CREATE INDEX IF NOT EXISTS idx_aliases_alias ON ops_product_aliases(alias);
        CREATE INDEX IF NOT EXISTS idx_aliases_product ON ops_product_aliases(product_id);
        CREATE INDEX IF NOT EXISTS idx_bindings_page ON ops_product_page_bindings(page_id, channel);
        CREATE INDEX IF NOT EXISTS idx_bindings_product ON ops_product_page_bindings(product_id);
        CREATE INDEX IF NOT EXISTS idx_auto_runs_thread ON ops_automation_runs(thread_id);
        CREATE INDEX IF NOT EXISTS idx_auto_runs_created ON ops_automation_runs(created_at);
        CREATE INDEX IF NOT EXISTS idx_outbox_status ON ops_outbox_messages(status);
        """)

        _migrate_db(conn)
        init_default_automation_rules(page_id="*", db_path=db_path)

        if seed_demo:
            seed_demo_products(db_path)

        conn.commit()


def seed_demo_products(db_path: Path | str | None = None) -> List[dict]:
    """Chỉ gọi hàm này khi explicitly muốn nạp sản phẩm demo (dùng cho tests hoặc sandbox)."""
    now = time.time()
    for conn in get_connection(db_path):
        for prod in DEFAULT_PRODUCTS:
            conn.execute(
                """
                INSERT INTO ops_products (id, sku, name, description, price, sale_price, category, is_active, auto_sell_enabled, stock, weight_gram, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1, ?, 500, ?, ?)
                ON CONFLICT(sku) DO UPDATE SET
                    name=excluded.name,
                    price=excluded.price,
                    stock=excluded.stock
                """,
                (
                    prod["id"],
                    prod["sku"],
                    prod["name"],
                    prod.get("description", "Sản phẩm thử nghiệm Social Commerce"),
                    prod["price"],
                    prod.get("sale_price", 0),
                    prod["category"],
                    prod["stock"],
                    now,
                    now,
                ),
            )
            # Default binding to *
            conn.execute(
                """
                INSERT OR IGNORE INTO ops_product_page_bindings (id, product_id, page_id, channel, auto_sell_allowed, created_at)
                VALUES (?, ?, '*', '*', 1, ?)
                """,
                (f"bind_{prod['id']}_all", prod["id"], now),
            )
        conn.commit()
    return list_products(db_path)


# ============================================================
# Products CRUD & Page Scoped Bindings
# ============================================================

def list_products(
    db_path: Path | str | None = None,
    page_id: Optional[str] = None,
    channel: Optional[str] = None,
    active_only: bool = False,
    include_details: bool = True,
) -> List[dict]:
    """Lấy danh sách sản phẩm. Nếu có page_id, chỉ lấy sản phẩm gắn với page_id đó hoặc gắn toàn cục (*)."""
    init_db(db_path)
    for conn in get_connection(db_path):
        if page_id:
            # Query strictly bound products for this page
            p_sql = """
                SELECT DISTINCT p.*, b.custom_price, b.auto_sell_allowed, b.id as binding_id
                FROM ops_products p
                JOIN ops_product_page_bindings b ON p.id = b.product_id
                WHERE (b.page_id = ? OR b.page_id = '*')
            """
            params: list[Any] = [str(page_id).strip()]
            if channel and channel != "*":
                p_sql += " AND (b.channel = ? OR b.channel = '*')"
                params.append(channel.strip().lower())
            if active_only:
                p_sql += " AND p.is_active = 1 AND b.auto_sell_allowed = 1"
            p_sql += " ORDER BY p.category, p.price DESC"
            cur = conn.execute(p_sql, tuple(params))
        else:
            p_sql = "SELECT p.*, NULL as custom_price, p.auto_sell_enabled as auto_sell_allowed, NULL as binding_id FROM ops_products p WHERE 1=1"
            if active_only:
                p_sql += " AND p.is_active = 1"
            p_sql += " ORDER BY p.category, p.price DESC"
            cur = conn.execute(p_sql)

        rows = []
        for r in cur.fetchall():
            d = dict(r)
            # Override price with custom_price if specified in page binding
            if d.get("custom_price") is not None and d["custom_price"] > 0:
                d["original_price"] = d["price"]
                d["price"] = d["custom_price"]

            if include_details:
                # Aliases
                cur_al = conn.execute("SELECT id, alias, weight FROM ops_product_aliases WHERE product_id = ?", (d["id"],))
                alias_rows = [dict(a) for a in cur_al.fetchall()]
                d["aliases"] = [a["alias"] for a in alias_rows]
                d["alias_items"] = alias_rows

                # Variants
                cur_vr = conn.execute("SELECT * FROM ops_product_variants WHERE product_id = ? ORDER BY price ASC", (d["id"],))
                d["variants"] = [dict(v) for v in cur_vr.fetchall()]

                # Bindings
                cur_b = conn.execute("SELECT * FROM ops_product_page_bindings WHERE product_id = ?", (d["id"],))
                d["page_bindings"] = [dict(b) for b in cur_b.fetchall()]

            rows.append(d)
        return rows
    return []


def get_product(product_id_or_sku: str, db_path: Path | str | None = None) -> Optional[dict]:
    """Tìm sản phẩm theo id hoặc sku, kèm aliases, variants và page bindings."""
    if not product_id_or_sku:
        return None
    init_db(db_path)
    clean_val = str(product_id_or_sku).strip()
    for conn in get_connection(db_path):
        cur = conn.execute(
            "SELECT * FROM ops_products WHERE id = ? OR LOWER(sku) = LOWER(?) LIMIT 1",
            (clean_val, clean_val),
        )
        row = cur.fetchone()
        if not row:
            return None
        d = dict(row)

        cur_al = conn.execute("SELECT id, alias, weight FROM ops_product_aliases WHERE product_id = ?", (d["id"],))
        alias_rows = [dict(a) for a in cur_al.fetchall()]
        d["aliases"] = [a["alias"] for a in alias_rows]
        d["alias_items"] = alias_rows

        cur_vr = conn.execute("SELECT * FROM ops_product_variants WHERE product_id = ? ORDER BY price ASC", (d["id"],))
        d["variants"] = [dict(v) for v in cur_vr.fetchall()]

        cur_b = conn.execute("SELECT * FROM ops_product_page_bindings WHERE product_id = ?", (d["id"],))
        d["page_bindings"] = [dict(b) for b in cur_b.fetchall()]

        return d
    return None


def get_product_by_sku(sku: str, db_path: Path | str | None = None) -> Optional[dict]:
    return get_product(sku, db_path)


def search_products(keyword: str, page_id: Optional[str] = None, db_path: Path | str | None = None) -> List[dict]:
    """Tìm kiếm sản phẩm theo từ khóa tên, SKU hoặc alias từ khóa khách hay gọi."""
    init_db(db_path)
    k_clean = keyword.strip().lower() if keyword else ""
    if not k_clean:
        return list_products(db_path=db_path, page_id=page_id, active_only=True)

    all_prods = list_products(db_path=db_path, page_id=page_id, active_only=True, include_details=True)
    matched = []
    for p in all_prods:
        sku = (p.get("sku") or "").lower()
        name = (p.get("name") or "").lower()
        desc = (p.get("description") or "").lower()
        aliases = [str(a).lower() for a in p.get("aliases", [])]

        if k_clean in sku or k_clean in name or k_clean in desc or any(k_clean in a or a in k_clean for a in aliases):
            matched.append(p)
    return matched


def create_product(data: dict, db_path: Path | str | None = None) -> dict:
    """Tạo mới một sản phẩm trong Catalog."""
    init_db(db_path)
    now = time.time()
    prod_id = str(data.get("id") or f"prod_{uuid.uuid4().hex[:8]}")
    sku = str(data.get("sku") or "").strip().upper()
    if not sku:
        raise ValueError("Mã SKU là bắt buộc")
    name = str(data.get("name") or "").strip()
    if not name:
        raise ValueError("Tên sản phẩm là bắt buộc")

    price = int(data.get("price") or 0)
    sale_price = int(data.get("sale_price") or 0)
    stock = int(data.get("stock") or 0)
    weight_gram = int(data.get("weight_gram") or 500)
    category = str(data.get("category") or "general").strip()
    description = str(data.get("description") or "").strip()
    image_url = str(data.get("image_url") or "").strip()
    is_active = 1 if data.get("is_active", True) in (True, 1, "1", "true") else 0
    auto_sell = 1 if data.get("auto_sell_enabled", True) in (True, 1, "1", "true") else 0
    dims = json.dumps(data.get("dimensions") or {"length": 20, "width": 15, "height": 10})

    for conn in get_connection(db_path):
        conn.execute(
            """
            INSERT INTO ops_products (
                id, sku, name, description, price, sale_price, category,
                is_active, auto_sell_enabled, stock, weight_gram, dimensions_json,
                image_url, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (prod_id, sku, name, description, price, sale_price, category, is_active, auto_sell, stock, weight_gram, dims, image_url, now, now),
        )

        # Gắn alias nếu có
        for al in data.get("aliases", []):
            if isinstance(al, str) and al.strip():
                conn.execute(
                    "INSERT INTO ops_product_aliases (id, product_id, alias, weight, created_at) VALUES (?, ?, ?, 1.0, ?)",
                    (f"al_{uuid.uuid4().hex[:8]}", prod_id, al.strip().lower(), now),
                )

        # Gắn page bindings nếu có
        for b in data.get("page_bindings", []):
            pg = b.get("page_id") or "*"
            ch = b.get("channel") or "*"
            cp = b.get("custom_price")
            as_al = 1 if b.get("auto_sell_allowed", True) else 0
            conn.execute(
                "INSERT INTO ops_product_page_bindings (id, product_id, page_id, channel, custom_price, auto_sell_allowed, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f"bind_{uuid.uuid4().hex[:8]}", prod_id, pg, ch, cp, as_al, now),
            )

        # Ghi nhận biến thể nếu có
        for vr in data.get("variants", []):
            v_sku = str(vr.get("sku") or f"{sku}-{uuid.uuid4().hex[:4]}").strip().upper()
            v_title = str(vr.get("title") or "Biến thể").strip()
            v_price = int(vr.get("price") or price)
            v_stock = int(vr.get("stock") or stock)
            v_attrs = json.dumps(vr.get("attributes") or {})
            conn.execute(
                "INSERT INTO ops_product_variants (id, product_id, sku, title, price, stock, attributes_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (f"var_{uuid.uuid4().hex[:8]}", prod_id, v_sku, v_title, v_price, v_stock, v_attrs, now),
            )

        conn.commit()

    return get_product(prod_id, db_path) or {}


def update_product(product_id: str, data: dict, db_path: Path | str | None = None) -> dict:
    """Cập nhật thông tin sản phẩm Catalog."""
    init_db(db_path)
    existing = get_product(product_id, db_path)
    if not existing:
        raise ValueError(f"Không tìm thấy sản phẩm với ID: {product_id}")

    now = time.time()
    fields = []
    vals = []

    for k in ["name", "category", "description", "image_url"]:
        if k in data and data[k] is not None:
            fields.append(f"{k} = ?")
            vals.append(str(data[k]).strip())

    if "sku" in data and data["sku"]:
        fields.append("sku = ?")
        vals.append(str(data["sku"]).strip().upper())

    for k in ["price", "sale_price", "stock", "weight_gram"]:
        if k in data and data[k] is not None:
            fields.append(f"{k} = ?")
            vals.append(int(data[k]))

    for k in ["is_active", "auto_sell_enabled"]:
        if k in data and data[k] is not None:
            fields.append(f"{k} = ?")
            vals.append(1 if data[k] in (True, 1, "1", "true") else 0)

    if "dimensions" in data and isinstance(data["dimensions"], dict):
        fields.append("dimensions_json = ?")
        vals.append(json.dumps(data["dimensions"]))

    fields.append("updated_at = ?")
    vals.append(now)

    vals.append(existing["id"])

    for conn in get_connection(db_path):
        if fields:
            sql = f"UPDATE ops_products SET {', '.join(fields)} WHERE id = ?"
            conn.execute(sql, tuple(vals))

        # Cập nhật aliases nếu truyền danh sách mới
        if "aliases" in data and isinstance(data["aliases"], list):
            conn.execute("DELETE FROM ops_product_aliases WHERE product_id = ?", (existing["id"],))
            for al in data["aliases"]:
                if isinstance(al, str) and al.strip():
                    conn.execute(
                        "INSERT INTO ops_product_aliases (id, product_id, alias, weight, created_at) VALUES (?, ?, ?, 1.0, ?)",
                        (f"al_{uuid.uuid4().hex[:8]}", existing["id"], al.strip().lower(), now),
                    )

        # Cập nhật bindings nếu truyền
        if "page_bindings" in data and isinstance(data["page_bindings"], list):
            conn.execute("DELETE FROM ops_product_page_bindings WHERE product_id = ?", (existing["id"],))
            for b in data["page_bindings"]:
                pg = b.get("page_id") or "*"
                ch = b.get("channel") or "*"
                cp = b.get("custom_price")
                as_al = 1 if b.get("auto_sell_allowed", True) else 0
                conn.execute(
                    "INSERT INTO ops_product_page_bindings (id, product_id, page_id, channel, custom_price, auto_sell_allowed, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (f"bind_{uuid.uuid4().hex[:8]}", existing["id"], pg, ch, cp, as_al, now),
                )

        conn.commit()

    return get_product(existing["id"], db_path) or {}


def delete_product(product_id: str, db_path: Path | str | None = None) -> bool:
    """Xóa sản phẩm khỏi Catalog (kèm variants, aliases, bindings liên quan)."""
    init_db(db_path)
    existing = get_product(product_id, db_path)
    if not existing:
        return False
    for conn in get_connection(db_path):
        conn.execute("DELETE FROM ops_product_aliases WHERE product_id = ?", (existing["id"],))
        conn.execute("DELETE FROM ops_product_variants WHERE product_id = ?", (existing["id"],))
        conn.execute("DELETE FROM ops_product_page_bindings WHERE product_id = ?", (existing["id"],))
        conn.execute("DELETE FROM ops_products WHERE id = ?", (existing["id"],))
        conn.commit()
        return True
    return False


def upsert_product(
    sku: str,
    name: str,
    price: int,
    category: str = "general",
    stock: int = 100,
    is_active: bool = True,
    db_path: Path | str | None = None,
    **kwargs: Any,
) -> dict:
    """Upsert tương thích ngược cho tests và các hàm gọi cũ."""
    existing = get_product_by_sku(sku, db_path)
    data = {
        "sku": sku,
        "name": name,
        "price": price,
        "category": category,
        "stock": stock,
        "is_active": is_active,
        **kwargs,
    }
    if existing:
        return update_product(existing["id"], data, db_path)
    return create_product(data, db_path)


# ============================================================
# Product Aliases & Page Bindings
# ============================================================

def add_product_alias(product_id: str, alias: str, weight: float = 1.0, db_path: Path | str | None = None) -> dict:
    init_db(db_path)
    clean_alias = str(alias).strip().lower()
    if not clean_alias:
        raise ValueError("Alias không được để trống")
    now = time.time()
    al_id = f"al_{uuid.uuid4().hex[:8]}"
    for conn in get_connection(db_path):
        conn.execute(
            "INSERT INTO ops_product_aliases (id, product_id, alias, weight, created_at) VALUES (?, ?, ?, ?, ?)",
            (al_id, product_id, clean_alias, weight, now),
        )
        conn.commit()
    return {"id": al_id, "product_id": product_id, "alias": clean_alias, "weight": weight}


def delete_product_alias(alias_id: str, db_path: Path | str | None = None) -> bool:
    init_db(db_path)
    for conn in get_connection(db_path):
        cur = conn.execute("DELETE FROM ops_product_aliases WHERE id = ?", (alias_id,))
        conn.commit()
        return cur.rowcount > 0
    return False


def list_product_aliases(product_id: Optional[str] = None, db_path: Path | str | None = None) -> List[dict]:
    init_db(db_path)
    for conn in get_connection(db_path):
        if product_id:
            cur = conn.execute("SELECT * FROM ops_product_aliases WHERE product_id = ?", (product_id,))
        else:
            cur = conn.execute("SELECT * FROM ops_product_aliases ORDER BY created_at DESC")
        return [dict(r) for r in cur.fetchall()]
    return []


def bind_product_to_page(
    product_id: str,
    page_id: str,
    channel: str = "*",
    custom_price: Optional[int] = None,
    auto_sell_allowed: int = 1,
    db_path: Path | str | None = None,
) -> dict:
    init_db(db_path)
    now = time.time()
    bind_id = f"bind_{uuid.uuid4().hex[:8]}"
    for conn in get_connection(db_path):
        conn.execute(
            """
            INSERT INTO ops_product_page_bindings (id, product_id, page_id, channel, custom_price, auto_sell_allowed, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (bind_id, product_id, page_id.strip(), channel.strip().lower(), custom_price, auto_sell_allowed, now),
        )
        conn.commit()
    return {
        "id": bind_id,
        "product_id": product_id,
        "page_id": page_id,
        "channel": channel,
        "custom_price": custom_price,
        "auto_sell_allowed": auto_sell_allowed,
    }


def unbind_product_from_page(binding_id: str, db_path: Path | str | None = None) -> bool:
    init_db(db_path)
    for conn in get_connection(db_path):
        cur = conn.execute("DELETE FROM ops_product_page_bindings WHERE id = ?", (binding_id,))
        conn.commit()
        return cur.rowcount > 0
    return False


def list_product_page_bindings(product_id: Optional[str] = None, page_id: Optional[str] = None, db_path: Path | str | None = None) -> List[dict]:
    init_db(db_path)
    for conn in get_connection(db_path):
        sql = "SELECT b.*, p.name as product_name, p.sku as product_sku FROM ops_product_page_bindings b JOIN ops_products p ON b.product_id = p.id WHERE 1=1"
        params: list[Any] = []
        if product_id:
            sql += " AND b.product_id = ?"
            params.append(product_id)
        if page_id:
            sql += " AND (b.page_id = ? OR b.page_id = '*')"
            params.append(page_id)
        sql += " ORDER BY b.created_at DESC"
        cur = conn.execute(sql, tuple(params))
        return [dict(r) for r in cur.fetchall()]
    return []


# ============================================================
# Product Variants & Inventory Movements
# ============================================================

def create_product_variant(
    product_id: str,
    sku: str,
    title: str,
    price: int = 0,
    stock: int = 0,
    attributes: Optional[dict] = None,
    db_path: Path | str | None = None,
) -> dict:
    init_db(db_path)
    now = time.time()
    var_id = f"var_{uuid.uuid4().hex[:8]}"
    for conn in get_connection(db_path):
        conn.execute(
            """
            INSERT INTO ops_product_variants (id, product_id, sku, title, price, stock, attributes_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (var_id, product_id, sku.strip().upper(), title.strip(), price, stock, json.dumps(attributes or {}), now),
        )
        conn.commit()
    return {"id": var_id, "product_id": product_id, "sku": sku, "title": title, "price": price, "stock": stock}


def delete_product_variant(variant_id: str, db_path: Path | str | None = None) -> bool:
    init_db(db_path)
    for conn in get_connection(db_path):
        cur = conn.execute("DELETE FROM ops_product_variants WHERE id = ?", (variant_id,))
        conn.commit()
        return cur.rowcount > 0
    return False


def list_product_variants(product_id: str, db_path: Path | str | None = None) -> List[dict]:
    init_db(db_path)
    for conn in get_connection(db_path):
        cur = conn.execute("SELECT * FROM ops_product_variants WHERE product_id = ? ORDER BY price ASC", (product_id,))
        return [dict(r) for r in cur.fetchall()]
    return []


def record_inventory_movement(
    product_id: str,
    delta: int,
    reason: str,
    variant_id: Optional[str] = None,
    order_id: Optional[str] = None,
    db_path: Path | str | None = None,
) -> dict:
    init_db(db_path)
    now = time.time()
    mv_id = f"mov_{uuid.uuid4().hex[:8]}"
    for conn in get_connection(db_path):
        conn.execute(
            """
            INSERT INTO ops_inventory_movements (id, product_id, variant_id, delta, reason, order_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (mv_id, product_id, variant_id, delta, reason, order_id, now),
        )
        # Update main stock
        conn.execute("UPDATE ops_products SET stock = MAX(0, stock + ?), updated_at = ? WHERE id = ?", (delta, now, product_id))
        if variant_id:
            conn.execute("UPDATE ops_product_variants SET stock = MAX(0, stock + ?) WHERE id = ?", (delta, variant_id))
        conn.commit()
    return {"id": mv_id, "product_id": product_id, "delta": delta, "reason": reason}


# ============================================================
# Automation Case Rules & Logs
# ============================================================

DEFAULT_CASE_TYPES = [
    "faq_reply",
    "price_reply",
    "stock_reply",
    "ask_missing_phone",
    "ask_missing_address",
    "create_order_draft",
    "auto_confirm_order",
    "auto_create_shipment",
    "send_tracking_code",
    "handoff_to_staff",
]


def init_default_automation_rules(page_id: str = "*", db_path: Path | str | None = None) -> None:
    """Nạp bộ rule mặc định cho một page hoặc toàn cục (*)."""
    now = time.time()
    defaults = [
        {"case_type": "faq_reply", "enabled": 1, "level": 2, "min_confidence": 0.8},
        {"case_type": "price_reply", "enabled": 1, "level": 2, "min_confidence": 0.85},
        {"case_type": "stock_reply", "enabled": 1, "level": 2, "min_confidence": 0.85},
        {"case_type": "ask_missing_phone", "enabled": 1, "level": 2, "min_confidence": 0.8},
        {"case_type": "ask_missing_address", "enabled": 1, "level": 2, "min_confidence": 0.8},
        {"case_type": "create_order_draft", "enabled": 1, "level": 1, "min_confidence": 0.85},
        {"case_type": "auto_confirm_order", "enabled": 0, "level": 3, "min_confidence": 0.9, "max_cod_amount": 3000000, "require_staff_approval": 1},
        {"case_type": "auto_create_shipment", "enabled": 0, "level": 3, "min_confidence": 0.9, "max_cod_amount": 3000000, "require_staff_approval": 1},
        {"case_type": "send_tracking_code", "enabled": 0, "level": 3, "min_confidence": 0.9, "require_staff_approval": 1},
        {"case_type": "handoff_to_staff", "enabled": 1, "level": 0, "min_confidence": 0.5},
    ]
    for conn in get_connection(db_path):
        for d in defaults:
            rule_id = f"rule_{page_id}_{d['case_type']}".replace("*", "all")
            conn.execute(
                """
                INSERT OR IGNORE INTO ops_automation_rules (
                    id, page_id, channel, case_type, enabled, level, min_confidence,
                    require_product_match, require_phone, require_address, max_cod_amount,
                    require_staff_approval, message_template, cooldown_seconds, created_at, updated_at
                ) VALUES (?, ?, '*', ?, ?, ?, ?, 1, 1, 1, ?, ?, '', 30, ?, ?)
                """,
                (
                    rule_id,
                    page_id,
                    d["case_type"],
                    d["enabled"],
                    d["level"],
                    d["min_confidence"],
                    d.get("max_cod_amount", 5000000),
                    d.get("require_staff_approval", 0),
                    now,
                    now,
                ),
            )
        conn.commit()


def list_automation_rules(page_id: Optional[str] = None, channel: Optional[str] = None, db_path: Path | str | None = None) -> List[dict]:
    init_db(db_path)
    for conn in get_connection(db_path):
        sql = "SELECT * FROM ops_automation_rules WHERE 1=1"
        params: list[Any] = []
        if page_id:
            sql += " AND (page_id = ? OR page_id = '*')"
            params.append(page_id)
        if channel and channel != "*":
            sql += " AND (channel = ? OR channel = '*')"
            params.append(channel.lower())
        sql += " ORDER BY case_type ASC"
        cur = conn.execute(sql, tuple(params))
        rows = [dict(r) for r in cur.fetchall()]
        if not rows and (not page_id or page_id == "*"):
            init_default_automation_rules(page_id="*", db_path=db_path)
            cur = conn.execute("SELECT * FROM ops_automation_rules ORDER BY case_type ASC")
            rows = [dict(r) for r in cur.fetchall()]
        return rows
    return []


def get_automation_rule(case_type: str, page_id: str = "*", channel: str = "*", db_path: Path | str | None = None) -> Optional[dict]:
    init_db(db_path)
    for conn in get_connection(db_path):
        # 1. Tìm rule riêng của page trước
        cur = conn.execute(
            "SELECT * FROM ops_automation_rules WHERE case_type = ? AND page_id = ? AND (channel = ? OR channel = '*') LIMIT 1",
            (case_type, page_id, channel),
        )
        row = cur.fetchone()
        if row:
            return dict(row)
        # 2. Fallback sang rule toàn cục (*)
        cur_all = conn.execute(
            "SELECT * FROM ops_automation_rules WHERE case_type = ? AND page_id = '*' LIMIT 1",
            (case_type,),
        )
        row_all = cur_all.fetchone()
        return dict(row_all) if row_all else None
    return None


def save_automation_rule(rule_data: dict, db_path: Path | str | None = None) -> dict:
    init_db(db_path)
    now = time.time()
    case_type = str(rule_data.get("case_type") or "").strip()
    if not case_type:
        raise ValueError("case_type là bắt buộc")
    page_id = str(rule_data.get("page_id") or "*").strip()
    channel = str(rule_data.get("channel") or "*").strip().lower()

    existing = get_automation_rule(case_type, page_id=page_id, channel=channel, db_path=db_path)
    rule_id = rule_data.get("id") or (existing["id"] if existing else f"rule_{uuid.uuid4().hex[:8]}")

    enabled = 1 if rule_data.get("enabled", True) in (True, 1, "1", "true") else 0
    level = int(rule_data.get("level", 2))
    min_confidence = float(rule_data.get("min_confidence", 0.85))
    req_prod = 1 if rule_data.get("require_product_match", True) in (True, 1, "1", "true") else 0
    req_phone = 1 if rule_data.get("require_phone", True) in (True, 1, "1", "true") else 0
    req_addr = 1 if rule_data.get("require_address", True) in (True, 1, "1", "true") else 0
    max_cod = int(rule_data.get("max_cod_amount", 5000000))
    req_staff = 1 if rule_data.get("require_staff_approval", False) in (True, 1, "1", "true") else 0
    msg_tpl = str(rule_data.get("message_template") or "").strip()
    cooldown = int(rule_data.get("cooldown_seconds", 30))

    for conn in get_connection(db_path):
        conn.execute(
            """
            INSERT INTO ops_automation_rules (
                id, page_id, channel, case_type, enabled, level, min_confidence,
                require_product_match, require_phone, require_address, max_cod_amount,
                require_staff_approval, message_template, cooldown_seconds, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                enabled=excluded.enabled,
                level=excluded.level,
                min_confidence=excluded.min_confidence,
                require_product_match=excluded.require_product_match,
                require_phone=excluded.require_phone,
                require_address=excluded.require_address,
                max_cod_amount=excluded.max_cod_amount,
                require_staff_approval=excluded.require_staff_approval,
                message_template=excluded.message_template,
                cooldown_seconds=excluded.cooldown_seconds,
                updated_at=excluded.updated_at
            """,
            (
                rule_id,
                page_id,
                channel,
                case_type,
                enabled,
                level,
                min_confidence,
                req_prod,
                req_phone,
                req_addr,
                max_cod,
                req_staff,
                msg_tpl,
                cooldown,
                now,
                now,
            ),
        )
        conn.commit()

    return get_automation_rule(case_type, page_id=page_id, channel=channel, db_path=db_path) or {}


def delete_automation_rule(rule_id: str, db_path: Path | str | None = None) -> bool:
    init_db(db_path)
    for conn in get_connection(db_path):
        cur = conn.execute("DELETE FROM ops_automation_rules WHERE id = ?", (rule_id,))
        conn.commit()
        return cur.rowcount > 0
    return False


def record_automation_run(
    case_type: str,
    decision_reason: str,
    status: str,
    thread_id: Optional[str] = None,
    page_id: Optional[str] = None,
    order_id: Optional[str] = None,
    payload: Optional[dict] = None,
    db_path: Path | str | None = None,
) -> dict:
    init_db(db_path)
    now = time.time()
    run_id = f"run_{uuid.uuid4().hex[:10]}"
    for conn in get_connection(db_path):
        conn.execute(
            """
            INSERT INTO ops_automation_runs (id, case_type, thread_id, page_id, order_id, status, decision_reason, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, case_type, thread_id, page_id, order_id, status, decision_reason, json.dumps(payload or {}, ensure_ascii=False), now),
        )
        conn.commit()
    return {"id": run_id, "case_type": case_type, "status": status, "decision_reason": decision_reason}


def list_automation_runs(
    page_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    limit: int = 50,
    db_path: Path | str | None = None,
) -> List[dict]:
    init_db(db_path)
    for conn in get_connection(db_path):
        sql = "SELECT * FROM ops_automation_runs WHERE 1=1"
        params: list[Any] = []
        if page_id:
            sql += " AND page_id = ?"
            params.append(page_id)
        if thread_id:
            sql += " AND thread_id = ?"
            params.append(thread_id)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        cur = conn.execute(sql, tuple(params))
        rows = []
        for r in cur.fetchall():
            d = dict(r)
            if d.get("payload_json"):
                try:
                    d["payload"] = json.loads(d["payload_json"])
                except Exception:
                    d["payload"] = None
            rows.append(d)
        return rows
    return []


def queue_outbox_message(
    body: str,
    thread_id: Optional[str] = None,
    page_id: Optional[str] = None,
    channel: Optional[str] = None,
    recipient_id: Optional[str] = None,
    db_path: Path | str | None = None,
) -> dict:
    init_db(db_path)
    now = time.time()
    msg_id = f"out_{uuid.uuid4().hex[:10]}"
    for conn in get_connection(db_path):
        conn.execute(
            """
            INSERT INTO ops_outbox_messages (id, thread_id, page_id, channel, recipient_id, body, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (msg_id, thread_id, page_id, channel or "facebook", recipient_id, body.strip(), now),
        )
        conn.commit()
    return {"id": msg_id, "body": body, "status": "pending", "created_at": now}


def list_outbox_messages(
    status: Optional[str] = None,
    page_id: Optional[str] = None,
    limit: int = 50,
    db_path: Path | str | None = None,
) -> List[dict]:
    init_db(db_path)
    for conn in get_connection(db_path):
        sql = "SELECT * FROM ops_outbox_messages WHERE 1=1"
        params: list[Any] = []
        if status:
            sql += " AND status = ?"
            params.append(status)
        if page_id:
            sql += " AND page_id = ?"
            params.append(page_id)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        cur = conn.execute(sql, tuple(params))
        return [dict(r) for r in cur.fetchall()]
    return []


def update_outbox_status(message_id: str, status: str, error: Optional[str] = None, db_path: Path | str | None = None) -> bool:
    init_db(db_path)
    now = time.time()
    sent_at = now if status == "sent" else None
    for conn in get_connection(db_path):
        cur = conn.execute(
            "UPDATE ops_outbox_messages SET status = ?, error = ?, sent_at = COALESCE(sent_at, ?) WHERE id = ?",
            (status, error, sent_at, message_id),
        )
        conn.commit()
        return cur.rowcount > 0
    return False


# ============================================================
# Order CRUD
# ============================================================

def create_order(
    crm_id: Optional[str] = None,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    page_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    items: Optional[List[dict]] = None,
    shipping_address: Optional[str | dict] = None,
    cod_amount: Optional[int] = None,
    shipping_fee: int = 0,
    payment_method: str = "cod",
    customer_notes: Optional[str] = None,
    internal_notes: Optional[str] = None,
    ai_confidence: float = 0.0,
    missing_fields: Optional[List[str]] = None,
    status: str = "draft",
    source: str = "inbox",
    actor: str = "system",
    db_path: Path | str | None = None,
) -> dict:
    init_db(db_path)
    now = time.time()
    order_id = f"ord_{uuid.uuid4().hex[:10]}"
    items_list = items or []

    # Calculate item totals
    calc_total = 0
    clean_items = []
    for it in items_list:
        q = max(1, int(it.get("quantity") or 1))
        p = max(0, int(it.get("price") or 0))
        item_total = q * p
        calc_total += item_total
        clean_items.append({
            "product_id": it.get("product_id"),
            "sku": it.get("sku"),
            "name": str(it.get("name") or "Sản phẩm").strip(),
            "quantity": q,
            "price": p,
            "total": item_total,
        })

    # Default COD amount = total amount + shipping fee if not specified
    final_cod = cod_amount if cod_amount is not None else (calc_total + shipping_fee)

    addr_str = json.dumps(shipping_address, ensure_ascii=False) if isinstance(shipping_address, dict) else (shipping_address or "")
    missing_json = json.dumps(missing_fields or [], ensure_ascii=False)

    for conn in get_connection(db_path):
        conn.execute(
            """
            INSERT INTO ops_orders (
                id, crm_id, customer_name, customer_phone, page_id, thread_id,
                status, total_amount, cod_amount, shipping_fee, payment_method,
                shipping_address, customer_notes, internal_notes, ai_confidence,
                missing_fields, source, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                crm_id,
                customer_name,
                customer_phone,
                page_id,
                thread_id,
                status,
                calc_total,
                final_cod,
                shipping_fee,
                payment_method,
                addr_str,
                customer_notes,
                internal_notes,
                ai_confidence,
                missing_json,
                source,
                now,
                now,
            ),
        )

        for ci in clean_items:
            conn.execute(
                """
                INSERT INTO ops_order_items (order_id, product_id, sku, name, quantity, price, total)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (order_id, ci["product_id"], ci["sku"], ci["name"], ci["quantity"], ci["price"], ci["total"]),
            )

        # Ghi audit log tạo đơn
        conn.execute(
            """
            INSERT INTO ops_order_audit_logs (order_id, action, actor, details, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (order_id, "created", actor, json.dumps({"status": status, "total": calc_total, "items_count": len(clean_items)}, ensure_ascii=False), now),
        )

        conn.commit()

    return get_order(order_id, db_path=db_path) or {}


def get_order(order_id: str, db_path: Path | str | None = None) -> Optional[dict]:
    if not order_id:
        return None
    init_db(db_path)
    for conn in get_connection(db_path):
        cur = conn.execute("SELECT * FROM ops_orders WHERE id = ?", (order_id.strip(),))
        row = cur.fetchone()
        if not row:
            return None
        ord_dict = dict(row)

        # Parse JSON fields
        try:
            ord_dict["missing_fields"] = json.loads(ord_dict.get("missing_fields") or "[]")
        except Exception:
            ord_dict["missing_fields"] = []

        try:
            ord_dict["shipping_address_obj"] = json.loads(ord_dict.get("shipping_address") or "{}")
        except Exception:
            ord_dict["shipping_address_obj"] = None

        # Fetch items
        cur_items = conn.execute("SELECT * FROM ops_order_items WHERE order_id = ? ORDER BY id ASC", (order_id,))
        ord_dict["items"] = [dict(r) for r in cur_items.fetchall()]

        # Fetch shipment if exists
        cur_ship = conn.execute("SELECT * FROM ops_shipments WHERE order_id = ? ORDER BY created_at DESC LIMIT 1", (order_id,))
        ship_row = cur_ship.fetchone()
        ord_dict["shipment"] = dict(ship_row) if ship_row else None

        # Fetch audit logs
        cur_logs = conn.execute("SELECT * FROM ops_order_audit_logs WHERE order_id = ? ORDER BY created_at DESC", (order_id,))
        ord_dict["audit_logs"] = [dict(r) for r in cur_logs.fetchall()]

        return ord_dict
    return None


def list_orders(
    status: Optional[str] = None,
    crm_id: Optional[str] = None,
    thread_id: Optional[str] = None,
    page_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db_path: Path | str | None = None,
) -> List[dict]:
    init_db(db_path)
    query = "SELECT * FROM ops_orders WHERE 1=1"
    params: list[Any] = []

    if status:
        query += " AND status = ?"
        params.append(status.strip())
    if crm_id:
        query += " AND crm_id = ?"
        params.append(crm_id.strip())
    if thread_id:
        query += " AND thread_id = ?"
        params.append(thread_id.strip())
    if page_id:
        query += " AND page_id = ?"
        params.append(page_id.strip())

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    for conn in get_connection(db_path):
        cur = conn.execute(query, tuple(params))
        orders = []
        for r in cur.fetchall():
            o = dict(r)
            try:
                o["missing_fields"] = json.loads(o.get("missing_fields") or "[]")
            except Exception:
                o["missing_fields"] = []
            cur_ship = conn.execute("SELECT * FROM ops_shipments WHERE order_id = ? ORDER BY created_at DESC LIMIT 1", (o["id"],))
            ship_row = cur_ship.fetchone()
            o["shipment"] = dict(ship_row) if ship_row else None
            orders.append(o)
        return orders
    return []


def update_order(
    order_id: str,
    updates: dict,
    actor: str = "staff",
    db_path: Path | str | None = None,
) -> Optional[dict]:
    current = get_order(order_id, db_path=db_path)
    if not current:
        return None

    allowed_fields = {
        "status",
        "customer_name",
        "customer_phone",
        "shipping_address",
        "total_amount",
        "cod_amount",
        "shipping_fee",
        "payment_method",
        "customer_notes",
        "internal_notes",
        "ai_confidence",
        "missing_fields",
    }

    set_clauses = []
    params = []
    now = time.time()

    for k, v in updates.items():
        if k in allowed_fields:
            if k == "missing_fields" and isinstance(v, list):
                set_clauses.append(f"{k} = ?")
                params.append(json.dumps(v, ensure_ascii=False))
            elif k == "shipping_address" and isinstance(v, dict):
                set_clauses.append(f"{k} = ?")
                params.append(json.dumps(v, ensure_ascii=False))
            else:
                set_clauses.append(f"{k} = ?")
                params.append(v)

    if not set_clauses and "items" not in updates:
        return current

    for conn in get_connection(db_path):
        if set_clauses:
            set_clauses.append("updated_at = ?")
            params.append(now)
            params.append(order_id)
            conn.execute(f"UPDATE ops_orders SET {', '.join(set_clauses)} WHERE id = ?", tuple(params))

        # Update items if provided
        if "items" in updates and isinstance(updates["items"], list):
            conn.execute("DELETE FROM ops_order_items WHERE order_id = ?", (order_id,))
            new_total = 0
            for it in updates["items"]:
                q = max(1, int(it.get("quantity") or 1))
                p = max(0, int(it.get("price") or 0))
                item_tot = q * p
                new_total += item_tot
                conn.execute(
                    """
                    INSERT INTO ops_order_items (order_id, product_id, sku, name, quantity, price, total)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (order_id, it.get("product_id"), it.get("sku"), str(it.get("name") or "Sản phẩm").strip(), q, p, item_tot),
                )
            conn.execute("UPDATE ops_orders SET total_amount = ?, updated_at = ? WHERE id = ?", (new_total, now, order_id))

        # Record audit log
        conn.execute(
            """
            INSERT INTO ops_order_audit_logs (order_id, action, actor, details, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (order_id, "updated", actor, json.dumps({k: updates[k] for k in updates if k in allowed_fields or k == "items"}, ensure_ascii=False), now),
        )
        conn.commit()

    return get_order(order_id, db_path=db_path)


def delete_order(order_id: str, db_path: Path | str | None = None) -> bool:
    init_db(db_path)
    for conn in get_connection(db_path):
        cur = conn.execute("DELETE FROM ops_orders WHERE id = ?", (order_id,))
        conn.commit()
        return cur.rowcount > 0
    return False


# ============================================================
# Shipments & Shipping Events CRUD
# ============================================================

def create_shipment(
    order_id: str,
    provider: str = "ghn",
    tracking_code: Optional[str] = None,
    external_order_code: Optional[str] = None,
    status: str = "pending",
    fee: int = 0,
    cod_amount: int = 0,
    expected_delivery_time: Optional[str] = None,
    provider_response: Optional[dict] = None,
    actor: str = "staff",
    db_path: Path | str | None = None,
) -> dict:
    init_db(db_path)
    now = time.time()
    shipment_id = f"shp_{uuid.uuid4().hex[:10]}"
    resp_str = json.dumps(provider_response or {}, ensure_ascii=False)

    for conn in get_connection(db_path):
        conn.execute(
            """
            INSERT INTO ops_shipments (
                id, order_id, provider, tracking_code, external_order_code,
                status, fee, cod_amount, expected_delivery_time, provider_response,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                shipment_id,
                order_id,
                provider,
                tracking_code,
                external_order_code,
                status,
                fee,
                cod_amount,
                expected_delivery_time,
                resp_str,
                now,
                now,
            ),
        )

        # Update order status to shipment_created
        conn.execute(
            "UPDATE ops_orders SET status = 'shipment_created', shipping_fee = ?, updated_at = ? WHERE id = ?",
            (fee, now, order_id),
        )

        # Record audit log
        conn.execute(
            """
            INSERT INTO ops_order_audit_logs (order_id, action, actor, details, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                order_id,
                "shipment_created",
                actor,
                json.dumps({
                    "shipment_id": shipment_id,
                    "provider": provider,
                    "tracking_code": tracking_code,
                    "fee": fee,
                }, ensure_ascii=False),
                now,
            ),
        )
        conn.commit()

    return get_shipment(shipment_id, db_path=db_path) or {}


def get_shipment(shipment_id: str, db_path: Path | str | None = None) -> Optional[dict]:
    if not shipment_id:
        return None
    init_db(db_path)
    for conn in get_connection(db_path):
        cur = conn.execute("SELECT * FROM ops_shipments WHERE id = ?", (shipment_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    return None


def get_shipment_by_tracking(tracking_code: str, db_path: Path | str | None = None) -> Optional[dict]:
    if not tracking_code:
        return None
    init_db(db_path)
    for conn in get_connection(db_path):
        cur = conn.execute("SELECT * FROM ops_shipments WHERE tracking_code = ?", (tracking_code.strip(),))
        row = cur.fetchone()
        return dict(row) if row else None
    return None


def update_shipment_status(
    shipment_id: str,
    new_status: str,
    description: Optional[str] = None,
    location: Optional[str] = None,
    raw_payload: Optional[dict] = None,
    actor: str = "webhook",
    db_path: Path | str | None = None,
) -> Optional[dict]:
    shipment = get_shipment(shipment_id, db_path=db_path)
    if not shipment:
        return None

    now = time.time()
    order_id = shipment["order_id"]
    provider = shipment["provider"]

    # Map shipment status to order status
    status_map = {
        "picking": "picking",
        "ready_to_pick": "picking",
        "shipping": "shipping",
        "delivering": "shipping",
        "delivered": "delivered",
        "delivery_fail": "failed",
        "failed": "failed",
        "cancelled": "cancelled",
        "returned": "returned",
    }
    target_order_status = status_map.get(new_status.lower(), shipment["status"])

    for conn in get_connection(db_path):
        conn.execute(
            "UPDATE ops_shipments SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, now, shipment_id),
        )
        conn.execute(
            "UPDATE ops_orders SET status = ?, updated_at = ? WHERE id = ?",
            (target_order_status, now, order_id),
        )

        # Record shipping event
        conn.execute(
            """
            INSERT INTO ops_shipping_events (shipment_id, provider, status, description, location, event_time, raw_payload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                shipment_id,
                provider,
                new_status,
                description or f"Trạng thái vận chuyển: {new_status}",
                location or "",
                now,
                json.dumps(raw_payload or {}, ensure_ascii=False),
            ),
        )

        # Record audit log on order
        conn.execute(
            """
            INSERT INTO ops_order_audit_logs (order_id, action, actor, details, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                order_id,
                "status_update",
                actor,
                json.dumps({"shipment_status": new_status, "order_status": target_order_status, "desc": description}, ensure_ascii=False),
                now,
            ),
        )
        conn.commit()

    return get_shipment(shipment_id, db_path=db_path)


def record_audit_log(order_id: str, action: str, actor: str, details: dict, db_path: Path | str | None = None) -> None:
    init_db(db_path)
    now = time.time()
    for conn in get_connection(db_path):
        conn.execute(
            """
            INSERT INTO ops_order_audit_logs (order_id, action, actor, details, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (order_id, action, actor, json.dumps(details or {}, ensure_ascii=False), now),
        )
        conn.commit()


def list_audit_logs(order_id: str, db_path: Path | str | None = None) -> List[dict]:
    init_db(db_path)
    for conn in get_connection(db_path):
        cur = conn.execute("SELECT * FROM ops_order_audit_logs WHERE order_id = ? ORDER BY created_at ASC", (order_id,))
        rows = []
        for r in cur.fetchall():
            d = dict(r)
            if d.get("details"):
                try:
                    d["details"] = json.loads(d["details"])
                except Exception:
                    pass
            rows.append(d)
        return rows
    return []
