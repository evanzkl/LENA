from __future__ import annotations

# ---------------------------------------------------------------------------
# Stub Spanish translator.
# Replace the ENGLISH_TO_SPANISH dictionary or swap out translate_text() with
# a real translation API (e.g. Google Translate, DeepL) when ready.
# ---------------------------------------------------------------------------

ENGLISH_TO_SPANISH: dict[str, str] = {
    "a": "un",
    "an": "un",
    "the": "el",
    "and": "y",
    "or": "o",
    "is": "es",
    "are": "son",
    "was": "fue",
    "be": "ser",
    "in": "en",
    "on": "en",
    "at": "en",
    "to": "a",
    "of": "de",
    "for": "para",
    "with": "con",
    "by": "por",
    "from": "de",
    "this": "este",
    "that": "ese",
    "it": "ello",
    "not": "no",
    "no": "no",
    "yes": "sí",
    "hello": "hola",
    "world": "mundo",
    "open": "abierto",
    "closed": "cerrado",
    "exit": "salida",
    "entrance": "entrada",
    "stop": "alto",
    "go": "vamos",
    "sale": "venta",
    "price": "precio",
    "new": "nuevo",
    "free": "gratis",
    "now": "ahora",
    "buy": "comprar",
    "store": "tienda",
    "restaurant": "restaurante",
    "hotel": "hotel",
    "please": "por favor",
    "thank": "gracias",
    "you": "tú",
    "street": "calle",
    "road": "camino",
    "city": "ciudad",
    "building": "edificio",
    "floor": "piso",
    "door": "puerta",
    "window": "ventana",
    "room": "habitación",
    "phone": "teléfono",
    "email": "correo",
    "address": "dirección",
    "welcome": "bienvenido",
    "caution": "precaución",
    "warning": "advertencia",
    "danger": "peligro",
    "emergency": "emergencia",
    "parking": "estacionamiento",
    "menu": "menú",
    "special": "especial",
    "daily": "diario",
    "today": "hoy",
    "water": "agua",
    "food": "comida",
    "drink": "bebida",
    "coffee": "café",
    "tea": "té",
    "hot": "caliente",
    "cold": "frío",
    "large": "grande",
    "small": "pequeño",
    "medium": "mediano",
    "open": "abierto",
    "hours": "horas",
    "monday": "lunes",
    "tuesday": "martes",
    "wednesday": "miércoles",
    "thursday": "jueves",
    "friday": "viernes",
    "saturday": "sábado",
    "sunday": "domingo",
}


def _translate_word(word: str) -> str:
    """Translate a single word; preserves punctuation attached to the word."""
    # Strip trailing/leading punctuation for lookup, reattach afterwards
    stripped = word.strip(".,!?;:\"'()")
    prefix = word[: len(word) - len(word.lstrip("\"'("))]
    suffix = word[len(word.rstrip(".,!?;:\"')"))]  if word != word.rstrip(".,!?;:\"')") else ""
    translated = ENGLISH_TO_SPANISH.get(stripped.lower(), stripped)
    # Preserve original capitalisation style
    if stripped.isupper():
        translated = translated.upper()
    elif stripped.istitle():
        translated = translated.capitalize()
    return prefix + translated + suffix


def translate_text(text: str, target_lang: str = "es") -> str:
    """
    Stub translation: maps known English words to Spanish equivalents.
    Unknown words are kept as-is.  Swap this function body for a real
    translation API call when ready.
    """
    words = text.split()
    return " ".join(_translate_word(w) for w in words)
