from flask import Flask, render_template, request, jsonify
import pyodbc
import google.generativeai as genai

app = Flask(__name__)

def get_sqlserver_connection():
    return pyodbc.connect(
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        r'SERVER=GUGAN\SQLEXPRESS;'
        r'DATABASE=Learn;'
        r'Trusted_Connection=yes;'
    )

def fetch_table_names():
    conn = get_sqlserver_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")  
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


def fetch_column_names(table_name):
    conn = get_sqlserver_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'")  
    columns = [row[0] for row in cursor.fetchall()]
    conn.close()
    return columns

def fetch_data_from_sql(query):
    conn = get_sqlserver_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    result = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    conn.close()
    return result

genai.configure(api_key="AIzaSyCbhdZdMLJILJSyAsr57EZbkZTcW95vJ0E")  

def get_sql_query_from_gemini(query, table_name):
    prompt = f"""
You are a SQL expert. Your task is to analyze the user's query and generate only the **pure SQL Server query** required to fulfill the request.

### Instructions:
1. Respond with the **SQL query only**, with no additional text, characters, or formatting (e.g., no quotation marks, code blocks, or explanations).
2. Do not include any markdown or programming syntax in the response.
3. Ensure the query is syntactically correct for SQL Server.
4. If the query includes a column alias that conflicts with SQL Server reserved keywords (e.g., `Year`), rename the alias to avoid conflicts (e.g., `year_col` instead of `Year`).
5. Check if the column `Year` or any other relevant column (e.g., `OrderDate`) is present in the table before using it. If the column does not exist, do not use it in the query.
6. If needed, extract or derive values (e.g., `YEAR(OrderDate)`) in the query instead of using an alias that could conflict with existing columns.
7. Use alternative methods if a column alias or column is conflicting. For example, if `YEAR(OrderDate)` is used, do not create an alias like `year_col`, but instead use `YEAR(OrderDate)` directly or check if a `year_col` column is already present in the table.
8. Use proper window functions, subqueries, and CTEs (Common Table Expressions) as needed to ensure compatibility with SQL Server syntax.
9. Ensure the query complies with the **SQL Server ONLY_FULL_GROUP_BY equivalent** by properly grouping or aggregating non-aggregated columns.

### Example:
- User query: "Get the total sales value from the `super store` table"
  - Response: SELECT SUM(Sales) AS TotalSalesValue FROM super store;

- User query: "state name that starts with n"
  - Response: SELECT DISTINCT State FROM super store WHERE State LIKE 'N%';

- User query: "which city that has the highest profit in 2017?"
  - Response: SELECT TOP 1 City, SUM(Profit) AS TotalProfit FROM super store WHERE YEAR(OrderDate) = 2017 GROUP BY City ORDER BY SUM(Profit) DESC;

- User query: "state that has the highest sales for each year"
  - Response: 
WITH SalesByYearState AS (
    SELECT 
        YEAR(OrderDate) AS year_col, 
        State, 
        SUM(Sales) AS TotalSales, 
        RANK() OVER (PARTITION BY YEAR(OrderDate) ORDER BY SUM(Sales) DESC) AS rank
    FROM super store
    GROUP BY YEAR(OrderDate), State
)
SELECT year_col, State, TotalSales
FROM SalesByYearState
WHERE rank = 1;

- User query: "Get the total sales by year"
  - Response: SELECT YEAR(OrderDate) AS year_col, SUM(Sales) AS TotalSales FROM super store GROUP BY YEAR(OrderDate);

- User query: "In each year, find the state with the highest sales"
  - Response:
WITH YearlyStateSales AS (
    SELECT 
        YEAR(OrderDate) AS year_col, 
        State, 
        SUM(Sales) AS TotalSales, 
        RANK() OVER (PARTITION BY YEAR(OrderDate) ORDER BY SUM(Sales) DESC) AS rank
    FROM super store
    GROUP BY YEAR(OrderDate), State
)
SELECT year_col, State, TotalSales
FROM YearlyStateSales
WHERE rank = 1;

Table_name are {table_name}
column_name are {fetch_column_names(table_name)}
User query: "{query}"
"""

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()

@app.route('/')
def home():
    return render_template('chat.html')

@app.route('/get_tables', methods=['GET'])
def get_tables():
    try:
        tables = fetch_table_names()
        return jsonify({'tables': tables})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.json.get('input')
    table_name = request.json.get('table_name')  
    if not table_name:
        return jsonify({'error': 'Table name is required'}), 400  

    sql_query = get_sql_query_from_gemini(user_input, table_name)
    
    try:
        data = fetch_data_from_sql(sql_query)
        result = f"""
Analyze the given data and user query, and generate a **concise insight** that clearly explains the significance of the result values.The insight should be in the conversation format and should not be written in markdown or programming language. 

### Guidelines:
1. **Provide a clear, concise insight** that adds meaningful context to the result values, Elabrate the insight.
2. **Highlight key terms or values** in the insights with **bold font** and and **attractive colors** (e.g., blue, green, or red), remove the double star**.
3. Ensure that the insight is **clear**, **concise**, and provides value to the user query.
4. **Remove the double stars** (for example, **Insight** to Insight).
5.Strictly follow this -**Remove the double stars** for all over the insights **$100000** to **$100000**

##Please provide:
    1. A natural language explanation 
    2. Key insights from the results
    3. Any interesting patterns or trends
    4. Suggestions for additional analysis if relevant
    5. Any limitations or caveats about the results
    6. Every point in new line

##Example:
Insight(in bold font):
Sales showed a significant increase from 2014 (484,247.50) to 2017 (733,215.25), indicating a positive growth trend.
### Data:  
{data}  

### User Query:  
{user_input}  

### Expected Output:
1. A **concise insight** summarizing the results with emphasis on key points.
"""
        model = genai.GenerativeModel("gemini-1.5-flash")
        responsetext = model.generate_content(result, generation_config={"temperature": 0.7})
        
        return jsonify({
            'response': data,
            'responsetext': responsetext.text.strip(),
            'query': sql_query
        })
    except Exception as e:
        return jsonify({'response': f"Error: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)
