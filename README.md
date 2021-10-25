# Pyccoma

Directly scrape images from [Piccoma](https://piccoma.com).

## Prerequisites
* Python 3.8+

## Setup

You can get started by installing using pip or manually from source.

### Install from PyPI

```bash
$ pip install pyccoma
```

### Install from source

* First, you should get a copy of this project in your local machine by either downloading the zip file or cloning the repository. `git clone https://github.com/catsital/pyccoma.git`
* `cd` into `pyccoma` directory.
* Run `python setup.py install` to install package.

## Quickstart

### Using the command-line utility

To download a single episode, simply use:

```bash
$ pyccoma https://piccoma.com/web/viewer/8195/1185884
```

You can also pass multiple links (separated by whitespace) to download in one go:

```bash
$ pyccoma https://piccoma.com/web/viewer/60171/1575237 https://piccoma.com/web/viewer/5796/332058 https://piccoma.com/web/viewer/13034/623225
```

See more examples on how to aggregate and batch download using the command-line utility on [the next section]('https://github.com/catsital/pyccoma/#usage') below.

### Using Python shell

Create a `Scraper` instance and use `fetch` to scrape and download images from a viewer page.

```python
>>> from pyccoma import Scraper
>>> pyc = Scraper()
>>> pyc.fetch('https://piccoma.com/web/viewer/8195/1185884')

Title: ひげを剃る。そして女子高生を拾う。(しめさば ぶーた 足立いまる)
Episode: 第1話 失恋と女子高生 (1)
  |███████████████████████████████████████████████████████████| 100.0% (14/14)
Elapsed time: 00:00:17
```

You can use `login` to have access to rental or paywalled episodes from your own library.

```python
>>> pyc.login(email, password)
>>> pyc.fetch('https://piccoma.com/web/viewer/s/4995/1217972')

Title: かぐや様は告らせたい～天才たちの恋愛頭脳戦～(赤坂アカ)
Episode: 第135話
  |███████████████████████████████████████████████████████████| 100.0% (20/20)
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

### Using filter to aggregate and download in batch

* Downloading all free episodes in a single product page:

```bash
$ pyccoma https://piccoma.com/web/product/67171/episodes?etype=E --filter all --include is_free
```

* Downloading all free episodes across multiple products:

```bash
$ pyccoma https://piccoma.com/web/product/5523/episodes?etype=E https://piccoma.com/web/product/23019/episodes?etype=E --filter all --include is_free
```

* Downloading all first episodes across multiple products:

```bash
$ pyccoma https://piccoma.com/web/product/6575/episodes?etype=E https://piccoma.com/web/product/41993/episodes?etype=E --filter min
```

* Downloading all free volumes across multiple products offered on a [campaign]('https://piccoma.com/web/event_list'):

```bash
$ pyccoma https://piccoma.com/web/product/6342/episodes?etype=V https://piccoma.com/web/product/4708/episodes?etype=V --filter all --include is_limited_free
```

* Downloading using custom with range:

```bash
$ pyccoma https://piccoma.com/web/product/16070/episodes?etype=E --filter custom --range 1 5
```

### Accessing your library

**Requires user login.**

* Downloading all your purchased items:

```bash
$ pyccoma purchase --filter all --include is_purchased --email foo@bar.com
```

* Downloading the most recent episodes you have read from your history:

```bash
$ pyccoma history --filter max --include "is_limited_read|(is_already_read&is_free)" --email foo@bar.com
```

* Downloading latest unread episodes using free pass (if available) from your bookmarks:

```bash
$ pyccoma bookmark --filter min --include is_limited_free --exclude is_already_read --email foo@bar.com
```

### Narrowing down the results

You can set restrictive conditions using the include and exclude options in the command-line utility. These two options take in statuses as arguments. To have a clearer picture as to what these statuses correspond to, see figure below.

![s_piccoma_web_episode_etypeE](https://user-images.githubusercontent.com/18095632/137633753-6959890c-c6ec-461e-8b15-7218ee47cbe7.png)

```python
{
  1437090: {'title': '第1話 (1)', 'url': 'https://piccoma.com/web/viewer/54715/1437090', 'is_free': True, 'is_limited_read': False, 'is_already_read': True, 'is_limited_free': False, 'is_purchased': False},
  1437091: {'title': '第1話 (2)', 'url': 'https://piccoma.com/web/viewer/54715/1437091', 'is_free': True, 'is_limited_read': False, 'is_already_read': True, 'is_limited_free': False, 'is_purchased': False},
  1437092: {'title': '第2話 (1)', 'url': 'https://piccoma.com/web/viewer/54715/1437092', 'is_free': True, 'is_limited_read': False, 'is_already_read': True, 'is_limited_free': False, 'is_purchased': False},
  1437093: {'title': '第2話 (2)', 'url': 'https://piccoma.com/web/viewer/54715/1437093', 'is_free': False, 'is_limited_read': False, 'is_already_read': True, 'is_limited_free': True, 'is_purchased': False},
  1437094: {'title': '第3話 (1)', 'url': 'https://piccoma.com/web/viewer/54715/1437094', 'is_free': False, 'is_limited_read': True, 'is_already_read': True, 'is_limited_free': False, 'is_purchased': False},
  1437095: {'title': '第3話 (2)', 'url': 'https://piccoma.com/web/viewer/54715/1437095', 'is_free': False, 'is_limited_read': True, 'is_already_read': True, 'is_limited_free': False, 'is_purchased': False},
  1437096: {'title': '第4話 (1)', 'url': 'https://piccoma.com/web/viewer/54715/1437096', 'is_free': False, 'is_limited_read': True, 'is_already_read': True, 'is_limited_free': False, 'is_purchased': False},
  1437097: {'title': '第4話 (2)', 'url': 'https://piccoma.com/web/viewer/54715/1437097', 'is_free': False, 'is_limited_read': False, 'is_already_read': False, 'is_limited_free': True, 'is_purchased': False}
}
```

## Options

### Required

|          Option           |              Description           |          Examples                                      |
|---------------------------|------------------------------------|--------------------------------------------------------|
|          url              | Must be a valid url                | `https://piccoma.com/web/product/4995/episodes?etype=V`, `https://piccoma.com/web/product/12482/episodes?etype=E`, `https://piccoma.com/web/viewer/12482/631201`, `bookmark`, `history`, `purchase` |

### Optional

|          Option           |              Description           |          Examples                                      |
|---------------------------|------------------------------------|--------------------------------------------------------|
|   -o, --output            | Local directory to save downloaded images     | `D:/piccoma/` (absolute path), `/piccoma/download/` (relative path)                                         |
|   -f, --format            | Image format                       | `jpeg`, `jpg`, `bmp`, `png` (default)          |
|   --omit-author           | Omit author names from titles      |                                                        |

### Login

|          Option           |              Description           |          Examples                                      |
|---------------------------|------------------------------------|--------------------------------------------------------|
|   --email        | Your registered email address; this does not support OAuth authentication              | `foo@bar.com`                                          |

### Filter

|  Option   |                    Description                         |                         Examples                               |
|-----------|--------------------------------------------------------|----------------------------------------------------------------|
| --etype   | Preferred episode type to scrape manga, smartoon, and novel when scraping `history`, `bookmark`, `purchase`; takes in three arguments, the first one for manga, the second for smartoon, and the last one for novel  | `volume` to scrape for volumes, `episode` to scrape for episodes |
| --filter  | Filter to use when scraping episodes from a product page or your library | `min`, `max`, `all`, or `custom` by defining --range. Use `min` to scrape for the first item, `max` for the last item, `all` to scrape all items, and `custom` to scrape for a specific index range |
| --range   | Range to use when scraping episodes; takes in two arguments, start and end; will always override --filter to parse custom, if omitted or otherwise | `0 10` will scrape the first up to the ninth episode |
| --include | Status arguments to include when parsing a library or product; can parse in `\|` and `&` operators as conditionals, see [use cases above]('https://github.com/catsital/pyccoma/#usage') | `is_purchased`, `is_free`, `is_already_read`, `is_limited_read`, `is_limited_free` |
| --exclude | Status arguments to exclude when parsing a library or product; can parse in `\|` and `&` operators as conditionals, see [use cases above]('https://github.com/catsital/pyccoma/#usage') | `is_purchased`, `is_free`, `is_already_read`, `is_limited_read`, `is_limited_free` |

### Logging

|          Option           |              Description           |          Examples                                      |
|---------------------------|------------------------------------|--------------------------------------------------------|
|   --l, --loglevel         | Set the log message threshold      | `debug`, `info` (default), `warning`, `error`, `none`  |

## License

See [LICENSE](https://github.com/catsital/pyccoma/blob/main/LICENSE) for details.

## Disclaimer

Pyccoma was made for the sole purpose of helping users download media from [Piccoma](https://piccoma.com) for offline consumption. This is for private use only, do not use this tool to promote piracy.
