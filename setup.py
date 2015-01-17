try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'My Project',
    'author': 'Tom Barron',
    'url': 'URL to get it at.',
    'download_url': 'Where to download it.',
    'author_email': 'tom.barron@comcast.net',
    'version': '0.1',
    'install_requires': [],
    'packages': ['editor'],
    'scripts': [],
    'name': 'editor'
}

setup(**config)
