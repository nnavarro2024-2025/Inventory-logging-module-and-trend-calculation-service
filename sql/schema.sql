PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE,
    name TEXT NOT NULL,
    category TEXT,
    unit TEXT
);

CREATE TABLE IF NOT EXISTS batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    batch_code TEXT,
    quantity REAL NOT NULL,
    received_date TEXT NOT NULL,
    expiry_date TEXT,
    location TEXT
);

CREATE TABLE IF NOT EXISTS consumption_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity REAL NOT NULL,
    user_id TEXT,
    consumed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS inventory_receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    batch_id INTEGER REFERENCES batches(id),
    quantity REAL NOT NULL,
    received_at TEXT NOT NULL
);