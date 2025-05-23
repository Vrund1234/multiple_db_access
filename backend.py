from flask import Flask, request, jsonify
import psycopg2
import pymongo
import mysql.connector
import pyodbc
import google.generativeai as genai
import traceback

app = Flask(__name__)

# ✅ Load Google Gemini API Key from Environment Variable
genai.configure(api_key="AIzaSyCKx7VQ7VgmzMk2WO68IMh0uVcfNcwovsY")


def generate_sql(nl_query, db_type):
    """Generate SQL using Gemini AI for different databases."""
    try:
        # model = genai.GenerativeModel("gemini-1.5-pro-latest")
        # model = genai.GenerativeModel("models/gemini-pro")
        # model = genai.GenerativeModel("Gemini 2.0 Flash")
        # model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        


        prompt = f"""
        Convert this user query into a **valid** SQL query for **{db_type}**.
        ❌ Do NOT include database names (like `DemoDB.table_name`).
        ✅ Just return SQL for a **single** database at a time.
        ❌ Do NOT use cross-database references.
        
        User Query: {nl_query}
        SQL:
        """
        response = model.generate_content(prompt)

        # ✅ Ensure clean SQL (remove accidental formatting)
        sql_query = response.text.strip().replace("```sql", "").replace("```", "").strip()
        return sql_query
    except Exception as e:
        return f"Error generating SQL: {str(e)}"
    

import json
import pymongo
from bson import ObjectId

class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to convert MongoDB ObjectId to a string."""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)  # Convert ObjectId to string
        return super().default(obj)

def execute_mongo_query(collection_name, db_config):
    """Fetch data from MongoDB while ensuring it is JSON serializable."""
    try:
        client = pymongo.MongoClient(db_config["host"], int(db_config["port"]))
        db = client[db_config["database"]]
        collection = db[collection_name]

        # ✅ Fetch full documents including `_id`
        data = list(collection.find())

        # ✅ Convert to JSON-safe format
        return json.loads(JSONEncoder().encode({"data": data}))

    except Exception as e:
        return {"error": str(e)}



def execute_sql_query(sql_query, db_type, db_config):
    """Execute the SQL query on the selected database type."""
    try:
        if db_type == "PostgreSQL":
            conn = psycopg2.connect(**db_config)
        elif db_type == "MySQL":
            conn = mysql.connector.connect(**db_config)
        elif db_type == "MSSQL":
            conn = pyodbc.connect(
                f"DRIVER={{SQL Server}};SERVER={db_config['host']};DATABASE={db_config['database']};UID={db_config['user']};PWD={db_config['password']}"
            )
        else:
            return {"error": "Invalid database type"}

        cursor = conn.cursor()
        cursor.execute(sql_query)
        result = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]

        cursor.close()
        conn.close()

        return {"columns": column_names, "data": [list(row) for row in result]}

    except Exception as e:
        return {"error": str(e)}


def execute_mongo_query(collection_name, db_config):
    """Fetch data from MongoDB."""
    try:
        client = pymongo.MongoClient(db_config["host"], int(db_config["port"]))
        db = client[db_config["database"]]
        collection = db[collection_name]
        data = list(collection.find({}, {"_id": 0}))  # Exclude `_id` field for cleaner output

        return {"data": data}

    except Exception as e:
        return {"error": str(e)}


# @app.route("/connect", methods=["POST"])
# def connect():
#     """Connect to the selected database."""
#     try:
#         data = request.json
#         db_type = data.get("db_type")
#         db_config = data.get("db_config")

#         if not db_type or not db_config:
#             return jsonify({"error": "Database type and connection details are required"}), 400

#         return jsonify({"message": f"Connected to {db_type} successfully!", "db_type": db_type, "db_config": db_config})

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


@app.route("/connect", methods=["POST"])
def connect():
    """Connect to the selected database and validate credentials."""
    try:
        data = request.json
        db_type = data.get("db_type")
        db_config = data.get("db_config")

        if not db_type or not db_config:
            return jsonify({"error": "Database type and connection details are required"}), 400

        # ✅ Validate connection based on database type
        if db_type == "PostgreSQL":
            conn = psycopg2.connect(**db_config)
        elif db_type == "MySQL":
            conn = mysql.connector.connect(**db_config)
        elif db_type == "MSSQL":
            conn = pyodbc.connect(
                f"DRIVER={{SQL Server}};SERVER={db_config['host']};DATABASE={db_config['database']};"
                f"UID={db_config['user']};PWD={db_config['password']}"
            )
        elif db_type == "MongoDB":
            client = pymongo.MongoClient(db_config["host"], int(db_config["port"]))
            db = client[db_config["database"]]
            db.command("ping")  # ✅ Test MongoDB connection
        else:
            return jsonify({"error": "Invalid database type"}), 400

        # ✅ Close connection after successful validation
        if db_type in ["PostgreSQL", "MySQL", "MSSQL"]:
            conn.close()

        return jsonify({"message": f"Connected to {db_type} successfully!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/ask", methods=["POST"])
def ask():
    """Process user query."""
    try:
        data = request.json
        user_query = data.get("query")
        db_type = data.get("db_type")
        db_config = data.get("db_config")

        if not db_type or not db_config:
            return jsonify({"error": "No database selected. Please connect first."}), 400

        if db_type == "MongoDB":
            collection_name = user_query.split()[-1]  # Extract collection name
            result = execute_mongo_query(collection_name, db_config)
            return jsonify({"result": result})  # ✅ No `sql_query` in response for MongoDB

        else:
            sql_query = generate_sql(user_query, db_type)
            if sql_query.startswith("Error"):
                return jsonify({"error": sql_query}), 500

            result = execute_sql_query(sql_query, db_type, db_config)
            return jsonify({"sql": sql_query, "result": result})  # ✅ `sql_query` included only for SQL databases

    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500



if __name__ == "__main__":
    app.run(debug=True)
