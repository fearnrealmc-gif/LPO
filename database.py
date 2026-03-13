import sqlite3
import os

DB_PATH = "lpo_app.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create Sites table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            engineer TEXT NOT NULL,
            phone TEXT NOT NULL,
            delivery_point TEXT
        )
    ''')
    
    # Migration: add delivery_point if it doesn't exist
    try:
        cursor.execute("ALTER TABLE sites ADD COLUMN delivery_point TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists
    
    conn.commit()
    conn.close()

def add_site(name, engineer, phone, delivery_point):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO sites (name, engineer, phone, delivery_point) VALUES (?, ?, ?, ?)', (name, engineer, phone, delivery_point))
    conn.commit()
    conn.close()

def get_sites():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sites')
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_site(site_id, name, engineer, phone, delivery_point):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE sites SET name=?, engineer=?, phone=?, delivery_point=? WHERE id=?', (name, engineer, phone, delivery_point, site_id))
    conn.commit()
    conn.close()

def delete_site(site_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM sites WHERE id=?', (site_id,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
