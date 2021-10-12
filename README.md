# Pyccoma

Directly scrape images from [Piccoma](https://piccoma.com).

## Prerequisites
* Python 3.8+

## Setup

* First, you should get a copy of this project in your local machine by either downloading the zip file or cloning the repository. `git clone https://github.com/catsital/pyccoma.git`
* `cd` into `pyccoma` directory.
* Run `python setup.py install --user` to install package.

## Quickstart

Create a `Scraper` instance and use `fetch` to scrape and download images from a viewer page.

```python
>>> from pyccoma import Scraper
>>> pyc = Scraper()
>>> pyc.fetch('https://piccoma.com/web/viewer/8195/1185884')

Title: ひげを剃る。そして女子高生を拾う。(しめさば ぶーた 足立いまる)
Episode: 第1話 失恋と女子高生 (1)
|███████████████████████████████████████████████████████████| 100.0%
Elapsed time: 00:00:17
```

You can use `login` to have access to rental or paywalled episodes from your own library. Only email method is supported as of the moment.

```python
>>> pyc.login(email, password)
>>> pyc.fetch('https://piccoma.com/web/viewer/s/4995/1217972')

Title: かぐや様は告らせたい～天才たちの恋愛頭脳戦～(赤坂アカ)
Episode: 第135話
|███████████████████████████████████████████████████████████| 100.0%
Elapsed time: 00:00:23
```

Images are stored under the path specified in `fetch(url, path)`. A fixed directory tree structure like below is created with subfolders for the `product_name` and `episode_name`. It will return an absolute path if a relative one is given. If none is supplied, an `extract` folder will be automatically created inside the current working directory.

```
.
└───<extract>
    └───<product_name>
        └───<episode_name>
            ├───1.png
            ├───2.png
            └───...
```

## Usage

### Scraping public data

#### Using `get_episode_list` to scrape data from a product page:

```python
>>> product_info = pyc.get_episode_list('https://piccoma.com/web/product/12482/episodes')
>>> product_info
{'第1話 召喚と追放': {'url': 'https://piccoma.com/web/viewer/12482/631201', 'is_free': True, 'is_free_read': False, 'is_read': False, 'is_wait_free': False, 'is_purchased': False}, '第2話 森の魔女と精霊': {'url': 'https://piccoma.com/web/viewer/12482/631205', 'is_free': True, 'is_free_read': False, 'is_read': False, 'is_wait_free': False, 'is_purchased': False}}
```

`get_episode_list(url)` returns a dictionary of product data which includes the `episode`, `url`, and `status` categorized into `is_free`, `is_free_read`, `is_read`, `is_wait_free`, `is_purchased`. These statuses change accordingly when you are logged in and have accessed the episodes previously.

```python
>>> pyc.login(email, password)
>>> product_info = pyc.get_episode_list('https://piccoma.com/web/product/12482/episodes')
>>> product_info
{'第1話 召喚と追放': {'url': 'https://piccoma.com/web/viewer/12482/631201', 'is_free': True, 'is_free_read': False, 'is_read': True, 'is_wait_free': False, 'is_purchased': False}, '第2話 森の魔女と精霊': {'url': 'https://piccoma.com/web/viewer/12482/631205', 'is_free': True, 'is_free_read': False, 'is_read': True, 'is_wait_free': False, 'is_purchased': False}}
```

You can use these statuses to narrow down the results based on your library. See examples on the [next section]('https://github.com/catsital/pyccoma#accessing-your-library').

#### Using `get_pdata` to scrape data from a viewer page:

```python
>>> pdata = pyc.get_pdata('https://piccoma.com/web/viewer/12482/631201')
>>> pdata
{'title': '復讐を誓った白猫は竜王の膝の上で惰眠をむさぼる(あき クレハ ヤミーゴ)', 'ep_title': '第1話 召喚と追放', 'is_scrambled': True, 'img': ['https://pcm.kakaocdn.net/dna/e9073/btqzu1ySncw/RURZWSY6VAL9Z68AZO0CGJ/i00001.jpg?credential=4ggejDuJPPXMt5QR0LkfXOO2OCuoiXMt&expires=1633262400&signature=xGrL3pG2qXfOHyCbfOo1X6OPWRs%3D', 'https://pcm.kakaocdn.net/dna/bs75HK/btqzxG79lUN/RURZWSY6VAL9Z68AZO0CGJ/i00002.jpg?credential=4ggejDuJPPXMt5QR0LkfXOO2OCuoiXMt&expires=1633262400&signature=xGrL3pG2qXfOHyCbfOo1X6OPWRs%3D']}
```

`get_pdata(url)` returns a dictionary of episode data which includes the `title`, `ep_title`, `is_scrambled` status, and a list of `img` links.

### Accessing your library

#### Getting all the products you have read from your `history`:

```python
>>> history = pyc.get_history().values()
>>> history
{'ひげを剃る。そして女子高生を拾う。': 'https://piccoma.com/web/product/8195/episodes', '悪女はマリオネット': 'https://piccoma.com/web/product/67171/episodes', 'かぐや様は告らせたい～天才たちの恋愛頭脳戦～': 'https://piccoma.com/web/product/4995/episodes', '復讐を誓った白猫は竜王の膝の上で惰眠をむさぼる': 'https://piccoma.com/web/product/12482/episodes'}
```

#### Getting all your purchased products from your `purchase` library:

```python
>>> purchase = pyc.get_purchase().values()
>>> purchase
{'かぐや様は告らせたい～天才たちの恋愛頭脳戦～': 'https://piccoma.com/web/product/4995/episodes'}
```

#### Getting all your bookmarked products from your `bookmark` library:

```python
>>> bookmark = pyc.get_bookmark().values()
>>> bookmark
{'ひげを剃る。そして女子高生を拾う。': 'https://piccoma.com/web/product/8195/episodes', '悪女はマリオネット': 'https://piccoma.com/web/product/67171/episodes'}
```

#### Downloading all your purchased episodes from your `purchase` library:

```python
>>> purchase = pyc.get_purchase().values()
>>> purchased_episodes = [episode['url'] for title in purchase
                          for episode in pyc.get_episode_list(title).values()
                          if episode['is_purchased']]
>>> for episode in purchased_episodes:
        pyc.fetch(episode, 'piccoma')

Title: かぐや様は告らせたい～天才たちの恋愛頭脳戦～(赤坂アカ)
Episode: 第135話
|███████████████████████████████████████████████████████████| 100.0%
Elapsed time: 00:00:23

Title: かぐや様は告らせたい～天才たちの恋愛頭脳戦～(赤坂アカ)
Episode: 第136話
|███████████████████████████████████████████████████████████| 100.0%
Elapsed time: 00:00:25
```

#### Downloading the most recent episodes you have availed by using free pass from your `bookmark` library:

```python
>>> bookmark = pyc.get_bookmark().values()
>>> latest_free_episodes = [[episode['url'] for episode in pyc.get_episode_list(title).values()
                            if episode['is_free_read']]
                            for title in bookmark]
>>> latest_free_episodes = [episode[-1] for episode in latest_free_episodes if episode]
>>> for episode in latest_free_episodes:
        pyc.fetch(episode, 'piccoma')

Title: ひげを剃る。そして女子高生を拾う。(しめさば ぶーた 足立いまる)
Episode: 第2話 生活と遠慮 (1)
|███████████████████████████████████████████████████████████| 100.0%
Elapsed time: 00:00:18

Title: 悪女はマリオネット(Manggle hanirim)
Episode: 第29話
|███████████████████████████████████████████████████████████| 100.0%
Elapsed time: 00:01:38
```

#### Downloading the next free episodes you can get from your `bookmark` library if free pass has not been used yet (should be run only once):

```python
>>> bookmark = pyc.get_bookmark().values()
>>> next_free_episodes = [[episode['url'] for episode in pyc.get_episode_list(title).values()
                          if episode['is_wait_free'] and not episode['is_read']]
                          for title in bookmark]
>>> next_free_episodes = [episode[0] for episode in next_free_episodes if episode]
>>> for episode in next_free_episodes:
        pyc.fetch(episode, 'piccoma')

Title: 悪女はマリオネット(Manggle hanirim)
Episode: 第30話
|███████████████████████████████████████████████████████████| 100.0%
Elapsed time: 00:01:45
```

Given the example above, let's say that you have only used the free episode pass on ひげを剃る。そして女子高生を拾う。while you have yet to use it on 悪女はマリオネット, this will automatically discard ひげを剃る。そして女子高生を拾う。 and use the free pass on 悪女はマリオネット given that it has an episode with status `is_wait_free` and that it has not been read yet.

## License

See [LICENSE](https://github.com/catsital/pyccoma/blob/main/LICENSE) for details.

## Disclaimer

Pyccoma was made for the sole purpose of helping users download media from [Piccoma](https://piccoma.com) for offline consumption. This is for private use only, do not use this tool to promote piracy.
