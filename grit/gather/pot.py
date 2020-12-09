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


def MakeHtmlPlaceholderName(tag_name, type, existing_tags):
  # The way we do this is a bit limited in case tags of the same type are
  # nested, but this will never (or at least almost never?) happen for the
  # types of tags that can be embedded in messages.
  exist_count = len([name for name in existing_tags if name == tag_name])
  postfix = ''
  if exist_count > 1:
    postfix = '_%d' % exist_count

  if tag_name in _HTML_PLACEHOLDER_NAMES:  # use meaningful names
    tag_name = _HTML_PLACEHOLDER_NAMES[tag_name]

  if type == 'begin':
    return 'BEGIN_' + tag_name.upper() + postfix
  elif type == 'end':
    return 'END_' + tag_name.upper() + postfix
  else:
    return tag_name.upper() + postfix


def GetPlaceholderizedText(msg):
  tag_list = []
  def Replacement(matchobj):
    (gettext_ph, open_tag_contents, open_tag, close_tag_contents, close_tag, unary_tag_contents, unary_tag) = matchobj.groups()
    if gettext_ph:
      return gettext_ph.upper()
    elif open_tag:
      tag_list.append(open_tag)
      return MakeHtmlPlaceholderName(open_tag, 'begin', tag_list)
    elif close_tag:
      return MakeHtmlPlaceholderName(close_tag, 'end', tag_list)
    elif unary_tag:
      tag_list.append(unary_tag)
      return MakeHtmlPlaceholderName(unary_tag, None, tag_list)
  return re.sub('%{([^}]+)}|<(([a-zA-Z]+)[^>]*)(?<!/)>|</(([a-zA-Z]+)[^>]*)>|<(([a-zA-Z]+)[^>]*)/>', Replacement, msg)


def GetPlaceholders(msg):
  tag_list = []
  ph_names = re.findall('%{([^}]+)}|<(([a-zA-Z]+)[^>]*)(?<!/)>|</(([a-zA-Z]+)[^>]*)>|<(([a-zA-Z]+)[^>]*)/>', msg)
  placeholders = []
  for (gettext_ph, open_tag_contents, open_tag, close_tag_contents, close_tag, unary_tag_contents, unary_tag) in ph_names:
    if gettext_ph != '':
      placeholders.append(tclib.Placeholder(gettext_ph.upper(), '%%{%s}' % gettext_ph, '(replaceable)'))
    elif open_tag != '':
      tag_list.append(open_tag)
      placeholders.append(tclib.Placeholder(MakeHtmlPlaceholderName(open_tag, 'begin', tag_list), '<%s>' % open_tag_contents, '(HTML code)'))
    elif close_tag != '':
      placeholders.append(tclib.Placeholder(MakeHtmlPlaceholderName(close_tag, 'end', tag_list), '</%s>' % close_tag_contents, '(HTML code)'))
    elif unary_tag != '':
      tag_list.append(unary_tag)
      placeholders.append(tclib.Placeholder(MakeHtmlPlaceholderName(unary_tag, None, tag_list), '<%s/>' % unary_tag_contents, '(HTML code)'))
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
