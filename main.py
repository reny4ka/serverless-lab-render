from flask import Flask, request, jsonify
import psycopg2
import os
from urllib.parse import urlparse

app = Flask(__name__)


def get_db_connection():
    DATABASE_URL = os.environ.get('DATABASE_URL')

    if not DATABASE_URL: return None

    try:
        url = urlparse(DATABASE_URL)
        conn = psycopg2.connect(
            database=url.path[1:], user=url.username, password=url.password, host=url.hostname, port=url.port,
            sslmode='require'
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
    return None


def init_db():
    conn = get_db_connection()

    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
            CREATE TABLE IF NOT EXISTS messages ( id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            
            created_at TIMESTAMP DEFAULT NOW()
            ) """)
                conn.commit()
        except Exception as e:
            print(f"Init DB error: {e}")
        finally:
            conn.close()



@app.route('/save', methods=['POST'])
def save_message():
    conn = get_db_connection() 
    if not conn:
        return jsonify({"error": "DB not connected"}), 500

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data"}), 400

        message = data.get('message', '')
        if not message:
            return jsonify({"error": "Message is required"}), 400
        with conn.cursor() as cur:
            cur.execute("INSERT INTO messages (content) VALUES (%s)", (message,))
            conn.commit()
        return jsonify({"status": "saved", "message": message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close() 


@app.route('/messages')
def get_messages():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "DB not connected"}), 500

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, content, created_at FROM messages ORDER BY id DESC LIMIT 10")
            rows = cur.fetchall()

        messages = [{"id": r[0], "text": r[1], "time": r[2].isoformat()} for r in rows]
        return jsonify(messages)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/')
def hello():
    return "Hello, Serverless with DB! ??\n", 200, {'Content-Type': 'text/plain'}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
