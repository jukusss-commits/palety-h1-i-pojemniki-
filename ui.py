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
        self.geometry("1400x950")
        
        header = tk.Frame(self, bg="#FF6B6B", height=60)
        header.pack(fill="x")
        
        header_label = tk.Label(
            header, 
            text=f"H1 PALETY - {user['nazwa']} ({user['rola']})", 
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
        
        logout_btn = tk.Button(self, text="Wyloguj", command=self.logout, bg="#FF6B6B", fg="white", font=("Arial", 11, "bold"), padx=20, pady=10)
        logout_btn.pack(pady=10, padx=20, fill="x")
        
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
        
        info_frame = tk.Frame(historia_win, bg="white")
        info_frame.pack(fill="x", padx=10, pady=10)
        tk.Label(info_frame, text="E2 = Poprzednia transakcja | H1 = Bieżąca transakcja", font=("Arial", 10, "italic"), bg="white").pack()
        
        columns = ("Data", "Typ", "E2-Saldo.P", "E2-Saldo.Po", "E2-Przyjęto.P", "E2-Wydano.P", "H1-Saldo.P", "H1-Saldo.Po", "Kierowca")
        tree = ttk.Treeview(historia_win, columns=columns, height=20, show="headings")
        
        widths = [150, 80, 90, 90, 100, 100, 90, 90, 100]
        for col, width in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width)
        
        historia = db.get_historia(self.selected_klient_id, 100)
        for trans in historia:
            data = trans['data'].split('.')[0] if '.' in trans['data'] else trans['data']
            
            e2_przyjeto = trans['palety'] if trans['typ'] == 'PRZYJECIE' else "-"
            e2_wydano = trans['palety'] if trans['typ'] == 'WYDANIE' else "-"
            
            tree.insert("", "end", values=(
                data, 
                trans['typ'], 
                trans['saldo_przed_palety'],
                trans['saldo_przed_pojemniki'],
                e2_przyjeto,
                e2_wydano,
                trans['saldo_po_palety'],
                trans['saldo_po_pojemniki'],
                trans['kierowca'] or "-"
            ))
        
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        def drukuj():
            plik = f"historia_{klient_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(plik, 'w', encoding='utf-8') as f:
                f.write("="*150 + "\n")
                f.write(f"HISTORIA TRANSAKCJI: {klient_name}\n")
                f.write(f"Data wydruku: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*150 + "\n\n")
                f.write("LEGENDA: E2 = Stan przed | H1 = Stan po\n\n")
                f.write(f"{'Data':<18} {'Typ':<10} {'E2-Sal.P':<10} {'E2-Sal.Po':<11} {'E2-Przj.P':<10} {'E2-Wyd.P':<10} {'H1-Sal.P':<10} {'H1-Sal.Po':<11} {'Kierowca':<15}\n")
                f.write("-"*150 + "\n")
                for trans in historia:
                    data = trans['data'].split('.')[0] if '.' in trans['data'] else trans['data']
                    e2_przyjeto = str(trans['palety']) if trans['typ'] == 'PRZYJECIE' else "-"
                    e2_wydano = str(trans['palety']) if trans['typ'] == 'WYDANIE' else "-"
                    f.write(f"{data:<18} {trans['typ']:<10} {str(trans['saldo_przed_palety']):<10} {str(trans['saldo_przed_pojemniki']):<11} {e2_przyjeto:<10} {e2_wydano:<10} {str(trans['saldo_po_palety']):<10} {str(trans['saldo_po_pojemniki']):<11} {(trans['kierowca'] or '-'):<15}\n")
                f.write("="*150 + "\n")
            messagebox.showinfo("OK", f"Historia wydrukowana:\n{plik}")
        
        tk.Button(historia_win, text="🖨️ Drukuj", command=drukuj, font=("Arial", 11, "bold"), bg="#FF9800", fg="white", padx=20, pady=8).pack(pady=10)
    
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
        
        # Pytaj o wydruk PRZED rozliczeniem
        druk_win = tk.Toplevel(self)
        druk_win.title("Druk paragonu?")
        druk_win.geometry("400x300")
        druk_win.resizable(False, False)
        
        tk.Label(druk_win, text="Czy chcesz wydrukować paragon?", font=("Arial", 12, "bold")).pack(pady=20)
        
        info_frame = tk.Frame(druk_win, bg="#F5F5F5")
        info_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(info_frame, text=f"Przyjęte palety: {przyjete_p}", font=("Arial", 11)).pack(anchor="w", pady=5)
        tk.Label(info_frame, text=f"Przyjęte pojemniki: {przyjete_po}", font=("Arial", 11)).pack(anchor="w", pady=5)
        tk.Label(info_frame, text=f"Wydane palety: {wydane_p}", font=("Arial", 11)).pack(anchor="w", pady=5)
        tk.Label(info_frame, text=f"Wydane pojemniki: {wydane_po}", font=("Arial", 11)).pack(anchor="w", pady=5)
        
        netto_p = przyjete_p - wydane_p
        netto_po = przyjete_po - wydane_po
        tk.Label(info_frame, text=f"\nNetto palety: {netto_p}", font=("Arial", 11, "bold"), fg="#1976D2").pack(anchor="w", pady=5)
        tk.Label(info_frame, text=f"Netto pojemniki: {netto_po}", font=("Arial", 11, "bold"), fg="#1976D2").pack(anchor="w", pady=5)
        
        btn_frame = tk.Frame(druk_win)
        btn_frame.pack(fill="x", padx=20, pady=20)
        
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
            
            messagebox.showinfo("✅ Sukces", "Rozliczenie zapisane (bez druku)!")
            self.clear_inputs()
            self.update_saldo()
            self.update_magazyn_display()
            druk_win.destroy()
        
        tk.Button(btn_frame, text="✅ TAK - Drukuj", command=rozlicz_i_drukuj, font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", padx=20, pady=10).pack(fill="x", pady=5)
        tk.Button(btn_frame, text="❌ NIE - Bez druku", command=rozlicz_bez_druku, font=("Arial", 12, "bold"), bg="#FF9800", fg="white", padx=20, pady=10).pack(fill="x", pady=5)
    
    def drukuj_paragon_z_danymi(self, przyjete_p, przyjete_po, wydane_p, wydane_po, kierowca):
        klient_name = self.selected_label.cget("text")
        pracownik = self.user['nazwa']
        
        plik = f"paragon_{klient_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(plik, 'w', encoding='utf-8') as f:
            f.write("╔" + "═"*78 + "╗\n")
            f.write("║" + " "*20 + "H1 PALETY - PARAGON ROZLICZENIA" + " "*27 + "║\n")
            f.write("╚" + "═"*78 + "╝\n\n")
            
            f.write(f"Data:              {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Klient:            {klient_name}\n")
            f.write(f"Kierowca:          {kierowca or 'Brak'}\n")
            f.write(f"Pracownik:         {pracownik}\n\n")
            
            f.write("─"*80 + "\n")
            f.write("PRZYJĘTE\n")
            f.write("─"*80 + "\n")
            f.write(f"Palety:            {przyjete_p:>10} szt.\n")
            f.write(f"Pojemniki:         {przyjete_po:>10} szt.\n")
            f.write("─"*80 + "\n\n")
            
            f.write("WYDANE\n")
            f.write("─"*80 + "\n")
            f.write(f"Palety:            {wydane_p:>10} szt.\n")
            f.write(f"Pojemniki:         {wydane_po:>10} szt.\n")
            f.write("─"*80 + "\n\n")
            
            netto_palety = przyjete_p - wydane_p
            netto_pojemniki = przyjete_po - wydane_po
            
            f.write("SALDO (NETTO)\n")
            f.write("─"*80 + "\n")
            f.write(f"Palety:            {netto_palety:>10} szt.\n")
            f.write(f"Pojemniki:         {netto_pojemniki:>10} szt.\n")
            f.write("═"*80 + "\n\n")
            
            f.write(f"Podpis kierowcy: ________________    Podpis pracownika: ________________\n\n")
            f.write("╔" + "═"*78 + "╗\n")
            f.write("║" + " "*78 + "║\n")
            f.write("║" + " "*78 + "║\n")
            f.write("╚" + "═"*78 + "╝\n")
    
    def clear_inputs(self):
        self.przyjete_p.delete(0, "end")
        self.przyjete_p.insert(0, "0")
        self.przyjete_po.delete(0, "end")
        self.przyjete_po.insert(0, "0")
        self.wydane_p.delete(0, "end")
        self.wydane_p.insert(0, "0")
        self.wydane_po.delete(0, "end")
        self.wydane_po.insert(0, "0")
    
    def logout(self):
        self.destroy()
        app = LoginWindow()
        app.mainloop()

def run_ui():
    app = LoginWindow()
    app.mainloop()
