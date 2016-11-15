#!/usr/bin/env python

'''Parser to use a PO file as a translation source.
'''


import codecs
import re
import sys


_PH_RE = re.compile(r'(^|.*?[^\\])%{(?P<phname>[^}]+?)}')


def Parse(po_file, callback_function, defs=None, debug=False,
          target_platform=None):
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
    defs:               None, or a dictionary of preprocessor definitions.
    debug:              Default False. Set True for verbose debug output.
    target_platform:    None, or a sys.platform-like identifier of the build
                        target platform.

  Return:
    None
  '''
  def MakeTextPart(text):
    return (False, text)
  msg_id = None
  for line in po_file.readlines():
    line = codecs.decode(line, 'utf-8')
    if not msg_id:
      if line.startswith('#: id: '):
        msg_id = line[7:].strip()
    else:
      if line.startswith('msgstr'):
        quoted_text = line[6:].strip()
        unquoted_text = quoted_text[1:-1]
        parts = []
        while True:
          match = _PH_RE.match(unquoted_text)
          if match:
            ph_name = match.group('phname')
            len_before = match.end() - len(ph_name) - 3
            normal_text_before = unquoted_text[:len_before]
            if len(normal_text_before):
              parts.append(MakeTextPart(normal_text_before))
            parts.append((True, ph_name))
            unquoted_text = unquoted_text[match.end():]
          else:
            if len(unquoted_text):
              parts.append(MakeTextPart(unquoted_text))
            break
        callback_function(msg_id, parts)
        msg_id = None
        parts = []


if __name__ == '__main__':
  def JustPrint(msg_id, parts):
    print 'msg_id %s' % msg_id
    print parts
  with open(sys.argv[1]) as f:
    Parse(f, JustPrint)
