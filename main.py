import os
from flask import Flask
import psycopg2

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

@app.route("/")
def home():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        return "TRAFFICLAB Backend running & Database Connected!"
    except Exception as e:
        return f"Database Connection Error: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
