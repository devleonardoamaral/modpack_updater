import os
import re
import time
import zipfile
import platform
import shutil
import tempfile
import http.client
import threading
import tkinter as tk
from urllib.parse import urlparse
from tkinter import filedialog, ttk
from .utils import default_path


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.url = (
            "https://codeload.github.com/devleonardoamaral/minecraft_ultimaesperanca_modpack/zip/refs/heads/master"
        )
        self.tooltip = None

        if platform.system() == "Windows":
            ttk.Style().theme_use("winnative")
        elif platform.system() == "Linux":
            ttk.Style().theme_use("clam")

        icon = tk.PhotoImage(file=os.path.normpath("app/assets/logo.png"))
        self.root.iconphoto(True, icon)

        self.default_dir = default_path()
        self.downloading = False
        self.modpack_size = 350

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        width = 500
        height = 250

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.x_scale = width / screen_width
        self.y_scale = height / screen_height

        self.root.title("Última Esperança: Instalador e Atualizador de Modpacks")
        self.root.wm_resizable(False, False)
        self.root.wm_geometry(f"{width}x{height}+{x}+{y}")

        self.frame = tk.Frame(self.root)
        self.frame.pack(expand=True, fill="both", padx=25, pady=10)

        self.directory_label = ttk.Label(self.frame, text="Diretório do Minecraft:", anchor="w")
        self.directory_label.pack(fill="x", anchor="n")

        self.directory_frame = ttk.Frame(self.frame)
        self.directory_frame.pack(fill="x", anchor="n")

        self.directory_frame.columnconfigure(0, weight=1)

        self.directory_entry = ttk.Entry(self.directory_frame)
        self.directory_entry.insert(0, default_path())
        self.directory_entry.grid(row=0, column=0, sticky="we", padx=(0, 5))

        self.directory_button = ttk.Button(self.directory_frame, text="Explorar", command=self.select_directory)
        self.directory_button.grid(row=0, column=1, padx=(5, 0))

        self.shader_label = ttk.Label(self.frame, text="Habilitar shader?", name="shader_label")
        self.shader_label.pack(anchor="w", pady=(10, 0))

        self.shader_label.bind("<Enter>", self.show_tooltip)
        self.shader_label.bind("<Leave>", self.hide_tooltip)
        self.shader_label.bind("<Motion>", self.move_tooltip)

        self.shader_combobox = ttk.Combobox(
            self.frame, values=["Não", "ComplementaryUnbound_r5.3.zip"], state="readonly", name="shader_combobox"
        )
        self.shader_combobox.set("ComplementaryUnbound_r5.3.zip")
        self.shader_combobox.pack(fill="x", anchor="n")

        self.shader_combobox.bind("<Enter>", self.show_tooltip)
        self.shader_combobox.bind("<Leave>", self.hide_tooltip)

        def shader_combobox_on_select(event):
            self.shader_combobox.select_clear()
            self.shader_combobox.tk_focusNext().focus_set()

        self.shader_combobox.bind("<<ComboboxSelected>>", shader_combobox_on_select)
        self.shader_combobox.bind("<Motion>", self.move_tooltip)

        self.progress_label = ttk.Label(self.frame, text="Aguardando ação...")
        self.progress_label.pack(fill="x", anchor="s", pady=(10, 5))

        self.progress_bar = ttk.Progressbar(self.frame, mode="determinate", maximum=100)
        self.progress_bar.pack(fill="x", anchor="s")

        self.buttons_frame = ttk.Frame(self.frame)
        self.buttons_frame.pack(fill="x", anchor="s", pady=(10, 0))

        self.buttons_frame.grid_columnconfigure(0, weight=1)
        self.buttons_frame.grid_columnconfigure(1, weight=1)

        self.button_install = ttk.Button(self.buttons_frame, text="Instalar/Atualizar", command=self.install)
        self.button_install.grid(row=0, column=0, sticky="we", padx=(0, 5))

        self.button_cancel = ttk.Button(self.buttons_frame, text="Cancelar", command=self.cancel, state="disabled")
        self.button_cancel.grid(row=0, column=1, sticky="we", padx=(5, 0))

    def show_tooltip(self, event: tk.Event):
        self.hide_tooltip(event)

        if event.widget.winfo_name() in ["shader_label", "shader_combobox"]:
            self.tooltip = tk.Toplevel(self.shader_combobox)
            self.tooltip.overrideredirect(True)
            self.tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")

            label = tk.Label(
                self.tooltip,
                text=(
                    "Shaders melhoram significativamente a qualidade\n"
                    "gráfica, mas causam grande impacto no desempenho.\n"
                    " Se você enfrentar problemas, considere\n"
                    "instalar o modpack com o shader desativado."
                ),
                relief="solid",
                borderwidth=1,
            )
            label.pack()

    def hide_tooltip(self, event: tk.Event):
        if self.tooltip:
            self.tooltip.destroy()

    def move_tooltip(self, event: tk.Event):
        if self.tooltip:
            self.tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")

    def select_directory(self):
        selected_dir = filedialog.askdirectory(initialdir=self.directory_entry.get())

        if selected_dir:
            self.directory_entry.delete(0, tk.END)
            self.directory_entry.insert(0, selected_dir)

    def update_progress(self, step, status):
        self.progress_bar["value"] = step
        self.progress_label["text"] = status
        self.root.update_idletasks()

    def enable(self):
        self.directory_entry.config(state="normal")
        self.directory_button.config(state="normal")
        self.shader_combobox.config(state="readonly")
        self.button_install.config(state="normal")
        self.button_cancel.config(state="disabled")

    def disable(self):
        self.directory_entry.config(state="disabled")
        self.directory_button.config(state="disabled")
        self.shader_combobox.config(state="disabled")
        self.button_install.config(state="disabled")
        self.button_cancel.config(state="normal")

    def prepare_dest(self, dest_dir):
        mods_dir = os.path.join(dest_dir, "mods")

        if os.path.exists(mods_dir):
            shutil.rmtree(mods_dir)
        else:
            os.makedirs(dest_dir, exist_ok=True)

    def extract_zip(self, zip_file, dest_dir):
        with zipfile.ZipFile(zip_file) as zip_file:
            for member in zip_file.namelist():

                safe_path = os.path.normpath(member)
                if safe_path.startswith(".."):
                    raise ValueError(f"Caminho inseguro detectado no ZIP: {member}")

                member_path = member.split("/", 1)[-1]

                if member_path:
                    destination = os.path.join(dest_dir, member_path)

                    if member.endswith("/"):
                        os.makedirs(destination, exist_ok=True)
                    else:
                        with open(destination, "wb") as file:
                            file.write(zip_file.read(member))

    def download(self, temp, progress_start: int, progress_end: int):
        self.update_progress(progress_start, "Iniciando Download...")
        parsed_url = urlparse(self.url)
        connection = http.client.HTTPSConnection(parsed_url.netloc)
        headers = {
            "User-Agent": "Python-Downloader",
            "Referer": "https://codeload.github.com/",
            "Accept": "*/*",
        }
        connection.request("GET", parsed_url.path, headers=headers)

        try:
            response = connection.getresponse()
            total_bytes = 0
            start_time = time.time()
            buffer_size = 8192

            length = response.headers.get("Content-Length")
            total_length = int(length) if length is not None else 0

            while chunk := response.read(buffer_size):
                if self.downloading is False:
                    raise Exception("Download cancelado")

                temp.write(chunk)
                total_bytes += len(chunk)

                elapsed_time = time.time() - start_time
                if elapsed_time > 0:
                    speed = total_bytes / elapsed_time
                    speed_mb = speed / (1024**2)
                    total_mb = total_bytes / (1024**2)

                    if total_length > 0:
                        progress_value = progress_start + (
                            (progress_end - progress_start) * (total_bytes / total_length)
                        )
                        self.update_progress(
                            progress_value,
                            f"Baixando... {total_mb:.2f} / {total_length / (1024**2):.2f} MB | {speed_mb:.2f} MB/s",
                        )
                    else:
                        total_size = total_mb if total_mb > self.modpack_size else self.modpack_size
                        progress_value = progress_start + ((progress_end - progress_start) * (total_mb / total_size))
                        self.update_progress(
                            progress_value,
                            f"Baixando... {total_mb:.2f} MB baixados | {speed_mb:.2f} MB/s",
                        )

        finally:
            connection.close()

    def cancel(self):
        self.downloading = False

    def install(self):
        self.thread = threading.Thread(target=self.installing, daemon=True)
        self.thread.start()

    def post_installation(self):
        shader = self.shader_combobox.get()
        if shader == "Não":
            config_shader_path = os.path.join(self.directory_entry.get(), "config", "oculus.properties")

            with open(config_shader_path, "r+") as file:
                content = file.read()
                file.seek(0)
                new_content = re.sub(r"enableShaders=true", "enableShaders=false", content)
                file.write(new_content)
                file.truncate()

    def installing(self):
        self.disable()
        dest_dir = self.directory_entry.get()

        try:
            # Passo 1: Remove arquivos antigos e cria diretórios
            self.update_progress(10, "Removendo arquivos antigos...")
            self.prepare_dest(dest_dir)

            # Passo 2: Baixa novos arquivos
            with tempfile.TemporaryFile() as temp:
                self.downloading = True
                self.download(temp, 10, 80)
                self.downloading = False
                self.update_progress(80, "Extraindo arquivos...")
                self.extract_zip(temp, dest_dir)
                self.update_progress(90, "Aplicando configurações...")
                self.post_installation()

            # Passo 2: Extraí novos arquivos
            self.update_progress(100, "Download e instalação do modpack concluído!")

        except Exception as error:
            self.update_progress(0, f"Falhou: {error}")

        self.thread = None
        self.enable()

    @classmethod
    def get_instance(cls):
        return cls(tk.Tk())
