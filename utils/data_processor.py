import pandas as pd
import mysql.connector as connector

def read_query(query):
    cnx = connector.connect(user='root', password='@h@hJ1de',
                              host='127.0.0.1',
                              database='osu')
    return pd.read_sql(query, cnx)

def export_osu_to_parquet(query, parquet_file):
    read_query(query).to_parquet(parquet_file)

__all__ = ['read_query', 'export_osu_to_parquet']
