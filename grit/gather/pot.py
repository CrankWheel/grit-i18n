#!/usr/bin/env python
# Copyright (c) 2020 CrankWheel ehf. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Supports making messages from a POT file (i.e. gettext).
'''

from grit.gather import interface
from grit import tclib

import re

MSG_RE = re.compile('^\s*\msgid\s"(?P<msg>.+)\"\s*$')

_HTML_PLACEHOLDER_NAMES = { 'a' : 'link', 'br' : 'break', 'b' : 'bold',
  'i' : 'italic', 'li' : 'item', 'ol' : 'ordered_list', 'p' : 'paragraph',
  'ul' : 'unordered_list', 'img' : 'image', 'em' : 'emphasis' }


def Unescape(msg):
  msg = msg.replace("\\n", "\n")
  msg = re.sub(r'\\(.)', r'\1', msg)
  return msg


def Escape(msg):
  msg = msg.replace("\\", "\\\\")
  msg = msg.replace("\"", "\\\"")
  msg = msg.replace("\n", "\\n")
  return msg


def MakeHtmlPlaceholderName(tag_name, type = None):
  if tag_name in _HTML_PLACEHOLDER_NAMES:  # use meaningful names
    tag_name = _HTML_PLACEHOLDER_NAMES[tag_name]
  if type == 'begin':
    return 'BEGIN_' + tag_name.upper()
  elif type == 'end':
    return 'END_' + tag_name.upper()
  else:
    return tag_name.upper()


def GetPlaceholderizedText(msg):
  tags_encountered = {}
  def AssertIfSameTagTwice(tag_name):
    tag_name = tag_name.upper()
    if tag_name in tags_encountered.keys():
      raise "This gatherer can't handle the same tag twice in a message"
    else:
      tags_encountered[tag_name] = 1

  def Replacement(matchobj):
    (gettext_ph, open_tag_contents, open_tag, close_tag_contents, close_tag, unary_tag_contents, unary_tag) = matchobj.groups()
    if gettext_ph:
      return gettext_ph.upper()
    elif open_tag:
      AssertIfSameTagTwice(open_tag)
      return MakeHtmlPlaceholderName(open_tag, 'begin')
    elif close_tag:
      return MakeHtmlPlaceholderName(close_tag, 'end')
    elif unary_tag:
      AssertIfSameTagTwice(unary_tag)
      return MakeHtmlPlaceholderName(unary_tag)
  return re.sub('%{([^}]+)}|<(([a-zA-Z]+)[^>^/]*)>|</(([a-zA-Z]+)[^>^/]*)>|<(([a-zA-Z]+)[^>^/]*)/>', Replacement, msg)


def GetPlaceholders(msg):
  ph_names = re.findall('%{([^}]+)}|<(([a-zA-Z]+)[^>^/]*)>|</(([a-zA-Z]+)[^>^/]*)>|<(([a-zA-Z]+)[^>^/]*)/>', msg)
  placeholders = []
  for (gettext_ph, open_tag_contents, open_tag, close_tag_contents, close_tag, unary_tag_contents, unary_tag) in ph_names:
    if gettext_ph != '':
      placeholders.append(tclib.Placeholder(gettext_ph.upper(), '%%{%s}' % gettext_ph, '(replaceable)'))
    elif open_tag != '':
      placeholders.append(tclib.Placeholder(MakeHtmlPlaceholderName(open_tag, 'begin'), '<%s>' % open_tag_contents, '(HTML code)'))
    elif close_tag != '':
      placeholders.append(tclib.Placeholder(MakeHtmlPlaceholderName(close_tag, 'end'), '</%s>' % close_tag_contents, '(HTML code)'))
    elif unary_tag != '':
      placeholders.append(tclib.Placeholder(MakeHtmlPlaceholderName(unary_tag), '<%s/>' % unary_tag_contents, '(HTML code)'))
  return placeholders


def ParseFile(text, uberclique):
  cliques = []
  lines = text.split('\n')
  for line in lines:
    match = MSG_RE.match(line)
    if match:
      msg = match.group('msg')
      msg = Unescape(msg)
      placeholders = GetPlaceholders(msg)
      msg = GetPlaceholderizedText(msg)
      cliques.append(uberclique.MakeClique(tclib.Message(text=msg, placeholders=placeholders)))
  return cliques


class PotFile(interface.GathererBase):
  '''A POT file gatherer. Each message template becomes a clique.
  '''

  def Parse(self):
    self.text_ = self._LoadInputFile()
    self.cliques_ = ParseFile(self.text_, self.uberclique)

  def GetText(self):
    return self.text_

  def GetTextualIds(self):
    return [self.extkey]

  def GetCliques(self):
    return self.cliques_

  def Translate(self, lang, pseudo_if_not_available=True,
                skeleton_gatherer=None, fallback_to_english=False):
    lines = []
    for clique in self.cliques_:
      lines.append("msgid \"%s\"" % Escape(clique.MessageForLanguage('en', False, False).GetRealContent()))
      lines.append("msgstr \"%s\"" % Escape(clique.MessageForLanguage(lang, pseudo_if_not_available, fallback_to_english).GetRealContent()))
      lines.append("\n")
    return '\n'.join(lines)
