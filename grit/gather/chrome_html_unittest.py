#!/usr/bin/env python
# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Unit tests for grit.gather.chrome_html'''


import os
import re
import sys
if __name__ == '__main__':
  sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), '../..'))

import tempfile
import unittest

from grit import lazy_re
from grit.gather import chrome_html


_NEW_LINE = lazy_re.compile('(\r\n|\r|\n)', re.MULTILINE)


def StandardizeHtml(text):
  '''Standardizes the newline format and png mime type in Html text.'''
  return _NEW_LINE.sub('\n', text).replace('data:image/x-png;',
                                           'data:image/png;')


class TempDir(object):
  def __init__(self, file_data):
    self.files = []
    self.dirs = []
    self.tmp_dir_name = tempfile.gettempdir()
    for name in file_data:
      file_path = self.tmp_dir_name + '/' + name
      dir_path = os.path.split(file_path)[0]
      if not os.path.exists(dir_path):
        self.dirs.append(dir_path)
        os.makedirs(dir_path)
      self.files.append(file_path)
      f = open(file_path, 'w')
      f.write(file_data[name])
      f.close()

  def CleanUp(self):
    self.dirs.reverse()
    for name in self.files:
      os.unlink(name)
    for name in self.dirs:
      os.removedirs(name)

  def GetPath(self, name):
    return self.tmp_dir_name + '/' + name


class ChromeHtmlUnittest(unittest.TestCase):
  '''Unit tests for ChromeHtml.'''

  def testFileResources(self):
    '''Tests inlined image file resources with available high DPI assets.'''

    tmp_dir = TempDir({
      'index.html': '''
      <!DOCTYPE HTML>
      <html>
        <head>
          <link rel="stylesheet" href="test.css">
        </head>
        <body>
          <!-- Don't need a body. -->
        </body>
      </html>
      ''',

      'test.css': '''
      .image {
        background: url('test.png');
      }
      ''',

      'test.png': 'PNG DATA',

      '1.4x/test.png': '1.4x PNG DATA',

      '1.8x/test.png': '1.8x PNG DATA',
    })

    html = chrome_html.ChromeHtml(tmp_dir.GetPath('index.html'))
    html.SetDefines({'scale_factors': '1.4x,1.8x'})
    html.Parse()
    self.failUnlessEqual(StandardizeHtml(html.GetData('en', 'utf-8')),
                         StandardizeHtml('''
      <!DOCTYPE HTML>
      <html>
        <head>
          <style>
      .image {
        background: -webkit-image-set(url("data:image/png;base64,UE5HIERBVEE=") 1x, url("data:image/png;base64,MS40eCBQTkcgREFUQQ==") 1.4x, url("data:image/png;base64,MS44eCBQTkcgREFUQQ==") 1.8x);
      }
      </style>
        </head>
        <body>
          <!-- Don't need a body. -->
        </body>
      </html>
      '''))
    tmp_dir.CleanUp()

  def testFileResourcesNoFile(self):
    '''Tests inlined image file resources without available high DPI assets.'''

    tmp_dir = TempDir({
      'index.html': '''
      <!DOCTYPE HTML>
      <html>
        <head>
          <link rel="stylesheet" href="test.css">
        </head>
        <body>
          <!-- Don't need a body. -->
        </body>
      </html>
      ''',

      'test.css': '''
      .image {
        background: url('test.png');
      }
      ''',

      'test.png': 'PNG DATA',
    })

    html = chrome_html.ChromeHtml(tmp_dir.GetPath('index.html'))
    html.SetDefines({'scale_factors': '2x'})
    html.Parse()
    self.failUnlessEqual(StandardizeHtml(html.GetData('en', 'utf-8')),
                         StandardizeHtml('''
      <!DOCTYPE HTML>
      <html>
        <head>
          <style>
      .image {
        background: -webkit-image-set(url("data:image/png;base64,UE5HIERBVEE=") 1x);
      }
      </style>
        </head>
        <body>
          <!-- Don't need a body. -->
        </body>
      </html>
      '''))
    tmp_dir.CleanUp()

  def testThemeResources(self):
    '''Tests inserting high DPI chrome://theme references.'''

    tmp_dir = TempDir({
      'index.html': '''
      <!DOCTYPE HTML>
      <html>
        <head>
          <link rel="stylesheet" href="test.css">
        </head>
        <body>
          <!-- Don't need a body. -->
        </body>
      </html>
      ''',

      'test.css': '''
      .image {
        background: url('chrome://theme/IDR_RESOURCE_NAME');
      }
      ''',
    })

    html = chrome_html.ChromeHtml(tmp_dir.GetPath('index.html'))
    html.SetDefines({'scale_factors': '2x'})
    html.Parse()
    self.failUnlessEqual(StandardizeHtml(html.GetData('en', 'utf-8')),
                         StandardizeHtml('''
      <!DOCTYPE HTML>
      <html>
        <head>
          <style>
      .image {
        background: -webkit-image-set(url("chrome://theme/IDR_RESOURCE_NAME") 1x, url("chrome://theme/IDR_RESOURCE_NAME@2x") 2x);
      }
      </style>
        </head>
        <body>
          <!-- Don't need a body. -->
        </body>
      </html>
      '''))
    tmp_dir.CleanUp()


if __name__ == '__main__':
  unittest.main()
