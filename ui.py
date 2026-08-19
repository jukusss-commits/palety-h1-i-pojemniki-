import tkinter as tk
from tkinter import messagebox, ttk
from config import WINDOW_WIDTH, WINDOW_HEIGHT
from database import db
from datetime import datetime
import os
import subprocess

# ===== LOGIN WINDOW =====
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("H1 Palety - Logowanie")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        
        main_frame = tk.Frame(self, bg="white")
        main_frame.pack(expand=True, fill="both")
        
        title = tk.Label(main_frame, text="H1 PALETY", font=("Arial", 48, "bold"), bg="white")
        title.pack(pady=20)
        
        pin_label = tk.Label(main_frame, text="PIN:", font=("Arial", 18), bg="white")
        pin_label.pack(pady=10)
        
        self.pin_entry = tk.Entry(main_frame, show="*", font=("Arial", 16), width=20)
        self.pin_entry.pack(pady=10)
        self.pin_entry.focus()
        self.pin_entry.bind('<Return>', lambda e: self.login())
        
        btn = tk.Button(main_frame, text="Zaloguj", command=self.login, font=("Arial", 14), bg="#4CAF50", fg="white", padx=20, pady=10)
        btn.pack(pady=10)
        
        self.error_label = tk.Label(main_frame, text="", font=("Arial", 12), bg="white", fg="#D32F2F")
        self.error_label.pack(pady=10)

    def login(self):
        pin = self.pin_entry.get()
        if not pin:
            self.error_label.config(text="Wpisz PIN!")
            return
        
        pracownik = db.get_pracownik_by_pin(pin)
        if not pracownik:
            self.error_label.config(text="Niepoprawny PIN!")
            self.pin_entry.delete(0, "end")
            return
        
        otwarta = db.get_aktywna_zmiana(pracownik['id'])
        if otwarta:
            messagebox.showerror("Błąd", "Masz otwartą zmianę! Najpierw ją zamknij.")
            self.pin_entry.delete(0, "end")
            return
        
        ma_rozbieznosc = db.czy_ma_otwarta_rozbieznosc(pracownik['id'])
        
        self.destroy()
        
        if pracownik['rola'] == 'pracownik':
            app = PoczatekZmianyWindow(pracownik, ma_rozbieznosc)
        elif pracownik['rola'] == 'kierownik':
            app = DashboardKierownika(pracownik)
        elif pracownik['rola'] == 'admin':
            app = PanelAdmina(pracownik)
        elif pracownik['rola'] == 'magazynier':
            app = PanelMagazyniera(pracownik)
        
        app.mainloop()

# ===== POCZĄTEK ZMIANY WINDOW =====
class PoczatekZmianyWindow(tk.Tk):
    def __init__(self, user, ma_rozbieznosc):
        super().__init__()
        self.user = user
        self.title(f"H1 Palety - Początek zmiany - {user['nazwa']}")
        self.geometry("600x500")
        
        header = tk.Frame(self, bg="#FF6B6B", height=60)
        header.pack(fill="x")
        tk.Label(header, text=f"POCZĄTEK ZMIANY - {user['nazwa']}", font=("Arial", 16, "bold"), bg="#FF6B6B", fg="white").pack(pady=15)
        
        main_frame = tk.Frame(self, bg="white")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        if ma_rozbieznosc:
            warning_frame = tk.Frame(main_frame, bg="#FFF3E0", relief="solid", borderwidth=2)
            warning_frame.pack(fill="x", pady=10)
            tk.Label(warning_frame, text="⚠️ UWAGA! Masz otwarte rozbieżności do wyjaśnienia!", font=("Arial", 12, "bold"), bg="#FFF3E0", fg="#E65100").pack(pady=10)
        
        last_zmiana = db.get_last_zmiana(user['id'])
        stan_poprzednika = last_zmiana['stan_faktyczny_koniec'] if last_zmiana else 0
        
        tk.Label(main_frame, text="Stan palet od poprzednika:", font=("Arial", 14, "bold"), bg="white").pack(pady=10)
        
        info_frame = tk.Frame(main_frame, bg="#E3F2FD", relief="solid", borderwidth=2)
        info_frame.pack(fill="x", pady=10)
        tk.Label(info_frame, text=f"{stan_poprzednika} palet", font=("Arial", 28, "bold"), bg="#E3F2FD", fg="#1976D2").pack(pady=20)
        
        tk.Label(main_frame, text="Czy przejmujesz ten stan?", font=("Arial", 13, "bold"), bg="white").pack(pady=10)
        
        btn_frame = tk.Frame(main_frame, bg="white")
        btn_frame.pack(fill="x", pady=20)
        
        def potwierdz():
            zmiana_id = db.start_zmiana(user['id'], stan_poprzednika)
            self.destroy()
            app = MainWindow(user, zmiana_id)
            app.mainloop()
        
        def niezgodnosc():
            faktyczny_win = tk.Toplevel(self)
            faktyczny_win.title("Faktyczny stan palet")
            faktyczny_win.geometry("400x300")
            faktyczny_win.grab_set()
            
            tk.Label(faktyczny_win, text="Ile palet masz faktycznie?", font=("Arial", 12, "bold")).pack(pady=20)
            
            entry = tk.Entry(faktyczny_win, font=("Arial", 16), width=10)
            entry.pack(pady=10)
            entry.focus()
            
            def zapisz_niezgodnosc():
                try:
                    stan_faktyczny = int(entry.get())
                    zmiana_id = db.start_zmiana(user['id'], stan_faktyczny)
                    rozbieznosc = stan_faktyczny - stan_poprzednika
                    
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        """INSERT INTO rozbieznosci 
                        (pracownik_id, zmiana_id, stan_przejety, stan_faktyczny, roznica, status)
                        VALUES (?, ?, ?, ?, ?, 'czeka')""",
                        (user['id'], zmiana_id, stan_poprzednika, stan_faktyczny, rozbieznosc)
                    )
                    conn.commit()
                    conn.close()
                    
                    messagebox.showinfo("OK", f"Rozbieżność: {rozbieznosc:+d} palet\nMasz 3 dni na wyjaśnienie!")
                    faktyczny_win.destroy()
                    self.destroy()
                    app = MainWindow(user, zmiana_id)
                    app.mainloop()
                except:
                    messagebox.showerror("Błąd", "Wpisz liczbę!")
            
            tk.Button(faktyczny_win, text="Potwierdź", command=zapisz_niezgodnosc, font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", padx=30, pady=10).pack(pady=20)
        
        tk.Button(btn_frame, text="✅ TAK - Przejmuję", command=potwierdz, font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", padx=20, pady=12).pack(fill="x", pady=5)
        tk.Button(btn_frame, text="❌ NIE - Mam inny stan", command=niezgodnosc, font=("Arial", 12, "bold"), bg="#FF9800", fg="white", padx=20, pady=12).pack(fill="x", pady=5)

# ===== MAIN WINDOW (PRACOWNIK) =====
class MainWindow(tk.Tk):
    def __init__(self, user, zmiana_id):
        super().__init__()
        self.user = user
        self.zmiana_id = zmiana_id
        self.title(f"H1 Palety - {user['nazwa']}")
        self.geometry("1400x950")
        
        header = tk.Frame(self, bg="#FF6B6B", height=60)
        header.pack(fill="x")
        
        header_label = tk.Label(
            header, 
            text=f"H1 PALETY - {user['nazwa']} (PRACOWNIK)", 
            font=("Arial", 18, "bold"),
            bg="#FF6B6B",
            fg="white"
        )
        header_label.pack(pady=15)
        
        main_frame = tk.Frame(self, bg="white")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        top_info_frame = tk.Frame(main_frame, bg="white")
        top_info_frame.pack(fill="x", pady=10)
        
        btn_add_klient = tk.Button(top_info_frame, text="➕ Dodaj klienta", command=self.add_klient_window, font=("Arial", 12, "bold"), bg="#FF9800", fg="white", padx=15, pady=8)
        btn_add_klient.pack(side="left", padx=5)
        
        mag_frame = tk.Frame(top_info_frame, bg="#FFE082", relief="solid", borderwidth=2, padx=15, pady=8)
        mag_frame.pack(side="left", padx=20, fill="x", expand=True)
        
        tk.Label(mag_frame, text="MAGAZYN - PALETY:", font=("Arial", 12, "bold"), bg="#FFE082").pack(side="left")
        self.mag_label = tk.Label(mag_frame, text="0", font=("Arial", 14, "bold"), bg="#FFE082", fg="#D32F2F")
        self.mag_label.pack(side="left", padx=10)
        
        left_right_frame = tk.Frame(main_frame, bg="white")
        left_right_frame.pack(fill="both", expand=True)
        
        left_frame = tk.Frame(left_right_frame, bg="white")
        left_frame.pack(side="left", fill="both", expand=False, padx=(0, 10))
        
        tk.Label(left_frame, text="🔍 SZUKAJ KLIENTA", font=("Arial", 13, "bold"), bg="white").pack(fill="x", pady=(0, 10))
        
        search_input_frame = tk.Frame(left_frame, bg="white")
        search_input_frame.pack(fill="x", pady=5)
        
        tk.Label(search_input_frame, text="Nazwa / NIP:", font=("Arial", 11), bg="white").pack()
        self.search_entry = tk.Entry(search_input_frame, font=("Arial", 12), width=25)
        self.search_entry.pack(fill="x")
        self.search_entry.bind('<KeyRelease>', self.on_search)
        
        results_frame = tk.Frame(left_frame, bg="white", relief="solid", borderwidth=1)
        results_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        tk.Label(results_frame, text="WYNIKI:", font=("Arial", 11, "bold"), bg="white").pack(fill="x", padx=5, pady=5)
        
        self.results_tree = ttk.Treeview(results_frame, columns=("Nazwa", "NIP"), height=15, show="tree")
        self.results_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.results_tree.bind('<Double-1>', self.on_result_click)
        
        right_frame = tk.Frame(left_right_frame, bg="white", relief="solid", borderwidth=2)
        right_frame.pack(side="left", fill="both", expand=True, padx=(10, 0))
        
        tk.Label(right_frame, text="📋 ROZLICZENIE", font=("Arial", 13, "bold"), bg="white").pack(fill="x", padx=10, pady=10)
        
        selected_frame = tk.Frame(right_frame, bg="#E3F2FD", relief="solid", borderwidth=1)
        selected_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(selected_frame, text="Wybrany klient:", font=("Arial", 10, "bold"), bg="#E3F2FD").pack(side="left", padx=5, pady=5)
        self.selected_label = tk.Label(selected_frame, text="Brak", font=("Arial", 11, "bold"), bg="#E3F2FD", fg="#D32F2F")
        self.selected_label.pack(side="left", padx=5, pady=5)
        
        saldo_frame = tk.Frame(right_frame, bg="#F5F5F5", relief="solid", borderwidth=1)
        saldo_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(saldo_frame, text="Aktualne saldo:", font=("Arial", 10, "bold"), bg="#F5F5F5").pack(fill="x", padx=5, pady=5)
        
        saldo_inner = tk.Frame(saldo_frame, bg="#F5F5F5")
        saldo_inner.pack(fill="x", padx=10, pady=5)
        
        self.palety_saldo = tk.Label(saldo_inner, text="Palety: 0", font=("Arial", 12, "bold"), bg="#F5F5F5", fg="#1976D2")
        self.palety_saldo.pack(side="left", padx=20)
        
        self.pojemniki_saldo = tk.Label(saldo_inner, text="Pojemniki: 0", font=("Arial", 12, "bold"), bg="#F5F5F5", fg="#1976D2")
        self.pojemniki_saldo.pack(side="left", padx=20)
        
        input_frame = tk.Frame(right_frame, bg="white")
        input_frame.pack(fill="x", padx=10, pady=10)
        
        przyjete_frame = tk.LabelFrame(input_frame, text="PRZYJĘTE", font=("Arial", 11, "bold"), bg="#E8F5E9", fg="#388E3C", padx=10, pady=10)
        przyjete_frame.pack(fill="x", pady=5)
        
        p_frame = tk.Frame(przyjete_frame, bg="#E8F5E9")
        p_frame.pack(fill="x")
        tk.Label(p_frame, text="Palety:", font=("Arial", 10), bg="#E8F5E9").pack(side="left", padx=5)
        self.przyjete_p = tk.Entry(p_frame, font=("Arial", 11), width=10)
        self.przyjete_p.pack(side="left", padx=5)
        self.przyjete_p.insert(0, "0")
        
        tk.Label(p_frame, text="Pojemniki:", font=("Arial", 10), bg="#E8F5E9").pack(side="left", padx=5)
        self.przyjete_po = tk.Entry(p_frame, font=("Arial", 11), width=10)
        self.przyjete_po.pack(side="left", padx=5)
        self.przyjete_po.insert(0, "0")
        
        wydane_frame = tk.LabelFrame(input_frame, text="WYDANE", font=("Arial", 11, "bold"), bg="#FFEBEE", fg="#D32F2F", padx=10, pady=10)
        wydane_frame.pack(fill="x", pady=5)
        
        w_frame = tk.Frame(wydane_frame, bg="#FFEBEE")
        w_frame.pack(fill="x")
        tk.Label(w_frame, text="Palety:", font=("Arial", 10), bg="#FFEBEE").pack(side="left", padx=5)
        self.wydane_p = tk.Entry(w_frame, font=("Arial", 11), width=10)
        self.wydane_p.pack(side="left", padx=5)
        self.wydane_p.insert(0, "0")
        
        tk.Label(w_frame, text="Pojemniki:", font=("Arial", 10), bg="#FFEBEE").pack(side="left", padx=5)
        self.wydane_po = tk.Entry(w_frame, font=("Arial", 11), width=10)
        self.wydane_po.pack(side="left", padx=5)
        self.wydane_po.insert(0, "0")
        
        kierowca_frame = tk.Frame(right_frame, bg="white")
        kierowca_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(kierowca_frame, text="Kierowca:", font=("Arial", 10, "bold"), bg="white").pack(side="left", padx=5)
        self.kierowca_entry = tk.Entry(kierowca_frame, font=("Arial", 11), width=30)
        self.kierowca_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        btn_frame = tk.Frame(right_frame, bg="white")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        btn_rozlicz = tk.Button(btn_frame, text="✅ ROZLICZ", command=self.rozlicz, font=("Arial", 13, "bold"), bg="#4CAF50", fg="white", padx=20, pady=12)
        btn_rozlicz.pack(fill="x")
        
        btn_historia = tk.Button(btn_frame, text="📖 Historia transakcji", command=self.show_historia_window, font=("Arial", 11), bg="#2196F3", fg="white", padx=20, pady=8)
        btn_historia.pack(fill="x", pady=(5, 0))
        
        btn_rozbieznosci = tk.Button(btn_frame, text="⚠️ Moje rozbieżności", command=self.show_rozbieznosci_window, font=("Arial", 11), bg="#FF9800", fg="white", padx=20, pady=8)
        btn_rozbieznosci.pack(fill="x", pady=(5, 0))
        
        bottom_frame = tk.Frame(self, bg="white")
        bottom_frame.pack(fill="x", padx=20, pady=10)
        
        btn_zamknij = tk.Button(bottom_frame, text="🔐 ZAMKNIJ ZMIANĘ", command=self.zamknij_zmiane, font=("Arial", 12, "bold"), bg="#D32F2F", fg="white", padx=20, pady=10)
        btn_zamknij.pack(side="left", padx=5)
        
        btn_logout = tk.Button(bottom_frame, text="Wyloguj", command=self.logout, font=("Arial", 11), bg="#757575", fg="white", padx=20, pady=10)
        btn_logout.pack(side="left", padx=5)
        
        self.selected_klient_id = None
        self.refresh_klienci()
        self.update_magazyn_display()
    
    def refresh_klienci(self):
        self.all_klienci = db.get_all_klienci()
    
    def on_search(self, event):
        search_text = self.search_entry.get().lower().strip()
        
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        filtered = []
        for k in self.all_klienci:
            if search_text == "" or search_text in k['nazwa'].lower() or (k['nip'] and search_text in k['nip']):
                filtered.append(k)
        
        for k in filtered:
            nip_display = k['nip'] if k['nip'] else "-"
            self.results_tree.insert("", "end", text=k['nazwa'], values=(k['nazwa'], nip_display), iid=k['id'])
    
    def on_result_click(self, event):
        selection = self.results_tree.selection()
        if not selection:
            return
        klient_id = int(selection[0])
        klient = next((k for k in self.all_klienci if k['id'] == klient_id), None)
        if klient:
            self.select_klient(klient)
    
    def select_klient(self, klient):
        self.selected_klient_id = klient['id']
        display = f"{klient['nazwa']}"
        if klient['nip']:
            display += f" (NIP: {klient['nip']})"
        self.selected_label.config(text=display, fg="#1976D2")
        self.update_saldo()
        self.load_last_kierowca()
    
    def update_magazyn_display(self):
        mag = db.get_magazyn()
        self.mag_label.config(text=str(mag['palety']))
    
    def load_last_kierowca(self):
        if not self.selected_klient_id:
            return
        historia = db.get_historia(self.selected_klient_id, 1)
        if historia and historia[0]['kierowca']:
            self.kierowca_entry.delete(0, "end")
            self.kierowca_entry.insert(0, historia[0]['kierowca'])
    
    def update_saldo(self):
        if not self.selected_klient_id:
            self.palety_saldo.config(text="Palety: 0")
            self.pojemniki_saldo.config(text="Pojemniki: 0")
            return
        saldo = db.get_saldo(self.selected_klient_id)
        self.palety_saldo.config(text=f"Palety: {saldo['palety']}")
        self.pojemniki_saldo.config(text=f"Pojemniki: {saldo['pojemniki']}")
    
    def add_klient_window(self):
        add_win = tk.Toplevel(self)
        add_win.title("Dodaj klienta")
        add_win.geometry("400x200")
        add_win.resizable(False, False)
        
        tk.Label(add_win, text="Nazwa klienta:", font=("Arial", 12, "bold")).pack(pady=(10, 5), padx=20)
        nazwa_entry = tk.Entry(add_win, font=("Arial", 12), width=40)
        nazwa_entry.pack(pady=5, padx=20)
        
        tk.Label(add_win, text="NIP (opcjonalnie):", font=("Arial", 12, "bold")).pack(pady=(10, 5), padx=20)
        nip_entry = tk.Entry(add_win, font=("Arial", 12), width=40)
        nip_entry.pack(pady=5, padx=20)
        
        def save_klient():
            nazwa = nazwa_entry.get().strip()
            nip = nip_entry.get().strip()
            if not nazwa:
                messagebox.showerror("Błąd", "Wpisz nazwę!")
                return
            result = db.add_klient(nazwa, nip if nip else "")
            if result["status"]:
                messagebox.showinfo("Sukces", f"Klient '{nazwa}' dodany!")
                self.refresh_klienci()
                self.search_entry.delete(0, "end")
                self.on_search(None)
                add_win.destroy()
            else:
                if result["error"] == "nazwa_exists":
                    messagebox.showerror("Błąd", "Klient o tej nazwie już istnieje!")
                elif result["error"] == "nip_exists":
                    messagebox.showerror("Błąd", "Klient o tym NIP już istnieje!")
        
        tk.Button(add_win, text="Dodaj", command=save_klient, font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", padx=30, pady=8).pack(pady=15)
    
    def show_historia_window(self):
        if not self.selected_klient_id:
            messagebox.showerror("Błąd", "Wybierz klienta!")
            return
        
        klient_name = self.selected_label.cget("text")
        historia_win = tk.Toplevel(self)
        historia_win.title(f"Historia - {klient_name}")
        historia_win.geometry("1400x700")
        
        title_frame = tk.Frame(historia_win, bg="#FF6B6B")
        title_frame.pack(fill="x")
        tk.Label(title_frame, text=f"Historia: {klient_name}", font=("Arial", 14, "bold"), bg="#FF6B6B", fg="white").pack(pady=10)
        
        columns = ("Data", "Typ", "Palety", "Pojemniki", "Saldo.P", "Saldo.Po", "Kierowca")
        tree = ttk.Treeview(historia_win, columns=columns, height=20, show="headings")
        
        widths = [150, 80, 80, 100, 80, 100, 100]
        for col, width in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width)
        
        historia = db.get_historia(self.selected_klient_id, 100)
        for trans in historia:
            data = trans['data'].split('.')[0] if '.' in trans['data'] else trans['data']
            tree.insert("", "end", values=(
                data, 
                trans['typ'], 
                trans['palety'],
                trans['pojemniki'],
                trans['saldo_po_palety'],
                trans['saldo_po_pojemniki'],
                trans['kierowca'] or "-"
            ))
        
        tree.pack(fill="both", expand=True, padx=10, pady=10)
    
    def show_rozbieznosci_window(self):
        rozbieznosci = db.get_rozbieznosci_pracownika(self.user['id'])
        
        if not rozbieznosci:
            messagebox.showinfo("OK", "Nie masz rozbieżności!")
            return
        
        rozb_win = tk.Toplevel(self)
        rozb_win.title("Moje rozbieżności")
        rozb_win.geometry("900x600")
        
        title_frame = tk.Frame(rozb_win, bg="#FF6B6B")
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="MOJE ROZBIEŻNOŚCI", font=("Arial", 14, "bold"), bg="#FF6B6B", fg="white").pack(pady=10)
        
        tree_frame = tk.Frame(rozb_win, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("Data", "Różnica", "Status", "Moja notatka", "Notatka kierownika")
        tree = ttk.Treeview(tree_frame, columns=columns, height=15, show="headings")
        
        widths = [120, 80, 100, 200, 300]
        for col, width in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width)
        
        for r in rozbieznosci:
            data = r['data_rozpoczecia'].split('.')[0] if '.' in r['data_rozpoczecia'] else r['data_rozpoczecia']
            tree.insert("", "end", values=(
                data,
                f"{r['roznica']:+d}",
                r['status'].upper(),
                r['notatka_pracownika'] or "-",
                r['notatka_kierownika'] or "-"
            ), iid=r['id'])
        
        tree.pack(fill="both", expand=True)
        
        action_frame = tk.Frame(rozb_win, bg="white")
        action_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(action_frame, text="Dodaj wyjaśnienie do rozbieżności:", font=("Arial", 11, "bold"), bg="white").pack()
        
        notatka_entry = tk.Entry(action_frame, font=("Arial", 11), width=80)
        notatka_entry.pack(fill="x", pady=5)
        
        def zapisz_notatka():
            selection = tree.selection()
            if not selection:
                messagebox.showerror("Błąd", "Wybierz rozbieżność!")
                return
            
            rozbieznosc_id = int(selection[0])
            notatka = notatka_entry.get().strip()
            
            if not notatka:
                messagebox.showerror("Błąd", "Wpisz wyjaśnienie!")
                return
            
            db.add_notatka_pracownika(rozbieznosc_id, notatka)
            messagebox.showinfo("OK", "Notatka dodana! Czekaj na zatwierdzenie kierownika.")
            rozb_win.destroy()
        
        tk.Button(action_frame, text="💾 Zapisz wyjaśnienie", command=zapisz_notatka, font=("Arial", 11, "bold"), bg="#4CAF50", fg="white", padx=20, pady=8).pack(pady=5)
    
    def rozlicz(self):
        if not self.selected_klient_id:
            messagebox.showerror("Błąd", "Wybierz klienta!")
            return
        
        try:
            przyjete_p = int(self.przyjete_p.get() or 0)
            przyjete_po = int(self.przyjete_po.get() or 0)
            wydane_p = int(self.wydane_p.get() or 0)
            wydane_po = int(self.wydane_po.get() or 0)
        except:
            messagebox.showerror("Błąd", "Wpisz prawidłowe liczby!")
            return
        
        if przyjete_p == 0 and przyjete_po == 0 and wydane_p == 0 and wydane_po == 0:
            messagebox.showerror("Błąd", "Wpisz co najmniej jedną wartość!")
            return
        
        kierowca = self.kierowca_entry.get().strip()
        
        druk_win = tk.Toplevel(self)
        druk_win.title("Druk paragonu?")
        druk_win.geometry("450x500")
        druk_win.resizable(False, False)
        druk_win.grab_set()
        
        tk.Label(druk_win, text="Czy chcesz wydrukować paragon?", font=("Arial", 12, "bold"), bg="white").pack(pady=20)
        
        info_frame = tk.Frame(druk_win, bg="#F5F5F5")
        info_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(info_frame, text=f"Przyjęte palety: {przyjete_p}", font=("Arial", 11), bg="#F5F5F5").pack(anchor="w", pady=5)
        tk.Label(info_frame, text=f"Przyjęte pojemniki: {przyjete_po}", font=("Arial", 11), bg="#F5F5F5").pack(anchor="w", pady=5)
        tk.Label(info_frame, text=f"Wydane palety: {wydane_p}", font=("Arial", 11), bg="#F5F5F5").pack(anchor="w", pady=5)
        tk.Label(info_frame, text=f"Wydane pojemniki: {wydane_po}", font=("Arial", 11), bg="#F5F5F5").pack(anchor="w", pady=5)
        
        netto_p = przyjete_p - wydane_p
        netto_po = przyjete_po - wydane_po
        tk.Label(info_frame, text=f"\nNetto palety: {netto_p}", font=("Arial", 11, "bold"), fg="#1976D2", bg="#F5F5F5").pack(anchor="w", pady=5)
        tk.Label(info_frame, text=f"Netto pojemniki: {netto_po}", font=("Arial", 11, "bold"), fg="#1976D2", bg="#F5F5F5").pack(anchor="w", pady=5)
        
        def rozlicz_i_drukuj():
            if przyjete_p > 0 or przyjete_po > 0:
                db.update_saldo(self.selected_klient_id, przyjete_p, przyjete_po, kierowca, "PRZYJECIE", self.user['id'])
            
            if wydane_p > 0 or wydane_po > 0:
                db.update_saldo(self.selected_klient_id, -wydane_p, -wydane_po, kierowca, "WYDANIE", self.user['id'])
            
            self.drukuj_paragon_z_danymi(przyjete_p, przyjete_po, wydane_p, wydane_po, kierowca)
            
            messagebox.showinfo("✅ Sukces", "Rozliczenie i druk wykonane!")
            self.clear_inputs()
            self.update_saldo()
            self.update_magazyn_display()
            druk_win.destroy()
        
        def rozlicz_bez_druku():
            if przyjete_p > 0 or przyjete_po > 0:
                db.update_saldo(self.selected_klient_id, przyjete_p, przyjete_po, kierowca, "PRZYJECIE", self.user['id'])
            
            if wydane_p > 0 or wydane_po > 0:
                db.update_saldo(self.selected_klient_id, -wydane_p, -wydane_po, kierowca, "WYDANIE", self.user['id'])
            
            self.zapisz_paragon_bez_druku(przyjete_p, przyjete_po, wydane_p, wydane_po, kierowca)
            
            messagebox.showinfo("✅ Sukces", "Rozliczenie zapisane (bez druku)!")
            self.clear_inputs()
            self.update_saldo()
            self.update_magazyn_display()
            druk_win.destroy()
        
        btn_frame = tk.Frame(druk_win, bg="white")
        btn_frame.pack(fill="both", padx=20, pady=20)
        
        tk.Button(btn_frame, text="✅ TAK - Drukuj", command=rozlicz_i_drukuj, font=("Arial", 11, "bold"), bg="#4CAF50", fg="white", padx=20, pady=8).pack(fill="x", pady=3)
        tk.Button(btn_frame, text="❌ NIE - Bez druku", command=rozlicz_bez_druku, font=("Arial", 11, "bold"), bg="#FF9800", fg="white", padx=20, pady=8).pack(fill="x", pady=3)
        tk.Button(btn_frame, text="✏️ POPRAW", command=lambda: druk_win.destroy(), font=("Arial", 11, "bold"), bg="#2196F3", fg="white", padx=20, pady=8).pack(fill="x", pady=3)
        tk.Button(btn_frame, text="❌ ZAMKNIJ", command=lambda: druk_win.destroy(), font=("Arial", 11, "bold"), bg="#9E9E9E", fg="white", padx=20, pady=8).pack(fill="x", pady=3)
    
    def drukuj_paragon_z_danymi(self, przyjete_p, przyjete_po, wydane_p, wydane_po, kierowca):
        klient_name = self.selected_label.cget("text")
        pracownik = self.user['nazwa']
        
        os.makedirs("archiwum", exist_ok=True)
        plik = f"archiwum/paragon_{klient_name.replace(' ', '_').replace('(', '').replace(')', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        netto_palety = przyjete_p - wydane_p
        netto_pojemniki = przyjete_po - wydane_po
        
        paragon = f"""
H1 PALETY - PARAGON
Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Klient: {klient_name}
Kierowca: {kierowca or 'Brak'}
Pracownik: {pracownik}

PRZYJĘTE
Palety: {przyjete_p}
Pojemniki: {przyjete_po}

WYDANE
Palety: {wydane_p}
Pojemniki: {wydane_po}

NETTO
Palety: {netto_palety:+d}
Pojemniki: {netto_pojemniki:+d}

Podpis: ________________

"""
        
        zawartosc = paragon + "\n\n" + paragon
        
        try:
            with open(plik, 'w', encoding='utf-8') as f:
                f.write(zawartosc)
            
            try:
                subprocess.Popen(f'notepad /p "{plik}"', shell=True)
            except:
                pass
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać: {str(e)}")
    
    def zapisz_paragon_bez_druku(self, przyjete_p, przyjete_po, wydane_p, wydane_po, kierowca):
        klient_name = self.selected_label.cget("text")
        pracownik = self.user['nazwa']
        
        os.makedirs("archiwum", exist_ok=True)
        plik = f"archiwum/paragon_{klient_name.replace(' ', '_').replace('(', '').replace(')', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        netto_palety = przyjete_p - wydane_p
        netto_pojemniki = przyjete_po - wydane_po
        
        paragon = f"""
H1 PALETY - PARAGON
Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Klient: {klient_name}
Kierowca: {kierowca or 'Brak'}
Pracownik: {pracownik}

PRZYJĘTE
Palety: {przyjete_p}
Pojemniki: {przyjete_po}

WYDANE
Palety: {wydane_p}
Pojemniki: {wydane_po}

NETTO
Palety: {netto_palety:+d}
Pojemniki: {netto_pojemniki:+d}

Podpis: ________________

"""
        
        zawartosc = paragon + "\n\n" + paragon
        
        try:
            with open(plik, 'w', encoding='utf-8') as f:
                f.write(zawartosc)
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać: {str(e)}")
    
    def clear_inputs(self):
        self.przyjete_p.delete(0, "end")
        self.przyjete_p.insert(0, "0")
        self.przyjete_po.delete(0, "end")
        self.przyjete_po.insert(0, "0")
        self.wydane_p.delete(0, "end")
        self.wydane_p.insert(0, "0")
        self.wydane_po.delete(0, "end")
        self.wydane_po.insert(0, "0")
    
    def zamknij_zmiane(self):
        zamknij_win = tk.Toplevel(self)
        zamknij_win.title("Zamknięcie zmiany")
        zamknij_win.geometry("500x400")
        zamknij_win.grab_set()
        
        tk.Label(zamknij_win, text="ZAMKNIĘCIE ZMIANY", font=("Arial", 14, "bold"), bg="white").pack(pady=20)
        
        frame = tk.Frame(zamknij_win, bg="white")
        frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(frame, text="Ile palet masz faktycznie?", font=("Arial", 12, "bold"), bg="white").pack(pady=10)
        
        entry = tk.Entry(frame, font=("Arial", 16), width=10)
        entry.pack(pady=10)
        entry.focus()
        
        def zapisz_i_wyloguj():
            try:
                stan_faktyczny = int(entry.get())
                
                wynik = db.end_zmiana(self.zmiana_id, stan_faktyczny)
                
                if wynik['ma_rozbieznosc']:
                    messagebox.showwarning(
                        "Rozbieżność",
                        f"Rozbieżność: {wynik['roznica']:+d} palet\nMasz 3 dni na wyjaśnienie!"
                    )
                else:
                    messagebox.showinfo("✅ OK", "Zmiana zamknięta bez rozbieżności!")
                
                pin_win = tk.Toplevel(zamknij_win)
                pin_win.title("Potwierdzenie PIN")
                pin_win.geometry("400x300")
                pin_win.grab_set()
                
                tk.Label(pin_win, text="Wpisz swój PIN do wylogowania", font=("Arial", 12, "bold")).pack(pady=20)
                
                pin_entry = tk.Entry(pin_win, show="*", font=("Arial", 14), width=15)
                pin_entry.pack(pady=10)
                pin_entry.focus()
                
                def potwierdz_wyloguj():
                    if pin_entry.get() == self.user['pin']:
                        zamknij_win.destroy()
                        pin_win.destroy()
                        self.logout()
                    else:
                        messagebox.showerror("Błąd", "Zły PIN!")
                
                tk.Button(pin_win, text="Wyloguj", command=potwierdz_wyloguj, font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", padx=30, pady=10).pack(pady=20)
                
            except:
                messagebox.showerror("Błąd", "Wpisz liczbę!")
        
        tk.Button(frame, text="Zamknij zmianę", command=zapisz_i_wyloguj, font=("Arial", 12, "bold"), bg="#D32F2F", fg="white", padx=20, pady=12).pack(pady=20)
    
    def logout(self):
        self.destroy()
        app = LoginWindow()
        app.mainloop()

# ===== DASHBOARD KIEROWNIKA =====
class DashboardKierownika(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.title(f"H1 Palety - Dashboard kierownika - {user['nazwa']}")
        self.geometry("1400x900")
        
        header = tk.Frame(self, bg="#2196F3", height=60)
        header.pack(fill="x")
        
        tk.Label(header, text=f"DASHBOARD KIEROWNIKA - {user['nazwa']}", font=("Arial", 16, "bold"), bg="#2196F3", fg="white").pack(pady=15)
        
        main_frame = tk.Frame(self, bg="white")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True)
        
        tab_rozbieznosci = tk.Frame(notebook, bg="white")
        notebook.add(tab_rozbieznosci, text="Rozbieżności")
        self.refresh_rozbieznosci(tab_rozbieznosci)
        
        tab_status = tk.Frame(notebook, bg="white")
        notebook.add(tab_status, text="Status pracowników")
        self.show_status_pracownikow(tab_status)
        
        logout_btn = tk.Button(self, text="Wyloguj", command=self.logout, bg="#757575", fg="white", font=("Arial", 11, "bold"), padx=20, pady=10)
        logout_btn.pack(pady=10, padx=20, fill="x")
    
    def refresh_rozbieznosci(self, parent):
        for widget in parent.winfo_children():
            widget.destroy()
        
        tk.Label(parent, text="WSZYSTKIE ROZBIEŻNOŚCI", font=("Arial", 13, "bold"), bg="white").pack(fill="x", padx=10, pady=10)
        
        tree_frame = tk.Frame(parent, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("Pracownik", "Data", "Stan przejęty", "Stan faktyczny", "Różnica", "Status", "Moja notatka", "Notatka KW")
        tree = ttk.Treeview(tree_frame, columns=columns, height=20, show="headings")
        
        widths = [120, 120, 100, 100, 80, 100, 200, 200]
        for col, width in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width)
        
        rozbieznosci = db.get_all_rozbieznosci()
        for r in rozbieznosci:
            data = r['data_rozpoczecia'].split('.')[0] if '.' in r['data_rozpoczecia'] else r['data_rozpoczecia']
            tree.insert("", "end", values=(
                r['pracownik_nazwa'],
                data,
                r['stan_przejety'],
                r['stan_faktyczny'],
                f"{r['roznica']:+d}",
                r['status'].upper(),
                r['notatka_pracownika'] or "-",
                r['notatka_kierownika'] or "-"
            ), iid=r['id'])
        
        tree.pack(fill="both", expand=True)
        
        action_frame = tk.Frame(parent, bg="white")
        action_frame.pack(fill="x", padx=10, pady=10)
        
        def zatwierdz():
            selection = tree.selection()
            if not selection:
                messagebox.showerror("Błąd", "Wybierz rozbieżność!")
                return
            
            rozbieznosc_id = int(selection[0])
            
            zatw_win = tk.Toplevel(parent)
            zatw_win.title("Zatwierdzenie rozbieżności")
            zatw_win.geometry("500x400")
            zatw_win.grab_set()
            
            tk.Label(zatw_win, text="Notatka kierownika:", font=("Arial", 11, "bold")).pack(pady=10)
            notatka = tk.Entry(zatw_win, font=("Arial", 11), width=50)
            notatka.pack(fill="x", padx=10, pady=5)
            
            tk.Label(zatw_win, text="Nowa różnica (opcjonalnie):", font=("Arial", 11, "bold")).pack(pady=10)
            nowa_roznica = tk.Entry(zatw_win, font=("Arial", 11), width=10)
            nowa_roznica.pack(pady=5)
            
            def zapisz_zatw():
                try:
                    nr = int(nowa_roznica.get()) if nowa_roznica.get() else None
                    db.zatwierdzenie_rozbieznosci(rozbieznosc_id, self.user['id'], notatka.get(), nr)
                    messagebox.showinfo("OK", "Rozbieżność zatwierdzona!")
                    zatw_win.destroy()
                    self.refresh_rozbieznosci(parent)
                except:
                    messagebox.showerror("Błąd", "Sprawdź dane!")
            
            tk.Button(zatw_win, text="Zatwierdź", command=zapisz_zatw, font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", padx=20, pady=10).pack(pady=20)
        
        tk.Button(action_frame, text="✅ Zatwierdź rozbieżność", command=zatwierdz, font=("Arial", 11, "bold"), bg="#4CAF50", fg="white", padx=20, pady=8).pack(side="left", padx=5)
    
    def show_status_pracownikow(self, parent):
        tk.Label(parent, text="STATUS PRACOWNIKÓW", font=("Arial", 13, "bold"), bg="white").pack(fill="x", padx=10, pady=10)
        
        tree_frame = tk.Frame(parent, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("Pracownik", "Status", "Rozbieżności")
        tree = ttk.Treeview(tree_frame, columns=columns, height=20, show="headings")
        
        widths = [200, 150, 150]
        for col, width in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width)
        
        pracownicy = db.get_all_pracownicy()
        for p in pracownicy:
            if p['rola'] == 'pracownik':
                aktywna = db.get_aktywna_zmiana(p['id'])
                rozbieznosci = db.get_rozbieznosci_pracownika(p['id'])
                otwarte = len([r for r in rozbieznosci if r['status'] == 'czeka'])
                
                status = "Online" if aktywna else "Offline"
                tree.insert("", "end", values=(p['nazwa'], status, f"{otwarte} do wyjaśnienia"))
        
        tree.pack(fill="both", expand=True)
    
    def logout(self):
        self.destroy()
        app = LoginWindow()
        app.mainloop()

# ===== PANEL ADMINA =====
class PanelAdmina(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.title(f"H1 Palety - Panel Admina - {user['nazwa']}")
        self.geometry("1400x900")
        
        header = tk.Frame(self, bg="#D32F2F", height=60)
        header.pack(fill="x")
        
        tk.Label(header, text=f"PANEL ADMINISTRACYJNY - {user['nazwa']}", font=("Arial", 16, "bold"), bg="#D32F2F", fg="white").pack(pady=15)
        
        main_frame = tk.Frame(self, bg="white")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True)
        
        tab_pracownicy = tk.Frame(notebook, bg="white")
        notebook.add(tab_pracownicy, text="Pracownicy")
        self.show_pracownicy_admin(tab_pracownicy)
        
        tab_rozbieznosci = tk.Frame(notebook, bg="white")
        notebook.add(tab_rozbieznosci, text="Rozbieżności")
        self.show_rozbieznosci_admin(tab_rozbieznosci)
        
        tab_klienci = tk.Frame(notebook, bg="white")
        notebook.add(tab_klienci, text="Klienci")
        self.show_klienci_admin(tab_klienci)
        
        tab_magazyn = tk.Frame(notebook, bg="white")
        notebook.add(tab_magazyn, text="Stan magazynu")
        self.show_magazyn_admin(tab_magazyn)
        
        logout_btn = tk.Button(self, text="Wyloguj", command=self.logout, bg="#757575", fg="white", font=("Arial", 11, "bold"), padx=20, pady=10)
        logout_btn.pack(pady=10, padx=20, fill="x")
    
    def show_pracownicy_admin(self, parent):
        tk.Label(parent, text="PRACOWNICY", font=("Arial", 13, "bold"), bg="white").pack(fill="x", padx=10, pady=10)
        
        btn_frame = tk.Frame(parent, bg="white")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        def add_pracownik_win():
            add_win = tk.Toplevel(parent)
            add_win.title("Dodaj pracownika")
            add_win.geometry("400x350")
            add_win.grab_set()
            
            tk.Label(add_win, text="Nazwa:", font=("Arial", 11, "bold")).pack(pady=5)
            nazwa = tk.Entry(add_win, font=("Arial", 11), width=40)
            nazwa.pack(pady=5)
            
            tk.Label(add_win, text="PIN:", font=("Arial", 11, "bold")).pack(pady=5)
            pin = tk.Entry(add_win, show="*", font=("Arial", 11), width=40)
            pin.pack(pady=5)
            
            tk.Label(add_win, text="Rola:", font=("Arial", 11, "bold")).pack(pady=5)
            rola = ttk.Combobox(add_win, values=["pracownik", "kierownik", "magazynier", "admin"], font=("Arial", 11), width=37, state="readonly")
            rola.pack(pady=5)
            rola.set("pracownik")
            
            def save():
                if db.add_pracownik(nazwa.get(), pin.get(), rola.get()):
                    messagebox.showinfo("OK", "Pracownik dodany!")
                    add_win.destroy()
                    self.show_pracownicy_admin(parent)
                else:
                    messagebox.showerror("Błąd", "PIN już istnieje!")
            
            tk.Button(add_win, text="Dodaj", command=save, font=("Arial", 11, "bold"), bg="#4CAF50", fg="white", padx=30, pady=10).pack(pady=20)
        
        tk.Button(btn_frame, text="➕ Dodaj pracownika", command=add_pracownik_win, font=("Arial", 11, "bold"), bg="#4CAF50", fg="white", padx=20, pady=8).pack(side="left", padx=5)
        
        def delete_pracownik_fn():
            selection = tree.selection()
            if not selection:
                messagebox.showerror("Błąd", "Wybierz pracownika!")
                return
            
            pracownik_id = int(selection[0])
            if messagebox.askyesno("Potwierdzenie", "Na pewno usunąć tego pracownika?"):
                if db.delete_pracownik(pracownik_id):
                    messagebox.showinfo("OK", "Pracownik usunięty!")
                    self.show_pracownicy_admin(parent)
                else:
                    messagebox.showerror("Błąd", "Nie udało się usunąć!")
        
        tk.Button(btn_frame, text="❌ Usuń pracownika", command=delete_pracownik_fn, font=("Arial", 11, "bold"), bg="#D32F2F", fg="white", padx=20, pady=8).pack(side="left", padx=5)
        
        tree_frame = tk.Frame(parent, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("ID", "Nazwa", "Rola")
        tree = ttk.Treeview(tree_frame, columns=columns, height=20, show="headings")
        
        widths = [50, 200, 150]
        for col, width in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width)
        
        pracownicy = db.get_all_pracownicy()
        for p in pracownicy:
            tree.insert("", "end", values=(p['id'], p['nazwa'], p['rola']), iid=p['id'])
        
        tree.pack(fill="both", expand=True)
    
    def show_rozbieznosci_admin(self, parent):
        tk.Label(parent, text="ROZBIEŻNOŚCI", font=("Arial", 13, "bold"), bg="white").pack(fill="x", padx=10, pady=10)
        
        tree_frame = tk.Frame(parent, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("Pracownik", "Data", "Różnica", "Status")
        tree = ttk.Treeview(tree_frame, columns=columns, height=20, show="headings")
        
        widths = [200, 150, 100, 150]
        for col, width in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width)
        
        rozbieznosci = db.get_all_rozbieznosci()
        for r in rozbieznosci:
            data = r['data_rozpoczecia'].split('.')[0] if '.' in r['data_rozpoczecia'] else r['data_rozpoczecia']
            tree.insert("", "end", values=(r['pracownik_nazwa'], data, f"{r['roznica']:+d}", r['status'].upper()))
        
        tree.pack(fill="both", expand=True)
    
    def show_klienci_admin(self, parent):
        tk.Label(parent, text="KLIENCI", font=("Arial", 13, "bold"), bg="white").pack(fill="x", padx=10, pady=10)
        
        tree_frame = tk.Frame(parent, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("ID", "Nazwa", "NIP")
        tree = ttk.Treeview(tree_frame, columns=columns, height=20, show="headings")
        
        widths = [50, 300, 200]
        for col, width in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width)
        
        klienci = db.get_all_klienci()
        for k in klienci:
            tree.insert("", "end", values=(k['id'], k['nazwa'], k['nip'] or "-"))
        
        tree.pack(fill="both", expand=True)
    
    def show_magazyn_admin(self, parent):
        tk.Label(parent, text="STAN MAGAZYNU", font=("Arial", 13, "bold"), bg="white").pack(fill="x", padx=10, pady=10)
        
        mag = db.get_magazyn()
        
        info_frame = tk.Frame(parent, bg="#E3F2FD", relief="solid", borderwidth=2)
        info_frame.pack(fill="x", padx=20, pady=20)
        
        tk.Label(info_frame, text=f"Palety w magazynie: {mag['palety']}", font=("Arial", 18, "bold"), bg="#E3F2FD", fg="#1976D2").pack(pady=20)
    
    def logout(self):
        self.destroy()
        app = LoginWindow()
        app.mainloop()

# ===== PANEL MAGAZYNIERA =====
class PanelMagazyniera(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.title(f"H1 Palety - Panel magazyniera - {user['nazwa']}")
        self.geometry("1000x700")
        
        header = tk.Frame(self, bg="#FF9800", height=60)
        header.pack(fill="x")
        
        tk.Label(header, text=f"PANEL MAGAZYNIERA - {user['nazwa']}", font=("Arial", 16, "bold"), bg="#FF9800", fg="white").pack(pady=15)
        
        main_frame = tk.Frame(self, bg="white")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        tk.Label(main_frame, text="OPERACJE MAGAZYNU", font=("Arial", 13, "bold"), bg="white").pack(fill="x", pady=10)
        
        op_frame = tk.Frame(main_frame, bg="#F5F5F5", relief="solid", borderwidth=2)
        op_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(op_frame, text="Typ operacji:", font=("Arial", 11, "bold"), bg="#F5F5F5").pack(side="left", padx=10, pady=10)
        typ = ttk.Combobox(op_frame, values=["przyjecie", "wydanie"], font=("Arial", 11), width=15, state="readonly")
        typ.pack(side="left", padx=5, pady=10)
        typ.set("przyjecie")
        
        tk.Label(op_frame, text="Ilość palet:", font=("Arial", 11, "bold"), bg="#F5F5F5").pack(side="left", padx=10, pady=10)
        ilosc = tk.Entry(op_frame, font=("Arial", 11), width=10)
        ilosc.pack(side="left", padx=5, pady=10)
        
        tk.Label(op_frame, text="Notatka:", font=("Arial", 11, "bold"), bg="#F5F5F5").pack(side="left", padx=10, pady=10)
        notatka = tk.Entry(op_frame, font=("Arial", 11), width=30)
        notatka.pack(side="left", padx=5, pady=10)
        
        def zapisz_operacja():
            try:
                i = int(ilosc.get())
                db.add_magazyn_operacja(self.user['id'], typ.get(), i, notatka.get())
                messagebox.showinfo("OK", "Operacja zapisana!")
                ilosc.delete(0, "end")
                notatka.delete(0, "end")
                refresh_operacje()
            except:
                messagebox.showerror("Błąd", "Sprawdź dane!")
        
        tk.Button(op_frame, text="💾 Zapisz", command=zapisz_operacja, font=("Arial", 11, "bold"), bg="#4CAF50", fg="white", padx=20, pady=8).pack(side="left", padx=5, pady=10)
        
        tk.Label(main_frame, text="HISTORIA OPERACJI", font=("Arial", 13, "bold"), bg="white").pack(fill="x", pady=10)
        
        tree_frame = tk.Frame(main_frame, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ("Data", "Typ", "Ilość", "Magazynier", "Notatka")
        tree = ttk.Treeview(tree_frame, columns=columns, height=20, show="headings")
        
        widths = [150, 100, 80, 150, 300]
        for col, width in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width)
        
        def refresh_operacje():
            for item in tree.get_children():
                tree.delete(item)
            
            operacje = db.get_magazyn_operacje()
            for op in operacje:
                data = op['data'].split('.')[0] if '.' in op['data'] else op['data']
                tree.insert("", "end", values=(data, op['typ'].upper(), op['ilosc'], op['magazynier_nazwa'], op['notatka'] or "-"))
        
        refresh_operacje()
        tree.pack(fill="both", expand=True)
        
        logout_btn = tk.Button(self, text="Wyloguj", command=self.logout, bg="#757575", fg="white", font=("Arial", 11, "bold"), padx=20, pady=10)
        logout_btn.pack(pady=10, padx=20, fill="x")
    
    def logout(self):
        self.destroy()
        app = LoginWindow()
        app.mainloop()

def run_ui():
    app = LoginWindow()
    app.mainloop()
