import os
import re
import logging

from typing import Optional

log = logging.getLogger(__name__)


def safe_filename(title: str) -> str:
    pattern = re.compile(r'[?"|:<>*/\\]', flags=re.VERBOSE)
    return pattern.sub("", str(title)).strip()


def create_path(path: str) -> str:
    if path:
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

    if os.path.exists(path):
        log.warning(f"Path already exists: {path}")
    else:
        log.debug(f"Creating path: {path}")

    os.makedirs(path, exist_ok=True)
    return path


def create_tags(text: str) -> str:
    identifiers = [
        r'is_read_for_free',
        r"is_wait_until_free",
        r"is_already_read",
        r"is_free",
        r"is_zero_plus",
        r"is_purchased",
    ]
    identifiers = "|".join(identifiers)
    pattern = r"(\b" + identifiers + r")\b(\s*(" + identifiers + r")\b)*"

    regex = re.compile(pattern, re.I)
    tags = regex.sub(r"episode['\1']", text.strip('"'))
    return tags


def trunc_title(title: str) -> str:
    return re.sub(r"\((?:[^)(]|\([^)(]*\))*\)", "", title)


def pad_string(
    text: str,
    length: Optional[int] = 0,
    padding: Optional[str] = "0"
) -> str:
    if len(text) <= length:
        for pad in range(length-len(text)):
            padding += "0"
        text = f"{padding}{text}"
    return text
