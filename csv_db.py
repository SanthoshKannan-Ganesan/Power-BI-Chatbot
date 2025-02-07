# import mysql.connector                                     ##//For mysql
# import pandas as pd
# from datetime import datetime

# def get_mysql_connection():
#     return mysql.connector.connect(
#         host="localhost",
#         user="root",
#         password="sree@2113",
#         database="power_bi"
#     )
# def to_camel_case(column_name):
#     words = column_name.split(' ')
#     return words[0] + ''.join(word.capitalize() for word in words[1:])

# def create_table_from_csv(csv_file_path, table_name):
#     df = pd.read_csv(csv_file_path)
#     conn = get_mysql_connection()
#     cursor = conn.cursor()
#     columns = []
#     for column, dtype in zip(df.columns, df.dtypes):
#         column = to_camel_case(column)
#         if dtype == 'int64':
#             mysql_dtype = 'INT'
#         elif dtype == 'float64':
#             mysql_dtype = 'FLOAT'
#         elif dtype == 'object':
#             mysql_dtype = 'VARCHAR(255)'
#         else:
#             mysql_dtype = 'TEXT'  
#         columns.append(f"`{column}` {mysql_dtype}")
#     create_table_query = f"CREATE TABLE IF NOT EXISTS `{table_name}` ({', '.join(columns)});"
#     cursor.execute(create_table_query)
#     conn.commit()


#     print(f"Table `{table_name}` created successfully.")
#     cursor.close()
#     conn.close()
# def insert_data_from_csv(csv_file_path, table_name):
#     df = pd.read_csv(csv_file_path)
#     conn = get_mysql_connection()
#     cursor = conn.cursor()
#     for index, row in df.iterrows():
#         columns = ', '.join([f"`{to_camel_case(col)}`" for col in df.columns])
#         placeholders = ', '.join(['%s'] * len(row))
#         values = tuple(row)  
#         insert_query = f"INSERT INTO `{table_name}` ({columns}) VALUES ({placeholders})"
#         try:
#             cursor.execute(insert_query, values)
#         except Exception as e:
#             print(f"Error inserting row {index + 1}: {e}")
#     conn.commit()
#     print(f"Data inserted into `{table_name}` successfully.")
#     cursor.close()
#     conn.close()
# csv_file_path = 'C:/Users/Gugan/Desktop/Tasks/super store.csv' 
# table_name = 'super_store'  
# create_table_from_csv(csv_file_path, table_name)
# insert_data_from_csv(csv_file_path, table_name)




##========================================================================================================



import pyodbc                                      ##//For sql server
import pandas as pd


def get_sqlserver_connection():
    return pyodbc.connect(
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        r'SERVER=GUGAN\SQLEXPRESS;'
        r'DATABASE=Learn;'
        r'Trusted_Connection=yes;'  
    )


def to_camel_case(column_name):
    words = column_name.split(' ')
    return words[0] + ''.join(word.capitalize() for word in words[1:])


def create_table_from_csv(csv_file_path):
    table_name = csv_file_path.split('/')[-1].split('.')[0].replace(' ', '_') 
    
    df = pd.read_csv(csv_file_path)
    conn = get_sqlserver_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{table_name}'")
    if cursor.fetchone():
        print(f"Table [{table_name}] already exists.")
        cursor.close()
        conn.close()
        return

    columns = []
    for column, dtype in zip(df.columns, df.dtypes):
        column = to_camel_case(column)
        if dtype == 'int64':
            sqlserver_dtype = 'INT'
        elif dtype == 'float64':
            sqlserver_dtype = 'FLOAT'
        elif dtype == 'object':
            sqlserver_dtype = 'VARCHAR(255)'
        else:
            sqlserver_dtype = 'TEXT'
        columns.append(f"[{column}] {sqlserver_dtype}")

    create_table_query = f"CREATE TABLE [{table_name}] ({', '.join(columns)});"
    cursor.execute(create_table_query)
    conn.commit()
    print(f"Table [{table_name}] created successfully.")

    cursor.close()
    conn.close()


def insert_data_from_csv(csv_file_path):
    table_name = csv_file_path.split('/')[-1].split('.')[0].replace(' ', '_') 

    df = pd.read_csv(csv_file_path)
    conn = get_sqlserver_connection()
    cursor = conn.cursor()

    for index, row in df.iterrows():
        columns = ', '.join([f"[{to_camel_case(col)}]" for col in df.columns])
        placeholders = ', '.join(['?'] * len(row))
        values = tuple(row)
        insert_query = f"INSERT INTO [{table_name}] ({columns}) VALUES ({placeholders})"
        try:
            cursor.execute(insert_query, values)
        except Exception as e:
            print(f"Error inserting row {index + 1}: {e}")

    conn.commit()
    print(f"Data inserted into [{table_name}] successfully.")
    cursor.close()
    conn.close()


csv_file_path = 'C:/Users/Gugan/Desktop/Tasks/super store.csv'

create_table_from_csv(csv_file_path)
insert_data_from_csv(csv_file_path)
