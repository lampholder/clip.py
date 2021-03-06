#!/usr/bin/python
# This Python file uses the following encoding: utf-8

# Because I'm always forgetting even basic git syntax:
# git clone git://github.com/lampholder/clip.py

import re
import sys
import random
import zlib, base64
import urllib, urllib2

class KeyValUtils:

  # Please change the unique prefix before using
  # import random
  # ''.join(random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_') for n in xrange(30))
  _unique_prefix = 'CehyI68s607EbrMVN3Vo4Q59ORjKoj'
  _words = '/usr/share/dict/words'
  _unique_key_hunt_retry_count = 20
  _maintain_index = True

  def generate_key(self):
    words_file = open(self._words, 'r')
    suitable = re.compile('^[A-Za-z]{1,6}$')
    key = ""
    try_count = 0
    suitable_words = filter(lambda x: suitable.match(x), words_file)
    while key == "" and try_count < self._unique_key_hunt_retry_count:
      try_count += 1
      key = random.choice(suitable_words).rstrip().lower()
      try:
        response = urllib2.urlopen('https://secure.openkeyval.org/%s-%s' % (self._unique_prefix, key))
        if response.code == 200:
          # Try again!
          key = ""
      except urllib2.HTTPError, e:
        if e.code == 404:
          # Great, this key is not already in use
          return key
        else:
          raise Exception('Remote store is inaccessible/misbehaving')
    raise Exception('Exceeded unique key hunt retry count - check your words file')

  def index(self):
    try:
      response = urllib2.urlopen('https://secure.openkeyval.org/%sINDEX' % self._unique_prefix)
      return set(zlib.decompress(base64.b64decode(response.read())).split(','))
    except urllib2.HTTPError, e:
      if e.code == 404:
        return set()
      else:
        raise e

  def _write_index(self, index):
    if len(index) > 0:
      index_data = base64.b64encode(zlib.compress(','.join(index)))
    else:
      index_data = ''
    new_index = urllib.urlencode({'data': index_data})
    request = urllib2.Request('https://secure.openkeyval.org/%sINDEX' % self._unique_prefix, new_index)
    try:
      response = urllib2.urlopen(request)
    except urllib2.HTTPError, e:
      sys.stderr.write("Unable to write index record")
      raise e

  def store(self, value, key=None):
    if key is not None:
      if not self.get_valid_key_regex().match(key):
        raise Exception('Invalid key [%s] specified' % key) 
    else:
      key = self.generate_key()

    data = urllib.urlencode({'data': value})
    request = urllib2.Request('https://secure.openkeyval.org/%s-%s' % (self._unique_prefix, key), data)
    response = urllib2.urlopen(request)

    if self._maintain_index:
      index = self.index()
      index.add(key)
      self._write_index(index)

    return key

  def fetch(self, key):
    response = urllib2.urlopen('https://secure.openkeyval.org/%s-%s' % (self._unique_prefix, key))
    return response.read()

  def delete(self, key):
    if not self.get_valid_key_regex().match(key):
      raise Exception('Invalid key [%s] specified' % key)
    data = urllib.urlencode({'data': ''})
    request = urllib2.Request('https://secure.openkeyval.org/%s-%s' % (self._unique_prefix, key), data)
    response = urllib2.urlopen(request)

    if self._maintain_index:
      index = self.index()
      if key in index:
        index.remove(key)
        self._write_index(index)

    return 'deleted' in response.read()

  def get_valid_key_regex(self):
    return re.compile('^[A-Za-z0-9_-]{1,%d}' % (128 - 1 - len(self._unique_prefix)))


def main():
  from optparse import OptionParser
  
  parser = OptionParser()
  parser.add_option('-c', '--copy', dest='copy', action='store_true', default=False, help='later')
  parser.add_option('-p', '--paste', dest='paste', action='store_true', default=False, help='later')
  parser.add_option('-d', '--delete', dest='delete', action='store_true', default=False, help='later')
  parser.add_option('-i', '--index', dest='index', action='store_true', default=False, help='later')
  
  namespace, extra = parser.parse_args()

  key = None
  if len(extra) > 0:
    key = extra[0]
  
  if not (namespace.copy or namespace.paste or namespace.delete or namespace.index):
    if sys.stdin.isatty() and key is not None:
      namespace.paste = True
    else:
      namespace.copy = True
  
  correct_usage = namespace.copy \
              or  namespace.index \
              or (namespace.paste and key is not None) \
              or (namespace.delete and key is not None)

  if not correct_usage:
    parser.print_help();
    exit(1)

  kv = KeyValUtils()

  if namespace.copy:
    infile = sys.stdin
  
    value = ""
    for line in infile:
      value += line
      if len(value) > 65536:
        sys.stderr.write('Input too large; 64 KiB maximum\n')
        exit(1)
    try:
      key = kv.store(key=key, value=value)
      print 'Clipped to \'%s\'' % key
      exit()
    except urllib2.HTTPError, e:
      sys.stderr.write('Clip failed; response code %s\n' % e.code)
      exit(1)

  if namespace.index:
    try:
      index = kv.index()
      if index is not None:
        for key in kv.index():
          print key
    except urllib2.HTTPError, e:
      if e.code == 404:
        sys.stderr.write('Index not found\n')
      else:
        raise e
    exit()

  if namespace.paste and key is not None:
    outfile = sys.stdout
    try:
      outfile.write(kv.fetch(key))
      exit()
    except urllib2.HTTPError, e:
      if e.code == 404:
        sys.stderr.write('No clip \'%s\'\n' % key)
      else:
        sys.stderr.write('Failed to fetch clip; response code %s\n' % e.code)
      exit(1)
  
  if namespace.delete and key is not None:
    try:
      if kv.delete(key):
        print 'Deleted clip \'%s\'' % key
      else:
        print 'No clip \'%s\'' % key
      exit()
    except urllib2.HTTPError, e:
      sys.stderr.write('Failed to delete clip; response code %s\n' % e.code)

if  __name__ =='__main__':
  main()
