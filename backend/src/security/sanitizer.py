import bleach


ALLOWED_TAGS = []


def sanitize_text(value: str):

    if not value:
        return ""

    return bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        strip=True
    )