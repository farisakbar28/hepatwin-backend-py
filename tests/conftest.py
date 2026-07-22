"""Konfigurasi pytest bersama.

Menyisipkan root repo ke sys.path supaya test bisa `from app... import ...`
tanpa instalasi package. Konsisten dengan cara app/main.py mengatur path.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
