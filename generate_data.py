from pathlib import Path
import random
from datetime import timedelta

import pandas as pd
from faker import Faker


fake = Faker()
random.seed(42)
Faker.seed(42)

DATA_FOLDER = Path("data")
DATA_FOLDER.mkdir(exist_ok=True)


def create_customers(number_of_customers=200):
    countries = [
        "United States",
        "Canada",
        "Germany",
        "India",
        "Mexico",
    ]

    segments = [
        "Enterprise",
        "Small Business",
        "Consumer",
    ]

    customers = []

    for customer_id in range(1, number_of_customers + 1):
        customers.append(
            {
                "customer_id": customer_id,
                "customer_name": fake.company(),
                "country": random.choice(countries),
                "customer_segment": random.choice(segments),
                "signup_date": fake.date_between(
                    start_date="-3y",
                    end_date="today",
                ),
            }
        )

    return pd.DataFrame(customers)


def create_products(number_of_products=50):
    categories = [
        "Electronics",
        "Home",
        "Clothing",
        "Beauty",
        "Sports",
    ]

    products = []

    for product_id in range(1, number_of_products + 1):
        products.append(
            {
                "product_id": product_id,
                "product_name": fake.catch_phrase(),
                "category": random.choice(categories),
                "unit_price": round(
                    random.uniform(10, 500),
                    2,
                ),
            }
        )

    return pd.DataFrame(products)


def create_orders(customers, products, number_of_orders=1500):
    statuses = [
        "Completed",
        "Processing",
        "Cancelled",
        "Returned",
    ]

    orders = []

    customer_ids = customers["customer_id"].tolist()

    for order_id in range(1, number_of_orders + 1):
        product = products.sample(1).iloc[0]
        quantity = random.randint(1, 5)
        unit_price = float(product["unit_price"])

        orders.append(
            {
                "order_id": order_id,
                "customer_id": random.choice(customer_ids),
                "product_id": int(product["product_id"]),
                "order_date": fake.date_between(
                    start_date="-12m",
                    end_date="today",
                ),
                "quantity": quantity,
                "unit_price": unit_price,
                "order_value": round(
                    quantity * unit_price,
                    2,
                ),
                "order_status": random.choice(statuses),
            }
        )

    return pd.DataFrame(orders)


def create_shipments(orders):
    carriers = ["DHL", "FedEx", "UPS", "USPS"]

    shipments = []

    eligible_orders = orders[
        orders["order_status"] != "Cancelled"
    ]

    for shipment_id, (_, order) in enumerate(
        eligible_orders.iterrows(),
        start=1,
    ):
        order_date = pd.to_datetime(order["order_date"])

        promised_days = random.randint(2, 7)

        if random.random() < 0.22:
            actual_days = promised_days + random.randint(1, 6)
            shipment_status = "Delayed"
        else:
            actual_days = max(
                1,
                promised_days + random.randint(-1, 1),
            )
            shipment_status = "Delivered"

        promised_date = order_date + timedelta(
            days=promised_days
        )

        actual_delivery_date = order_date + timedelta(
            days=actual_days
        )

        delay_days = max(
            0,
            actual_days - promised_days,
        )

        shipments.append(
            {
                "shipment_id": shipment_id,
                "order_id": int(order["order_id"]),
                "carrier": random.choice(carriers),
                "promised_delivery_date": promised_date.date(),
                "actual_delivery_date": actual_delivery_date.date(),
                "delay_days": delay_days,
                "shipment_status": shipment_status,
            }
        )

    shipments_dataframe = pd.DataFrame(shipments)

    # Add a few intentional data-quality problems.
    if len(shipments_dataframe) >= 10:
        shipments_dataframe.loc[2, "carrier"] = None
        shipments_dataframe.loc[
            5,
            "actual_delivery_date",
        ] = None
        shipments_dataframe.loc[8, "delay_days"] = -1

    return shipments_dataframe


def create_metadata():
    metadata = [
        {
            "table_name": "customers",
            "column_name": "customer_id",
            "description": "Unique identifier for each customer.",
            "data_type": "INTEGER",
        },
        {
            "table_name": "customers",
            "column_name": "customer_segment",
            "description": "Business classification of the customer.",
            "data_type": "TEXT",
        },
        {
            "table_name": "orders",
            "column_name": "order_value",
            "description": "Total monetary value of an order.",
            "data_type": "DECIMAL",
        },
        {
            "table_name": "orders",
            "column_name": "order_status",
            "description": "Current status of the order.",
            "data_type": "TEXT",
        },
        {
            "table_name": "shipments",
            "column_name": "delay_days",
            "description": (
                "Number of days a shipment arrived "
                "after the promised delivery date."
            ),
            "data_type": "INTEGER",
        },
        {
            "table_name": "shipments",
            "column_name": "shipment_status",
            "description": "Current delivery status of the shipment.",
            "data_type": "TEXT",
        },
        {
            "table_name": "products",
            "column_name": "category",
            "description": "Commercial category assigned to the product.",
            "data_type": "TEXT",
        },
    ]

    return pd.DataFrame(metadata)


def main():
    customers = create_customers()
    products = create_products()
    orders = create_orders(customers, products)
    shipments = create_shipments(orders)
    metadata = create_metadata()

    customers.to_csv(
        DATA_FOLDER / "customers.csv",
        index=False,
    )

    products.to_csv(
        DATA_FOLDER / "products.csv",
        index=False,
    )

    orders.to_csv(
        DATA_FOLDER / "orders.csv",
        index=False,
    )

    shipments.to_csv(
        DATA_FOLDER / "shipments.csv",
        index=False,
    )

    metadata.to_csv(
        DATA_FOLDER / "metadata.csv",
        index=False,
    )

    print("Sample logistics data created successfully.")
    print(f"Customers created: {len(customers)}")
    print(f"Products created: {len(products)}")
    print(f"Orders created: {len(orders)}")
    print(f"Shipments created: {len(shipments)}")


if __name__ == "__main__":
    main()