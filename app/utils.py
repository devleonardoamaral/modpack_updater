import os
import sys
import platform


def default_path():
    """Retorna o caminho padrão do Minecraft baseado no sistema operacional."""
    system = platform.system()

    if system == "Windows":
        appdata = os.getenv("APPDATA")

        if not appdata:
            raise EnvironmentError("A variável APPDATA não está definida.")

        return os.path.join(appdata, ".minecraft")

    elif system == "Darwin":
        return os.path.expanduser("~/Library/Application Support/minecraft")

    else:
        return os.path.expanduser("~/.minecraft")


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, os.path.normpath(relative_path))
