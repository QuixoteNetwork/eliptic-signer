import sys
import os

from kivy.config import Config
from kivy.utils import platform

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Solo tiene sentido en escritorio
if platform != "android":
    Config.set("kivy", "window_icon", resource_path("assets/logo.ico"))

from kivy.app import App
from kivy.core.window import Window

from ui.main_screen import MainScreen


class ElipticSigner(App):
    def build(self):
        if platform != "android":
            Window.size = (400, 600)

        self.title = "Eliptic Signer: Ed25519 Sign & Verify"
        return MainScreen()


if __name__ == "__main__":
    ElipticSigner().run()