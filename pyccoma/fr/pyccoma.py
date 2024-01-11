#!/usr/bin/env python

import json
import logging
import requests
from urllib.parse import parse_qs
from typing import Mapping, Union, Dict

from pyccoma import Scraper
from pyccoma.exceptions import PyccomaError, PageError, LoginError
from pyccoma.helpers import trunc_title

from pyccoma.fr.urls import (
    base_url,
    login_url,
    api_url,
    history_url,
    bookmark_url,
    purchase_url,
)

log = logging.getLogger(__name__)


class Pyccoma(Scraper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_url = self.get_api_url()
        self.history_url = history_url % self.api_url
        self.bookmark_url = bookmark_url % self.api_url
        self.purchase_url = purchase_url % self.api_url

        self._etype = {
            "manga": "volume",
            "smartoon": "episode",
            "novel": "episode"
        }

    @property
    def manga(self) -> str:
        return self._etype['manga']

    @property
    def smartoon(self) -> str:
        return self._etype['smartoon']

    @property
    def novel(self) -> str:
        return self._etype['novel']

    @manga.setter
    def manga(self, value: str) -> None:
        if value in ('volume', 'episode'):
            self._etype['manga'] = value
        else:
            raise ValueError("Invalid type.")

    @smartoon.setter
    def smartoon(self, value: str) -> None:
        if value in ('volume', 'episode'):
            self._etype['smartoon'] = value
        else:
            raise ValueError("Invalid type.")

    @novel.setter
    def novel(self, value: str) -> None:
        if value in ('volume', 'episode'):
            self._etype['novel'] = value
        else:
            raise ValueError("Invalid type.")

    def parse_json(self, url: str) -> json:
        try:
            page = self.session.get(url, headers=self.headers)
            page.raise_for_status()
            return page.json()

        except requests.exceptions.HTTPError:
            raise PageError(url)
        except requests.exceptions.ConnectionError:
            raise PageError(url)
        except Exception:
            log.error("Failed to parse page.")

    def get_api_url(self) -> str:
        try:
            page = self.parse_page(base_url).xpath('//script[@id = "__NEXT_DATA__"]/text()')[0]  # noqa:E501
            build_id = json.loads(page)['buildId']
            new_api_url = api_url % build_id
            return new_api_url
        except IndexError:
            raise PageError(base_url)

    def login(self, email: str, password: str) -> None:
        try:
            session = self.session.get(login_url, headers=self.headers)

            params = {
                'email': email,
                'password': password,
                'redirect': '/fr/',
            }

            login = self.session.post(
                login_url,
                data=params,
                cookies=session.cookies,
                headers=self.headers
            )

            if login.ok and not 'error' in login.text:
                self._is_login = True
                log.info(f"Successfully logged in as {email}")
            else:
                self._is_login = False
                log.error(f"Failed to log in as {email}")

        except Exception:
            raise SystemExit("Failed to establish connection to server.")

    def get_list(self, url: str) -> Mapping[int, Dict[str, bool]]:
        try:
            return self.get_episode_list(url)
        except Exception:
            raise PageError(url)

    def get_episode_list(
        self,
        url: str
    ) -> Mapping[int, Dict[str, Union[str, bool]]]:
        try:
            if 'episode' in url:
                type = 'episode'
            elif 'volume' in url:
                type = 'volume'
            else:
                raise ValueError("Invalid url.")

            product_id = url.split("/")[-1]
            url = self.api_url + f"/product/{type}/{product_id}.json?id={product_id}&pathname=%2Fproduct%2F%5Bid%5D"  # noqa:E501
            page = self.parse_json(url)['pageProps']['initialState']['episode']['episodeList']['episode_list']  # noqa:E501

            episodes = {
                id + 1: {
                    'title': episode['title'],
                    'url': f"{base_url}/viewer/{product_id}/{episode['id']}",  # noqa:E501
                    'is_free': True if 'FR01' in episode['use_type'] else False,  # noqa:E501
                    'is_read_for_free': True if 'RD01' in episode['use_type'] else False,  # noqa:E501
                    'is_wait_until_free': True if 'WF15' in episode['use_type'] else False,  # noqa:E501
                    'is_purchased': True if 'AB01' in episode['use_type'] else False,  # noqa:E501
                    'is_already_read': episode['is_read'] if self._is_login else False,  # noqa:E501
                }
                for id, episode in enumerate(page)
            }

            if not episodes:
                log.debug(f"No episodes found on {url}.")

            return episodes

        except KeyError:
            log.error("Unable to fetch list.")
        except AttributeError:
            raise PageError(url)
        except Exception as err:
            raise PyccomaError(err)

    def get_bdata(self, url: str) -> Dict[str, str]:
        try:
            page = self.parse_json(url)['pageProps']['initialState']

            if 'history' in url:
                page = page['history']['products']
            elif 'bookmark' in url:
                page = page['bookmark']['products']
            elif 'purchase' in url:
                page = page['purchase']['purchase']['products']

            product_type = [
                self.smartoon if episode['category_id'] == 2 else
                self.novel if episode['category_id'] == 3 else self.manga
                for episode in page
            ]

            items = {
                episode['title']: f"{base_url}/product/{etype}/{episode['id']}"
                for episode, etype in zip(page, product_type)
            }

            return items

        except Exception:
            log.error("Failed to parse library.")

    def get_pdata(self, url: str) -> Dict[str, Union[str, bool]]:
        try:
            log.info(f"Parsing data from {url}")
            product_id = url.split("/")[-2]
            episode_id = url.split("/")[-1]
            url = self.api_url + f"/viewer/{product_id}/{episode_id}.json?productId={product_id}&episodeId={episode_id}"  # noqa:E501
            page = self.parse_json(url)['pageProps']['initialState']

            authors = ' '.join([author['name'] for author in page['productDetail']['productDetail']['product']['authors']])  # noqa:E501
            title = page['productDetail']['productDetail']['product']['title'] + f" ({authors})"  # noqa:E501
            images = [episode['path'] for episode in page['viewer']['pData']['img']]  # noqa:E501

            pdata = {
                'title': title if not self.omit_author else trunc_title(title),
                'ep_title': page['viewer']['pData']['title'],
                'img': images
            }

            return pdata

        except TypeError or IndexError:
            log.error("Unable to fetch page data.")

    def get_checksum(self, img_url: str) -> str:
        return ' '.join(parse_qs(img_url)['q'])

    def get_history(self) -> Dict[str, str]:
        if self._is_login:
            return self.get_bdata(self.history_url)
        else:
            raise LoginError

    def get_bookmark(self) -> Dict[str, str]:
        if self._is_login:
            return self.get_bdata(self.bookmark_url)
        else:
            raise LoginError

    def get_purchase(self) -> Dict[str, str]:
        if self._is_login:
            return self.get_bdata(self.purchase_url)
        else:
            raise LoginError
