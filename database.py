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
            nazwa TEXT UNIQUE NOT NULL,
            nip TEXT UNIQUE
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS saldo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            klient_id INTEGER NOT NULL,
            palety INTEGER DEFAULT 0,
            pojemniki INTEGER DEFAULT 0,
            data_zmiana TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(klient_id) REFERENCES klienci(id)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS magazyn (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            palety INTEGER DEFAULT 0,
            data_zmiana TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transakcje (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            klient_id INTEGER NOT NULL,
            typ TEXT NOT NULL,
            palety INTEGER DEFAULT 0,
            pojemniki INTEGER DEFAULT 0,
            kierowca TEXT,
            pracownik_id INTEGER,
            saldo_przed_palety INTEGER DEFAULT 0,
            saldo_przed_pojemniki INTEGER DEFAULT 0,
            saldo_po_palety INTEGER DEFAULT 0,
            saldo_po_pojemniki INTEGER DEFAULT 0,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(klient_id) REFERENCES klienci(id),
            FOREIGN KEY(pracownik_id) REFERENCES pracownicy(id)
        )
        """)
        
        cursor.execute("SELECT * FROM pracownicy WHERE pin = '0000'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO pracownicy (nazwa, pin, rola) VALUES ('Admin', '0000', 'admin')")
        
        cursor.execute("SELECT * FROM magazyn")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO magazyn (palety) VALUES (0)")
        
        conn.commit()
        conn.close()

    def get_pracownik_by_pin(self, pin):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pracownicy WHERE pin = ?", (pin,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

    def add_pracownik(self, nazwa, pin, rola="pracownik"):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO pracownicy (nazwa, pin, rola) VALUES (?, ?, ?)", (nazwa, pin, rola))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()

    def add_klient(self, nazwa, nip=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM klienci WHERE nazwa = ?", (nazwa,))
        if cursor.fetchone():
            conn.close()
            return {"status": False, "error": "nazwa_exists"}
        
        if nip:
            cursor.execute("SELECT * FROM klienci WHERE nip = ?", (nip,))
            if cursor.fetchone():
                conn.close()
                return {"status": False, "error": "nip_exists"}
        
        try:
            cursor.execute("INSERT INTO klienci (nazwa, nip) VALUES (?, ?)", (nazwa, nip if nip else None))
            conn.commit()
            conn.close()
            return {"status": True}
        except:
            conn.close()
            return {"status": False, "error": "unknown"}

    def get_all_klienci(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM klienci ORDER BY nazwa")
        result = cursor.fetchall()
        conn.close()
        return [dict(r) for r in result]

    def get_saldo(self, klient_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT palety, pojemniki FROM saldo WHERE klient_id = ?", (klient_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return dict(result)
        return {"palety": 0, "pojemniki": 0}

    def get_magazyn(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT palety FROM magazyn LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        if result:
            return dict(result)
        return {"palety": 0}

    def update_magazyn(self, palety_zmiana=0):
        conn = self.get_connection()
        cursor = conn.cursor()
        mag = self.get_magazyn()
        new_palety = mag["palety"] + palety_zmiana
        cursor.execute(
            "UPDATE magazyn SET palety = ?, data_zmiana = CURRENT_TIMESTAMP WHERE id = 1",
            (new_palety,)
        )
        conn.commit()
        conn.close()
        return {"palety": new_palety}

    def update_saldo(self, klient_id, palety_zmiana=0, pojemniki_zmiana=0, kierowca="", typ="PRZYJECIE", pracownik_id=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        saldo = self.get_saldo(klient_id)
        
        saldo_przed_p = saldo["palety"]
        saldo_przed_po = saldo["pojemniki"]
        
        new_palety = saldo["palety"] + palety_zmiana
        new_pojemniki = saldo["pojemniki"] + pojemniki_zmiana
        
        cursor.execute("SELECT id FROM saldo WHERE klient_id = ?", (klient_id,))
        if cursor.fetchone():
            cursor.execute(
                "UPDATE saldo SET palety = ?, pojemniki = ?, data_zmiana = CURRENT_TIMESTAMP WHERE klient_id = ?",
                (new_palety, new_pojemniki, klient_id)
            )
        else:
            cursor.execute(
                "INSERT INTO saldo (klient_id, palety, pojemniki) VALUES (?, ?, ?)",
                (klient_id, new_palety, new_pojemniki)
            )
        
        cursor.execute(
            """INSERT INTO transakcje 
            (klient_id, typ, palety, pojemniki, kierowca, pracownik_id, 
             saldo_przed_palety, saldo_przed_pojemniki, saldo_po_palety, saldo_po_pojemniki) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (klient_id, typ, palety_zmiana, pojemniki_zmiana, kierowca, pracownik_id,
             saldo_przed_p, saldo_przed_po, new_palety, new_pojemniki)
        )
        conn.commit()
        conn.close()
        
        if typ == "PRZYJECIE":
            self.update_magazyn(palety_zmiana)
        elif typ == "WYDANIE":
            self.update_magazyn(-palety_zmiana)
        
        return {"palety": new_palety, "pojemniki": new_pojemniki}

    def get_historia(self, klient_id, limit=10):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM transakcje WHERE klient_id = ? ORDER BY data DESC LIMIT ?",
            (klient_id, limit)
        )
        result = cursor.fetchall()
        conn.close()
        return [dict(r) for r in result]

db = Database()
