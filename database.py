import sqlite3
from datetime import datetime, timedelta
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
        
        # NOWA TABELA: ZMIANA
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS zmiana (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pracownik_id INTEGER NOT NULL,
            data_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_end TIMESTAMP,
            stan_poczatkowy INTEGER NOT NULL,
            stan_faktyczny_koniec INTEGER,
            status TEXT DEFAULT 'aktywna',
            zawieszyl_pracownik_id INTEGER,
            FOREIGN KEY(pracownik_id) REFERENCES pracownicy(id),
            FOREIGN KEY(zawieszyl_pracownik_id) REFERENCES pracownicy(id)
        )
        """)
        
        # NOWA TABELA: ROZBIEŻNOŚCI
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS rozbieznosci (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pracownik_id INTEGER NOT NULL,
            zmiana_id INTEGER NOT NULL,
            data_rozpoczecia TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            stan_przejety INTEGER NOT NULL,
            stan_faktyczny INTEGER NOT NULL,
            roznica INTEGER NOT NULL,
            status TEXT DEFAULT 'czeka',
            notatka_pracownika TEXT,
            notatka_kierownika TEXT,
            data_zatwierdzenia TIMESTAMP,
            zatwierdził_id INTEGER,
            licznik_dni INTEGER DEFAULT 0,
            ostatni_login TIMESTAMP,
            FOREIGN KEY(pracownik_id) REFERENCES pracownicy(id),
            FOREIGN KEY(zmiana_id) REFERENCES zmiana(id),
            FOREIGN KEY(zatwierdził_id) REFERENCES pracownicy(id)
        )
        """)
        
        # NOWA TABELA: OPERACJE MAGAZYNU
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS magazyn_operacje (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            magazynier_id INTEGER NOT NULL,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            typ TEXT NOT NULL,
            ilosc INTEGER NOT NULL,
            notatka TEXT,
            FOREIGN KEY(magazynier_id) REFERENCES pracownicy(id)
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

    def update_pracownik_pin(self, pracownik_id, nowy_pin):
        """Zmienić PIN pracownika"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE pracownicy SET pin = ? WHERE id = ?", (nowy_pin, pracownik_id))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()

    def delete_pracownik(self, pracownik_id):
        """Usunąć pracownika"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM pracownicy WHERE id = ?", (pracownik_id,))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()

    def get_all_pracownicy(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pracownicy ORDER BY nazwa")
        result = cursor.fetchall()
        conn.close()
        return [dict(r) for r in result]

    def get_pracownik_by_id(self, pracownik_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pracownicy WHERE id = ?", (pracownik_id,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

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
            self.update_magazyn(-abs(palety_zmiana))

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

    # ===== NOWE FUNKCJE DLA ZMIAN =====
    def start_zmiana(self, pracownik_id, stan_poczatkowy):
        """Rozpocząć zmianę pracownika"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO zmiana (pracownik_id, stan_poczatkowy, status) VALUES (?, ?, 'aktywna')",
            (pracownik_id, stan_poczatkowy)
        )
        conn.commit()
        zmiana_id = cursor.lastrowid
        conn.close()
        return zmiana_id

    def get_aktywna_zmiana(self, pracownik_id):
        """Pobrać aktywną zmianę pracownika"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM zmiana WHERE pracownik_id = ? AND status = 'aktywna'",
            (pracownik_id,)
        )
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

    def get_last_zmiana(self, pracownik_id):
        """Pobrać ostatnią zmianę pracownika"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM zmiana WHERE pracownik_id = ? ORDER BY data_start DESC LIMIT 1",
            (pracownik_id,)
        )
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

    def end_zmiana(self, zmiana_id, stan_faktyczny):
        """Zakończyć zmianę i zwrócić rozbieżność jeśli istnieje"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM zmiana WHERE id = ?", (zmiana_id,))
        zmiana = dict(cursor.fetchone())
        
        stan_teoretyczny = zmiana['stan_poczatkowy']
        roznica = stan_faktyczny - stan_teoretyczny
        
        cursor.execute(
            "UPDATE zmiana SET data_end = CURRENT_TIMESTAMP, stan_faktyczny_koniec = ?, status = 'zamknieta' WHERE id = ?",
            (stan_faktyczny, zmiana_id)
        )
        
        # Jeśli jest rozbieżność, utwórz rekord
        if roznica != 0:
            cursor.execute(
                """INSERT INTO rozbieznosci 
                (pracownik_id, zmiana_id, stan_przejety, stan_faktyczny, roznica, status, licznik_dni, ostatni_login)
                VALUES (?, ?, ?, ?, ?, 'czeka', 0, CURRENT_TIMESTAMP)""",
                (zmiana['pracownik_id'], zmiana_id, stan_teoretyczny, stan_faktyczny, roznica)
            )
        
        conn.commit()
        conn.close()
        
        return {
            "stan_teoretyczny": stan_teoretyczny,
            "stan_faktyczny": stan_faktyczny,
            "roznica": roznica,
            "ma_rozbieznosc": roznica != 0
        }

    def zawiesz_zmiane(self, zmiana_id, zawieszyl_id):
        """Zawiesić zmianę (koniec przesunięcia przez innego pracownika)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM zmiana WHERE id = ?", (zmiana_id,))
        zmiana = dict(cursor.fetchone())
        
        stan_faktyczny = zmiana['stan_poczatkowy']  # Bierze stan początkowy jako faktyczny
        
        cursor.execute(
            "UPDATE zmiana SET data_end = CURRENT_TIMESTAMP, stan_faktyczny_koniec = ?, status = 'zawieszona', zawieszyl_pracownik_id = ? WHERE id = ?",
            (stan_faktyczny, zawieszyl_id, zmiana_id)
        )
        conn.commit()
        conn.close()
        
        return stan_faktyczny

    # ===== ROZBIEŻNOŚCI =====
    def get_rozbieznosci_pracownika(self, pracownik_id):
        """Pobrać rozbieżności pracownika"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM rozbieznosci WHERE pracownik_id = ? ORDER BY data_rozpoczecia DESC",
            (pracownik_id,)
        )
        result = cursor.fetchall()
        conn.close()
        return [dict(r) for r in result]

    def get_all_rozbieznosci(self):
        """Pobrać wszystkie rozbieżności"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT r.*, p.nazwa as pracownik_nazwa FROM rozbieznosci r
            JOIN pracownicy p ON r.pracownik_id = p.id
            ORDER BY r.data_rozpoczecia DESC"""
        )
        result = cursor.fetchall()
        conn.close()
        return [dict(r) for r in result]

    def get_otwarte_rozbieznosci_pracownika(self, pracownik_id):
        """Pobrać otwarte rozbieżności pracownika"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM rozbieznosci WHERE pracownik_id = ? AND status IN ('czeka', 'wyjasnione')",
            (pracownik_id,)
        )
        result = cursor.fetchall()
        conn.close()
        return [dict(r) for r in result]

    def add_notatka_pracownika(self, rozbieznosc_id, notatka):
        """Dodać notatkę pracownika do rozbieżności"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE rozbieznosci SET notatka_pracownika = ?, status = 'wyjasnione' WHERE id = ?",
            (notatka, rozbieznosc_id)
        )
        conn.commit()
        conn.close()

    def zatwierdzenie_rozbieznosci(self, rozbieznosc_id, kierownik_id, notatka_kierownika="", nowa_roznica=None):
        """Zatwierdzić rozbieżność (kierownik)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if nowa_roznica is not None:
            cursor.execute(
                """UPDATE rozbieznosci 
                SET status = 'zatwierdzona', notatka_kierownika = ?, 
                    data_zatwierdzenia = CURRENT_TIMESTAMP, zatwierdził_id = ?,
                    roznica = ?
                WHERE id = ?""",
                (notatka_kierownika, kierownik_id, nowa_roznica, rozbieznosc_id)
            )
        else:
            cursor.execute(
                """UPDATE rozbieznosci 
                SET status = 'zatwierdzona', notatka_kierownika = ?, 
                    data_zatwierdzenia = CURRENT_TIMESTAMP, zatwierdził_id = ?
                WHERE id = ?""",
                (notatka_kierownika, kierownik_id, rozbieznosc_id)
            )
        
        conn.commit()
        conn.close()

    def czy_ma_otwarta_rozbieznosc(self, pracownik_id):
        """Sprawdzić czy pracownik ma otwartą rozbieżność do wyjaśnienia"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as count FROM rozbieznosci WHERE pracownik_id = ? AND status = 'czeka'",
            (pracownik_id,)
        )
        result = cursor.fetchone()
        conn.close()
        return result['count'] > 0

    # ===== LOGIKA 3 DNI (12H OD LOGOWANIA) =====
    def record_login_i_sprawdz_rozbieznosci(self, pracownik_id):
        """
        Zaloguj pracownika i sprawdź rozbieżności.
        Logika: każde logowanie +12h licznika, po 3 logowaniach rozbieżność wygasa.
        Kierownik może zatwierdził wcześniej (licznik stop).
        Zwraca True jeśli rozbieżność wygasła.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Pobierz otwarte rozbieżności pracownika
        cursor.execute(
            "SELECT * FROM rozbieznosci WHERE pracownik_id = ? AND status IN ('czeka', 'wyjasnione')",
            (pracownik_id,)
        )
        rozbieznosci = [dict(r) for r in cursor.fetchall()]
        
        expired = False
        
        for rozb in rozbieznosci:
            # Zwiększ licznik dni
            nowy_licznik = (rozb['licznik_dni'] or 0) + 1
            
            # Jeśli licznik >= 3, rozbieżność wygasa
            if nowy_licznik >= 3:
                cursor.execute(
                    """UPDATE rozbieznosci 
                    SET status = 'wygasla', licznik_dni = ?
                    WHERE id = ?""",
                    (nowy_licznik, rozb['id'])
                )
                expired = True
            else:
                # Inaczej, aktualizuj licznik i ostatni login
                cursor.execute(
                    """UPDATE rozbieznosci 
                    SET licznik_dni = ?, ostatni_login = CURRENT_TIMESTAMP
                    WHERE id = ?""",
                    (nowy_licznik, rozb['id'])
                )
        
        conn.commit()
        conn.close()
        
        return expired

    # ===== MAGAZYN OPERACJE =====
    def add_magazyn_operacja(self, magazynier_id, typ, ilosc, notatka=""):
        """Dodać operację magazynu"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO magazyn_operacje (magazynier_id, typ, ilosc, notatka) VALUES (?, ?, ?, ?)",
            (magazynier_id, typ, ilosc, notatka)
        )
        conn.commit()
        conn.close()
        self.update_magazyn(ilosc if typ == "przyjecie" else -ilosc)

    def get_magazyn_operacje(self, limit=50):
        """Pobrać operacje magazynu"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT m.*, p.nazwa as magazynier_nazwa FROM magazyn_operacje m
            JOIN pracownicy p ON m.magazynier_id = p.id
            ORDER BY m.data DESC LIMIT ?""",
            (limit,)
        )
        result = cursor.fetchall()
        conn.close()
        return [dict(r) for r in result]

db = Database()
