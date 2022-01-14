#!/usr/bin/env python

import os
import re
import sys
import zipfile
import logging
import requests
import threading

from functools import lru_cache
from bs4 import BeautifulSoup as bs
from time import time, gmtime, strftime
from requests import get, session, Response
from typing import Optional, Mapping, Union, Dict, List

from pycasso import Canvas

from pyccoma.exceptions import PyccomaError, PageError, LoginError
from pyccoma.urls import (
    base_url,
    login_url,
    history_url,
    bookmark_url,
    purchase_url
)
from pyccoma.helpers import (
    create_path,
    safe_filename,
    trunc_title,
    valid_url,
    pad_string
)
from pyccoma.utils import (
    display_progress_bar,
    get_checksum,
    get_seed,
    get_key,
    retry
)

log = logging.getLogger(__name__)

class Scraper:
    CSRF_NAME = 'csrfmiddlewaretoken'

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/92.0.4515.107 Safari/537.36',
            'Referer': '{0}?next_url=/web/'.format(login_url)
        }
        self.session = session()
        self.session.verify = True
        self.__is_login = False
        self._lock = threading.Lock()
        self._etype = {
            'manga': 'V',
            'smartoon': 'E',
            'novel': 'E'
        }
        self._format = 'png'
        self._archive = False
        self._omit_author = False
        self._retry_count = 3
        self._retry_interval = 1
        self._zeropad = 0

    @property
    def manga(self) -> str:
        return self._etype['manga']

    @property
    def smartoon(self) -> str:
        return self._etype['smartoon']

    @property
    def novel(self) -> str:
        return self._etype['novel']

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

    @manga.setter
    def manga(self, value: str) -> None:
        if value in ('volume', 'episode'):
            self._etype['manga'] = value.upper()[0]
        else:
            raise ValueError("Invalid type.")

    @smartoon.setter
    def smartoon(self, value: str) -> None:
        if value in ('volume', 'episode'):
            self._etype['smartoon'] = value.upper()[0]
        else:
            raise ValueError("Invalid type.")

    @novel.setter
    def novel(self, value: str) -> None:
        if value in ('volume', 'episode'):
            self._etype['novel'] = value.upper()[0]
        else:
            raise ValueError("Invalid type.")

    @format.setter
    def format(self, value: str) -> None:
        if value in ('png', 'gif', 'bmp', 'jpeg'):
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

    def parse(self, page: str) -> str:
        return bs(page, 'html.parser')

    def parse_page(self, url: str) -> str:
        try:
            page = self.session.get(url, headers=self.headers)
            page.raise_for_status()
            soup = self.parse(page.text)
            return soup

        except requests.exceptions.HTTPError:
            raise PageError(url)
        except Exception:
            log.error(f"Failed to parse page.")

    def get_login_status(self) -> bool:
        page = self.parse_page(login_url)
        is_login = str(page.findAll('script')[3]).split('login')[1].split(":")[1].split(",")[0].strip().title()
        return eval(is_login)

    @property
    def _is_login(self) -> bool:
        return self.__is_login

    @_is_login.setter
    def _is_login(self, value: bool) -> None:
        self.__is_login = value

    def login(self, email: str, password: str) -> None:
        try:
            log.debug(f"Logging in as {email}")
            session = self.session.get(login_url, headers=self.headers)
            csrf = self.parse(session.text).find('input', attrs={'name': self.CSRF_NAME})['value']

            params = {
                self.CSRF_NAME: csrf,
                'next_url': '/web/',
                'email': email,
                'password': password
            }
            self.session.post(
                login_url,
                data=params,
                cookies=session.cookies,
                headers=self.headers
            )

            if self.get_login_status():
                self._is_login = True
                log.info(f"Successfully logged in as {email}")
            else:
                self._is_login = False
                log.error(f"Failed to log in as {email}")

        except Exception:
            raise SystemExit("Failed to establish connection to server.")

    def get_list(self, url: str) -> Mapping[int, Dict[str, bool]]:
        if url.endswith('V'):
            return self.get_volume_list(url)
        elif url.endswith('E'):
            return self.get_episode_list(url)
        else:
            raise ValueError("Invalid input.")

    def get_episode_list(self, url: str) -> Mapping[int, Dict[str, Union[str, bool]]]:
        try:
            url = self.get_valid_url(url, 1)
            page = self.parse_page(url).find('ul', attrs={'id':'js_episodeList'})
            log.debug(f"Parsing episode list from {url}")
            series_id = url.split('/')[-2]
            episode_title = [title.text for title in page.findAll('h2')]

            episode_id = [
                int(episode_id['data-episode_id'])
                for episode_id in page.select('a[data-episode_id]')
            ]
            episode_link = [
                "https://piccoma.com/web/viewer/{0}/{1}"
                .format(series_id, id) for id in episode_id
            ]

            status = page.findAll('li', attrs={'class':'PCM-product_episodeList'})

            episodes = {
                id: {
                    'title': title,
                    'url': link,
                    'is_free': True if '_free' in str(_status) else False,
                    'is_zero_plus': True if '_zeroPlus' in str(_status) else False,
                    'is_limited_read': True if '_waitfreeRead' in str(_status) else False,
                    'is_already_read': True if '_read' in str(_status) else False,
                    'is_limited_free': True if '_webwaitfree' in str(_status) else False,
                    'is_purchased': True if '_buy' in str(_status) else False
                }
                for id, title, link, _status in zip(episode_id, episode_title, episode_link, status)
            }

            if not episodes:
                log.debug(f"No episodes found on {url}")

            return episodes

        except ValueError:
            log.error("Invalid url, unable to fetch episode list.")
        except AttributeError:
            raise PageError(url)
        except Exception as err:
            raise PyccomaError(err)

    def get_volume_list(self, url: str) -> Mapping[int, Dict[str, Union[str, bool]]]:
        try:
            url = self.get_valid_url(url, 2)
            page = self.parse_page(url).find('ul', attrs={'id':'js_volumeList'})
            log.debug(f"Parsing volume list from {url}")
            series_id = url.split('/')[-2]
            volume_title = [title.text for title in page.findAll('h2')]

            volume_id = [
                [volume_id['data-episode_id'] for volume_id in links.select('a[data-episode_id]')]
                for links in page.findAll('div', attrs={'class':'PCM-prdVol_btns'})
            ]
            volume_link = [
                "https://piccoma.com/web/viewer/{0}/{1}"
                .format(series_id, id[0]) for id in volume_id
            ]

            status = page.findAll('li', attrs={'class':'PCM-prdVol'})

            volumes = {
                id + 1: {
                    'title': title,
                    'url': link,
                    'is_free': True if '_campaign_free' in str(_status) else False,
                    'is_limited_read': True if '_read' and '_campaign_free' in str(_status) else False,
                    'is_already_read': True if '_read' in str(_status) else False,
                    'is_limited_free': True if '_campaign_free' in str(_status) else False,
                    'is_purchased': True if '_read' in str(_status) else False
                }
                for id, (title, link, _status) in enumerate(zip(volume_title, volume_link, status))
            }

            if not volumes:
                log.debug(f"No volumes found on {url}")

            return volumes

        except ValueError:
            log.error("Invalid url, unable to fetch volume list.")
        except AttributeError:
            raise PageError(url)
        except Exception as err:
            raise PyccomaError(err)

    @lru_cache
    def get_history(self) -> Dict[str, str]:
        if self._is_login:
            return self.get_bdata(history_url)
        else:
            raise LoginError

    @lru_cache
    def get_bookmark(self) -> Dict[str, str]:
        if self._is_login:
            return self.get_bdata(bookmark_url)
        else:
            raise LoginError

    @lru_cache
    def get_purchase(self) -> Dict[str, str]:
        if self._is_login:
            return self.get_bdata(purchase_url)
        else:
            raise LoginError

    @staticmethod
    def get_valid_url(url: str, level: Optional[int] = None) -> str:
        if not valid_url(url, level):
            raise ValueError("Invalid url.")
        return url

    def get_bdata(self, url: str) -> Dict[str, str]:
        try:
            page = self.parse_page(url).find('section', attrs={'class':'PCM-productTile'})
            product_title = [title.text for title in page.select('span') if title.text]
            product_type = [self.smartoon if 'PCM-stt_smartoon' in str(_type)
                else self.novel if 'PCM-stt_novel' in str(_type) else self.manga
                for _type in [type for type in page.findAll('li', attrs={'class':'PCM-slotProducts_list'})]]
            product_link = [base_url + url.attrs['href'] + "/episodes?etype="
                for url in page.select('a', attrs={'class':'PCM-product'})]
            items = {title: link + type for title, link, type in zip(product_title, product_link, product_type)}
            return items

        except Exception:
            log.error("Failed to parse library.")

    def get_pdata(self, url: str) -> Dict[str, Union[str, bool]]:
        try:
            url = self.get_valid_url(url, 0)
            page = self.parse_page(url)

            log.info(f"Parsing data from {url}")

            title = safe_filename(page.find('title').text.split("｜")[1])
            ep_title = str(page).split("'title'")[1].split("'")[1].strip()
            is_scrambled = str(page).split("'isScrambled'")[1].split(":")[1].split(",")[0].strip().title()
            links = str(page).split("'img'")[1]
            images = ["https://" + image.split("',")[0].strip() for image in links.split("{'path':'//") if "'," in image]
            pdata = {
                'title': (title if not self.omit_author else trunc_title(title)),
                'ep_title': ep_title,
                'is_scrambled': eval(is_scrambled),
                'img': images
            }

            return pdata

        except TypeError or IndexError:
            log.error("Unable to fetch page data.")

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
                Canvas(img.raw, (50, 50), seed).export(
                    mode="scramble",
                    path=output,
                    format=self.format
                )
            else:
                with open(output, 'wb') as handler:
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
        path: str,
        title: str,
        ep_title: str
    ) -> None:
        try:
            img = self.get_img(img_url)

            if seed.isupper():
                img = Canvas(img.raw, (50, 50), seed).export(
                    mode="scramble",
                    format=self.format
                )
                img = img.getvalue()
            else:
                img = img.content

            archive = os.path.join(path, f"{title}_{ep_title}.cbz")

            with self._lock:
                with zipfile.ZipFile(archive, "a", zipfile.ZIP_DEFLATED, False) as file:
                    file.writestr(f"{page}.{self.format}", img)

        except Exception as err:
            log.error(f"Unable to download image. {err}")
        except KeyboardInterrupt:
            pass

    def fetch(self, url: str, path: Optional[str] = None) -> None:
        try:
            pdata = self.get_pdata(url)
            sys.stdout.write(f"\nTitle: {pdata['title']}\nEpisode: {pdata['ep_title']}\n")

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

    def _fetch(self, episode: List[str], title: str, ep_title: str, path: str) -> None:
        try:
            count = 0
            episode_size = len(episode)
            checksum = get_checksum(episode[0])
            key = get_key(episode[0])
            seed = get_seed(checksum, key)

            if not self.archive:
                head_path = os.path.join(path, f"{title}/{ep_title}/")
                path = create_path(head_path)
            else:
                path = create_path(path)

            for page, url in enumerate(episode):
                output = os.path.join(
                    path,
                    page_num := pad_string(str(page + 1), length=self.zeropad)
                )

                if os.path.exists(file_name := f"{output}.{self.format}"):
                    log.debug(f"File already exists: {file_name}")
                else:
                    if self.archive:
                        fetch = threading.Thread(
                            target=self.compress,
                            args=(url, seed, page_num, path, title, ep_title)
                        )
                    else:
                        fetch = threading.Thread(
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
