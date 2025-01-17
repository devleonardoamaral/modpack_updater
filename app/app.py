import os
import re
import time
import zipfile
import shutil
import tempfile
import platform
import http.client
import threading
import tkinter as tk
from urllib.parse import urlparse
from tkinter import filedialog, ttk
from ttkthemes import ThemedTk
from .utils import default_path, resource_path

SCALE_FACTOR = None

if platform.system() == "Windows":
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
        scaleFactor = windll.shcore.GetScaleFactorForDevice(0) / 100
    except Exception as e:
        print(f"Erro ao ajustar DPI: {e}")


class App:
    def __init__(self, root: ThemedTk):
        self.root = root

        if SCALE_FACTOR is not None:
            root.tk.call("tk", "scaling", SCALE_FACTOR)

        root.set_theme("black")

        self.url = (
            "https://codeload.github.com/devleonardoamaral/minecraft_ultimaesperanca_modpack/zip/refs/heads/master"
        )
        self.tooltip = None

        if platform.system() == "Windows":
            self.root.wm_iconbitmap(default=resource_path("app/assets/icon.ico"))
        else:
            icon = tk.PhotoImage(file=resource_path("app/assets/logo.png"))
            self.root.iconphoto(True, icon)

        self.default_dir = default_path()
        self.downloading = False
        self.modpack_size = 350

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        width = 600
        height = 520

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.x_scale = width / screen_width
        self.y_scale = height / screen_height

        self.root.title("Última Esperança: Instalador e Atualizador de Modpacks")
        self.root.wm_resizable(False, False)
        self.root.wm_geometry(f"{width}x{height}+{x}+{y}")

        self.banner_image = tk.PhotoImage(file=resource_path("./app/assets/background.png"))
        self.banner_label = ttk.Label(self.root, image=self.banner_image, borderwidth=0, relief="flat")
        self.banner_label.pack()

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(expand=True, fill="both")

        self.frame = ttk.Frame(self.main_frame)
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

        self.additional_config_label = ttk.Label(self.frame, text="Configurações do Minecraft")
        self.additional_config_label.pack(anchor="w", pady=(20, 0))

        self.additional_config_frame = ttk.Frame(self.frame, relief="groove", borderwidth=2)
        self.additional_config_frame.pack(fill="both", anchor="n", pady=(0, 10))

        self.preset_label = ttk.Label(
            self.additional_config_frame, text="Predefinição de Performance:", name="preset_label"
        )
        self.preset_label.pack(anchor="w", padx=5)
        self.preset_label.bind("<Enter>", self.show_tooltip)
        self.preset_label.bind("<Leave>", self.hide_tooltip)
        self.preset_label.bind("<Motion>", self.move_tooltip)

        self.preset_combobox = ttk.Combobox(
            self.additional_config_frame, values=["Qualidade", "Performance"], state="readonly", name="preset_combobox"
        )
        self.preset_combobox.set("Qualidade")
        self.preset_combobox.pack(fill="x", anchor="n", padx=5, pady=(0, 5))
        self.preset_combobox.bind("<Enter>", self.show_tooltip)
        self.preset_combobox.bind("<Leave>", self.hide_tooltip)
        self.preset_combobox.bind("<<ComboboxSelected>>", self.combobox_on_select)
        self.preset_combobox.bind("<Motion>", self.move_tooltip)

        self.shader_frame_label = ttk.Label(self.frame, text="Configurações do Shader")
        self.shader_frame_label.pack(anchor="w", pady=(10, 0))

        self.shader_frame = ttk.Frame(self.frame, relief="groove", borderwidth=2)
        self.shader_frame.pack(fill="x", anchor="n", pady=(0, 10))

        self.shader_label = ttk.Label(self.shader_frame, text="Habilitar shader?", name="shader_label")
        self.shader_label.pack(anchor="w", padx=5, pady=(5, 0))
        self.shader_label.bind("<Enter>", self.show_tooltip)
        self.shader_label.bind("<Leave>", self.hide_tooltip)
        self.shader_label.bind("<Motion>", self.move_tooltip)

        self.shader_combobox = ttk.Combobox(
            self.shader_frame, values=["Não", "ComplementaryUnbound_r5.3"], state="readonly", name="shader_combobox"
        )
        self.shader_combobox.set("ComplementaryUnbound_r5.3")
        self.shader_combobox.pack(fill="x", anchor="n", padx=5)
        self.shader_combobox.bind("<Enter>", self.show_tooltip)
        self.shader_combobox.bind("<Leave>", self.hide_tooltip)
        self.shader_combobox.bind("<<ComboboxSelected>>", self.combobox_on_select)
        self.shader_combobox.bind("<Motion>", self.move_tooltip)

        self.shader_preset_label = ttk.Label(self.shader_frame, text="Qualidade do shader:", name="shader_preset_label")
        self.shader_preset_label.pack(anchor="w", padx=5, pady=(5, 0))
        self.shader_preset_label.bind("<Enter>", self.show_tooltip)
        self.shader_preset_label.bind("<Leave>", self.hide_tooltip)
        self.shader_preset_label.bind("<Motion>", self.move_tooltip)

        self.shader_preset_combobox = ttk.Combobox(
            self.shader_frame,
            values=["Baixa", "Média", "Alta"],
            state="readonly",
            name="shader_preset_combobox",
        )
        self.shader_preset_combobox.set("Média")
        self.shader_preset_combobox.pack(fill="x", anchor="n", padx=5, pady=(0, 5))
        self.shader_preset_combobox.bind("<Enter>", self.show_tooltip)
        self.shader_preset_combobox.bind("<Leave>", self.hide_tooltip)
        self.shader_preset_combobox.bind("<<ComboboxSelected>>", self.combobox_on_select)
        self.shader_preset_combobox.bind("<Motion>", self.move_tooltip)

        self.progress_label = ttk.Label(self.frame, text="Aguardando ação...", anchor="sw")
        self.progress_label.pack(fill="both", expand=True, anchor="sw", pady=(0, 5))

        self.progress_bar = ttk.Progressbar(self.frame, mode="determinate", maximum=100)
        self.progress_bar.pack(fill="x", anchor="n")

        self.buttons_frame = ttk.Frame(self.frame)
        self.buttons_frame.pack(fill="x", anchor="n", pady=(10, 0))

        self.buttons_frame.grid_columnconfigure(0, weight=1)
        self.buttons_frame.grid_columnconfigure(1, weight=1)

        self.button_install = ttk.Button(self.buttons_frame, text="Instalar/Atualizar", command=self.install)
        self.button_install.grid(row=0, column=0, sticky="we", padx=(0, 5))

        self.button_cancel = ttk.Button(self.buttons_frame, text="Cancelar", command=self.cancel, state="disabled")
        self.button_cancel.grid(row=0, column=1, sticky="we", padx=(5, 0))

        self.footer_label = ttk.Label(self.root, image=self.banner_image, borderwidth=0, relief="flat")
        self.footer_label.pack(anchor="sw")

    def combobox_on_select(self, event):
        if event.widget.winfo_name() == "shader_combobox" and event.widget.get() == "Não":
            self.shader_preset_combobox.config(state="disabled")
        else:
            self.shader_preset_combobox.config(state="readonly")

        event.widget.select_clear()
        event.widget.tk_focusNext().focus_set()

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
                relief="flat",
            )
            label.pack(ipadx=5, ipady=5)

        elif event.widget.winfo_name() in ["preset_label", "preset_combobox"]:
            self.tooltip = tk.Toplevel(self.shader_combobox)
            self.tooltip.overrideredirect(True)
            self.tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")

            label = tk.Label(
                self.tooltip,
                text=(
                    "Ajusta as configurações do Minecraft relacionadas\n"
                    "à performance. Configurações afetadas:\n\n"
                    "Qualidade:\n"
                    " - Distância de Renderização: 12 chunks\n"
                    " - Distãncia das sombras: 12 chunks\n"
                    " - Distãncia da Simulação: 12 chunks\n"
                    "Performance:\n"
                    " - Distância de Renderização: 8 chunks\n"
                    " - Distãncia das sombras: 8 chunks\n"
                    " - Distãncia da Simulação: 8 chunks"
                ),
                relief="flat",
                justify="left",
            )
            label.pack(ipadx=5, ipady=5)

        elif event.widget.winfo_name() in ["shader_preset_label", "shader_preset_combobox"]:
            self.tooltip = tk.Toplevel(self.shader_combobox)
            self.tooltip.overrideredirect(True)
            self.tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")

            label = tk.Label(
                self.tooltip,
                text=(
                    "Ajusta a qualidade gráfica do shader. Essa configuração pode\n"
                    "melhorar a experiência visual, mas tem um enorme impacto no\n"
                    "desempenho."
                ),
                relief="flat",
            )
            label.pack(ipadx=5, ipady=5)

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
        self.preset_combobox.config(state="readonly")
        self.shader_combobox.config(state="readonly")
        self.button_install.config(state="normal")
        self.button_cancel.config(state="disabled")

        if self.shader_combobox.get() == "Não":
            self.shader_preset_combobox.config(state="disabled")
        else:
            self.shader_preset_combobox.config(state="readonly")

    def disable(self):
        self.directory_entry.config(state="disabled")
        self.directory_button.config(state="disabled")
        self.preset_combobox.config(state="disabled")
        self.shader_combobox.config(state="disabled")
        self.shader_preset_combobox.config(state="disabled")
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

    def post_installation(self, progress_start: int, progress_end: int):
        self.update_progress(progress_start, "Configurando 'options.txt'...")
        preset = self.preset_combobox.get()
        shader = self.shader_combobox.get()
        shader_preset = self.shader_preset_combobox.get()

        options_path = os.path.join(self.directory_entry.get(), "options.txt")
        with open(options_path, "r+") as file:
            content = file.read()
            new_content = content

            new_content = re.sub(r"fullscreen:true", "fullscreen:false", new_content)
            new_content = re.sub(r"lastServer:[\.\d\:]+", "lastServer:177.137.151.231:25565", new_content)

            if preset == "Qualidade":
                new_content = re.sub(r"renderDistance:\d+", "renderDistance:12", new_content)
                new_content = re.sub(r"simulationDistance:\d+", "simulationDistance:12", new_content)
            else:
                new_content = re.sub(r"renderDistance:\d+", "renderDistance:8", new_content)
                new_content = re.sub(r"simulationDistance:\d+", "simulationDistance:8", new_content)

            file.seek(0)
            file.write(new_content)
            file.truncate()

        self.update_progress(
            progress_start + ((progress_end - progress_start) * 0.33), "Configurando 'ComplementaryUnbound_r5.3.txt'..."
        )
        complementary_config_path = os.path.join(
            self.directory_entry.get(), "shaderpacks", "ComplementaryUnbound_r5.3.txt"
        )
        if shader_preset in ["Baixa", "Média"]:
            with open(complementary_config_path, "w") as file:
                if shader_preset == "Baixa":
                    file.write("""#Thu Jan 16 14:16:59 BRT 2025
shadowDistance=96.0
FXAA_DEFINE=-1
SHADOW_QUALITY=0
LIGHTSHAFT_QUALI_DEFINE=0
BLOCK_REFLECT_QUALITY=1""")
                elif shader_preset == "Média":
                    file.write("""#Thu Jan 16 14:16:43 BRT 2025
shadowDistance=128.0
SHADOW_QUALITY=1
LIGHTSHAFT_QUALI_DEFINE=1
BLOCK_REFLECT_QUALITY=1""")
        else:
            if os.path.exists(complementary_config_path):
                os.remove(complementary_config_path)

        self.update_progress(
            progress_start + ((progress_end - progress_start) * 0.66), "Configurando 'oculus.properties'..."
        )
        config_shader_path = os.path.join(self.directory_entry.get(), "config", "oculus.properties")
        with open(config_shader_path, "r+") as file:
            content = file.read()
            new_content = content

            if shader == "Não":
                new_content = re.sub(r"enableShaders=(?:true|false)", "enableShaders=false", content)
            else:
                new_content = re.sub(r"enableShaders=(?:true|false)", "enableShaders=true", content)

            if preset == "Qualidade":
                new_content = re.sub(r"maxShadowRenderDistance=\d+", "maxShadowRenderDistance=12", new_content)
            else:
                new_content = re.sub(r"maxShadowRenderDistance=\d+", "maxShadowRenderDistance=8", new_content)

            file.seek(0)
            file.write(new_content)
            file.truncate()

        self.update_progress(progress_end, "Configurações aplicadas!")

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
                self.post_installation(90, 100)

            # Passo 2: Extraí novos arquivos
            self.update_progress(100, "Download e instalação concluídos! Você já pode fechar essa janela.")

        except Exception as error:
            self.update_progress(0, f"Falhou: {error}")

        self.thread = None
        self.enable()

    @classmethod
    def get_instance(cls):
        return cls(ThemedTk())
