#!/usr/bin/env python

import os
import re
import sys
import logging
import requests
import threading

from functools import lru_cache
from typing import Optional, Mapping, Union, Dict
from time import time, gmtime, strftime
from bs4 import BeautifulSoup as bs

from pycasso import Canvas

from pyccoma.urls import base_url, login_url, history_url, bookmark_url, purchase_url
from pyccoma.helpers import create_path, safe_filename, trunc_title
from pyccoma.utils import display_progress_bar

log = logging.getLogger(__name__)

class Scraper:
    CSRF_NAME = 'csrfmiddlewaretoken'

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Referer': '{0}?next_url=/web/'.format(login_url)
        }
        self.session = requests.session()
        self.session.verify = True
        self.__is_login = False
        self._lock = threading.Lock()
        self._etype = {
            'manga': 'V',
            'smartoon': 'E'
        }
        self._format = 'png'
        self._omit_author = False

    @property
    def manga(self) -> str:
        return self._etype['manga']

    @property
    def smartoon(self) -> str:
        return self._etype['smartoon']

    @property
    def format(self) -> str:
        return self._format

    @property
    def omit_author(self) -> bool:
        return self._omit_author

    @manga.setter
    def manga(self, value: str) -> None:
        if value in ('volume', 'episode'):
            self._etype['manga'] = value.upper()[0]
        else:
            log.error("Invalid type.")

    @smartoon.setter
    def smartoon(self, value: str) -> None:
        if value in ('volume', 'episode'):
            self._etype['smartoon'] = value.upper()[0]
        else:
            log.error("Invalid type.")

    @format.setter
    def format(self, value: str) -> None:
        if value in ('png', 'jpg', 'bmp', 'jpeg'):
            self._format = value.lower()
        else:
            log.error("Invalid format.")

    @omit_author.setter
    def omit_author(self, value: bool) -> None:
        self._omit_author = value

    def parse(self, page: str) -> str:
        return bs(page, 'html.parser')

    def parse_page(self, url: str) -> str:
        try:
            page = self.session.get(url, headers=self.headers)
            soup = self.parse(page.text)
            return soup

        except Exception:
            log.error('Error encountered: Failed to parse page')

    def get_login_status(self) -> bool:
        page = self.parse_page(login_url)
        is_login = str(page.findAll('script')[3]).split('login')[1].split(":")[1].split(",")[0].strip().title()
        return eval(is_login)

    @property
    def is_login(self) -> bool:
        return self.__is_login

    @is_login.setter
    def is_login(self, value: str) -> None:
        if type(value) is bool:
            self.__is_login = value

    def login(self, email: str, password: str) -> None:
        try:
            log.debug("Logging in as: {0}".format(email))
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
                self.is_login = True
                log.info("Successfully logged in as: {0}".format(email))
            else:
                self.is_login = False
                log.error("Failed to log in as: {0}".format(email))

        except Exception:
            log.error('Error encountered: failed to establish connection to server')
            raise SystemExit

    def get_checksum(self, img_url: str) -> str:
        return img_url.split('/')[-2]

    def get_key(self, img_url: str) -> str:
        return img_url.split('?')[1].split('&')[1].split('=')[1]

    def get_seed(self, checksum: str, expiry_key: int) -> str:
        for num in expiry_key:
            if int(num) != 0: checksum = checksum[-int(num):] + checksum[:len(checksum)-int(num)]
        return checksum

    def get_list(self, url: str) -> Mapping[int, Dict[str, bool]]:
        if url.endswith('V'):
            return self.get_volume_list(url)
        elif url.endswith('E'):
            return self.get_episode_list(url)
        else:
            log.error("Error encountered: Invalid type")

    def get_episode_list(self, url: str) -> Mapping[int, Dict[str, bool]]:
        try:
            if 'episodes?etype=E' not in url:
                log.error('Error encountered: Invalid url, unable to fetch all episode links')
            else:
                page = self.parse_page(url).find('ul', attrs={'id':'js_episodeList'})
                log.debug('Parsing episode list from {0}'.format(url))
                series_id = url.split('/')[-2]
                episode_title = [title.text for title in page.findAll('h2')]

                episode_id = [int(episode_id['data-episode_id']) for episode_id in page.select('a[data-episode_id]')]
                episode_link = ["https://piccoma.com/web/viewer/{0}/{1}".format(series_id, id) for id in episode_id]

                status = page.findAll('li', attrs={'class':'PCM-product_episodeList'})

                episodes = {
                    id: {
                        'title': title,
                        'url': link,
                        'is_free': True if 'status_free' in str(_status) else False,
                        'is_limited_read': True if 'status_waitfreeRead' in str(_status) else False,
                        'is_already_read': True if 'PCM-epList_read' in str(_status) else False,
                        'is_limited_free': True if 'status_webwaitfree' in str(_status) else False,
                        'is_purchased': True if 'status_buy' in str(_status) else False
                        }
                    for id, title, link, _status in zip(episode_id, episode_title, episode_link, status)
                }

                return episodes

        except IndexError:
            log.error('Error encountered: Invalid url, unable to fetch episode list')

        except Exception as exception:
            log.error('Error encountered: {0}'.format(exception))

    def get_volume_list(self, url: str) -> Mapping[int, Dict[str, bool]]:
        try:
            if 'episodes?etype=V' not in url:
                log.error('Error encountered: Invalid url, unable to fetch all volume links')
            else:
                page = self.parse_page(url).find('ul', attrs={'id':'js_volumeList'})
                log.debug('Parsing volume list from {0}'.format(url))
                series_id = url.split('/')[-2]
                volume_title = [title.text for title in page.findAll('h2')]

                volume_id = [[volume_id['data-episode_id'] for volume_id in links.select('a[data-episode_id]')]
                             for links in page.findAll('div', attrs={'class':'PCM-prdVol_btns'})]
                volume_link = ["https://piccoma.com/web/viewer/{0}/{1}".format(
                    series_id,
                    id[0] if len(id) == 1 else id[1]
                ) for id in volume_id]

                status = page.findAll('li', attrs={'class':'PCM-prdVol'})

                volumes = {
                    id + 1: {
                        'title': title,
                        'url': link,
                        'is_free': True if 'status_free' in str(_status) else False,
                        'is_limited_read': True if 'status_waitfreeRead' in str(_status) else False,
                        'is_already_read': True if 'PCM-volList_read' in str(_status) else False,
                        'is_limited_free': True if 'status_webwaitfree' in str(_status) else False,
                        'is_purchased': True if '読む' in str(_status) else False
                    }
                    for id, (title, link, _status) in enumerate(
                        zip(volume_title, volume_link, status)
                    )
                }

                return volumes

        except IndexError:
            log.error('Error encountered: Invalid url, unable to fetch volume list')

        except Exception as exception:
            log.error('Error encountered: {0}'.format(exception))

    @lru_cache
    def get_history(self) -> Dict[str, str]:
        return self.get_bdata(history_url)

    @lru_cache
    def get_bookmark(self) -> Dict[str, str]:
        return self.get_bdata(bookmark_url)

    @lru_cache
    def get_purchase(self) -> Dict[str, str]:
        return self.get_bdata(purchase_url)

    def get_bdata(self, url: str) -> Dict[str, str]:
        if self.is_login:
            page = self.parse_page(url).find('section', attrs={'class':'PCM-productTile'})
            product_title = [title.text for title in page.select('span') if title.text]
            product_type = [self.smartoon if 'PCM-stt_smartoon' in str(_type) else self.manga
                            for _type in [type for type in page.findAll('li', attrs={'class':'PCM-slotProducts_list'})]]
            product_link = [base_url + url.attrs['href'] + "/episodes?etype="
                            for url in page.select('a', attrs={'class':'PCM-product'})]
            items = {title: link + type for title, link, type in zip(product_title, product_link, product_type)}
            return items
        else:
            log.error("You must be logged in to access your library.")

    def get_pdata(self, url: str) -> Dict[str, bool]:
        try:
            if 'viewer' in url:
                page = self.parse_page(url)

                log.debug('Parsing data from {0}'.format(url))

                title = safe_filename(page.find('title').text.split("｜")[1])
                script = page.findAll('script')[5]

                ep_title = str(script).split('title')[1].split("'")[2].strip()
                is_scrambled = str(script).split('isScrambled')[1].split(":")[1].split(",")[0].strip().title()
                links = str(script).split("'img'")[1]
                images = ["https://" + image.split("',")[0].strip() for image in links.split("{'path':'//") if "'," in image]
                pdata = {
                    'title': (title if not self.omit_author else trunc_title(title)),
                    'ep_title': ep_title,
                    'is_scrambled': eval(is_scrambled),
                    'img': images
                }

                return pdata

            else:
                log.error('Error encountered: Invalid url, unable to fetch page data')

        except Exception:
            log.error('Error encountered: Unable to fetch page data on {0}'.format(url))

    def get_image(self, img_url: str, seed: str, output: str) -> None:
        try:
            with self._lock:
                img = requests.get(img_url, headers=self.headers, stream=True)
            if img.status_code == 200:
                if seed.isupper():
                    Canvas(img.raw, 50, seed).export(path=output)
                else:
                    with open(output, 'wb') as handler:
                        for chunk in img.iter_content(1024):
                            if chunk:
                                handler.write(chunk)

                log.info('Downloading: {0}'.format(output))
            else:
                log.error('Failed to download: {0}'.format(img_url))

        except Exception:
            log.error('Failed to write {0}'.format(output))

    def fetch(self, url: str, path: Optional[str] = None) -> None:
        try:
            pdata = self.get_pdata(url)
            if not pdata and not self.is_login:
                log.error('Restricted content: Login required')
            elif not pdata and self.is_login:
                log.error('Restricted content: Coins required for access')
            else:
                sys.stdout.write(f"\nTitle: {pdata['title']}\nEpisode: {pdata['ep_title']}\n")

                if not path:
                    path = os.path.join(os.getcwd(), 'extract')

                tail_path = '{0}/{1}/'.format(pdata['title'], pdata['ep_title'])
                head_path = os.path.join(path, tail_path)
                dest_path = create_path(head_path)

                start_time = time()
                self._fetch(pdata['img'], dest_path)

                with self._lock:
                    exec_time = strftime("%H:%M:%S", gmtime(time() - start_time))
                    sys.stdout.write(f"\nElapsed time: {exec_time}\n")
                    sys.stdout.flush()

        except TypeError:
            log.error('Error encountered: Unable to fetch episode')

        except Exception as exception:
            log.error('Error encountered: {0}'.format(exception))

        except KeyboardInterrupt:
            pass

    def _fetch(self, episode: list, path: str) -> None:
        try:
            count = 0
            episode_size = len(episode)
            checksum = self.get_checksum(episode[0])
            key = self.get_key(episode[0])
            seed = self.get_seed(checksum, key)

            for page, url in enumerate(episode):
                output = os.path.join(path, f"{page + 1}.{self.format}")

                if os.path.exists(output):
                    log.debug('Skipping download, file already exists: {0}'.format(output))
                else:
                    download = threading.Thread(target=self.get_image, args=(url, seed, output))
                    download.start()
                with self._lock:
                    count += 1
                    display_progress_bar(count, episode_size)

        except Exception:
            log.error("Error encountered: Unable to fetch episode")
