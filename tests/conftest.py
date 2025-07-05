# tests/conftest.py
import sys
import os

# Insere o diretório-pai (o root do seu projeto) no início do sys.path
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root not in sys.path:
    sys.path.insert(0, root)
