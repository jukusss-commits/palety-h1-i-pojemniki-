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
        self.geometry("1200x800")
        
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
        
        top_frame = tk.Frame(main_frame, bg="white")
        top_frame.pack(fill="x", pady=10)
        
        klient_label = tk.Label(top_frame, text="Klient:", font=("Arial", 12, "bold"), bg="white")
        klient_label.pack(side="left", padx=5)
        
        self.klient_var = tk.StringVar(value="")
        klienci = db.get_all_klienci()
        self.klient_data = {k['nazwa']: k['id'] for k in klienci}
        klient_names = list(self.klient_data.keys())
        
        self.klient_combo = tk.OptionMenu(top_frame, self.klient_var, *klient_names, command=self.on_klient_change)
        self.klient_combo.pack(side="left", padx=5, fill="x", expand=True)
        
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
        
        palety_label = tk.Label(input_frame, text="Palety:", font=("Arial", 12), bg="white")
        palety_label.pack(side="left", padx=5)
        self.palety_input = tk.Entry(input_frame, font=("Arial", 12), width=8)
        self.palety_input.pack(side="left", padx=5)
        self.palety_input.insert(0, "0")
        
        pojemniki_label = tk.Label(input_frame, text="Pojemniki:", font=("Arial", 12), bg="white")
        pojemniki_label.pack(side="left", padx=5)
        self.pojemniki_input = tk.Entry(input_frame, font=("Arial", 12), width=8)
        self.pojemniki_input.pack(side="left", padx=5)
        self.pojemniki_input.insert(0, "0")
        
        kierowca_label = tk.Label(input_frame, text="Kierowca:", font=("Arial", 12), bg="white")
        kierowca_label.pack(side="left", padx=5)
        self.kierowca_input = tk.Entry(input_frame, font=("Arial", 12), width=15)
        self.kierowca_input.pack(side="left", padx=5)
        
        btn_frame = tk.Frame(main_frame, bg="white")
        btn_frame.pack(fill="x", pady=15)
        
        btn_przyjecie = tk.Button(
            btn_frame,
            text="PRZYJECIE +",
            font=("Arial", 14, "bold"),
            bg="#4CAF50",
            fg="white",
            height=2,
            command=self.przyjecie
        )
        btn_przyjecie.pack(side="left", padx=10, fill="both", expand=True)
        
        btn_wydanie = tk.Button(
            btn_frame,
            text="WYDANIE -",
            font=("Arial", 14, "bold"),
            bg="#FF9800",
            fg="white",
            height=2,
            command=self.wydanie
        )
        btn_wydanie.pack(side="left", padx=10, fill="both", expand=True)
        
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
    
    def on_klient_change(self, value):
        self.update_saldo()
        self.refresh_historia()
    
    def update_saldo(self):
        klient_name = self.klient_var.get()
        if not klient_name:
            return
        klient_id = self.klient_data[klient_name]
        saldo = db.get_saldo(klient_id)
        self.palety_label.config(text=f"PALETY: {saldo['palety']}")
        self.pojemniki_label.config(text=f"POJEMNIKI: {saldo['pojemniki']}")
    
    def refresh_historia(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        klient_name = self.klient_var.get()
        if not klient_name:
            return
        
        klient_id = self.klient_data[klient_name]
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
    
    def przyjecie(self):
        klient_name = self.klient_var.get()
        if not klient_name:
            messagebox.showerror("Blad", "Wybierz klienta!")
            return
        
        try:
            palety = int(self.palety_input.get() or 0)
            pojemniki = int(self.pojemniki_input.get() or 0)
        except:
            messagebox.showerror("Blad", "Wpisz liczby!")
            return
        
        if palety == 0 and pojemniki == 0:
            messagebox.showerror("Blad", "Wpisz co najmniej cos!")
            return
        
        kierowca = self.kierowca_input.get()
        klient_id = self.klient_data[klient_name]
        db.update_saldo(klient_id, palety, pojemniki, kierowca, "PRZYJECIE", self.user['id'])
        
        messagebox.showinfo("OK", f"Przyjeto:\n{palety} palet\n{pojemniki} pojemnikow")
        self.clear_inputs()
        self.update_saldo()
        self.refresh_historia()
    
    def wydanie(self):
        klient_name = self.klient_var.get()
        if not klient_name:
            messagebox.showerror("Blad", "Wybierz klienta!")
            return
        
        try:
            palety = int(self.palety_input.get() or 0)
            pojemniki = int(self.pojemniki_input.get() or 0)
        except:
            messagebox.showerror("Blad", "Wpisz liczby!")
            return
        
        if palety == 0 and pojemniki == 0:
            messagebox.showerror("Blad", "Wpisz co najmniej cos!")
            return
        
        kierowca = self.kierowca_input.get()
        klient_id = self.klient_data[klient_name]
        db.update_saldo(klient_id, -palety, -pojemniki, kierowca, "WYDANIE", self.user['id'])
        
        messagebox.showinfo("OK", f"Wydano:\n{palety} palet\n{pojemniki} pojemnikow")
        self.clear_inputs()
        self.update_saldo()
        self.refresh_historia()
    
    def clear_inputs(self):
        self.palety_input.delete(0, "end")
        self.palety_input.insert(0, "0")
        self.pojemniki_input.delete(0, "end")
        self.pojemniki_input.insert(0, "0")
        self.kierowca_input.delete(0, "end")
    
    def logout(self):
        self.destroy()
        app = LoginWindow()
        app.mainloop()

def run_ui():
    app = LoginWindow()
    app.mainloop()
