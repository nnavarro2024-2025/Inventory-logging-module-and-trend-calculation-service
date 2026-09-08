Lab 4: Retail & Food Inventory Management

This small project provides:
- SQL schema: sql/schema.sql
- Python inventory module: python/inventory.py
- Demo script: python/demo.py

Quick start

1. Create a virtual environment and install requirements:

```bash
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

2. Run the demo:

```bash
python python/demo.py
```

What it does

- Tracks products, batches, receipts, and consumption.
- Computes usage rates (average daily consumption) using Pandas.
- Finds batches nearing expiry and simulates restock alerts based on usage and threshold days.

Files of interest

- sql/schema.sql: schema and example SQL queries.
- python/inventory.py: `InventoryManager` with methods to seed data, compute trends, and simulate alerts.
- python/demo.py: simple seeding and run-through demonstrating outputs.
