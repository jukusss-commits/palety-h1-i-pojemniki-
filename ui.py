import customtkinter as ctk
import tkinter.messagebox as messagebox
from config import WINDOW_WIDTH, WINDOW_HEIGHT, THEME
from database import db

class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("H1 Palety - Logowanie")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        ctk.set_appearance_mode(THEME)
        ctk.set_default_color_theme("blue")
        
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(expand=True, fill="both")
        
        title = ctk.CTkLabel(main_frame, text="H1 PALETY", font=("Arial", 48, "bold"))
        title.pack(pady=20)
        
        pin_label = ctk.CTkLabel(main_frame, text="PIN:", font=("Arial", 18))
        pin_label.pack(pady=10)
        
        self.pin_entry = ctk.CTkEntry(main_frame, show="*", font=("Arial", 16), width=200)
        self.pin_entry.pack(pady=10)
        
        btn = ctk.CTkButton(main_frame, text="Zaloguj", command=self.login)
        btn.pack(pady=10)

    def login(self):
        pin = self.pin_entry.get()
        pracownik = db.get_pracownik_by_pin(pin)
        if pracownik:
            messagebox.showinfo("OK", f"Zalogowany: {pracownik['nazwa']}")
        else:
            messagebox.showerror("Błąd", "Niepoprawny PIN!")

def run_ui():
    app = LoginWindow()
    app.mainloop()
