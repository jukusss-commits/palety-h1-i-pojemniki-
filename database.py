import sqlite3
from datetime import datetime
import os

class Database:
    def __init__(self, db_path="data/palety.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pracownicy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nazwa TEXT NOT NULL,
            pin TEXT UNIQUE NOT NULL,
            rola TEXT DEFAULT 'pracownik'
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS klienci (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nazwa TEXT UNIQUE NOT NULL
        )
        """)
        
        cursor.execute("SELECT * FROM pracownicy WHERE pin = '0000'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO pracownicy (nazwa, pin, rola) VALUES ('Admin', '0000', 'admin')")
        
        conn.commit()
        conn.close()

    def get_pracownik_by_pin(self, pin):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pracownicy WHERE pin = ?", (pin,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

db = Database()
