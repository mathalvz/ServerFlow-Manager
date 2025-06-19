import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from tkinter import ttk  # Import Themed Tkinter
import subprocess
import threading
import os
import shlex
import time
import json  # Importar para salvar/carregar configurações
import webbrowser  # Importar para abrir URLs no navegador
import re  # Importar para regex na função load_server_for_editing
import socket  # Importar para verificar porta
import sys  # Importar para sys.platform para abrir logs

CONFIG_FILE = "server_configs.json"


# Função para verificar se uma porta está em uso
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return False
        except socket.error:
            return True


class Server:
    """Representa um servidor configurado para ser gerenciado."""

    def __init__(
        self,
        name,
        command,
        working_dir,
        system_log_widget,
        app_root,
        autostart=False,
        expected_port=None,
    ):
        self.name = name
        self.command = command  # O comando completo (ex: "live-server . --port 8080")
        self.working_dir = working_dir
        self.autostart = autostart
        self.expected_port = expected_port  # A porta que o servidor DEVE usar (para 'Abrir no Navegador')
        self.process = None
        self.output_buffer = ""
        self.output_label = None
        self.system_log_widget = system_log_widget
        self.app_root = app_root
        self.autostart_var = tk.BooleanVar(
            value=self.autostart
        )  # Variável para o checkbox
        self.status_label_widget = None  # Novo widget para exibir o status
        self.log_file_path = None  # Caminho do arquivo de log para este servidor
        self.log_file_handle = None  # Handle do arquivo de log

    def _update_output_label(self):
        """Atualiza o widget de saída na thread principal do Tkinter."""
        if self.output_label:
            self.output_label.config(state=tk.NORMAL)
            self.output_label.delete(1.0, tk.END)
            self.output_label.insert(tk.END, self.output_buffer)
            self.output_label.see(tk.END)
            self.output_label.config(state=tk.DISABLED)

    def _set_status(self, text, style_name=""):
        """Define o texto e o estilo do label de status."""
        if self.status_label_widget:
            self.app_root.after(0, lambda: self._update_status_widget(text, style_name))

    def _update_status_widget(self, text, style_name):
        self.status_label_widget.config(text=text, style=style_name)

    def _read_output(self, stream):
        """Lê a saída do processo em uma thread separada e escreve no buffer e no arquivo de log."""
        for line in iter(stream.readline, ""):
            self.output_buffer += line
            if self.log_file_handle:
                try:
                    self.log_file_handle.write(line)
                except Exception as e:
                    self._log_system(
                        f"Erro ao escrever no log para '{self.name}': {e}\n"
                    )
            self.app_root.after(0, self._update_output_label)
        stream.close()

    def start(self):
        """Inicia o processo do servidor."""
        if self.process and self.process.poll() is None:
            self._log_system(f"Servidor '{self.name}' já está em execução.\n")
            return

        # Verifica a disponibilidade da porta antes de iniciar, se aplicável
        if self.expected_port and is_port_in_use(self.expected_port):
            self._log_system(
                f"Erro: Porta {self.expected_port} já está em uso para '{self.name}'.\n"
            )
            messagebox.showerror(
                "Porta em Uso",
                f"A porta {self.expected_port} já está em uso. Não foi possível iniciar o servidor '{self.name}'.",
            )
            self._set_status("Porta em Uso", "Red.TLabel")
            return

        try:
            self.output_buffer = ""
            if self.output_label:
                self.output_label.config(state=tk.NORMAL)
                self.output_label.delete(1.0, tk.END)
                self.output_label.insert(tk.END, "Iniciando...\n")
                self.output_label.config(state=tk.DISABLED)

            # Garante que o diretório de logs exista
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            # Nome do arquivo de log, substituindo caracteres inválidos por '_'
            sanitized_name = re.sub(r'[\\/:*?"<>|]', "_", self.name)
            self.log_file_path = os.path.join(log_dir, f"{sanitized_name}.log")

            try:
                self.log_file_handle = open(self.log_file_path, "a", encoding="utf-8")
            except IOError as e:
                self._log_system(
                    f"Erro ao abrir arquivo de log para '{self.name}': {e}\n"
                )
                self.log_file_handle = (
                    None  # Garante que seja None se a abertura falhar
                )

            self._set_status("Iniciando...", "Orange.TLabel")

            self.process = subprocess.Popen(
                self.command,
                cwd=self.working_dir if self.working_dir else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Mantém o pipe para capturar e exibir E logar
                text=True,
                bufsize=1,
                shell=True,
            )
            running_servers[self.name] = self
            self._log_system(f"Iniciando '{self.name}' (PID: {self.process.pid})...\n")
            self._set_status(
                "Executando", "Green.TLabel"
            )  # Define o status como Executando

            stdout_thread = threading.Thread(
                target=self._read_output, args=(self.process.stdout,)
            )
            stderr_thread = threading.Thread(
                target=self._read_output, args=(self.process.stderr,)
            )
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()

            wait_thread = threading.Thread(target=self._wait_for_process)
            wait_thread.daemon = True
            wait_thread.start()

        except FileNotFoundError:
            self._log_system(
                f"Erro: Interpretador de comando não encontrado para '{self.name}'. "
                "Verifique se o shell está configurado corretamente.\n"
            )
            if self.output_label:
                self.output_label.config(state=tk.NORMAL)
                self.output_label.insert(
                    tk.END, "Erro: Interpretador de comando não encontrado.\n"
                )
                self.output_label.config(state=tk.DISABLED)
            self._set_status("Erro de Comando", "Red.TLabel")
        except Exception as e:
            self._log_system(f"Erro ao iniciar '{self.name}': {e}\n")
            if self.output_label:
                self.output_label.config(state=tk.NORMAL)
                self.output_label.insert(tk.END, f"Erro: {e}\n")
                self.output_label.config(state=tk.DISABLED)
            self._set_status("Erro", "Red.TLabel")

    def _wait_for_process(self):
        """Espera o processo terminar e atualiza os logs."""
        try:
            self.process.wait()
            exit_code = self.process.poll()
            if self.name in running_servers:
                del running_servers[self.name]

            self.app_root.after(0, lambda: self._update_process_status(exit_code))
        except Exception as e:
            self._log_system(f"Erro ao esperar pelo processo '{self.name}': {e}\n")
            self.app_root.after(0, lambda: self._update_process_status(None, error=e))
        finally:
            # Garante que o handle do arquivo de log seja fechado
            if self.log_file_handle:
                try:
                    self.log_file_handle.close()
                    self._log_system(f"Arquivo de log para '{self.name}' fechado.\n")
                except Exception as e:
                    self._log_system(
                        f"Erro ao fechar arquivo de log para '{self.name}': {e}\n"
                    )
                self.log_file_handle = None  # Reseta o handle

    def _update_process_status(self, exit_code, error=None):
        if self.output_label:
            self.output_label.config(state=tk.NORMAL)

        if error:
            self._log_system(f"Servidor '{self.name}' saiu com erro: {error}\n")
            if self.output_label:
                self.output_label.insert(tk.END, f"\nErro: {error}")
            self._set_status("Erro", "Red.TLabel")
        elif exit_code is not None:
            if exit_code != 0:
                self._log_system(
                    f"Servidor '{self.name}' saiu com código {exit_code}.\n"
                )
                if self.output_label:
                    self.output_label.insert(tk.END, f"\nSaiu com código {exit_code}.")
                self._set_status(f"Saiu ({exit_code})", "Red.TLabel")
            else:
                self._log_system(f"Servidor '{self.name}' saiu normalmente.\n")
                if self.output_label:
                    self.output_label.insert(tk.END, "\nSaiu normalmente.")
                self._set_status("Parado", "Gray.TLabel")

        if self.output_label:
            self.output_label.see(tk.END)
            self.output_label.config(state=tk.DISABLED)

    def stop(self):
        """Tenta parar o processo do servidor."""
        if self.process and self.process.poll() is None:
            try:
                self._set_status("Parando...", "Orange.TLabel")
                self.process.terminate()
                self.process.wait(timeout=5)
                if self.process.poll() is None:
                    self.process.kill()
                    self._log_system(f"Servidor '{self.name}' parado à força.\n")
                    self._set_status("Parado (Forçado)", "Red.TLabel")
                else:
                    self._log_system(f"Servidor '{self.name}' parado.\n")
                    self._set_status("Parado", "Gray.TLabel")

                if self.name in running_servers:
                    del running_servers[self.name]

                if self.output_label:
                    self.output_label.config(state=tk.NORMAL)
                    self.output_label.insert(tk.END, "\nParado.")
                    self.output_label.see(tk.END)
                    self.output_label.config(state=tk.DISABLED)
            except Exception as e:
                self._log_system(f"Erro ao tentar parar '{self.name}': {e}\n")
                if self.output_label:
                    self.output_label.config(state=tk.NORMAL)
                    self.output_label.insert(tk.END, f"\nErro ao parar: {e}")
                    self.output_label.config(state=tk.DISABLED)
                self._set_status("Erro ao Parar", "Red.TLabel")
            finally:  # Garante que o handle do arquivo de log seja fechado
                if self.log_file_handle:
                    try:
                        self.log_file_handle.close()
                        self._log_system(
                            f"Arquivo de log para '{self.name}' fechado (parada manual).\n"
                        )
                    except Exception as e:
                        self._log_system(
                            f"Erro ao fechar arquivo de log para '{self.name}': {e}\n"
                        )
                    self.log_file_handle = None
        else:
            self._log_system(f"Servidor '{self.name}' não está em execução.\n")
            self._set_status(
                "Parado", "Gray.TLabel"
            )  # Garante que o status seja 'Parado' se não estiver em execução
            if (
                self.log_file_handle
            ):  # Fecha se ainda estiver aberto de uma tentativa anterior
                try:
                    self.log_file_handle.close()
                except Exception:
                    pass
                self.log_file_handle = None

    def _log_system(self, message):
        """Adiciona uma mensagem ao log do sistema na thread principal do Tkinter."""
        self.app_root.after(0, lambda: self._update_system_log_widget(message))

    def _update_system_log_widget(self, message):
        self.system_log_widget.config(state=tk.NORMAL)
        self.system_log_widget.insert(tk.END, message)
        self.system_log_widget.see(tk.END)
        self.system_log_widget.config(state=tk.DISABLED)

    def to_dict(self):
        """Converte o objeto Server em um dicionário para serialização."""
        return {
            "name": self.name,
            "command": self.command,
            "working_dir": self.working_dir,
            "autostart": self.autostart_var.get(),  # Pega o valor atual do checkbox
            "expected_port": self.expected_port,
        }

    def update_details(self, name, command, working_dir, autostart, expected_port):
        """Atualiza os detalhes do servidor."""
        self.name = name
        self.command = command
        self.working_dir = working_dir
        self.autostart_var.set(autostart)
        self.autostart = autostart  # Atualiza o atributo interno também
        self.expected_port = expected_port

    def open_in_browser(self):
        """Tenta abrir a URL do servidor no navegador padrão."""
        if self.expected_port:
            url = f"http://localhost:{self.expected_port}"
            self._log_system(f"Abrindo '{url}' no navegador para '{self.name}'.\n")
            try:
                webbrowser.open_new_tab(url)
            except Exception as e:
                self._log_system(f"Erro ao abrir o navegador para '{self.name}': {e}\n")
                messagebox.showerror(
                    "Erro no Navegador", f"Não foi possível abrir o navegador: {e}"
                )
        else:
            self._log_system(
                f"Servidor '{self.name}' não tem uma porta definida para abrir no navegador.\n"
            )
            messagebox.showinfo(
                "Informação",
                "Este servidor não tem uma porta definida para abrir no navegador.",
            )


def save_configs(servers_list):
    """Salva a lista de configurações de servidores em um arquivo JSON."""
    data_to_save = [server.to_dict() for server in servers_list]
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=4)
        print(f"Configurações salvas em {CONFIG_FILE}")
    except IOError as e:
        print(f"Erro ao salvar configurações: {e}")


def load_configs():
    """Carrega as configurações de servidores de um arquivo JSON."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON do arquivo de configuração: {e}")
            return []
        except IOError as e:
            print(f"Erro ao carregar configurações: {e}")
            return []
    return []


def create_dummy_files():
    """Cria arquivos dummy para demonstração."""
    node_content = """
import http.server
import socketserver
import os
import signal
import sys
import datetime

PORT = 3000

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(f"Hello from Dummy Node.js Server (Python)! Time: {datetime.datetime.now().strftime('%H:%M:%S')}\\n".encode('utf-8'))

    def log_message(self, format, *args):
        # Suppress HTTP request logging
        pass

def start_server():
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"Dummy Node.js Server (Python) running on port {PORT}")
        httpd.serve_forever()

def signal_handler(sig, frame):
    print("Dummy Node.js Server received signal. Exiting...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    start_server()
"""

    go_dummy_content = """
import http.server
import socketserver
import os
import signal
import sys
import datetime

PORT = 8080

class MyGoHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(f"Hello from Dummy Go Server (Python)! Time: {datetime.datetime.now().strftime('%H:%M:%S')}\\n".encode('utf-8'))

    def log_message(self, format, *args):
        # Suppress HTTP request logging
        pass

def start_server():
    with socketserver.TCPServer(("", PORT), MyGoHandler) as httpd:
        print(f"Dummy Go Server (Python) running on port {PORT}")
        httpd.serve_forever()

def signal_handler(sig, frame):
    print("Dummy Go Server received signal. Exiting...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    start_server()
"""

    try:
        with open("node_dummy_server.py", "w") as f:
            f.write(node_content)
        print("Created node_dummy_server.py")
    except IOError as e:
        print(f"Error creating node_dummy_server.py: {e}")

    try:
        with open("go_dummy_server.py", "w") as f:
            f.write(go_dummy_content)
        print("Created go_dummy_server.py")
    except IOError as e:
        print(f"Error creating go_dummy_server.py: {e}")


running_servers = {}
editing_server_obj = None  # Variável global para o servidor sendo editado


def open_log_file(file_path):
    """Abre o arquivo de log no aplicativo padrão do sistema."""
    if not file_path or not os.path.exists(file_path):
        messagebox.showinfo(
            "Log Não Encontrado",
            "O arquivo de log não existe para este servidor ou não foi gerado ainda.",
        )
        return

    try:
        if sys.platform == "win32":
            os.startfile(file_path)
        elif sys.platform == "darwin":  # macOS
            subprocess.Popen(["open", file_path])
        else:  # Linux e outros
            subprocess.Popen(["xdg-open", file_path])
    except Exception as e:
        messagebox.showerror(
            "Erro ao Abrir Log", f"Não foi possível abrir o arquivo de log: {e}"
        )


def main():
    global editing_server_obj, servers_instances_widgets  # Necessário para modificar globalmente

    root = tk.Tk()
    root.title("Gerenciador de Servidores de Banco de Dados/APIs (Python)")
    root.geometry("800x700")
    root.minsize(850, 750)  # Define um tamanho mínimo para a janela

    # Aplica um tema ttk e define estilos para os labels de status
    style = ttk.Style()
    style.theme_use("clam")  # 'clam' é um tema moderno e amplamente disponível

    style.configure(
        "Green.TLabel", foreground="green", font=("TkDefaultFont", 10, "bold")
    )
    style.configure("Red.TLabel", foreground="red", font=("TkDefaultFont", 10, "bold"))
    style.configure(
        "Orange.TLabel", foreground="orange", font=("TkDefaultFont", 10, "bold")
    )
    style.configure("Gray.TLabel", foreground="gray", font=("TkDefaultFont", 10))

    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill="both", padx=15, pady=15)  # Aumentado padding

    # --- Tab 1: Adicionar Novo Servidor ---
    add_server_tab = ttk.Frame(notebook)
    notebook.add(add_server_tab, text="Adicionar/Editar Servidor")

    add_server_frame = ttk.LabelFrame(
        add_server_tab,
        text="Configurações do Servidor",
        padding=15,  # Aumentado padding
    )
    add_server_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    add_server_frame.columnconfigure(1, weight=1)

    ttk.Label(add_server_frame, text="Nome do Servidor:").grid(
        row=0, column=0, sticky="w", pady=5, padx=10  # Ajustado padx
    )
    server_name_entry = ttk.Entry(add_server_frame)
    server_name_entry.grid(
        row=0, column=1, columnspan=2, sticky="ew", pady=5, padx=10
    )  # Ajustado padx
    server_name_entry.insert(0, "Novo Servidor DB")

    ttk.Label(add_server_frame, text="Tipo de Comando:").grid(
        row=1, column=0, sticky="w", pady=5, padx=10
    )

    command_types = {
        "Python Script (Procurar)": {
            "type": "browse_file",
            "prefix": "python -u ",
            "is_http": False,
        },
        "Node.js Script (Procurar)": {
            "type": "browse_file",
            "prefix": "node ",
            "is_http": False,
        },
        "Go App (Executável ou go run)": {
            "type": "browse_file",
            "prefix_func": lambda p: "go run " if p.lower().endswith(".go") else "",
            "is_http": False,
        },
        "Python SimpleHTTPServer (Servir Pasta)": {
            "type": "fixed_command_with_port_or_folder",  # Permite customizar pasta ou porta
            "base_command": "python -m http.server",
            "is_http": True,
            "default_port": 8000,
            "port_arg_format": "{}",  # Porta é o argumento principal
        },
        "Live-Server (Procurar Pasta Frontend)": {
            "type": "browse_folder",
            "prefix": "live-server ",
            "is_http": True,
            "default_port": 8080,
            "port_arg_format": "--port {}",  # Como adicionar a porta
        },
        "MongoDB Daemon (Padrão)": {
            "type": "fixed_command",
            "command": "mongod --dbpath ./data/db --port 27017",
            "is_http": False,
        },
        "PostgreSQL Server (Padrão)": {
            "type": "fixed_command",
            "command": "pg_ctl start -D /usr/local/var/postgres",
            "is_http": False,
        },
        "Redis Server (Padrão)": {
            "type": "fixed_command",
            "command": "redis-server",
            "is_http": False,
        },
        "Comando Personalizado (Manual)": {
            "type": "manual_entry",
            "prefix": "",
            "is_http": False,
        },
    }
    command_options = list(command_types.keys())
    command_type_var = tk.StringVar(root)
    command_type_var.set(command_options[0])

    command_type_dropdown = ttk.OptionMenu(
        add_server_frame, command_type_var, *command_options
    )
    command_type_dropdown.grid(
        row=1, column=1, sticky="ew", pady=5, padx=10
    )  # Ajustado padx

    command_args_label = ttk.Label(add_server_frame, text="Argumentos/Caminho:")
    command_args_label.grid(row=2, column=0, sticky="w", pady=5, padx=10)

    command_args_entry = ttk.Entry(add_server_frame)
    command_args_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=10)
    command_args_entry.insert(0, "my_custom_server.py")

    browse_file_button = ttk.Button(add_server_frame, text="Procurar Arquivo")
    browse_file_button.grid(row=2, column=2, sticky="e", pady=5, padx=10)

    ttk.Label(add_server_frame, text="Diretório de Trabalho (opcional):").grid(
        row=3, column=0, sticky="w", pady=5, padx=10
    )
    server_working_dir_entry = ttk.Entry(add_server_frame)
    server_working_dir_entry.grid(row=3, column=1, sticky="ew", pady=5, padx=10)

    browse_dir_button = ttk.Button(add_server_frame, text="Procurar Pasta")
    browse_dir_button.grid(row=3, column=2, sticky="e", pady=5, padx=10)

    def browse_working_directory(entry_widget):
        """Abre uma caixa de diálogo para selecionar um diretório de trabalho."""
        dir_path = filedialog.askdirectory(title="Selecionar Diretório de Trabalho")
        if dir_path:
            final_path = f'"{dir_path}"' if " " in dir_path else dir_path
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, final_path)

    browse_dir_button.config(
        command=lambda: browse_working_directory(server_working_dir_entry)
    )

    # Nova linha para a porta personalizada
    port_label = ttk.Label(add_server_frame, text="Porta (opcional):")
    port_label.grid(row=4, column=0, sticky="w", pady=5, padx=10)
    server_port_var = tk.StringVar(root)
    port_entry = ttk.Entry(add_server_frame, textvariable=server_port_var)
    port_entry.grid(row=4, column=1, sticky="ew", pady=5, padx=10)

    autostart_checkbox_var = tk.BooleanVar(root)  # Nova variável para o autostart
    autostart_checkbox = ttk.Checkbutton(
        add_server_frame,
        text="Iniciar Automaticamente ao Abrir",
        variable=autostart_checkbox_var,
    )
    autostart_checkbox.grid(
        row=5, column=0, columnspan=3, sticky="w", pady=10, padx=10
    )  # Aumentado pady

    add_save_button = ttk.Button(add_server_frame, text="Adicionar Servidor")
    add_save_button.grid(row=6, column=0, columnspan=3, pady=15)  # Aumentado pady

    def on_command_type_selected(*args):
        selected_type_key = command_type_var.get()
        details = command_types[selected_type_key]

        command_args_entry.config(state=tk.NORMAL)
        command_args_entry.delete(0, tk.END)

        browse_file_button.config(
            state=tk.DISABLED, command=None, text="Procurar Arquivo"
        )
        command_args_label.config(text="Argumentos/Caminho:")  # Reset label text

        # Lógica para mostrar/esconder campo de porta
        if details.get("is_http", False):
            port_label.grid(row=4, column=0, sticky="w", pady=5, padx=10)
            port_entry.grid(row=4, column=1, sticky="ew", pady=5, padx=10)
            server_port_var.set(
                str(details.get("default_port", ""))
            )  # Define porta padrão
            autostart_checkbox.grid(
                row=5, column=0, columnspan=3, sticky="w", pady=10, padx=10
            )  # Ajusta linha do checkbox
            add_save_button.grid(
                row=6, column=0, columnspan=3, pady=15
            )  # Ajusta linha do botão
        else:
            port_label.grid_forget()
            port_entry.grid_forget()
            server_port_var.set("")  # Limpa o valor da porta
            autostart_checkbox.grid(
                row=4, column=0, columnspan=3, sticky="w", pady=10, padx=10
            )  # Ajusta linha do checkbox
            add_save_button.grid(
                row=5, column=0, columnspan=3, pady=15
            )  # Ajusta linha do botão

        if details["type"] == "browse_file":
            browse_file_button.config(
                state=tk.NORMAL,
                text="Procurar Arquivo",
                command=lambda: browse_command_file(
                    command_args_entry,
                    details.get("prefix_func", details.get("prefix", "")),
                ),
            )
            if callable(details.get("prefix_func")):
                command_args_label.config(
                    text="Caminho/Argumentos (ex: main.go ou ./my_go_app):"
                )
            else:
                command_args_label.config(text="Caminho/Argumentos:")
        elif details["type"] == "browse_folder":
            browse_file_button.config(
                state=tk.NORMAL,
                text="Procurar Pasta",
                command=lambda: browse_folder_for_command(
                    command_args_entry, details["prefix"]
                ),
            )
            command_args_label.config(text="Pasta Frontend:")
        elif details["type"] == "fixed_command":
            command_args_entry.insert(0, details["command"])
            command_args_entry.config(state=tk.DISABLED)
            command_args_label.config(text="Comando Padrão:")
        elif details["type"] == "fixed_command_with_port_or_folder":
            command_args_entry.insert(
                0, details["base_command"]
            )  # Inicia com o comando base
            command_args_entry.config(
                state=tk.NORMAL
            )  # Pode ser editável ou para o browse
            browse_file_button.config(
                state=tk.NORMAL,
                text="Procurar Pasta/Arquivo",  # Pode ser um arquivo ou pasta para o HTTP
                command=lambda: browse_folder_or_file_for_simple_http(
                    command_args_entry, details["base_command"]
                ),
            )
            command_args_label.config(text="Comando Base / Pasta:")
        elif details["type"] == "manual_entry":
            command_args_entry.config(state=tk.NORMAL)
            command_args_label.config(text="Comando Completo:")

    command_type_var.trace("w", on_command_type_selected)

    def browse_command_file(entry_widget, prefix_or_func):
        file_path = filedialog.askopenfilename(
            title="Selecionar Arquivo de Comando",
            filetypes=(
                ("Todos os arquivos", "*.*"),
                ("Arquivos Python", "*.py"),
                ("Executáveis", "*.exe"),
                ("Arquivos Go", "*.go"),
            ),
        )
        if file_path:
            prefix_to_use = (
                prefix_or_func(file_path)
                if callable(prefix_or_func)
                else prefix_or_func
            )
            final_path_arg = f'"{file_path}"' if " " in file_path else file_path
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, f"{prefix_to_use}{final_path_arg}".strip())

    def browse_folder_for_command(entry_widget, prefix):
        dir_path = filedialog.askdirectory(title="Selecionar Pasta Frontend")
        if dir_path:
            final_path_arg = f'"{dir_path}"' if " " in dir_path else dir_path
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, f"{prefix}{final_path_arg}".strip())

    def browse_folder_or_file_for_simple_http(entry_widget, base_command):
        """Permite selecionar uma pasta para o Python SimpleHTTPServer."""
        dir_path = filedialog.askdirectory(title="Selecionar Pasta para Servir HTTP")
        if dir_path:
            entry_widget.delete(0, tk.END)
            # O SimpleHTTPServer serve a pasta onde é executado, então o working_dir será a pasta selecionada
            # O comando args aqui será apenas a porta
            entry_widget.insert(
                0, base_command
            )  # O comando base é o que vai na entrada
            server_working_dir_entry.delete(0, tk.END)
            server_working_dir_entry.insert(0, dir_path)
            messagebox.showinfo(
                "Diretório de Trabalho Definido",
                f"O diretório de trabalho foi definido como:\n{dir_path}\n"
                "O comando de porta será adicionado automaticamente.",
            )

    servers_instances = []  # List to keep track of Server objects
    servers_instances_widgets = (
        {}
    )  # Mapeia nome do servidor para o frame do widget na GUI

    # --- Tab 2: Lista de Servidores (com Scroll) ---
    servers_tab = ttk.Frame(notebook)
    notebook.add(servers_tab, text="Servidores Atuais")  # Renomeado para maior clareza

    # Canvas + Scrollbar para lista de servidores
    server_canvas = tk.Canvas(servers_tab)
    server_scrollbar = ttk.Scrollbar(
        servers_tab, orient="vertical", command=server_canvas.yview
    )
    server_scrollable_frame = ttk.Frame(server_canvas)

    server_scrollable_frame.bind(
        "<Configure>",
        lambda e: server_canvas.configure(scrollregion=server_canvas.bbox("all")),
    )

    server_canvas.create_window((0, 0), window=server_scrollable_frame, anchor="nw")
    server_canvas.configure(yscrollcommand=server_scrollbar.set)

    server_canvas.pack(
        side="left", fill="both", expand=True, padx=10, pady=10
    )  # Ajustado padding
    server_scrollbar.pack(side="right", fill="y")

    # --- Tab 3: Log Geral do Sistema ---
    system_log_tab = ttk.Frame(notebook)
    notebook.add(system_log_tab, text="Log do Sistema")

    system_log = scrolledtext.ScrolledText(
        system_log_tab, wrap=tk.WORD, height=25, state=tk.DISABLED  # Altura ajustada
    )
    system_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    system_log.insert(tk.END, "Logs do Sistema:\n")

    def add_server_widget_to_gui(server_obj, scrollable_frame, canvas_widget):
        """Adiciona widgets do servidor à GUI."""
        # Se o servidor já tem um widget, remova-o antes de recriar
        if server_obj.name in servers_instances_widgets:
            servers_instances_widgets[server_obj.name].destroy()
            del servers_instances_widgets[server_obj.name]

        server_frame = ttk.LabelFrame(
            scrollable_frame, text=f"Servidor: {server_obj.name}", padding=10
        )
        server_frame.pack(fill=tk.X, pady=5, padx=5)
        servers_instances_widgets[server_obj.name] = (
            server_frame  # Armazena o frame do widget
        )

        # Configura o grid para o server_frame, permitindo expansão
        server_frame.grid_columnconfigure(
            0, weight=1
        )  # Coluna para o output_text e status
        server_frame.grid_rowconfigure(1, weight=1)  # Linha para o output_text

        # Frame para botões e status
        top_row_frame = ttk.Frame(server_frame)
        top_row_frame.grid(row=0, column=0, sticky="ew", pady=5, padx=5)
        top_row_frame.columnconfigure(
            0, weight=1
        )  # Permite que a área de botões se expanda
        top_row_frame.columnconfigure(
            1, weight=1
        )  # Permite que o status se alinhe à direita

        buttons_frame = ttk.Frame(top_row_frame)
        buttons_frame.grid(row=0, column=0, sticky="w")  # Botões à esquerda do status

        col_idx = 0
        start_button = ttk.Button(
            buttons_frame,
            text="Iniciar",
            command=lambda s=server_obj: threading.Thread(
                target=s.start, daemon=True
            ).start(),
        )
        start_button.grid(row=0, column=col_idx, padx=3, pady=2)
        col_idx += 1

        stop_button = ttk.Button(
            buttons_frame,
            text="Parar",
            command=lambda s=server_obj: threading.Thread(
                target=s.stop, daemon=True
            ).start(),
        )
        stop_button.grid(row=0, column=col_idx, padx=3, pady=2)
        col_idx += 1

        edit_button = ttk.Button(
            buttons_frame,
            text="Editar",
            command=lambda s=server_obj: load_server_for_editing(s),
        )
        edit_button.grid(row=0, column=col_idx, padx=3, pady=2)
        col_idx += 1

        delete_button = ttk.Button(
            buttons_frame,
            text="Excluir",
            command=lambda s=server_obj: delete_server_action(s),
        )
        delete_button.grid(row=0, column=col_idx, padx=3, pady=2)
        col_idx += 1

        duplicate_button = ttk.Button(
            buttons_frame,
            text="Duplicar",
            command=lambda s=server_obj: duplicate_server_action(s),
        )
        duplicate_button.grid(row=0, column=col_idx, padx=3, pady=2)
        col_idx += 1

        # O botão "Ver Log"
        view_log_button = ttk.Button(
            buttons_frame,
            text="Ver Log",
            command=lambda s=server_obj: open_log_file(s.log_file_path),
        )
        view_log_button.grid(row=0, column=col_idx, padx=3, pady=2)
        col_idx += 1

        # O botão "Abrir no Navegador" só aparece se houver uma porta esperada
        if server_obj.expected_port:
            open_browser_button = ttk.Button(
                buttons_frame,
                text="Abrir no Navegador",
                command=lambda s=server_obj: s.open_in_browser(),
            )
            open_browser_button.grid(row=0, column=col_idx, padx=3, pady=2)
            col_idx += 1  # Incrementa para futuras expansões

        # Label de Status
        status_label = ttk.Label(top_row_frame, text="Parado", style="Gray.TLabel")
        status_label.grid(row=0, column=1, sticky="e", padx=5)  # À direita dos botões
        server_obj.status_label_widget = status_label

        server_output_text = scrolledtext.ScrolledText(
            server_frame, wrap=tk.WORD, height=5, state=tk.DISABLED
        )
        # Usando grid para a área de saída para consistência
        server_output_text.grid(row=1, column=0, sticky="nsew", pady=5, padx=5)
        server_obj.output_label = server_output_text

        # Atualiza a área de rolagem do Canvas
        canvas_widget.update_idletasks()
        canvas_widget.config(scrollregion=canvas_widget.bbox("all"))

    def delete_server_action(server_obj_to_delete):
        """Remove um servidor da lista e da GUI."""
        if messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o servidor '{server_obj_to_delete.name}'?",
        ):
            if (
                server_obj_to_delete.process
                and server_obj_to_delete.process.poll() is None
            ):
                server_obj_to_delete.stop()  # Tenta parar o processo antes de excluir

            # Remove da lista de instâncias
            servers_instances.remove(server_obj_to_delete)

            # Remove o widget da GUI
            if server_obj_to_delete.name in servers_instances_widgets:
                servers_instances_widgets[server_obj_to_delete.name].destroy()
                del servers_instances_widgets[server_obj_to_delete.name]

            save_configs(servers_instances)  # Salva as configurações atualizadas
            server_obj_to_delete._log_system(
                f"Servidor '{server_obj_to_delete.name}' excluído.\n"
            )
            messagebox.showinfo(
                "Sucesso",
                f"Servidor '{server_obj_to_delete.name}' excluído com sucesso!",
            )

            # Atualiza a área de rolagem do Canvas após a remoção
            server_canvas.update_idletasks()
            server_canvas.config(scrollregion=server_canvas.bbox("all"))

    def duplicate_server_action(server_obj_to_duplicate):
        """Duplica um servidor existente."""
        new_name = f"{server_obj_to_duplicate.name} (Cópia)"
        # Garantir nome único
        i = 1
        while any(s.name == new_name for s in servers_instances):
            new_name = f"{server_obj_to_duplicate.name} (Cópia {i})"
            i += 1

        new_server = Server(
            new_name,
            server_obj_to_duplicate.command,
            server_obj_to_duplicate.working_dir,
            system_log,
            root,
            server_obj_to_duplicate.autostart_var.get(),
            server_obj_to_duplicate.expected_port,
        )
        servers_instances.append(new_server)
        add_server_widget_to_gui(new_server, server_scrollable_frame, server_canvas)
        save_configs(servers_instances)
        new_server._log_system(f"Servidor '{new_name}' duplicado com sucesso.\n")
        messagebox.showinfo("Sucesso", f"Servidor '{new_name}' duplicado com sucesso!")

    def load_server_for_editing(server_obj):
        """Carrega os detalhes do servidor para edição na aba de Adicionar Servidor."""
        global editing_server_obj
        editing_server_obj = server_obj

        # Mudar para a aba de adicionar/editar
        notebook.select(add_server_tab)

        # Preencher os campos com os dados do servidor
        server_name_entry.delete(0, tk.END)
        server_name_entry.insert(0, server_obj.name)

        # Tentar selecionar o tipo de comando correto e preencher command_args_entry e port_entry
        found_type = False
        for type_key, details in command_types.items():
            if details.get("type") == "fixed_command_with_port_or_folder":
                # Para Python SimpleHTTPServer, o comando pode ter apenas a porta, ou ser 'python -m http.server'
                if server_obj.command.startswith(details["base_command"]):
                    command_type_var.set(type_key)
                    command_args_entry.delete(0, tk.END)

                    # Se o comando tiver a porta, remova-a para mostrar apenas o comando base no campo de args
                    cmd_without_port = server_obj.command
                    if server_obj.expected_port:
                        port_str = str(server_obj.expected_port)
                        if cmd_without_port.endswith(f" {port_str}"):
                            cmd_without_port = cmd_without_port[
                                : -len(f" {port_str}")
                            ].strip()

                    command_args_entry.insert(
                        0, cmd_without_port
                    )  # Insere o comando base ou caminho
                    server_port_var.set(
                        str(server_obj.expected_port)
                        if server_obj.expected_port
                        else ""
                    )
                    found_type = True
                    break
            elif details.get(
                "type"
            ) == "browse_folder" and server_obj.command.startswith(details["prefix"]):
                command_type_var.set(type_key)
                command_args_entry.delete(0, tk.END)
                # Extrair o caminho da pasta do comando
                path_part = server_obj.command[len(details["prefix"]) :].strip()
                # Remover aspas se existirem
                if path_part.startswith('"') and path_part.endswith('"'):
                    path_part = path_part[1:-1]

                # Se houver --port, remova para o campo de args
                if details.get("port_arg_format"):
                    port_regex = r"\s+" + details["port_arg_format"].replace(
                        "{}", r"(\d+)"
                    )
                    match = re.search(port_regex, path_part)
                    if match:
                        server_port_var.set(match.group(1))
                        path_part = re.sub(port_regex, "", path_part).strip()

                command_args_entry.insert(0, path_part)
                found_type = True
                break
            elif (
                server_obj.command.startswith(details.get("prefix", ""))
                and details.get("type") == "browse_file"
            ) or (
                callable(details.get("prefix_func"))
                and details["prefix_func"](server_obj.command) in server_obj.command
                and details.get("type") == "browse_file"
            ):
                command_type_var.set(type_key)
                command_args_entry.delete(0, tk.END)
                # Tentar remover prefixo para exibir apenas o caminho/argumento
                if callable(details.get("prefix_func")):
                    prefix_used = details["prefix_func"](server_obj.command)
                    if server_obj.command.startswith(prefix_used):
                        command_args_entry.insert(
                            0, server_obj.command[len(prefix_used) :].strip()
                        )
                    else:  # Fallback se não encontrar o prefixo exato gerado
                        command_args_entry.insert(0, server_obj.command)
                else:
                    if server_obj.command.startswith(details.get("prefix", "")):
                        command_args_entry.insert(
                            0, server_obj.command[len(details["prefix"]) :].strip()
                        )
                    else:
                        command_args_entry.insert(
                            0, server_obj.command
                        )  # Caso não comece com o prefixo
                server_port_var.set("")  # Não tem porta para scripts/apps diretos
                found_type = True
                break
            elif (
                details.get("type") == "fixed_command"
                and server_obj.command == details["command"]
            ):
                command_type_var.set(type_key)
                command_args_entry.delete(0, tk.END)
                command_args_entry.insert(0, details["command"])
                server_port_var.set("")  # Não tem porta
                command_args_entry.config(state=tk.DISABLED)  # Fixo
                found_type = True
                break
            elif details.get("type") == "manual_entry":
                # Para entrada manual, apenas preenche o comando e deixa editável
                # Isso deve ser um último recurso se nenhum outro tipo corresponder
                if not found_type:  # Se não encontrou um tipo mais específico
                    command_type_var.set(type_key)
                    command_args_entry.delete(0, tk.END)
                    command_args_entry.insert(0, server_obj.command)
                    server_port_var.set("")
                    command_args_entry.config(state=tk.NORMAL)
                    found_type = True  # Marcar como encontrado para não ser substituído
                    break  # Sair do loop

        if (
            not found_type
        ):  # Se o comando não se encaixa em nenhum tipo pré-definido, trata como manual
            command_type_var.set("Comando Personalizado (Manual)")
            command_args_entry.delete(0, tk.END)
            command_args_entry.insert(0, server_obj.command)
            server_port_var.set("")
            command_args_entry.config(state=tk.NORMAL)

        server_working_dir_entry.delete(0, tk.END)
        server_working_dir_entry.insert(0, server_obj.working_dir)

        autostart_checkbox_var.set(server_obj.autostart_var.get())

        # Atualizar o texto do botão
        add_save_button.config(
            text="Salvar Edições",
            command=lambda: add_new_server_action(is_editing=True),
        )

        on_command_type_selected()  # Chamar para configurar os campos corretamente (visibilidade da porta, etc.)

    def add_new_server_action(is_editing=False):
        """Ação para adicionar ou salvar um servidor."""
        global editing_server_obj

        name = server_name_entry.get().strip()
        base_command_part = command_args_entry.get().strip()
        working_dir = server_working_dir_entry.get().strip()
        autostart = autostart_checkbox_var.get()
        port_value = server_port_var.get().strip()
        expected_port = None

        if not name:
            messagebox.showerror("Erro", "Nome do Servidor é obrigatório.")
            return
        if not base_command_part:
            messagebox.showerror("Erro", "O comando é obrigatório.")
            return

        selected_type_key = command_type_var.get()
        details = command_types[selected_type_key]

        final_command_str = base_command_part  # Inicia com a parte base do comando

        if details.get("is_http", False):
            try:
                if port_value:
                    expected_port = int(port_value)
                    # Formatar o comando para incluir a porta
                    if "port_arg_format" in details:
                        if details["type"] == "fixed_command_with_port_or_folder":
                            # Para SimpleHTTPServer, a porta vai direto após o comando base
                            final_command_str = f"{base_command_part} {expected_port}"
                        else:
                            final_command_str = f"{base_command_part} {details['port_arg_format'].format(expected_port)}"
                    elif details["type"] == "browse_folder":
                        # Para live-server, se a pasta já tiver aspas, adiciona a porta depois
                        if final_command_str.endswith('"') and " " in final_command_str:
                            final_command_str = f'{final_command_str[:-1]} {details["port_arg_format"].format(expected_port)}"'
                        else:
                            final_command_str = f"{final_command_str} {details['port_arg_format'].format(expected_port)}"

                else:  # Se for HTTP mas nenhuma porta foi fornecida, usa a padrão do tipo de comando
                    expected_port = details.get("default_port")
                    if (
                        expected_port
                    ):  # Se houver porta padrão, adiciona ao comando final
                        if "port_arg_format" in details:
                            if details["type"] == "fixed_command_with_port_or_folder":
                                final_command_str = (
                                    f"{base_command_part} {expected_port}"
                                )
                            else:
                                final_command_str = f"{base_command_part} {details['port_arg_format'].format(expected_port)}"
                        elif details["type"] == "browse_folder":
                            if (
                                final_command_str.endswith('"')
                                and " " in final_command_str
                            ):
                                final_command_str = f'{final_command_str[:-1]} {details["port_arg_format"].format(expected_port)}"'
                            else:
                                final_command_str = f"{final_command_str} {details['port_arg_format'].format(expected_port)}"
            except ValueError:
                messagebox.showerror(
                    "Erro de Porta", "A porta deve ser um número válido."
                )
                return

        if is_editing and editing_server_obj:
            old_name = editing_server_obj.name
            editing_server_obj.update_details(
                name, final_command_str, working_dir, autostart, expected_port
            )
            if old_name != name:
                if old_name in running_servers:
                    server_to_move = running_servers.pop(old_name)
                    running_servers[name] = server_to_move

                # Recria o widget para refletir a mudança de nome no título do frame
                add_server_widget_to_gui(
                    editing_server_obj, server_scrollable_frame, server_canvas
                )

            editing_server_obj._log_system(f"Servidor '{name}' editado com sucesso.\n")
            messagebox.showinfo("Sucesso", f"Servidor '{name}' editado com sucesso!")
        else:
            new_server = Server(
                name,
                final_command_str,
                working_dir,
                system_log,
                root,
                autostart,
                expected_port,
            )
            servers_instances.append(new_server)
            add_server_widget_to_gui(new_server, server_scrollable_frame, server_canvas)
            new_server._log_system(f"Servidor '{name}' adicionado com sucesso.\n")
            messagebox.showinfo("Sucesso", f"Servidor '{name}' adicionado com sucesso!")

        save_configs(servers_instances)  # Salva as configurações após adicionar/editar

        # Resetar formulário
        server_name_entry.delete(0, tk.END)
        server_name_entry.insert(0, "Novo Servidor DB")
        command_type_var.set(command_options[0])
        server_working_dir_entry.delete(0, tk.END)
        command_args_entry.delete(0, tk.END)
        command_args_entry.config(state=tk.NORMAL)
        autostart_checkbox_var.set(False)
        server_port_var.set("")  # Limpa o campo da porta

        # Restaurar o botão para "Adicionar Servidor"
        add_save_button.config(text="Adicionar Servidor", command=add_new_server_action)
        editing_server_obj = None  # Limpa o objeto em edição

    add_save_button.config(command=add_new_server_action)

    create_dummy_files()

    # Carregar configurações e iniciar servidores
    loaded_servers_data = load_configs()
    if not loaded_servers_data:
        # Se não houver configurações salvas, adicione alguns exemplos
        initial_servers_data = [
            {
                "name": "Python HTTP (Dummy Node.js)",
                "command": "python -u node_dummy_server.py",
                "working_dir": ".",
                "autostart": False,
                "expected_port": 3000,  # Adicionado porta esperada
            },
            {
                "name": "Python HTTP (Dummy Go)",
                "command": "python -u go_dummy_server.py",
                "working_dir": ".",
                "autostart": False,
                "expected_port": 8080,  # Adicionado porta esperada
            },
            {
                "name": "Live-Server Exemplo",
                "command": "live-server . --port 8081",  # Exemplo com porta
                "working_dir": ".",
                "autostart": False,
                "expected_port": 8081,
            },
            {
                "name": "Python SimpleHTTPServer na 8000",
                "command": "python -m http.server 8000",
                "working_dir": ".",
                "autostart": False,
                "expected_port": 8000,
            },
        ]
        # Adicionar os exemplos à lista de instâncias para que sejam exibidos e salvos
        for s_data in initial_servers_data:
            s_obj = Server(
                s_data["name"],
                s_data["command"],
                s_data["working_dir"],
                system_log,
                root,
                s_data["autostart"],
                s_data.get("expected_port"),
            )
            servers_instances.append(s_obj)
            add_server_widget_to_gui(s_obj, server_scrollable_frame, server_canvas)
        save_configs(servers_instances)  # Salvar os exemplos inicialmente
    else:
        # Reconstruir objetos Server a partir das configurações carregadas
        for s_data in loaded_servers_data:
            s_obj = Server(
                s_data["name"],
                s_data["command"],
                s_data["working_dir"],
                system_log,
                root,
                s_data.get("autostart", False),
                s_data.get("expected_port"),
            )
            servers_instances.append(s_obj)
            add_server_widget_to_gui(s_obj, server_scrollable_frame, server_canvas)
            # Iniciar servidores com autostart=True
            if s_obj.autostart_var.get():
                threading.Thread(target=s_obj.start, daemon=True).start()

    on_command_type_selected()  # Chamada inicial para configurar a UI

    root.mainloop()


if __name__ == "__main__":
    main()
