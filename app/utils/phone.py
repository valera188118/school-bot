import re


_ALLOWED_PHONE_CHARS_RE = re.compile(r"^[\d\s()+-]+$")


def normalize_phone(raw_phone: str) -> str | None:
    phone = raw_phone.strip()
    if not phone or not _ALLOWED_PHONE_CHARS_RE.fullmatch(phone):
        return None

    if phone.count("+") > 1 or ("+" in phone and not phone.startswith("+")):
        return None

    digits = re.sub(r"\D", "", phone)
    if len(digits) != 11 or digits[0] not in {"7", "8"}:
        return None

    return f"+7{digits[1:]}"
