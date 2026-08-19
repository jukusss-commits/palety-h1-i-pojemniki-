from database import db

print("Inicjalizacja bazy danych...")
db.add_pracownik("Jan", "1111", "kierownik")
db.add_pracownik("Maria", "2222", "magazynier")
db.add_klient("Klient A")
db.add_klient("Klient B")
print("✅ Gotowe! PIN: 0000")
