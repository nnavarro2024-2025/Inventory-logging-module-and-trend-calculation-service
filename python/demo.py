import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from python.inventory import InventoryManager

DB_PATH = os.path.join(os.getcwd(), 'inventory_demo.db')


def seed_and_run():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    im = InventoryManager(DB_PATH)
    schema_path = os.path.join(os.getcwd(), 'sql', 'schema.sql')
    im.init_schema(schema_path)

    # Seed products
    milk_id = im.add_product('MILK001', 'Whole Milk 1L', 'Dairy', 'L')
    bread_id = im.add_product('BRD001', 'Sliced Bread', 'Bakery', 'loaf')

    # Seed batches / receipts
    today = datetime.utcnow().date()
    im.add_batch(milk_id, 'BATCH-M-001', 50, received_date=today.isoformat(), expiry_date=(today + timedelta(days=10)).isoformat())
    im.add_batch(bread_id, 'BATCH-B-001', 30, received_date=today.isoformat(), expiry_date=(today + timedelta(days=3)).isoformat())

    # Seed some consumption over last 10 days
    for d in range(10):
        day = datetime.utcnow() - timedelta(days=d)
        # milk consumption: 3 units per day
        im.log_consumption(milk_id, 3, user_id='kitchen', consumed_at=day.isoformat())
        # bread consumption: 2 units per day
        im.log_consumption(bread_id, 2, user_id='counter', consumed_at=day.isoformat())

    print('\nCurrent on-hand:')
    print(im.current_on_hand())

    print('\nMilk timeseries (last 7 days):')
    print(im.consumption_timeseries(milk_id, days=7))

    print('\nUsage rate (milk):')
    print(im.calculate_usage_rate(milk_id, days=30))

    print('\nBatches near expiry (7 days):')
    print(im.batches_with_expiry(within_days=7))

    print('\nSimulated restock alerts:')
    alerts = im.simulate_restock_alerts(threshold_days=5, safety_days=2)
    for a in alerts:
        print(a)

    im.close()


if __name__ == '__main__':
    seed_and_run()
