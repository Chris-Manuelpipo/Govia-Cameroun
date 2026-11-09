"""Configuration des tests : base réelle, sans LLM, journal isolé. Sans ChromaDB, sauf si GOVIA_TEST_CHROMA=1."""
import os
import sys
import tempfile
from pathlib import Path

if not os.getenv("GOVIA_TEST_CHROMA"):
    os.environ["GOVIA_DISABLE_CHROMA"] = "1"
os.environ["GOVIA_USE_LLM"] = "0"
os.environ["GOVIA_AUDIT_LOG"] = str(Path(tempfile.mkdtemp()) / "audit.jsonl")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
