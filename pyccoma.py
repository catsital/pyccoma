import os
import re
import requests
from pycasso import UnscrambleImg as pyc
from bs4 import BeautifulSoup as bs

class Scraper:
    CSRF_NAME = 'csrfmiddlewaretoken'
    login_url = 'https://piccoma.com/web/acc/email/signin'
    login_type = ['email', 'facebook', 'twitter', 'apple']

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

    def login_session(self):
        return self.session.get(self.login_url, headers=self.headers)

    def login_csrf(self) -> str:
        soup = self.parse(self.login_session().text)
        return soup.find('input', attrs={'name': self.CSRF_NAME})['value']

    def cookies(self) -> str:
        return self.login_session().cookies

    def login(self, email, password):
        params = {
            self.CSRF_NAME: self.login_csrf(),
            'next_url': '/web/',
            'email': email,
            'password': password
        }
        self.session.post(self.login_url,
                          data=params,
                          cookies=self.cookies(),
                          headers=self.headers)

    def get_checksum(self, img_url) -> str:
        return img_url.split('/')[-2]

    def get_key(self, img_url) -> str:
        return img_url.split('?')[1].split('&')[1].split('=')[1]

    def get_seed(self, checksum, expiry_key) -> str:
        for num in expiry_key:
            if int(num) != 0: checksum = checksum[-int(num):] + checksum[:len(checksum)-int(num)]
        return checksum

    def get_image(self, url) -> list:
        script = self.parse_page(url).findAll('script')[5]
        data = str(script).split('img')[1]
        images = ["https://" + image.split("',")[0].strip() for image in data.split("{'path':'//") if "'," in image]
        return images

    def fetch(self, url, path='extract'):
        try:
            chapter_title = self.parse_title(url).split("｜")[0]
            series_title = self.parse_title(url).split("｜")[1]
            leaf_path = series_title + "/" + chapter_title + "/"
            dest_path = os.path.join(path, leaf_path)
            os.makedirs(dest_path)

            chapter = self.get_image(url)
            checksum = self.get_checksum(chapter[0])
            key = self.get_key(chapter[0])

            slice_size = 50
            seed = self.get_seed(checksum, key)

            for page_num, page in enumerate(chapter):
                img = requests.get(page, headers=self.headers, stream=True).raw
                canvas = pyc(img, slice_size, seed, dest_path + str(page_num+1))
                canvas.unscramble()
        except Exception as e:
            raise
