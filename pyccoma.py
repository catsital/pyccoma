import requests
from bs4 import BeautifulSoup as bs

class Pyccoma:
    CSRF_NAME = 'csrfmiddlewaretoken'
    api_base = 'https://api.piccoma.com/'
    login_url = 'https://piccoma.com/web/acc/email/signin'
    login_type = ['email', 'facebook', 'twitter', 'apple']

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

    def start(self):
        return self.session.get(self.login_url)

    def parse(self, page):
        return bs(page, 'html.parser')

    def cookies(self):
        return self.start().cookies

    def login_csrf(self):
        soup = self.parse(self.start().text)
        return soup.find('input', attrs={'name': self.CSRF_NAME})['value']

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

    def get_image(self):
        page = self.session.get(self.url).text
        soup = self.parse(page)
        script = soup.findAll('script')[5]
        data = str(script).split('img')[1]
        images = ["https://" + image.split("',")[0].strip() for image in data.split("{'path':'//") if "'," in image]
        print(images)

    def parse_qs(self, img_url):
        seed = img_url.split('/')[6]
        return seed[-14:] + seed[:8]

    def get_seed(self):
        return self.parse_qs(self.get_image()[0])
