"""Extraction du texte des pièces justificatives scannées (Tesseract, en local).

Tesseract lit uniquement le texte d'une image : il ne compare ni visages ni empreintes.
En revanche, l'image transmise peut contenir une photo ; l'interface demande donc de
ne transmettre ni photo d'identité ni empreinte, et l'image n'est jamais conservée.
"""
from __future__ import annotations

import io
from typing import Optional

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None


def extract_text(contenu: bytes, langue: str = "fra+eng") -> Optional[str]:
    """Renvoie le texte lu dans l'image, ou None si l'OCR est indisponible ou échoue."""
    if pytesseract is None or Image is None:
        print("[OCR] Tesseract ou Pillow non installés : OCR indisponible.")
        return None
    try:
        image = Image.open(io.BytesIO(contenu))
        texte = pytesseract.image_to_string(image, lang=langue)
    except Exception as erreur:  # image illisible ou binaire Tesseract absent
        print(f"[OCR] Échec de l'extraction : {type(erreur).__name__}")
        return None
    return texte.strip() or None
