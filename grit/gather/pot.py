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


def Unescape(msg):
  msg = msg.replace("\\n", "\n")
  msg = re.sub(r'\\(.)', r'\1', msg)
  return msg


def Escape(msg):
  msg = msg.replace("\\", "\\\\")
  msg = msg.replace("\"", "\\\"")
  msg = msg.replace("\n", "\\n")
  return msg


def GetPlaceholderizedText(msg):
  def Replacement(matchobj):
    return matchobj.group(1).upper()
  return re.sub('%{([^}]+)}', Replacement, msg)


def GetPlaceholders(msg):
  ph_names = re.findall('%{([^}]+)}', msg)
  placeholders = []
  for ph in ph_names:
    placeholders.append(tclib.Placeholder(ph.upper(), '%%{%s}' % ph, '(replaceable)'))
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
