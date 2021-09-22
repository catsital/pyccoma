import os
import re
import time
import logging
import requests
import threading
from pycasso import UnscrambleImg as pyc
from bs4 import BeautifulSoup as bs

log = logging.getLogger(__name__)

class Scraper:
    CSRF_NAME = 'csrfmiddlewaretoken'
    login_url = 'https://piccoma.com/web/acc/email/signin'

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Referer': '{0}?next_url=/web/'.format(self.login_url)
        }
        self.session = requests.session()
        self.session.verify = True

    def parse(self, page) -> str:
        return bs(page, 'html.parser')

    def parse_page(self, url) -> str:
        page = self.session.get(url, headers=self.headers).text
        soup = self.parse(page)
        return soup

    @property
    def _login(self) -> dict:
        session = self.session.get(self.login_url, headers=self.headers)
        page = self.parse(session.text)
        csrf = page.find('input', attrs={'name': self.CSRF_NAME})['value']
        cookies = session.cookies
        is_login = str(page.findAll('script')[3]).split('login')[1].split(":")[1].split(",")[0].strip().title()
        login = {
            'csrf': csrf,
            'cookies': cookies,
            'is_login': eval(is_login)
        }
        return login

    @property
    def _login_csrf(self) -> str:
        return self._login['csrf']

    @property
    def _login_cookies(self) -> str:
        return self._login['cookies']

    @property
    def _is_login(self) -> bool:
        return self._login['is_login']

    def login(self, email, password) -> None:
        log.debug("Logging in as: {0}".format(email))
        params = {
            self.CSRF_NAME: self._login_csrf,
            'next_url': '/web/',
            'email': email,
            'password': password
        }
        self.session.post(self.login_url,
                          data=params,
                          cookies=self._login_cookies,
                          headers=self.headers)

        if self._is_login:
            log.info('Login successful: {0}'.format(email))
        else:
            log.error('Login failed: {0}'.format(email))

    @staticmethod
    def safe_filename(title) -> str:
        pattern = re.compile(r'[?"|:<>*/\\]', flags=re.VERBOSE)
        return pattern.sub("", str(title))

    @staticmethod
    def create_path(path, dest_path=None) -> None:
        if path:
            if not os.path.isabs(path):
                path = os.path.join(os.getcwd(), path)
        else:
            path = os.path.join(os.getcwd(), 'extract')

        if os.path.exists(dest_path):
            log.warning('Path already exists: {0}'.format(dest_path))
        else:
            log.debug('Creating path: {0}'.format(dest_path))

        os.makedirs(dest_path, exist_ok=True)

    def get_checksum(self, img_url) -> str:
        return img_url.split('/')[-2]

    def get_key(self, img_url) -> str:
        return img_url.split('?')[1].split('&')[1].split('=')[1]

    def get_seed(self, checksum, expiry_key) -> str:
        for num in expiry_key:
            if int(num) != 0: checksum = checksum[-int(num):] + checksum[:len(checksum)-int(num)]
        return checksum

    def get_episode_list(self, url) -> dict:
        try:
            if 'episodes' not in url:
                log.error('Error encountered: Invalid url, unable to fetch all episode links')
            else:
                page = self.parse_page(url).find('ul', attrs={'id':'js_episodeList'})
                log.debug('Parsing episode list from {0}'.format(url))
                series_id = url.split('/')[-2]
                episode_title = [title.text for title in page.findAll('h2')]
                episode_link = ["https://piccoma.com/web/viewer/{0}/{1}".format(series_id, episode_id['data-episode_id'])
                                for episode_id in page.select('a[data-episode_id]')]
                episodes = {title:link for title, link in zip(episode_title, episode_link)}
                return episodes

        except IndexError:
            log.error('Error encountered: Invalid url, unable to fetch episode list')

        except Exception as exception:
            log.error('Error encountered: {0}'.format(exception))

    def get_pdata(self, url) -> dict:
        try:
            page = self.parse_page(url)
            log.debug('Parsing data from {0}'.format(url))

            title = self.safe_filename(page.find('title').text.split("｜")[1])
            script = page.findAll('script')[5]

            ep_title = str(script).split('title')[1].split("'")[2].strip()
            is_scrambled = str(script).split('isScrambled')[1].split(":")[1].split(",")[0].strip().title()
            links = str(script).split("'img'")[1]
            images = ["https://" + image.split("',")[0].strip() for image in links.split("{'path':'//") if "'," in image]
            pdata = {
                'title': title,
                'ep_title': ep_title,
                'is_scrambled': eval(is_scrambled),
                'img': images
            }
            return pdata

        except IndexError:
            log.error('Error encountered: Unable to fetch page data')

        except Exception as exception:
            log.error('Error encountered: {0}'.format(exception))

    def get_image(self, episode, seed, output) -> None:
        try:
            img = requests.get(episode, headers=self.headers, stream=True)
            if img.status_code == 200:
                if seed.isupper():
                    canvas = pyc(img.raw, 50, seed, output)
                    canvas.unscramble()
                else:
                    with open(output + '.png', 'wb') as handler:
                        for chunk in img.iter_content(1024):
                            if chunk:
                                handler.write(chunk)

                log.info('Downloading: {0}'.format(output))
            else:
                log.error('Failed to download: {0}'.format(episode))

        except Exception:
            log.error('Error encountered on {0}: Failed to write {1}.png'.format(episode, output))

    def fetch(self, url, path) -> None:
        try:
            pdata = self.get_pdata(url)
            if not self._is_login and not pdata:
                log.error('Restricted content: Login required')
            elif self._is_login and not pdata:
                log.error('Restricted content: Coins required for access')
            elif not self._is_login and pdata:
                log.warning('No login session detected, downloading as guest')
            else:
                leaf_path = '{0}/{1}/'.format(pdata['title'], pdata['ep_title'])
                dest_path = os.path.join(path, leaf_path)
                self.create_path(path, dest_path)

                episode = pdata['img']
                checksum = self.get_checksum(episode[0])
                key = self.get_key(episode[0])
                seed = self.get_seed(checksum, key)

                start_time = time.time()

                for page_num, page in enumerate(episode):
                    output = dest_path + str(page_num+1)
                    if os.path.exists(output + ".png"):
                        log.warning('Skipping download, file already exists: {0}.png'.format(output))
                    else:
                        download = threading.Thread(target=self.get_image, args=(page, seed, output))
                        download.start()
                        time.sleep(1)

                exec_time = time.time() - start_time
                log.debug('Total elapsed time: {0}'.format(exec_time))

        except TypeError:
            log.error('Error encountered: Unable to fetch episode')

        except Exception as exception:
            log.error('Error encountered: {0}'.format(exception))
