import sys
import logging

from time import sleep
from typing import Callable
from functools import wraps
from requests import Response

log = logging.getLogger(__name__)

def get_checksum(img_url: str) -> str:
    return img_url.split('/')[-2]

def get_key(img_url: str) -> str:
    return img_url.split('?')[1].split('&')[1].split('=')[1]

def get_seed(checksum: str, expiry_key: int) -> str:
    for num in expiry_key:
        if int(num) != 0: checksum = checksum[-int(num):] + checksum[:len(checksum)-int(num)]
    return checksum

def retry(retries: int, interval: int) -> Callable[..., Response]:
    def _retry(func):
        @wraps(func)
        def download(*args, **kwargs):
            try:
                for retry in range(1, retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as err:
                        if retry == retries:
                            raise Exception from err
                        else:
                            log.error(f"Retrying ({retry}/{retries}) {err}")
                            sleep(interval)
            except Exception:
                log.error(f"Maximum retries exceeded ({retry}/{retries})")
        return download
    return _retry

def display_progress_bar(
    file_count: int,
    total_count: int,
    char: str = "█",
    scale: float = 0.55
) -> None:
    max_width = int(100 * scale)
    filled = int(round(max_width * file_count / float(total_count)))
    remaining = max_width - filled
    progress_bar = char * filled + " " * remaining
    percent = round(100.0 * file_count / float(total_count), 1)
    text = f"  |{progress_bar}| {percent}% ({file_count}/{total_count})\r"
    sys.stdout.write(text)
