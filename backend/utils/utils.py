import re

def sanitize_json(text: str) -> str:
    text = text.replace("'", '"')
    text = re.sub(r",\s*([}\]])", r"\1", text)
    return text
