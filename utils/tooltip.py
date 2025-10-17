"""Tooltip widget for Tkinter"""
import tkinter as tk

class Tooltip:
    """
    Tworzy prosty, wielokrotnie używalny dymek pomocy (tooltip) 
    dla widgetów Tkinter (przycisków, etykiet, itp.).
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.id = None
        self.x = 0
        self.y = 0
        
        # Oczekuje na najechanie kursorem: po 500 ms wywołuje show()
        self.widget.bind("<Enter>", self.schedule)
        # Po opuszczeniu kursora: wywołuje hide()
        self.widget.bind("<Leave>", self.hide)

    def schedule(self, event=None):
        # Anuluje poprzednie oczekiwanie, jeśli nastąpiło ponowne wejście
        self.cancel()
        # Ustawia nowe oczekiwanie na 500 ms (0.5 sekundy)
        self.id = self.widget.after(500, self.show)

    def cancel(self):
        # Anuluje zaplanowane wyświetlenie dymka (jeśli istnieje)
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show(self, event=None):
        """Wyświetla dymek pomocy."""
        if self.tip_window or not self.text:
            return

        # 1. Tworzenie okna Toplevel
        x = self.widget.winfo_rootx() + 20 # Przesunięcie o 20px w prawo
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 1 # Pod widgetem
        
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True) # Usuwa ramkę okna
        self.tip_window.wm_geometry(f"+{x}+{y}")

        # 2. Dodanie etykiety z tekstem
        label = tk.Label(self.tip_window, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1) # Minimalny padding wewnętrzny

    def hide(self, event=None):
        """Ukrywa i niszczy dymek pomocy."""
        self.cancel()
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None
