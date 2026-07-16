import pandas as pd
import numpy as np


def generate_sales_data(n_records=2500, seed=42):
    """Generate realistic sales data with seasonal trends, growth, and patterns."""
    np.random.seed(seed)

    regions = {
        'North America': ['USA', 'Canada', 'Mexico'],
        'Europe': ['UK', 'Germany', 'France'],
        'Asia Pacific': ['India', 'Japan', 'Australia'],
        'Latin America': ['Brazil', 'Argentina', 'Colombia'],
    }

    categories = {
        'Electronics': {
            'products': ['MacBook Pro', 'iPhone 15', 'iPad Air', 'AirPods Pro', 'Sony Camera'],
            'base_price': 800, 'margin': 0.25
        },
        'Clothing': {
            'products': ['Nike Jacket', 'Adidas Shoes', 'Levi Jeans', 'Zara Dress', 'H&M T-Shirt'],
            'base_price': 120, 'margin': 0.55
        },
        'Food & Beverage': {
            'products': ['Premium Coffee', 'Organic Snacks', 'Fresh Juice', 'Dark Chocolate', 'Green Tea'],
            'base_price': 35, 'margin': 0.40
        },
        'Home & Garden': {
            'products': ['Smart Lamp', 'Indoor Plant Kit', 'Memory Foam Cushion', 'Persian Rug', 'Wall Mirror'],
            'base_price': 150, 'margin': 0.45
        },
        'Sports & Outdoors': {
            'products': ['Tennis Racket', 'Yoga Mat Pro', 'Adjustable Dumbbells', 'Running Shoes', 'Camping Tent'],
            'base_price': 180, 'margin': 0.35
        },
    }

    sales_channels = ['Online', 'Retail Store', 'Wholesale', 'Marketplace']
    payment_methods = ['Credit Card', 'Debit Card', 'PayPal', 'Bank Transfer', 'Cash']
    customer_segments = ['Premium', 'Regular', 'New', 'Returning']

    data = []
    start_date = pd.Timestamp('2024-01-01')
    end_date = pd.Timestamp('2026-06-30')
    date_range = (end_date - start_date).days

    for i in range(n_records):
        # Pick region and country
        region = np.random.choice(list(regions.keys()))
        country = np.random.choice(regions[region])

        # Pick category and product
        category = np.random.choice(list(categories.keys()))
        cat_info = categories[category]
        product = np.random.choice(cat_info['products'])

        # Generate date with seasonal pattern (more sales in Q4)
        day_offset = np.random.randint(0, date_range)
        date = start_date + pd.Timedelta(days=day_offset)
        month = date.month

        # Seasonal multiplier (higher in Nov-Dec, lower in Jan-Feb)
        seasonal = 1.0
        if month in [11, 12]:
            seasonal = 1.6
        elif month in [6, 7, 8]:
            seasonal = 1.2
        elif month in [1, 2]:
            seasonal = 0.7

        # Growth trend (sales grow over time)
        days_elapsed = (date - start_date).days
        growth = 1.0 + (days_elapsed / date_range) * 0.3

        # Calculate revenue
        base = cat_info['base_price']
        price_variation = np.random.uniform(0.7, 1.8)
        quantity = np.random.choice([1, 1, 1, 2, 2, 3, 4, 5], p=[0.35, 0.2, 0.15, 0.1, 0.08, 0.05, 0.04, 0.03])
        unit_price = round(base * price_variation, 2)
        revenue = round(unit_price * quantity * seasonal * growth, 2)
        cost = round(revenue * (1 - cat_info['margin']), 2)
        profit = round(revenue - cost, 2)

        # Customer info
        customer_id = f'CUST-{np.random.randint(1, 500):04d}'
        segment = np.random.choice(customer_segments, p=[0.15, 0.40, 0.25, 0.20])
        channel = np.random.choice(sales_channels, p=[0.45, 0.25, 0.15, 0.15])
        payment = np.random.choice(payment_methods, p=[0.35, 0.25, 0.20, 0.12, 0.08])

        # Satisfaction score (1-5)
        satisfaction = np.random.choice([1, 2, 3, 4, 5], p=[0.02, 0.05, 0.15, 0.45, 0.33])

        data.append({
            'order_id': f'ORD-{i+1001:05d}',
            'date': date,
            'customer_id': customer_id,
            'customer_segment': segment,
            'product': product,
            'category': category,
            'region': region,
            'country': country,
            'channel': channel,
            'payment_method': payment,
            'quantity': quantity,
            'unit_price': unit_price,
            'revenue': revenue,
            'cost': cost,
            'profit': profit,
            'margin_pct': round((profit / revenue) * 100, 1) if revenue > 0 else 0,
            'satisfaction': satisfaction,
        })

    df = pd.DataFrame(data)
    df = df.sort_values('date').reset_index(drop=True)
    return df


if __name__ == '__main__':
    df = generate_sales_data()
    print(f"Generated {len(df)} records")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Total revenue: ${df['revenue'].sum():,.2f}")
    print(f"Total profit: ${df['profit'].sum():,.2f}")
    print(f"Regions: {df['region'].unique()}")
    print(f"Categories: {df['category'].unique()}")
    print(f"\nSample:\n{df.head()}")
