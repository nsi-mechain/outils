import os
import threading
import socket
import http.server
import socketserver
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

import tkinter as tk
from tkinter import messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "localhost"
    return ip

class PlaceholderEntry(tk.Entry):
    """Entry avec texte d'aide grisé."""
    def __init__(self, master=None, placeholder="PLACEHOLDER", color='grey', textvariable=None, **kwargs):
        super().__init__(master, textvariable=textvariable, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']
        self.textvariable = textvariable
        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)
        self.foc_out()
        if self.textvariable is not None:
            self.textvariable.trace_add("write", self.remove_placeholder_on_write)

    def remove_placeholder_on_write(self, *args):
        if self.get() and self['fg'] == self.placeholder_color:
            self.delete(0, tk.END)
            self.config(fg=self.default_fg_color)

    def foc_in(self, *args):
        if self['fg'] == self.placeholder_color:
            self.delete(0, tk.END)
            self.config(fg=self.default_fg_color)

    def foc_out(self, *args):
        if not self.get():
            self.config(fg=self.placeholder_color)
            self.delete(0, tk.END)
            self.insert(0, self.placeholder)

    def set_text(self, text):
        self.config(fg=self.default_fg_color)
        self.delete(0, tk.END)
        self.insert(0, text)
        self.foc_out()

class ServerApp:
    def __init__(self, root):
        self.root = root
        root.title("Gestion de serveurs HTTP / FTP")
        root.geometry("600x285")
        root.resizable(False, False)
        root.grid_columnconfigure(1, weight=1)

        self.http_dir = tk.StringVar()
        self.http_url = tk.StringVar()
        self.http_thread = None
        self.http_running = False
        self.http_port = 8080

        self.ftp_dir = tk.StringVar()
        self.ftp_url = tk.StringVar()
        self.ftp_thread = None
        self.ftp_running = False
        self.ftp_port = 2121

        # HTTP widgets
        tk.Label(root, text="Répertoire HTTP :").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.http_entry = PlaceholderEntry(
            root, placeholder="glisser un dossier ici", textvariable=self.http_dir, width=70
        )
        self.http_entry.grid(row=0, column=1, sticky='we', padx=5, pady=5)
        self.http_entry.drop_target_register(DND_FILES)
        self.http_entry.dnd_bind('<<Drop>>', self.on_drop_http)
        self.http_btn = tk.Button(root, text="Lancer HTTP", command=self.toggle_http)
        self.http_btn.grid(row=1, column=0, columnspan=3, sticky='we', padx=5, pady=5, ipady=5)
        tk.Label(root, text="URL HTTP :").grid(row=2, column=0, sticky='w', padx=5)
        tk.Label(root, textvariable=self.http_url, fg="blue").grid(row=2, column=1, columnspan=2, sticky='w', padx=5)

        # Séparateur noir épais (ligne horizontale)
        separator = tk.Frame(root, bg="black", height=2, width=780)
        separator.grid(row=10, column=0, columnspan=3, pady=10, padx=5, sticky='we')

        # FTP widgets
        tk.Label(root, text="Répertoire FTP :").grid(row=11, column=0, sticky='w', padx=5, pady=(10,5))
        self.ftp_entry = PlaceholderEntry(
            root, placeholder="glisser un dossier ici", textvariable=self.ftp_dir, width=70
        )
        self.ftp_entry.grid(row=11, column=1, sticky='we', padx=5, pady=(10,5))
        self.ftp_entry.drop_target_register(DND_FILES)
        self.ftp_entry.dnd_bind('<<Drop>>', self.on_drop_ftp)
        self.ftp_btn = tk.Button(root, text="Lancer FTP", command=self.toggle_ftp)
        self.ftp_btn.grid(row=12, column=0, columnspan=3, sticky='we', padx=5, pady=5, ipady=5)
        tk.Label(root, text="URL FTP :").grid(row=13, column=0, sticky='w', padx=5, pady=(0, 20))
        tk.Label(root, textvariable=self.ftp_url, fg="blue").grid(
            row=13, column=1, columnspan=2, sticky='w', padx=5, pady=(0, 20)
        )

        root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # Gestion du drag & drop HTTP
    def on_drop_http(self, event):
        path = self.clean_drop_path(event.data)
        self.http_dir.set(path)
        self.http_entry.set_text(path)

    # Gestion du drag & drop FTP
    def on_drop_ftp(self, event):
        path = self.clean_drop_path(event.data)
        self.ftp_dir.set(path)
        self.ftp_entry.set_text(path)

    # Nettoyage du chemin déposé (pour gérer accolades et multi-dossiers)
    def clean_drop_path(self, data):
        paths = data.split()
        if paths:
            path = paths[0]
            if path.startswith("{") and path.endswith("}"):
                path = path[1:-1]
            return path
        return data

    def toggle_http(self):
        if not self.http_running:
            self.start_http()
        else:
            self.stop_http()

    def start_http(self):
        directory = self.http_dir.get()
        if not directory or not os.path.isdir(directory):
            messagebox.showerror("Erreur", "Répertoire HTTP invalide.")
            return

        self.http_running = True
        self.http_btn.config(text="Arrêter HTTP")
        ip = get_local_ip()
        self.http_url.set(f"http://{ip}:{self.http_port}/")
        self.http_thread = threading.Thread(target=self.run_http_server, daemon=True)
        self.http_thread.start()

    def run_http_server(self):
        handler = http.server.SimpleHTTPRequestHandler
        os.chdir(self.http_dir.get())
        with socketserver.TCPServer(("", self.http_port), handler) as httpd:
            try:
                httpd.serve_forever()
            except Exception:
                pass
        self.http_running = False
        self.http_btn.config(text="Lancer HTTP")
        self.http_url.set("")

    def stop_http(self):
        try:
            socket.create_connection(("localhost", self.http_port), timeout=1).close()
        except Exception:
            pass
        self.http_running = False
        self.http_btn.config(text="Lancer HTTP")
        self.http_url.set("")

    def toggle_ftp(self):
        if not self.ftp_running:
            self.start_ftp()
        else:
            self.stop_ftp()

    def start_ftp(self):
        directory = self.ftp_dir.get()
        if not directory or not os.path.isdir(directory):
            messagebox.showerror("Erreur", "Répertoire FTP invalide.")
            return

        self.ftp_running = True
        self.ftp_btn.config(text="Arrêter FTP")
        ip = get_local_ip()
        self.ftp_url.set(f"ftp://{ip}:{self.ftp_port}/")
        self.ftp_thread = threading.Thread(target=self.run_ftp_server, daemon=True)
        self.ftp_thread.start()

    def run_ftp_server(self):
        authorizer = DummyAuthorizer()
        authorizer.add_anonymous(self.ftp_dir.get(), perm='elr')
        handler = FTPHandler
        handler.authorizer = authorizer
        address = ('', self.ftp_port)
        server = FTPServer(address, handler)
        try:
            server.serve_forever()
        except Exception:
            pass
        self.ftp_running = False
        self.ftp_btn.config(text="Lancer FTP")
        self.ftp_url.set("")

    def stop_ftp(self):
        try:
            socket.create_connection(("localhost", self.ftp_port), timeout=1).close()
        except Exception:
            pass
        self.ftp_running = False
        self.ftp_btn.config(text="Lancer FTP")
        self.ftp_url.set("")

    def on_closing(self):
        self.stop_http()
        self.stop_ftp()
        self.root.destroy()

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ServerApp(root)
    root.mainloop()

