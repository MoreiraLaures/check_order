"""
Resolução de caminhos compatível com execução normal (dev) e empacotada (.exe).

Dois contextos distintos:
  BUNDLE_DIR  — onde os assets embutidos (templates) são extraídos pelo PyInstaller
                → sys._MEIPASS quando frozen, raiz do projeto em dev
  RUNTIME_DIR — onde o usuário tem seus arquivos (.env, response/)
                → pasta do .exe quando frozen, raiz do projeto em dev
"""
import os
import sys


def _bundle_dir() -> str:
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _runtime_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BUNDLE_DIR: str = _bundle_dir()
RUNTIME_DIR: str = _runtime_dir()
