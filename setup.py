from distutils.core import setup

setup (
  name = 'clip.py',
  version = '0.1',
  author = 'Thomas Lant',
  author_email = 'thomas.lant@gmail.com',
  packages = [],
  scripts = ['bin/clip.py'],
  license = 'LICENSE.txt',
  description = 'A lightweight tool for clipping fragments of text to openkeyval.org, indexed via randomly provided English words',
  long_description = open('README.txt').read(),
)
