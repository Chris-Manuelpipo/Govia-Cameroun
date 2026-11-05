"""Configuration des tests : base réelle, sans ChromaDB ni LLM, journal isolé."""
import os
import sys
import tempfile
from pathlib import Path

os.environ["GOVIA_DISABLE_CHROMA"] = "1"
os.environ["GOVIA_USE_LLM"] = "0"
os.environ["GOVIA_AUDIT_LOG"] = str(Path(tempfile.mkdtemp()) / "audit.jsonl")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
