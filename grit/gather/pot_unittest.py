#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (c) 2020 CrankWheel ehf. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

'''Unit tests for PotFile gatherer'''


import os
import sys
if __name__ == '__main__':
  sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))


import StringIO
import unittest

from grit.gather import pot

POT_FILE = r"""## This file is a PO Template file.
## `msgid`s here are often extracted from source code.
msgid ""
msgstr ""

#: web/controllers/auth_controller_common.ex:139
msgid "Email domain reserved for %{lname} (%{sname}). Please contact your administrator for access."
msgstr ""

#: web/templates/webext/recording.html.eex:71
msgid "Success!\nGo ahead!!"
msgstr ""

#: web/templates/webext/recording.html.eex:19
msgid "Recording \\ \"preview\""
msgstr ""
"""

INTENDED_OUTPUT = ur"""msgid "Email domain reserved for %{lname} (%{sname}). Please contact your administrator for access."
msgstr "ÉPÉmåïPåïl dôPômåïPåïn réPéséPérvéPéd fôPôr %{lname} (%{sname}). PléåPéåséPé côPôntåPåct ýôüPýôür åPådmïPïnïPïstråPåtôPôr fôPôr åPåccéPéss."


msgid "Success!\nGo ahead!!"
msgstr "SüPüccéPéss!\nGôPô åPåhéåPéåd!!"


msgid "Recording \\ \"preview\""
msgstr "RéPécôPôrdïPïng \\ \"préPévïéPïéw\""
"""


class PotUnittest(unittest.TestCase):
  def testGather(self):
    input = StringIO.StringIO(POT_FILE)
    gatherer = pot.PotFile(input)
    gatherer.Parse()
    self.failUnless(gatherer.GetText() == input.getvalue())
    self.failUnless(len(gatherer.GetCliques()) == 3)
    self.failUnless(gatherer.GetCliques()[0].GetMessage().GetRealContent() ==
                    r"Email domain reserved for %{lname} (%{sname}). Please contact your administrator for access.")
    self.failUnless(gatherer.Translate('fr').strip() == INTENDED_OUTPUT.strip())


if __name__ == '__main__':
  unittest.main()

