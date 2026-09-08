import sqlite3
from datetime import datetime, timedelta
import pandas as pd


class InventoryManager:
    def __init__(self, db_path=':memory:'):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        self.conn.close()

    def init_schema(self, schema_sql: str = None):
        if schema_sql:
            with open(schema_sql, 'r', encoding='utf-8') as f:
                sql = f.read()
            self.conn.executescript(sql)
        else:
            raise ValueError('Provide path to schema SQL file')
        self.conn.commit()

    def add_product(self, sku: str, name: str, category: str = None, unit: str = None):
        cur = self.conn.cursor()
        cur.execute(
            'INSERT INTO products (sku, name, category, unit) VALUES (?,?,?,?)',
            (sku, name, category, unit)
        )
        self.conn.commit()
        return cur.lastrowid

    def add_batch(self, product_id: int, batch_code: str, quantity: float, received_date: str, expiry_date: str = None, location: str = None):
        cur = self.conn.cursor()
        cur.execute(
            'INSERT INTO batches (product_id, batch_code, quantity, received_date, expiry_date, location) VALUES (?,?,?,?,?,?)',
            (product_id, batch_code, quantity, received_date, expiry_date, location)
        )
        batch_id = cur.lastrowid
        # also create a receipt record
        cur.execute(
            'INSERT INTO inventory_receipts (product_id, batch_id, quantity, received_at) VALUES (?,?,?,?)',
            (product_id, batch_id, quantity, received_date)
        )
        self.conn.commit()
        return batch_id

    def log_consumption(self, product_id: int, quantity: float, user_id: str = None, consumed_at: str = None):
        if consumed_at is None:
            consumed_at = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute(
            'INSERT INTO consumption_logs (product_id, quantity, user_id, consumed_at) VALUES (?,?,?,?)',
            (product_id, quantity, user_id, consumed_at)
        )
        self.conn.commit()
        return cur.lastrowid

    def current_on_hand(self) -> pd.DataFrame:
        q = '''
        SELECT p.id AS product_id, p.sku, p.name,
          COALESCE(r.received,0) - COALESCE(c.consumed,0) AS on_hand
        FROM products p
        LEFT JOIN (
          SELECT product_id, SUM(quantity) AS received FROM inventory_receipts GROUP BY product_id
        ) r ON r.product_id = p.id
        LEFT JOIN (
          SELECT product_id, SUM(quantity) AS consumed FROM consumption_logs GROUP BY product_id
        ) c ON c.product_id = p.id
        '''
        df = pd.read_sql_query(q, self.conn)
        return df

    def batches_with_expiry(self, within_days: int = 7) -> pd.DataFrame:
        q = '''
        SELECT b.id AS batch_id, b.batch_code, p.id AS product_id, p.name, b.expiry_date,
          (julianday(b.expiry_date) - julianday('now')) AS days_to_expiry
        FROM batches b JOIN products p ON p.id = b.product_id
        WHERE b.expiry_date IS NOT NULL AND (julianday(b.expiry_date) - julianday('now')) <= ?
        ORDER BY days_to_expiry ASC
        '''
        df = pd.read_sql_query(q, self.conn, params=(within_days,))
        return df

    def consumption_timeseries(self, product_id: int, days: int = 30) -> pd.DataFrame:
        q = '''
        SELECT date(consumed_at) AS day, SUM(quantity) AS qty
        FROM consumption_logs
        WHERE product_id = ? AND consumed_at >= date('now', ?)
        GROUP BY day
        ORDER BY day
        '''
        df = pd.read_sql_query(q, self.conn, params=(product_id, f'-{days} days'))
        if df.empty:
            # return zeros for the range
            idx = pd.date_range(end=datetime.utcnow().date(), periods=days)
            return pd.DataFrame({'day': idx.strftime('%Y-%m-%d'), 'qty': [0]*len(idx)})
        return df

    def calculate_usage_rate(self, product_id: int, days: int = 30) -> dict:
        ts = self.consumption_timeseries(product_id, days)
        ts['qty'] = ts['qty'].astype(float)
        avg_daily = ts['qty'].mean()
        recent_avg_7 = ts.tail(7)['qty'].mean() if len(ts) >= 7 else avg_daily
        total = ts['qty'].sum()
        return {
            'product_id': product_id,
            'days': days,
            'total_consumed': float(total),
            'avg_daily': float(avg_daily or 0.0),
            'recent_avg_7': float(recent_avg_7 or 0.0)
        }

    def simulate_restock_alerts(self, threshold_days: int = 7, safety_days: int = 3) -> list:
        df = self.current_on_hand()
        alerts = []
        for _, row in df.iterrows():
            pid = int(row['product_id'])
            on_hand = float(row['on_hand'] or 0)
            usage = self.calculate_usage_rate(pid, days=30)
            avg = usage['avg_daily']
            days_until_stockout = float('inf')
            if avg > 0:
                days_until_stockout = on_hand / avg
            if days_until_stockout <= threshold_days:
                alerts.append({
                    'product_id': pid,
                    'name': row['name'],
                    'on_hand': on_hand,
                    'avg_daily': avg,
                    'days_until_stockout': days_until_stockout,
                    'reason': 'low_stock_predicted'
                })
        # Check expiry-based alerts
        exp_df = self.batches_with_expiry(within_days=threshold_days + safety_days)
        for _, b in exp_df.iterrows():
            alerts.append({
                'batch_id': int(b['batch_id']),
                'product_id': int(b['product_id']),
                'name': b['name'],
                'expiry_date': b['expiry_date'],
                'days_to_expiry': float(b['days_to_expiry']),
                'reason': 'expiry_soon'
            })
        return alerts


if __name__ == '__main__':
    print('Use this module from another script or run the demo.')
