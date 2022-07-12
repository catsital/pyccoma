#!/usr/bin/env python

import re
import logging

from typing import Mapping, Union, Dict

from pyccoma import Scraper
from pyccoma.exceptions import PyccomaError, PageError, LoginError
from pyccoma.helpers import trunc_title

from pyccoma.jp.urls import (
    base_url,
    login_url,
    history_url,
    bookmark_url,
    purchase_url,
)

log = logging.getLogger(__name__)


class Pyccoma(Scraper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._etype = {
            "manga": "V",
            "smartoon": "E",
            "novel": "E"
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

    def get_login_status(self) -> bool:
        is_login = self.parse_page(login_url).xpath(
            '//script[contains(text(), "login")]/text()'
        )[0].split(":")[1].split(",")[0].strip().title()
        return eval(is_login)

    def login(self, email: str, password: str) -> None:
        try:
            session = self.session.get(login_url, headers=self.headers)
            csrf = self.parse(session.text).xpath(
                f'//input[@name = "csrfmiddlewaretoken"]/@value'
            )

            params = {
                'csrfmiddlewaretoken': csrf,
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
        try:
            if url.endswith('V'):
                return self.get_volume_list(url)
            elif url.endswith('E'):
                return self.get_episode_list(url)
            else:
                raise ValueError("Invalid input.")

        except Exception:
            raise PageError(url)

    def get_episode_list(
        self,
        url: str
    ) -> Mapping[int, Dict[str, Union[str, bool]]]:
        try:
            page = self.parse_page(url).xpath('//ul[@id="js_episodeList"]')[0]
            episode_title = [
                title.text_content() for title in page.xpath(
                    './/div[@class="PCM-epList_title"]/h2'
                )
            ]
            episode_id = [id for id in page.xpath('./li/a/@data-episode_id')]
            series_id = url.split('/')[-2]

            episode_link = [
                "https://piccoma.com/web/viewer/{0}/{1}"
                .format(series_id, id) for id in episode_id
            ]

            status = [_status for _status in page.xpath('./li')]

            episodes = {
                id: {
                    'title': title,
                    'url': link,
                    'is_free': True if _status.find_class('PCM-epList_status_free') else False,  # noqa:E501
                    'is_zero_plus': True if _status.find_class('PCM-epList_status_zeroPlus') else False,  # noqa:E501
                    'is_read_for_free': True if _status.find_class('PCM-epList_status_waitfreeRead') else False,  # noqa:E501
                    'is_already_read': True if _status.find_class('PCM-epList_read') else False,  # noqa:E501
                    'is_wait_until_free': True if _status.find_class('PCM-epList_status_webwaitfree') else False,  # noqa:E501
                    'is_purchased': True if _status.find_class('PCM-epList_status_buy') else False  # noqa:E501
                }
                for id, title, link, _status in zip(
                    episode_id,
                    episode_title,
                    episode_link,
                    status
                )
            }

            if not episodes:
                log.debug(f"No episodes found on {url}")

            return episodes

        except KeyError:
            log.error("Unable to fetch episode list.")
        except AttributeError:
            raise PageError(url)
        except Exception as err:
            raise PyccomaError(err)

    def get_volume_list(
        self,
        url: str
    ) -> Mapping[int, Dict[str, Union[str, bool]]]:
        try:
            page = self.parse_page(url).xpath('//ul[@id="js_volumeList"]')[0]
            volume_title = [
                title.text_content() for title in page.xpath(
                    './/div[@class="PCM-prdVol_title"]//h2'
                )
            ]
            series_id = url.split('/')[-2]
            volume_id = [
                [id for id in links.xpath('./a/@data-episode_id')]
                for links in page.xpath('//div[@class="PCM-prdVol_btns"]')
            ]
            volume_link = [
                "https://piccoma.com/web/viewer/{0}/{1}"
                .format(series_id, id[0]) for id in volume_id
            ]

            xpath_status = './li'
            status = [_status for _status in page.xpath(f'{xpath_status}')]

            volumes = {
                id + 1: {
                    'title': title,
                    'url': link,
                    'is_free': True if _status.find_class('PCM-prdVol_freeBtn') else False,  # noqa:E501
                    'is_read_for_free': True if (_status.find_class('PCM-prdVol_readBtn') and _status.find_class('PCM-prdVol_campaign_free')) else False,  # noqa:E501
                    'is_already_read': True if _status.find_class('PCM-volList_read') else False,  # noqa:E501
                    'is_wait_until_free': True if _status.find_class('PCM-prdVol_campaign_free') else False,  # noqa:E501
                    'is_purchased': True if _status.find_class('PCM-prdVol_readBtn') else False  # noqa:E501
                }
                for id, (title, link, _status) in enumerate(
                    zip(
                        volume_title,
                        volume_link,
                        status
                    )
                )
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

    def get_bdata(self, url: str) -> Dict[str, str]:
        try:
            page = self.parse_page(url).xpath(
                '//section[@class="PCM-productTile"]'
            )[0]
            product_title = [
                title.text for title in page.xpath('.//p//span') if title.text
            ]
            product_type = [
                self.smartoon if 'PCM-stt_smartoon' in _type else
                self.novel if 'PCM-stt_novel' in _type else self.manga
                for _type in [
                    type.classes for type in page.xpath('.//li')
                ]
            ]
            product_link = [
                base_url + url + "/episodes?etype="
                for url in page.xpath('//a[@class="PCM-product"]/@href')
            ]
            items = {
                title: link + type for title, link, type in zip(
                    product_title, product_link, product_type
                )
            }
            return items

        except Exception:
            log.error("Failed to parse library.")

    def get_pdata(self, url: str) -> Dict[str, Union[str, bool]]:
        try:
            page = self.parse_page(url)

            log.info(f"Parsing data from {url}")

            title = page.xpath('//title')[0].text_content().split("｜")[1]

            page = page.xpath('//script[contains(text(), "pdata")]/text()')[0]
            ep_title = page.split("'title'")[1].split("'")[1].strip()

            pattern = r"(?<=:')[^']+(?=')"
            images = ["https:" + image for image in re.findall(pattern, page)]
            pdata = {
                'title': title if not self.omit_author else trunc_title(title),
                'ep_title': ep_title,
                'img': images
            }

            return pdata

        except TypeError or IndexError:
            log.error("Unable to fetch page data.")

    def get_checksum(self, img_url: str) -> str:
        return img_url.split('/')[-2]

    def get_history(self) -> Dict[str, str]:
        if self._is_login:
            return self.get_bdata(history_url)
        else:
            raise LoginError

    def get_bookmark(self) -> Dict[str, str]:
        if self._is_login:
            return self.get_bdata(bookmark_url)
        else:
            raise LoginError

    def get_purchase(self) -> Dict[str, str]:
        if self._is_login:
            return self.get_bdata(purchase_url)
        else:
            raise LoginError
