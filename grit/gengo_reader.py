#!/usr/bin/env python

'''Parser to use our specialized format for Gengo as a translation source.
'''


import codecs
import re
import sys


_MSG_RE = re.compile(
    r'\[\[\[\.BEGIN\.(?P<msgid>[0-9]+)\.\]\]\](?P<msgbody>.*?)\[\[\[\.END\.\]\]\]',
    re.DOTALL | re.MULTILINE)

_PH_RE = re.compile(r'\[\[\[(?P<phname>[^\|]+)\|[^\]]*\]\]\]')


def Parse(gengo_file, callback_function):
  '''Parse po_file, making a call to callback_function for every translation
  in the PO file.

  The callback function must have the signature as described below.  The 'parts'
  parameter is a list of tuples (is_placeholder, text).  The 'text' part is
  either the raw text (if is_placeholder is False) or the name of the placeholder
  (if is_placeholder is True).

  The PO reader does not support conditionals or target platform specifications,
  so the 'defs' and 'target_platform' parameters are ignored.

  Args:
    po_file:            open('fr.po')
    callback_function:  def Callback(msg_id, parts): pass

  Return:
    None
  '''
  def MakeTextPart(text):
    return (False, text)

  contents = codecs.decode(gengo_file.read(), 'utf-8')
  messages = _MSG_RE.findall(contents)
  for (message_id, message) in messages:
    parts = []
    while True:
      match = _PH_RE.search(message)
      if match:
        ph_name = match.group('phname')
        len_before = match.start()
        normal_text_before = message[:len_before]
        if len(normal_text_before):
          parts.append(MakeTextPart(normal_text_before))
        parts.append((True, ph_name))
        message = message[match.end():]
      else:
        if len(message):
          parts.append(MakeTextPart(message))
        break
    callback_function(message_id, parts)


if __name__ == '__main__':
  def JustPrint(msg_id, parts):
    print 'msg_id %s' % msg_id
    print parts
  with open(sys.argv[1]) as f:
    Parse(f, JustPrint)
