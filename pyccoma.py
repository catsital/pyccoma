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
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': 'https://piccoma.com/web/acc/signin?next_url=/web/'
        }
        self.session = requests.session()

    def parse(self, page) -> str:
        return bs(page, 'html.parser')

    def parse_page(self, url) -> str:
        page = self.session.get(url, headers=self.headers).text
        soup = self.parse(page)
        return soup

    def parse_title(self, url) -> str:
        pattern = re.compile(r'[?"|:<>*/\\]', flags=re.VERBOSE)
        title = self.parse_page(url).find('title').text
        return pattern.sub("", str(title))

    @property
    def login_session(self):
        return self.session.get(self.login_url, headers=self.headers)

    @property
    def login_csrf(self) -> str:
        soup = self.parse(self.login_session.text)
        return soup.find('input', attrs={'name': self.CSRF_NAME})['value']

    @property
    def cookies(self) -> str:
        return self.login_session.cookies

    def login(self, email, password) -> None:
        params = {
            self.CSRF_NAME: self.login_csrf,
            'next_url': '/web/',
            'email': email,
            'password': password
        }
        self.session.post(self.login_url,
                          data=params,
                          cookies=self.cookies,
                          headers=self.headers)

    def get_checksum(self, img_url) -> str:
        return img_url.split('/')[-2]

    def get_key(self, img_url) -> str:
        return img_url.split('?')[1].split('&')[1].split('=')[1]

    def get_seed(self, checksum, expiry_key) -> str:
        for num in expiry_key:
            if int(num) != 0: checksum = checksum[-int(num):] + checksum[:len(checksum)-int(num)]
        return checksum

    def get_pdata(self, url) -> dict:
        script = self.parse_page(url).findAll('script')[5]
        title = str(script).split('title')[1].split("'")[2].strip()
        is_scrambled = str(script).split('isScrambled')[1].split(":")[1].split(",")[0].strip().title()
        links = str(script).split("'img'")[1]
        images = ["https://" + image.split("',")[0].strip() for image in links.split("{'path':'//") if "'," in image]
        pdata = {
            'title': title,
            'is_scrambled': eval(is_scrambled),
            'img': images
        }
        return pdata

    def get_image(self, chapter, seed, output) -> None:
        try:
            img = requests.get(chapter, headers=self.headers, stream=True)
            if img.status_code == 200:
                if seed.isupper():
                    canvas = pyc(img.raw, 50, seed, output)
                    canvas.unscramble()
                else:
                    with open(output + '.png', 'wb') as handler:
                        for chunk in img.iter_content(1024):
                            if chunk:
                                handler.write(chunk)

                log.info('Downloading ' + output)
            else:
                log.error('Failed to download ' + chapter)
        except Exception as e:
            log.error('Encountered error: ' + str(e))

    def fetch(self, url, path='extract') -> None:
        try:
            chapter_title = self.parse_title(url).split("｜")[0]
            series_title = self.parse_title(url).split("｜")[1]
            leaf_path = series_title + "/" + chapter_title + "/"
            dest_path = os.path.join(path, leaf_path)
            os.makedirs(dest_path, exist_ok=True)

            chapter = self.get_pdata(url)['img']
            checksum = self.get_checksum(chapter[0])
            key = self.get_key(chapter[0])
            seed = self.get_seed(checksum, key)

            start_time = time.time()

            for page_num, page in enumerate(chapter):
                output = dest_path + str(page_num+1)
                if os.path.exists(output + ".png"):
                    log.warning('Skipping download, file already exists!')
                else:
                    download = threading.Thread(target=self.get_image, args=(page, seed, output))
                    download.start()
                    time.sleep(1)

            exec_time = time.time() - start_time
            log.debug('Total elapsed time: ' + str(exec_time))

        except Exception as e:
            log.error('Encountered error: ' + str(e))
