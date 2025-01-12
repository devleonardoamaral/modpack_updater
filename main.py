import io
import os
import time
import shutil
import zipfile
import platform
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import http.client
from urllib.parse import urlparse


def get_default_path():
    """Retorna o caminho padrão do Minecraft baseado no sistema operacional."""
    if platform.system() == "Windows":
        return os.path.join(os.getenv("APPDATA", ""), ".minecraft")
    elif platform.system() == "Darwin":  # macOS
        return os.path.expanduser("~/Library/Application Support/minecraft")
    else:  # Assume Linux ou outros sistemas Unix-like
        return os.path.expanduser("~/.minecraft")


def remove_old_files(dest_dir):
    """Remove a pasta 'mods' se existir."""
    mods_dir = os.path.join(dest_dir, "mods")
    if os.path.exists(mods_dir):
        shutil.rmtree(mods_dir)
    else:
        os.makedirs(dest_dir, exist_ok=True)


def download_zip(repo_url):
    """Baixa o arquivo ZIP do repositório do GitHub sem usar requests."""
    # Parse da URL
    parsed_url = urlparse(repo_url)

    # Estabelecendo a conexão com o servidor
    connection = http.client.HTTPSConnection(parsed_url.netloc)

    # Requisição para a URL (usando GET)
    connection.request("GET", parsed_url.path)

    # Obtendo a resposta
    response = connection.getresponse()

    # Verificando redirecionamento (302)
    if response.status == 302:
        # Se houver redirecionamento, pega o novo local
        new_location = response.getheader("Location")
        connection.close()
        return download_zip(new_location)  # Faz o download no novo local

    # Verificando se o status é 200 (OK)
    if response.status == 200:
        return response
    else:
        raise Exception(f"Falha no download: {response.status}")


def extract_zip(zip_file, dest_dir):
    """Extrai os arquivos do ZIP para o diretório de destino."""
    with zipfile.ZipFile(zip_file) as zip_file:
        for member in zip_file.namelist():
            member_path = member.split("/", 1)[-1]
            if member_path:
                destination = os.path.join(dest_dir, member_path)
                if member.endswith("/"):
                    os.makedirs(destination, exist_ok=True)
                else:
                    with open(destination, "wb") as file:
                        file.write(zip_file.read(member))


def download_github_repo(repo_url, dest_dir, progress_callback):
    """Baixa e extrai os arquivos do repositório GitHub."""
    try:
        # Passo 1: Remover arquivos antigos
        progress_callback(1, "Removendo arquivos antigos...")
        remove_old_files(dest_dir)

        # Passo 2: Baixar novos arquivos
        progress_callback(2, "Iniciando download...")
        response = download_zip(repo_url)
        temp_zip = io.BytesIO()

        total_bytes = 0  # Contador total de bytes baixados
        start_time = time.time()  # Marcar o tempo inicial
        buffer_size = 1024 * 10  # 10KB

        # Iterar sobre os chunks e calcular a velocidade de download
        while chunk := response.read(buffer_size):
            temp_zip.write(chunk)  # Escrever o chunk no buffer
            total_bytes += len(chunk)  # Incrementar o número de bytes baixados

            # Calcular a velocidade de download em megabytes por segundo
            elapsed_time = time.time() - start_time
            if elapsed_time > 0:  # Evitar divisão por zero
                speed = total_bytes / elapsed_time  # Bytes por segundo
                speed_mb = speed / (1024 * 1024)  # Converter para megabytes por segundo
                # Converter bytes baixados para MB
                total_mb = total_bytes / (1024 * 1024)  # Bytes para megabytes
                progress_callback(2, f"Baixando... {total_mb:.2f} MB baixados | {speed_mb:.2f} MB/s")

        # Passo 3: Extrair arquivos
        progress_callback(3, "Extraindo arquivos...")
        temp_zip.seek(0)
        extract_zip(temp_zip, dest_dir)

        # Passo 4: Concluído
        progress_callback(4, "Concluído!")
    except Exception as e:
        messagebox.showerror("Erro", str(e))


class GitHubDownloaderApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Instalador Última Esperança")

        self.repo_url = (
            "https://github.com/devleonardoamaral/minecraft_ultimaesperanca_modpack/archive/refs/heads/master.zip"
        )
        self.default_dir = get_default_path()

        self.entry_frame = tk.Frame(root)
        self.entry_frame.pack(pady=10)

        self.directory_label = tk.Label(self.entry_frame, text="Diretório de instalação do Minecraft:")
        self.directory_label.grid(row=0, column=0, padx=5, sticky="w")

        self.directory_entry = tk.Entry(self.entry_frame, width=50)
        self.directory_entry.insert(0, get_default_path())
        self.directory_entry.grid(row=1, column=0, padx=5)

        self.browse_button = tk.Button(self.entry_frame, text="Navegar", command=self.select_directory)
        self.browse_button.grid(row=1, column=1, padx=5)

        self.progress_label = tk.Label(root, text="Aguardando ação...")
        self.progress_label.pack(pady=5)

        self.progress_bar = ttk.Progressbar(root, length=400, mode="determinate", maximum=4)
        self.progress_bar.pack(pady=10)

        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=10)

        self.confirm_button = tk.Button(
            self.button_frame, text="Instalar/Atualizar Modpack", command=self.start_download
        )
        self.confirm_button.grid(row=0, column=0, padx=5)

        self.cancel_button = tk.Button(self.button_frame, text="Fechar", command=root.quit)
        self.cancel_button.grid(row=0, column=1, padx=5)

    def select_directory(self):
        selected_dir = filedialog.askdirectory(initialdir=self.default_dir)
        if selected_dir:
            self.directory_entry.delete(0, tk.END)
            self.directory_entry.insert(0, selected_dir)

    def start_download(self):
        dest_dir = self.directory_entry.get()
        if not dest_dir:
            messagebox.showerror(
                "Erro", "Por favor, selecione o diretório onde o Minecraft está instalado para prosseguir."
            )
            return

        self.progress_bar["value"] = 0
        self.progress_label["text"] = "Iniciando..."

        def update_progress(step, status):
            self.progress_bar["value"] = step
            self.progress_label["text"] = status
            self.root.update_idletasks()

        download_github_repo(self.repo_url, dest_dir, update_progress)
        messagebox.showinfo("Sucesso", "Download e instalação concluídos com sucesso!")


if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubDownloaderApp(root)
    root.mainloop()
