import os
import random

import numpy as np
import pandas as pd

from datetime import datetime, timedelta


random.seed(42)

np.random.seed(42)


NUMBER_OF_SHIPMENTS = 3000


carriers = [
    "DHL",
    "FedEx",
    "UPS",
    "BlueDart",
    "Delhivery"
]


regions = [
    "North",
    "South",
    "East",
    "West",
    "Central"
]


shipping_modes = [
    "Air",
    "Road",
    "Rail",
    "Sea"
]


weather_conditions = [
    "Clear",
    "Rain",
    "Storm",
    "Fog"
]


traffic_levels = [
    "Low",
    "Medium",
    "High"
]


priorities = [
    "Low",
    "Medium",
    "High"
]


vehicle_types = [
    "Truck",
    "Van",
    "Bike",
    "Container"
]


cities = [
    "Kochi",
    "Mumbai",
    "Delhi",
    "Bangalore",
    "Chennai",
    "Hyderabad",
    "Pune",
    "Kolkata",
    "Ahmedabad",
    "Jaipur",
    "Lucknow",
    "Indore",
    "Bhopal",
    "Surat",
    "Coimbatore"
]


records = []


start_date = datetime(
    2025,
    1,
    1
)


for i in range(
    1,
    NUMBER_OF_SHIPMENTS + 1
):

    order_date = (
        start_date
        + timedelta(
            days=random.randint(
                0,
                600
            )
        )
    )


    ship_date = (
        order_date
        + timedelta(
            days=random.randint(
                0,
                3
            )
        )
    )


    carrier = random.choice(
        carriers
    )

    region = random.choice(
        regions
    )

    shipping_mode = random.choice(
        shipping_modes
    )

    weather = random.choice(
        weather_conditions
    )

    traffic = random.choice(
        traffic_levels
    )

    priority = random.choice(
        priorities
    )

    vehicle = random.choice(
        vehicle_types
    )


    origin = random.choice(
        cities
    )

    destination = random.choice(
        cities
    )


    while destination == origin:

        destination = random.choice(
            cities
        )


    distance = random.randint(
        50,
        2500
    )


    weight = round(
        random.uniform(
            0.5,
            50
        ),
        2
    )


    shipping_cost = round(
        distance * random.uniform(
            1.5,
            3.5
        )
        + weight * random.uniform(
            10,
            30
        ),
        2
    )


    warehouse_delay = random.choice(
        [
            0,
            0,
            0,
            1,
            2
        ]
    )


    customs_delay = random.choice(
        [
            0,
            0,
            0,
            1,
            2,
            3
        ]
    )


    expected_days = max(
        1,
        int(distance / 450) + 2
    )


    extra_delay = 0


    if weather == "Rain":

        extra_delay += random.randint(
            0,
            2
        )


    if weather == "Storm":

        extra_delay += random.randint(
            1,
            4
        )


    if weather == "Fog":

        extra_delay += random.randint(
            0,
            2
        )


    if traffic == "Medium":

        extra_delay += random.randint(
            0,
            1
        )


    if traffic == "High":

        extra_delay += random.randint(
            1,
            3
        )


    extra_delay += (
        warehouse_delay
    )


    extra_delay += (
        customs_delay
    )


    if random.random() < 0.18:

        extra_delay += random.randint(
            1,
            4
        )


    actual_days = (
        expected_days
        + extra_delay
    )


    expected_delivery_date = (
        ship_date
        + timedelta(
            days=expected_days
        )
    )


    actual_delivery_date = (
        ship_date
        + timedelta(
            days=actual_days
        )
    )


    records.append({

        "shipment_id":
            f"S{i:05d}",

        "order_date":
            order_date,

        "ship_date":
            ship_date,

        "expected_delivery_date":
            expected_delivery_date,

        "actual_delivery_date":
            actual_delivery_date,

        "carrier":
            carrier,

        "origin":
            origin,

        "destination":
            destination,

        "region":
            region,

        "shipping_mode":
            shipping_mode,

        "distance_km":
            distance,

        "package_weight":
            weight,

        "shipping_cost":
            shipping_cost,

        "weather":
            weather,

        "traffic_level":
            traffic,

        "warehouse_delay":
            warehouse_delay,

        "customs_delay":
            customs_delay,

        "vehicle_type":
            vehicle,

        "order_priority":
            priority
    })


df = pd.DataFrame(
    records
)


os.makedirs(
    "data/raw",
    exist_ok=True
)


output_file = (
    "data/raw/shipments.csv"
)


df.to_csv(
    output_file,
    index=False
)


print(
    "Shipment dataset created successfully."
)

print(
    "Rows:",
    len(df)
)

print(
    "Saved to:",
    output_file
)

print(
    df.head()
)