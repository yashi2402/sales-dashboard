import pandas as pd
import numpy as np


def generate_sales_data(n_records=1000, seed=42):
    """Generate realistic sample sales data."""
    np.random.seed(seed)

    regions = ['North', 'South', 'East', 'West', 'Central']
    categories = ['Electronics', 'Clothing', 'Food & Beverage', 'Home & Garden', 'Sports']
    products = {
        'Electronics': ['Laptop', 'Phone', 'Tablet', 'Headphones', 'Camera'],
        'Clothing': ['Jacket', 'Shoes', 'T-Shirt', 'Jeans', 'Dress'],
        'Food & Beverage': ['Coffee', 'Snacks', 'Juice', 'Chocolate', 'Tea'],
        'Home & Garden': ['Lamp', 'Plant Pot', 'Cushion', 'Rug', 'Mirror'],
        'Sports': ['Football', 'Tennis Racket', 'Yoga Mat', 'Dumbbells', 'Running Shoes'],
    }

    data = []
    start_date = pd.Timestamp('2025-01-01')
    end_date = pd.Timestamp('2026-06-30')
    date_range = (end_date - start_date).days

    for i in range(n_records):
        category = np.random.choice(categories)
        product = np.random.choice(products[category])
        region = np.random.choice(regions)
        date = start_date + pd.Timedelta(days=np.random.randint(0, date_range))

        base_price = {
            'Electronics': 500, 'Clothing': 80, 'Food & Beverage': 20,
            'Home & Garden': 60, 'Sports': 100
        }[category]
        revenue = base_price * np.random.uniform(0.5, 3.0)
        quantity = np.random.randint(1, 10)

        data.append({
            'order_id': f'ORD-{i+1001:05d}',
            'date': date,
            'customer_id': f'CUST-{np.random.randint(1, 200):04d}',
            'product': product,
            'category': category,
            'region': region,
            'quantity': quantity,
            'revenue': round(revenue * quantity, 2),
        })

    df = pd.DataFrame(data)
    df = df.sort_values('date').reset_index(drop=True)
    return df


if __name__ == '__main__':
    df = generate_sales_data()
    print(f"Generated {len(df)} records")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Total revenue: ${df['revenue'].sum():,.2f}")
    print(f"\nSample:\n{df.head()}")
