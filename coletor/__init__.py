"""Coletor Fiscalizaí — descoberta de dados públicos em portais de transparência."""

from .discovery import discover
from .fetch import fetch
from .fingerprint import detect
from .report import build_report, to_markdown

__all__ = ["detect", "discover", "fetch", "build_report", "to_markdown"]
__version__ = "0.1.0"
