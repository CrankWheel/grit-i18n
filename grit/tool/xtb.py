#!/usr/bin/env python
# Copyright (c) 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The 'grit xtb' tool.
"""

import getopt
import os

from xml.sax import saxutils

from grit import grd_reader
from grit import lazy_re
from grit import tclib
from grit import util
from grit.tool import interface
from grit.tool import xmb


# Used to collapse presentable content to determine if
# xml:space="preserve" is needed.
_WHITESPACES_REGEX = lazy_re.compile(ur'\s\s*')


# See XmlEscape below.
_XML_QUOTE_ESCAPES = {
    u"'":  u'&apos;',
    u'"':  u'&quot;',
}
_XML_BAD_CHAR_REGEX = lazy_re.compile(u'[^\u0009\u000A\u000D'
                                      u'\u0020-\uD7FF\uE000-\uFFFD]')


def _XmlEscape(s):
  """Returns text escaped for XML in a way compatible with Google's
  internal Translation Console tool.  May be used for attributes as
  well as for contents.
  """
  if not type(s) == unicode:
    s = unicode(s)
  result = saxutils.escape(s, _XML_QUOTE_ESCAPES)
  return _XML_BAD_CHAR_REGEX.sub(u'', result).encode('utf-8')


def _WriteAttribute(file, name, value):
  """Writes an XML attribute to the specified file.

    Args:
      file: file to write to
      name: name of the attribute
      value: (unescaped) value of the attribute
    """
  if value:
    file.write(' %s="%s"' % (name, _XmlEscape(value)))


def _WriteMessage(file, message):
  presentable_content = message.GetPresentableContent()
  assert (type(presentable_content) == unicode or
          (len(message.parts) == 1 and
           type(message.parts[0] == tclib.Placeholder)))
  preserve_space = presentable_content != _WHITESPACES_REGEX.sub(
      u' ', presentable_content.strip())

  file.write('<translation')
  _WriteAttribute(file, 'id', message.GetId())
  if preserve_space:
    _WriteAttribute(file, 'xml:space', 'preserve')
  file.write('>')
  if not preserve_space:
    file.write('\n  ')

  parts = message.GetContent()
  for part in parts:
    if isinstance(part, tclib.Placeholder):
      file.write('<ph')
      _WriteAttribute(file, 'name', part.GetPresentation())
      file.write('/>')
    else:
      file.write(_XmlEscape(part))
  if not preserve_space:
    file.write('\n')
  file.write('</translation>\n')


def WriteXtbFile(file, messages):
  """Writes the given grit.tclib.Message items to the specified open
  file-like object in the XTB format.
  """
  file.write("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE translationbundle [
<!ELEMENT translationbundle (translation)*>
<!ATTLIST translationbundle class CDATA #IMPLIED>

<!ELEMENT translation (#PCDATA|ph)*>
<!ATTLIST translation id CDATA #IMPLIED>
<!ATTLIST msg xml:space (default|preserve) "default">

<!ELEMENT ph (#PCDATA|ex)*>
<!ATTLIST ph name CDATA #REQUIRED>
<translationbundle>
""")
  for message in messages:
    _WriteMessage(file, message)
  file.write('</translationbundle>')


def WriteMessagesToFile(file, messages):
  file.write('// Do not translate lines that start with //, like this one.\n//\n')
  for message in messages:
    file.write('// ID %s\n' % message.GetId())

    parts = message.GetContent()
    do_not_translate = []
    for part in parts:
      if isinstance(part, tclib.Placeholder):
        do_not_translate += [part.GetPresentation()]

    if do_not_translate:
      file.write('// Please do not modify the following parts of this message:\n')
      for dnt in do_not_translate:
        file.write('// %s\n' % dnt)

    file.write(message.GetPresentableContent().encode('utf-8'))
    file.write('\n\n\n')


class OutputXtbUntranslated(interface.Tool):
  """Outputs translateable messages in the .grd input file THAT DO NOT YET
HAVE A TRANSLATION to an .xtb file, which is the format that Google's internal
Translation Console tool outputs.

Usage: grit xtb LANG OUTPUTPATH

LANG is the language you want to use to determine whether messages already
have a translation or not.

OUTPUTPATH is the path you want to output the .xtb file to.

Other options:

  -D NAME[=VAL]     Specify a C-preprocessor-like define NAME with optional
                    value VAL (defaults to 1) which will be used to control
                    conditional inclusion of resources.

  -E NAME=VALUE     Set environment variable NAME to VALUE (within grit).

"""

  def __init__(self, defines=None):
    super(OutputXtbUntranslated, self).__init__()
    self.defines = defines or {}

  def ShortDescription(self):
    return 'Exports all untranslated messages into an XTB file.'

  def Run(self, opts, args):
    self.SetOptions(opts)

    limit_file = None
    limit_is_grd = False
    limit_file_dir = None
    output_format = 'xtb'
    own_opts, args = getopt.getopt(args, 'D:E:tp')
    for key, val in own_opts:
      if key == '-D':
        name, val = util.ParseDefine(val)
        self.defines[name] = val
      elif key == '-E':
        (env_name, env_value) = val.split('=', 1)
        os.environ[env_name] = env_value
      elif key == '-t':
        output_format = 'text'
      elif key == '-p':
        output_format = 'pot'
    if not len(args) == 2:
      print ('grit xtb takes exactly two arguments, LANG and OUTPUTPATH')
      return 2

    lang = args[0]
    xmb_path = args[1]
    res_tree = grd_reader.Parse(opts.input, debug=opts.extra_verbose)
    res_tree.SetOutputLanguage(lang)
    res_tree.SetDefines(self.defines)
    res_tree.OnlyTheseTranslations([lang])
    res_tree.RunGatherers()

    with open(xmb_path, 'wb') as output_file:
      self.Process(lang, res_tree, output_file, output_format)
    if limit_file:
      limit_file.close()
    print "Wrote %s" % xmb_path

  def Process(self, lang, res_tree, output_file, output_format):
    """Writes a document with the contents of res_tree into output_file,
    limiting output to messages missing translations.

    Args:
      lang: Language to check, e.g. 'is' or 'fr'
      res_tree: base.Node()
      output_file: file open for writing
    """
    ids_already_done = {}
    messages = []
    for node in res_tree:
      if not node.IsTranslateable():
        continue

      for clique in node.GetCliques():
        if not clique.IsTranslateable():
          continue
        if not clique.GetMessage().GetRealContent():
          continue

        # Some explanation is in order here.  Note that we can have
        # many messages with the same ID.
        #
        # The way we work around this is to maintain a list of cliques
        # per message ID (in the UberClique) and select the "best" one
        # (the first one that has a description, or an arbitrary one
        # if there is no description) for inclusion in the XMB file.
        # The translations are all going to be the same for messages
        # with the same ID, although the way we replace placeholders
        # might be slightly different.
        id = clique.GetMessage().GetId()
        if id in ids_already_done:
          continue
        ids_already_done[id] = 1

        clique = node.UberClique().BestClique(id)
        message = clique.GetMessage()
        # This indicates that there is no translation.
        if not lang in clique.clique.keys():
          messages += [message]

    # Ensure a stable order of messages, to help regression testing.
    messages.sort(key=lambda x:x.GetId())

    if output_format == 'xtb':
      WriteXtbFile(output_file, messages)
    elif output_format == 'text':
      WriteMessagesToFile(output_file, messages)
    elif output_format == 'pot':
      xmb.WritePotFile(output_file, messages)
    else:
      print "Unknown message format."
