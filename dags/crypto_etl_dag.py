import os
import datetime
import pandas as pd
import requests
from sqlalchemy import create_engine
from airflow.sdk import dag, task


@dag(
    dag_id="crypto_coingecko_etl_v3",
    start_date=datetime.datetime(2026, 1, 1),
    schedule="*/5 * * * *",
    catchup=False,
    description="Crypto Pipeline",
)

def crypto_coingecko_etl():

    @task
    def extract_and_transform():
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "bitcoin,ethereum,solana", "vs_currencies": "usd"}
        headers = {"accept": "application/json"}

        print("Extracting data")
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        raw_data = response.json()

        print("Transforming data")
        extracted_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        flattened_data = []
        for coin_id, price_info in raw_data.items():
            flattened_data.append(
                {
                    "coin_id": coin_id,
                    "price_usd": float(price_info["usd"]),
                    "extracted_at": extracted_at,
                }
            )
        return flattened_data

    @task
    def load_data(data_to_load):
        if not data_to_load:
            raise ValueError("No data to load")

        df = pd.DataFrame(data_to_load)
        db_user = os.environ.get("CRYPTO_USER")
        db_password = os.environ.get("CRYPTO_PASSWORD")
        db_host = os.environ.get("CRYPTO_HOST")
        db_name = os.environ.get("CRYPTO_NAME")

        DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}"

        print("Loading into database")
        engine = create_engine(DATABASE_URL)
        df.to_sql(
            name="crypto_prices", con=engine, if_exists="append", index=False
        )
        print("Loaded successfully")

    crypto_data = extract_and_transform()
    load_data(crypto_data)

crypto_coingecko_etl()