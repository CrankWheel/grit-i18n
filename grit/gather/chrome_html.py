#!/usr/bin/env python
# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Prepares a Chrome HTML file by inlining resources and adding references to
high DPI resources.

This is a small gatherer that takes a HTML file, looks for src attributes
and inlines the specified file, producing one HTML file with no external
dependencies. It recursively inlines the included files. When inlining CSS
image files this script also checks for the existence of high DPI versions
of the inlined file including those on relevant platforms.
"""

import os
import re
import sys
import types
import base64
import mimetypes

from grit.gather import interface
from grit.format import html_inline
from grit import lazy_re
from grit import util


# Matches a chrome theme source URL.
_THEME_SOURCE = lazy_re.compile('chrome://theme/IDR_[A-Z0-9_]*')
# Matches CSS image urls with the capture group 'filename'.
_CSS_IMAGE_URLS = lazy_re.compile(
    '(?P<attribute>content|background|[\w-]*-image):[ ]*' +
    'url\((?:\'|\")(?P<filename>[^"\'\)\(]*)(?:\'|\")')


def InsertImageSet(
    src_match, base_path, scale_factors, distribution):
  """Regex replace function which inserts -webkit-image-set.

  Takes a regex match for url('path'). If the file is local, checks for
  files of the same name in folders corresponding to the supported scale
  factors. If the file is from a chrome://theme/ source, inserts the
  supported @Nx scale factor request. In either case inserts a
  -webkit-image-set rule to fetch the appropriate image for the current
  scale factor.

  Args:
    src_match: regex match object from _CSS_IMAGE_URLS
    base_path: path to look for relative file paths in
    scale_factors: a list of the supported scale factors (i.e. ['2x'])
    distribution: string that should replace %DISTRIBUTION%.

  Returns:
    string
  """
  filename = src_match.group('filename')
  attr = src_match.group('attribute')
  prefix = src_match.string[src_match.start():src_match.start('filename')-1]

  # Any matches for which a chrome URL handler will serve all scale factors
  # can simply request all scale factors.
  if _THEME_SOURCE.match(filename):
    images = ["url(\"%s\") %s" % (filename, '1x')]
    for sc in scale_factors:
      images.append("url(\"%s@%s\") %s" % (filename, sc, sc))
    return "%s: -webkit-image-set(%s" % (attr, ', '.join(images))

  if filename.find(':') != -1:
    # filename is probably a URL, which we don't want to bother inlining
    return src_match.group(0)

  filename = filename.replace('%DISTRIBUTION%', distribution)
  filepath = os.path.join(base_path, filename)
  images = ["url(\"%s\") %s" % (filename, '1x')]

  for sc in scale_factors:
    # Check for existence of file and add to image set.
    scale_path = os.path.split(os.path.join(base_path, filename))
    scale_image_path = os.path.join(scale_path[0], sc, scale_path[1])
    if os.path.isfile(scale_image_path):
      # CSS always uses forward slashed paths.
      scale_image_name = re.sub('(?P<path>(.*/)?)(?P<file>[^/]*)',
                                '\\g<path>' + sc + '/\\g<file>',
                                filename)
      images.append("url(\"%s\") %s" % (scale_image_name, sc))
  return "%s: -webkit-image-set(%s" % (attr, ', '.join(images))

def InsertImageSets(
    filepath, text, scale_factors, distribution):
  """Helper function that adds references to external images available in any of
  scale_factors in CSS backgrounds."""
  # Add high DPI urls for css attributes: content, background,
  # or *-image.
  return _CSS_IMAGE_URLS.sub(
      lambda m: InsertImageSet(m, filepath, scale_factors, distribution),
      text).decode('utf-8').encode('ascii', 'ignore')


class ChromeHtml(interface.GathererBase):
  """Represents an HTML document processed for Chrome WebUI.

  HTML documents used in Chrome WebUI have local resources inlined and
  automatically insert references to high DPI assets used in CSS properties
  with the use of the -webkit-image-set value. This does not generate any
  translateable messages and instead generates a single DataPack resource.
  """

  def __init__(self, html):
    """Creates a new object that represents the file 'html'.
    Args:
      html: 'filename.html'
    """
    super(type(self), self).__init__()
    self.filename_ = html
    self.inlined_text_ = None
    # 1x resources are implicitly already in the source and do not need to be
    # added.
    self.scale_factors_ = []

  def SetDefines(self, defines):
    if 'scale_factors' in defines:
      self.scale_factors_ = defines['scale_factors'].split(',')

  def GetText(self):
    """Returns inlined text of the HTML document."""
    return self.inlined_text_

  def GetData(self, lang, encoding):
    """Returns inlined text of the HTML document."""
    return self.inlined_text_

  def Translate(self, lang, pseudo_if_not_available=True,
                skeleton_gatherer=None, fallback_to_english=False):
    """Returns this document translated."""
    return self.inlined_text_

  def Parse(self):
    """Parses and inlines the represented file."""
    self.inlined_text_ = html_inline.InlineToString(self.filename_, None,
        rewrite_function=lambda fp, t, d: InsertImageSets(
            fp, t, self.scale_factors_, d))

  @staticmethod
  def FromFile(html, extkey=None, encoding = 'utf-8'):
    """Creates a ChromeHtml object for the contents of 'html'.  Returns a new
    ChromeHtml object.

    Args:
      html: file('') | 'filename.html'
      extkey: ignored
      encoding: 'utf-8' (encoding is ignored)

    Return:
      ChromeHtml(text_of_file)
    """
    if not isinstance(html, types.StringTypes):
      html = html.name

    return ChromeHtml(html)
