# Pyccoma

Directly scrape images from [Piccoma](https://piccoma.com).

## Prerequisites
* Python 3.8+

## Setup

* First, you should get a copy of this project in your local machine by either downloading the zip file or cloning the repository. `git clone https://github.com/catsital/pyccoma.git`
* `cd` into `pyccoma` directory.
* Run `python setup.py install --user` to install package.

## Usage

Create a `Scraper` instance and use `fetch` to scrape and download images from a viewer page.

```python
from pyccoma import Scraper
pyc = Scraper()
pyc.fetch('https://piccoma.com/web/viewer/60171/1575239')
```

`fetch` can be reused as well to download multiple episodes in a single run.

```python
pyc.fetch('https://piccoma.com/web/viewer/13034/623225')
pyc.fetch('https://piccoma.com/web/viewer/13034/623226')
pyc.fetch('https://piccoma.com/web/viewer/13034/623227')
```

You can use `login` to have access to rental or paywalled episodes (usually denoted by `/s/` in the `url`) from your own library.

```python
pyc.login(email, password)
pyc.fetch('https://piccoma.com/web/viewer/s/60171/1575240')
```

Downloaded images are stored under the path specified in `fetch`, in a fixed directory tree structure like below.

```python
pyc.fetch('https://piccoma.com/web/viewer/60171/1575239', 'piccoma')
```

```
.
└───<piccoma>
    └───<product-name>
        └───<episode-name>
            ├───1.png
            ├───2.png
            └───...
```

If no value is supplied, it automatically creates an `extract` folder inside the project directory.

## Methods

`parse_page(url)`
* Returns the parsed html string of a page

`login(email, password)`
* Creates an authentication session to the website (only supports email method so far)

`get_pdata(url)`
* Returns a dictionary of episode data (including image links) parsed from either a product or episode page

`get_episode_list(url)`
* Returns a dictionary of episode links parsed from a product page

`fetch(url, path)`
* Downloads the images parsed from a viewer page

## License

See [LICENSE](https://github.com/catsital/pyccoma/blob/main/LICENSE) for details.

## Disclaimer

Pyccoma was made for the sole purpose of helping users download media from [Piccoma](https://piccoma.com) for offline consumption. This is for private use only, do not use this tool to promote piracy.
