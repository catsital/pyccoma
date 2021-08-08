import requests
import pyduktape
from pycasso import UnscrambleImg as pyc
from bs4 import BeautifulSoup as bs

class Pyccoma:
    CSRF_NAME = 'csrfmiddlewaretoken'
    login_url = 'https://piccoma.com/web/acc/email/signin'
    login_type = ['email', 'facebook', 'twitter', 'apple']

    piccoma_s_js = requests.get('https://piccoma.com/static/web/js/viewer/_s.min.js?1628219080').text

    def __init__(self, url):
        self.url = url
        self.headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Referer': 'https://piccoma.com/web/acc/signin?next_url=/web/',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        self.session = requests.session()

    def parse(self, page):
        return bs(page, 'html.parser')

    def login_session(self):
        return self.session.get(self.login_url, headers=self.headers)

    def login_csrf(self):
        soup = self.parse(self.login_session().text)
        return soup.find('input', attrs={'name': self.CSRF_NAME})['value']

    def cookies(self):
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

    def execute(self, script):
        ctx = pyduktape.DuktapeContext()
        output = ctx.eval_js(script)
        return output

    def get_checksum(self, img_url):
        return img_url.split('/')[-2]

    def get_key(self, img_url):
        return img_url.split('?')[1].split('&')[1].split('=')[1]

    def get_seed(self, checksum, expiry_key):
        init = """
               Object.defineProperty(new Function('return this')(), 'window', {
                value: new Function('return this')(),
                writable: false, enumerable: true, configurable: false
               });
               """
        js = init + self.piccoma_s_js + "get_seed('" + checksum + "','" + expiry_key + "');"
        return self.execute(js)

    def get_image(self):
        page = self.session.get(self.url).text
        soup = self.parse(page)
        script = soup.findAll('script')[5]
        data = str(script).split('img')[1]
        images = ["https://" + image.split("',")[0].strip() for image in data.split("{'path':'//") if "'," in image]
        return images

    def fetch(self):
        chapter = self.get_image()
        checksum = self.get_checksum(chapter[0])
        key = self.get_key(chapter[0])

        slice_size = 50
        seed = self.get_seed(checksum, key)

        for index, page in enumerate(chapter):
            e = requests.get(page, stream=True).raw
            t = pyc(e, slice_size, seed, str(index))
            t.unscramble()
