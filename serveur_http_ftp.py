import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import socket

import http.server
import socketserver

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "localhost"
    return ip

class ServerApp:
    def __init__(self, root):
        self.root = root
        root.title("Gestion de serveurs HTTP / FTP")
        root.geometry("800x270")
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
        tk.Entry(root, textvariable=self.http_dir, width=70).grid(row=0, column=1, sticky='we', padx=5, pady=5)
        tk.Button(root, text="Choisir", command=self.select_http_dir, width=12).grid(row=0, column=2, padx=5, pady=5)
        self.http_btn = tk.Button(root, text="Lancer HTTP", command=self.toggle_http)
        self.http_btn.grid(row=1, column=0, columnspan=3, sticky='we', padx=5, pady=5, ipady=5)
        tk.Label(root, text="URL HTTP :").grid(row=2, column=0, sticky='w', padx=5)
        tk.Label(root, textvariable=self.http_url, fg="blue").grid(row=2, column=1, columnspan=2, sticky='w', padx=5)

        # FTP widgets
        tk.Label(root, text="Répertoire FTP :").grid(row=3, column=0, sticky='w', padx=5, pady=(20,5))
        tk.Entry(root, textvariable=self.ftp_dir, width=70).grid(row=3, column=1, sticky='we', padx=5, pady=(20,5))
        tk.Button(root, text="Choisir", command=self.select_ftp_dir, width=12).grid(row=3, column=2, padx=5, pady=(20,5))
        self.ftp_btn = tk.Button(root, text="Lancer FTP", command=self.toggle_ftp)
        self.ftp_btn.grid(row=4, column=0, columnspan=3, sticky='we', padx=5, pady=5, ipady=5)
        tk.Label(root, text="URL FTP :").grid(row=5, column=0, sticky='w', padx=5, pady=(0, 20))
        tk.Label(root, textvariable=self.ftp_url, fg="blue").grid(
            row=5, column=1, columnspan=2, sticky='w', padx=5, pady=(0, 20)
        )

        root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def select_http_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.http_dir.set(d)

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
        import socket
        try:
            socket.create_connection(("localhost", self.http_port), timeout=1).close()
        except Exception:
            pass
        self.http_running = False
        self.http_btn.config(text="Lancer HTTP")
        self.http_url.set("")

    def select_ftp_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.ftp_dir.set(d)

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
        import socket
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
    root = tk.Tk()
    app = ServerApp(root)
    root.mainloop()
