#!/usr/bin/env python

import os
import sys
import logging
import zipfile
import requests

from lxml import html
from urllib.parse import parse_qs
from abc import ABCMeta, abstractmethod

from zipfile import ZipFile
from threading import Thread, Lock
from time import time, gmtime, strftime
from requests import get, session, Response
from typing import Optional, Mapping, Union, Dict, List
from functools import lru_cache

from pycasso import Canvas

from pyccoma.exceptions import PyccomaError, PageError
from pyccoma.helpers import create_path, pad_string, safe_filename
from pyccoma.utils import display_progress_bar, retry
from pyccoma.dd import dd

log = logging.getLogger(__name__)


class Scraper(metaclass=ABCMeta):
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/92.0.4515.107 Safari/537.36',
            'Referer': 'https://piccoma.com/'
        }
        self.session = session()
        self.session.verify = True
        self.__is_login = False
        self._lock = Lock()
        self._format = "png"
        self._archive = False
        self._omit_author = False
        self._retry_count = 3
        self._retry_interval = 1
        self._zeropad = 0

    @property
    def format(self) -> str:
        return self._format

    @property
    def archive(self) -> bool:
        return self._archive

    @property
    def omit_author(self) -> bool:
        return self._omit_author

    @property
    def retry_count(self) -> int:
        return self._retry_count

    @property
    def retry_interval(self) -> int:
        return self._retry_interval

    @property
    def zeropad(self) -> int:
        return self._zeropad

    @format.setter
    def format(self, value: str) -> None:
        if value in ('png', 'jpg', 'gif', 'bmp', 'jpeg'):
            self._format = value.lower()
        else:
            raise ValueError("Invalid format.")

    @archive.setter
    def archive(self, value: bool) -> None:
        self._archive = value

    @omit_author.setter
    def omit_author(self, value: bool) -> None:
        self._omit_author = value

    @retry_count.setter
    def retry_count(self, value: int) -> None:
        self._retry_count = value

    @retry_interval.setter
    def retry_interval(self, value: int) -> None:
        self._retry_interval = value

    @zeropad.setter
    def zeropad(self, value: int) -> None:
        self._zeropad = value

    @property
    def _is_login(self) -> bool:
        return self.__is_login

    @_is_login.setter
    def _is_login(self, value: bool) -> None:
        self.__is_login = value

    def parse(self, page: str) -> html:
        return html.fromstring(page)

    def parse_page(self, url: str) -> html:
        try:
            page = self.session.get(url, headers=self.headers)
            page.raise_for_status()
            soup = self.parse(page.text)
            return soup

        except requests.exceptions.HTTPError:
            raise PageError(url)
        except requests.exceptions.ConnectionError:
            raise PageError(url)
        except Exception:
            log.error("Failed to parse page.")

    @abstractmethod
    def login(self, email: str, password: str) -> None:
        pass

    @abstractmethod
    def get_list(self, url: str) -> Mapping[int, Dict[str, bool]]:
        pass

    @abstractmethod
    def get_episode_list(
        self,
        url: str
    ) -> Mapping[int, Dict[str, Union[str, bool]]]:
        pass

    @abstractmethod
    def get_bdata(self, url: str) -> Dict[str, str]:
        pass

    @abstractmethod
    def get_pdata(self, url: str) -> Dict[str, Union[str, bool]]:
        pass

    @retry()
    def get_img(self, img_url: str) -> Response:
        try:
            img = get(img_url, headers=self.headers, stream=True)
            return img
        except requests.exceptions.ConnectionError:
            raise Exception(img_url)

    def download(self, img_url: str, seed: str, output: str) -> None:
        try:
            img = self.get_img(img_url)

            if seed.isupper():
                Canvas(img.raw, (50, 50), dd(seed)).export(
                    mode="scramble",
                    path=output,
                    format=self.format
                )
            else:
                with open(f"{output}.{self.format}", 'wb') as handler:
                    for chunk in img.iter_content(1024):
                        if chunk:
                            handler.write(chunk)

        except Exception as err:
            log.error(f"Unable to download image. {err}")
        except KeyboardInterrupt:
            pass

    def compress(
        self,
        img_url: str,
        seed: str,
        page: str,
        file: ZipFile
    ) -> None:
        try:
            img = self.get_img(img_url)

            if seed.isupper():
                img = Canvas(img.raw, (50, 50), dd(seed)).export(
                    mode="scramble",
                    format=self.format
                )
                img = img.getvalue()
            else:
                img = img.content

            with self._lock:
                file.writestr(page, img)

        except Exception as err:
            log.error(f"Unable to download image. {err}")
        except KeyboardInterrupt:
            pass

    def fetch(self, url: str, path: Optional[str] = None) -> None:
        try:
            pdata = self.get_pdata(url)
            sys.stdout.write(
                f"\nTitle: {pdata['title']}\n"
                f"Episode: {pdata['ep_title']}\n"
            )

            if not path:
                path = os.path.join(os.getcwd(), 'extract')

            start_time = time()
            self._fetch(pdata['img'], pdata['title'], pdata['ep_title'], path)

            with self._lock:
                exec_time = strftime("%H:%M:%S", gmtime(time() - start_time))
                sys.stdout.write(f"\nElapsed time: {exec_time}\n\n")
                sys.stdout.flush()

        except TypeError:
            log.error("Unable to fetch episode.")
        except IndexError:
            log.error(f"Unable to access page on {url}")
        except Exception as err:
            raise PyccomaError(err)
        except KeyboardInterrupt:
            pass

    def _fetch(
        self,
        episode: List[str],
        title: str,
        ep_title: str,
        path: str
    ) -> None:
        try:
            count = 0
            episode_size = len(episode)
            checksum = self.get_checksum(episode[0])
            key = self.get_key(episode[0])
            seed = self.get_seed(checksum, key)
            title = safe_filename(title)
            ep_title = safe_filename(ep_title)

            if not self.archive:
                head_path = os.path.join(path, f"{title}/{ep_title}/")
                path = create_path(head_path)
            else:
                head_path = os.path.join(path, f"{title}_{ep_title}.cbz")
                path = create_path(path)

                if os.path.exists(head_path):
                    log.warning(f"File already exists: {head_path}")

                file = ZipFile(head_path, "a", zipfile.ZIP_DEFLATED, False)

            for page, url in enumerate(episode):
                output = os.path.join(
                    path,
                    page := pad_string(str(page + 1), length=self.zeropad)
                )

                if not self.archive and os.path.exists(file_name := f"{output}.{self.format}"):  # noqa:E501
                    log.debug(f"File already exists: {file_name}")
                elif self.archive and (file_name := f"{page}.{self.format}") in file.namelist():  # noqa:E501
                    log.debug(f"File already exists: {file_name}")
                else:
                    if self.archive:
                        fetch = Thread(
                            target=self.compress,
                            args=(url, seed, file_name, file)
                        )
                    else:
                        fetch = Thread(
                            target=self.download,
                            args=(url, seed, output)
                        )
                    fetch.start()

                with self._lock:
                    count += 1
                    display_progress_bar(count, episode_size)

        except Exception as err:
            log.error(f"Unable to fetch episode. {err}")
        except KeyboardInterrupt:
            pass

    @abstractmethod
    def get_checksum(img_url: str) -> str:
        pass

    def get_key(self, img_url: str) -> str:
        return ' '.join(parse_qs(img_url)['expires'])

    def get_seed(self, checksum: str, expiry_key: int) -> str:
        for num in expiry_key:
            if int(num) != 0:
                checksum = checksum[-int(num):] + checksum[:len(checksum)-int(num)]
        return checksum

    @abstractmethod
    @lru_cache
    def get_history(self) -> Dict[str, str]:
        pass

    @abstractmethod
    @lru_cache
    def get_bookmark(self) -> Dict[str, str]:
        pass

    @abstractmethod
    @lru_cache
    def get_purchase(self) -> Dict[str, str]:
        pass
