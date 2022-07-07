import sys
import logging

from time import sleep
from typing import Callable
from functools import wraps
from requests import Response

log = logging.getLogger(__name__)


def retry() -> Callable[..., Response]:
    def _retry(func):
        @wraps(func)
        def download(self, *args, **kwargs):
            with self._lock:
                try:
                    for retry in range(1, self.retry_count + 1):
                        try:
                            return func(self, *args, **kwargs)
                        except Exception as err:
                            if retry == self.retry_count:
                                raise Exception from err
                            else:
                                log.error(
                                    f"Retrying ({retry}/{self.retry_count}) "
                                    f"{err}"
                                )
                                sleep(self.retry_interval)
                except Exception:
                    log.error(
                        f"Maximum retries exceeded ({retry}/"
                        f"{self.retry_count})"
                    )
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
