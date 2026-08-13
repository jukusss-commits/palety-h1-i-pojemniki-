import tkinter as tk
from tkinter import messagebox, ttk
from config import WINDOW_WIDTH, WINDOW_HEIGHT
from database import db
from datetime import datetime

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

    def login(self):
        pin = self.pin_entry.get()
        if not pin:
            messagebox.showerror("Blad", "Wpisz PIN!")
            return
        pracownik = db.get_pracownik_by_pin(pin)
        if pracownik:
            self.destroy()
            app = MainWindow(pracownik)
            app.mainloop()
        else:
            messagebox.showerror("Blad", "Niepoprawny PIN!")
            self.pin_entry.delete(0, "end")

class MainWindow(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.title(f"H1 Palety - {user['nazwa']}")
        self.geometry("1200x900")
        
        header = tk.Frame(self, bg="#FF6B6B", height=80)
        header.pack(fill="x")
        
        header_label = tk.Label(
            header, 
            text=f"H1 PALETY - {user['nazwa']} ({user['rola']})", 
            font=("Arial", 20, "bold"),
            bg="#FF6B6B",
            fg="white"
        )
        header_label.pack(pady=20)
        
        main_frame = tk.Frame(self, bg="white")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        top_btn_frame = tk.Frame(main_frame, bg="white")
        top_btn_frame.pack(fill="x", pady=10)
        
        btn_add_klient = tk.Button(top_btn_frame, text="+ Dodaj klienta", command=self.add_klient_window, font=("Arial", 11), bg="#FF9800", fg="white")
        btn_add_klient.pack(side="left", padx=5)
        
        magazyn_frame = tk.Frame(main_frame, bg="#FFE082", relief="solid", borderwidth=2)
        magazyn_frame.pack(fill="x", pady=10)
        
        magazyn_title = tk.Label(magazyn_frame, text="MAGAZYN", font=("Arial", 12, "bold"), bg="#FFE082")
        magazyn_title.pack()
        
        magazyn_inner = tk.Frame(magazyn_frame, bg="#FFE082")
        magazyn_inner.pack(fill="x", padx=20, pady=10)
        
        self.mag_palety_label = tk.Label(magazyn_inner, text="PALETY: 0", font=("Arial", 14, "bold"), bg="#FFE082")
        self.mag_palety_label.pack(side="left", padx=20)
        
        search_frame = tk.Frame(main_frame, bg="white")
        search_frame.pack(fill="x", pady=10)
        
        search_label = tk.Label(search_frame, text="Szukaj (nazwa/NIP):", font=("Arial", 12, "bold"), bg="white")
        search_label.pack(side="left", padx=5)
        
        self.search_entry = tk.Entry(search_frame, font=("Arial", 12), width=20)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind('<KeyRelease>', self.on_search)
        
        top_frame = tk.Frame(main_frame, bg="white")
        top_frame.pack(fill="x", pady=10)
        
        klient_label = tk.Label(top_frame, text="Klient:", font=("Arial", 12, "bold"), bg="white")
        klient_label.pack(side="left", padx=5)
        
        self.klient_var = tk.StringVar(value="")
        self.refresh_klienci()
        
        self.klient_combo = ttk.Combobox(top_frame, textvariable=self.klient_var, values=sorted(self.klient_display.keys()), font=("Arial", 12), state="readonly", width=40)
        self.klient_combo.pack(side="left", padx=5, fill="x", expand=True)
        self.klient_combo.bind('<<ComboboxSelected>>', lambda e: self.on_klient_change(self.klient_var.get()))
        
        btn_historia = tk.Button(top_frame, text="Historia", command=self.show_historia_window, font=("Arial", 11), bg="#2196F3", fg="white")
        btn_historia.pack(side="left", padx=5)
        
        kierowca_label = tk.Label(top_frame, text="Kierowca:", font=("Arial", 12, "bold"), bg="white")
        kierowca_label.pack(side="left", padx=5)
        self.kierowca_input = tk.Entry(top_frame, font=("Arial", 12), width=15)
        self.kierowca_input.pack(side="left", padx=5)
        
        saldo_frame = tk.Frame(main_frame, bg="#F0F0F0", relief="solid", borderwidth=2)
        saldo_frame.pack(fill="x", pady=10)
        
        saldo_title = tk.Label(saldo_frame, text="SALDO KLIENTA", font=("Arial", 14, "bold"), bg="#F0F0F0")
        saldo_title.pack()
        
        saldo_inner = tk.Frame(saldo_frame, bg="#F0F0F0")
        saldo_inner.pack(fill="x", padx=20, pady=10)
        
        self.palety_label = tk.Label(saldo_inner, text="PALETY: 0", font=("Arial", 16, "bold"), bg="#F0F0F0", fg="#4CAF50")
        self.palety_label.pack(side="left", padx=20)
        
        self.pojemniki_label = tk.Label(saldo_inner, text="POJEMNIKI: 0", font=("Arial", 16, "bold"), bg="#F0F0F0", fg="#2196F3")
        self.pojemniki_label.pack(side="left", padx=20)
        
        input_frame = tk.Frame(main_frame, bg="white")
        input_frame.pack(fill="x", pady=10)
        
        przyjete_frame = tk.LabelFrame(input_frame, text="PRZYJETE", font=("Arial", 12, "bold"), bg="white", fg="#4CAF50")
        przyjete_frame.pack(side="left", padx=10, fill="both", expand=True)
        
        tk.Label(przyjete_frame, text="Palety:", font=("Arial", 11), bg="white").pack(side="left", padx=5, pady=5)
        self.przyjete_palety = tk.Entry(przyjete_frame, font=("Arial", 12), width=8)
        self.przyjete_palety.pack(side="left", padx=5)
        self.przyjete_palety.insert(0, "0")
        
        tk.Label(przyjete_frame, text="Pojemniki:", font=("Arial", 11), bg="white").pack(side="left", padx=5, pady=5)
        self.przyjete_pojemniki = tk.Entry(przyjete_frame, font=("Arial", 12), width=8)
        self.przyjete_pojemniki.pack(side="left", padx=5)
        self.przyjete_pojemniki.insert(0, "0")
        
        wydane_frame = tk.LabelFrame(input_frame, text="WYDANE", font=("Arial", 12, "bold"), bg="white", fg="#FF9800")
        wydane_frame.pack(side="left", padx=10, fill="both", expand=True)
        
        tk.Label(wydane_frame, text="Palety:", font=("Arial", 11), bg="white").pack(side="left", padx=5, pady=5)
        self.wydane_palety = tk.Entry(wydane_frame, font=("Arial", 12), width=8)
        self.wydane_palety.pack(side="left", padx=5)
        self.wydane_palety.insert(0, "0")
        
        tk.Label(wydane_frame, text="Pojemniki:", font=("Arial", 11), bg="white").pack(side="left", padx=5, pady=5)
        self.wydane_pojemniki = tk.Entry(wydane_frame, font=("Arial", 12), width=8)
        self.wydane_pojemniki.pack(side="left", padx=5)
        self.wydane_pojemniki.insert(0, "0")
        
        btn_frame = tk.Frame(main_frame, bg="white")
        btn_frame.pack(fill="x", pady=15)
        
        btn_rozlicz = tk.Button(
            btn_frame,
            text="ROZLICZ",
            font=("Arial", 16, "bold"),
            bg="#FF6B6B",
            fg="white",
            height=2,
            command=self.rozlicz
        )
        btn_rozlicz.pack(fill="both", expand=True)
        
        historia_label = tk.Label(main_frame, text="OSTATNIE TRANSAKCJE", font=("Arial", 12, "bold"), bg="white")
        historia_label.pack(fill="x", pady=(10, 5))
        
        columns = ("Data", "Typ", "Palety", "Pojemniki", "Kierowca")
        self.tree = ttk.Treeview(main_frame, columns=columns, height=6, show="headings")
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=200)
        
        self.tree.pack(fill="both", expand=True)
        
        logout_btn = tk.Button(self, text="Wyloguj", command=self.logout, bg="#FF6B6B", fg="white", font=("Arial", 12))
        logout_btn.pack(pady=10, padx=20, fill="x")
        
        self.update_magazyn_display()
    
    def refresh_klienci(self):
        self.all_klienci = db.get_all_klienci()
        self.klient_display = {}
        for k in self.all_klienci:
            display_name = f"{k['nazwa']} ({k['nip']})" if k['nip'] else k['nazwa']
            self.klient_display[display_name] = k['id']
    
    def add_klient_window(self):
        add_win = tk.Toplevel(self)
        add_win.title("Dodaj klienta")
        add_win.geometry("400x200")
        
        tk.Label(add_win, text="Nazwa:", font=("Arial", 12)).pack(pady=5)
        nazwa_entry = tk.Entry(add_win, font=("Arial", 12), width=40)
        nazwa_entry.pack(pady=5)
        
        tk.Label(add_win, text="NIP (opcjonalnie):", font=("Arial", 12)).pack(pady=5)
        nip_entry = tk.Entry(add_win, font=("Arial", 12), width=40)
        nip_entry.pack(pady=5)
        
        def save_klient():
            nazwa = nazwa_entry.get().strip()
            nip = nip_entry.get().strip()
            if not nazwa:
                messagebox.showerror("Blad", "Wpisz nazwę!")
                return
            result = db.add_klient(nazwa, nip if nip else "")
            if result["status"]:
                messagebox.showinfo("OK", "Klient dodany!")
                self.refresh_klienci()
                self.klient_combo['values'] = sorted(self.klient_display.keys())
                self.search_entry.delete(0, "end")
                add_win.destroy()
            else:
                if result["error"] == "nazwa_exists":
                    messagebox.showerror("Blad", "Nazwa już istnieje!")
                elif result["error"] == "nip_exists":
                    messagebox.showerror("Blad", "NIP już istnieje!")
                else:
                    messagebox.showerror("Blad", "Błąd przy dodawaniu!")
        
        tk.Button(add_win, text="Dodaj", command=save_klient, font=("Arial", 12), bg="#4CAF50", fg="white").pack(pady=10)
    
    def on_search(self, event):
        search_text = self.search_entry.get().lower().strip()
        
        if not search_text:
            self.klient_combo['values'] = sorted(self.klient_display.keys())
            return
        
        filtered = []
        for display_name in self.klient_display.keys():
            if search_text in display_name.lower():
                filtered.append(display_name)
        
        self.klient_combo['values'] = sorted(filtered)
    
    def update_magazyn_display(self):
        mag = db.get_magazyn()
        self.mag_palety_label.config(text=f"PALETY: {mag['palety']}")
    
    def on_klient_change(self, value):
        self.update_saldo()
        self.refresh_historia()
        self.load_last_kierowca()
    
    def load_last_kierowca(self):
        klient_display = self.klient_var.get()
        if not klient_display or klient_display not in self.klient_display:
            return
        
        klient_id = self.klient_display[klient_display]
        historia = db.get_historia(klient_id, 1)
        
        if historia and historia[0]['kierowca']:
            self.kierowca_input.delete(0, "end")
            self.kierowca_input.insert(0, historia[0]['kierowca'])
    
    def update_saldo(self):
        klient_display = self.klient_var.get()
        if not klient_display or klient_display not in self.klient_display:
            return
        klient_id = self.klient_display[klient_display]
        saldo = db.get_saldo(klient_id)
        self.palety_label.config(text=f"PALETY: {saldo['palety']}")
        self.pojemniki_label.config(text=f"POJEMNIKI: {saldo['pojemniki']}")
    
    def refresh_historia(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        klient_display = self.klient_var.get()
        if not klient_display or klient_display not in self.klient_display:
            return
        
        klient_id = self.klient_display[klient_display]
        historia = db.get_historia(klient_id, 10)
        
        for trans in historia:
            data = trans['data'].split('.')[0] if '.' in trans['data'] else trans['data']
            self.tree.insert("", 0, values=(
                data,
                trans['typ'],
                trans['palety'],
                trans['pojemniki'],
                trans['kierowca'] or "-"
            ))
    
    def show_historia_window(self):
        klient_display = self.klient_var.get()
        if not klient_display or klient_display not in self.klient_display:
            messagebox.showerror("Blad", "Wybierz klienta!")
            return
        
        klient_id = self.klient_display[klient_display]
        historia_win = tk.Toplevel(self)
        historia_win.title(f"Historia - {klient_display}")
        historia_win.geometry("900x600")
        
        title_label = tk.Label(historia_win, text=f"Historia transakcji: {klient_display}", font=("Arial", 14, "bold"))
        title_label.pack(pady=10)
        
        columns = ("Data", "Typ", "Palety", "Pojemniki", "Kierowca")
        tree = ttk.Treeview(historia_win, columns=columns, height=20, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=170)
        
        historia = db.get_historia(klient_id, 100)
        for trans in historia:
            data = trans['data'].split('.')[0] if '.' in trans['data'] else trans['data']
            tree.insert("", "end", values=(
                data,
                trans['typ'],
                trans['palety'],
                trans['pojemniki'],
                trans['kierowca'] or "-"
            ))
        
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        btn_frame = tk.Frame(historia_win)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        btn_druk = tk.Button(btn_frame, text="Drukuj", command=lambda: self.drukuj_historie(klient_display, historia), font=("Arial", 12), bg="#4CAF50", fg="white")
        btn_druk.pack(side="left", padx=5)
        
        btn_close = tk.Button(btn_frame, text="Zamknij", command=historia_win.destroy, font=("Arial", 12))
        btn_close.pack(side="left", padx=5)
    
    def drukuj_historie(self, klient_display, historia):
        klient_id = self.klient_display[klient_display]
        historia = db.get_historia(klient_id, 100)
        
        plik = f"historia_{klient_display.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(plik, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write(f"HISTORIA TRANSAKCJI: {klient_display}\n")
            f.write(f"Data wydruku: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"{'Data':<20} {'Typ':<12} {'Palety':<10} {'Pojemniki':<12} {'Kierowca':<20}\n")
            f.write("-"*70 + "\n")
            
            for trans in historia:
                data = trans['data'].split('.')[0] if '.' in trans['data'] else trans['data']
                kierowca = trans['kierowca'] or "-"
                f.write(f"{data:<20} {trans['typ']:<12} {trans['palety']:<10} {trans['pojemniki']:<12} {kierowca:<20}\n")
            
            f.write("\n" + "="*70 + "\n")
        
        messagebox.showinfo("OK", f"Historia wydrukowana do: {plik}")
    
    def rozlicz(self):
        klient_display = self.klient_var.get()
        if not klient_display or klient_display not in self.klient_display:
            messagebox.showerror("Blad", "Wybierz klienta!")
            return
        
        try:
            przyjete_p = int(self.przyjete_palety.get() or 0)
            przyjete_po = int(self.przyjete_pojemniki.get() or 0)
            wydane_p = int(self.wydane_palety.get() or 0)
            wydane_po = int(self.wydane_pojemniki.get() or 0)
        except:
            messagebox.showerror("Blad", "Wpisz liczby!")
            return
        
        if przyjete_p == 0 and przyjete_po == 0 and wydane_p == 0 and wydane_po == 0:
            messagebox.showerror("Blad", "Wpisz co najmniej cos!")
            return
        
        kierowca = self.kierowca_input.get()
        klient_id = self.klient_display[klient_display]
        
        if przyjete_p > 0 or przyjete_po > 0:
            db.update_saldo(klient_id, przyjete_p, przyjete_po, kierowca, "PRZYJECIE", self.user['id'])
        
        if wydane_p > 0 or wydane_po > 0:
            db.update_saldo(klient_id, -wydane_p, -wydane_po, kierowca, "WYDANIE", self.user['id'])
        
        messagebox.showinfo("OK", "Rozliczono!")
        self.clear_inputs()
        self.update_saldo()
        self.refresh_historia()
        self.update_magazyn_display()
    
    def clear_inputs(self):
        self.przyjete_palety.delete(0, "end")
        self.przyjete_palety.insert(0, "0")
        self.przyjete_pojemniki.delete(0, "end")
        self.przyjete_pojemniki.insert(0, "0")
        self.wydane_palety.delete(0, "end")
        self.wydane_palety.insert(0, "0")
        self.wydane_pojemniki.delete(0, "end")
        self.wydane_pojemniki.insert(0, "0")
    
    def logout(self):
        self.destroy()
        app = LoginWindow()
        app.mainloop()

def run_ui():
    app = LoginWindow()
    app.mainloop()
