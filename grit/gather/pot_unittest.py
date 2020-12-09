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
msgid "Hello <font size='+1'>user!</font>, <i>how are you?</i>"
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

msgid "To activate phone conferencing we need to sign you up to use <a href=\"https://www.conferencecall.co.uk/?utm_source=crankwheel&utm_campaign=options_page&utm_medium=affiliate\" target=\"_blank\">ConferenceCall.co.uk</a> services using your email address, <strong class=\"user-email-address\"></strong>."
msgstr ""

msgid "Here <a href=\"foo\">link</a> and there <a href=\"boo\">another link</a>."
msgstr ""

msgid "You can use <tt>{{emailAddress}}</tt>, <tt>{{name}}</tt> and <tt>{{frumpymump}}</tt> as replaceables."
msgstr ""

msgid "There can also be <br/> a mix... of these <a href=\"foo\">links</a> and <br/> <a href=\"boo\">things</a>."
msgstr ""
"""


INTENDED_OUTPUT = ur"""msgid "Hello <font size='+1'>user!</font>, <i>how are you?</i>"
msgstr "HéPéllôPô <font size='+1'>üPüséPér!</font>, <i>hôPôw åPåréPé ýôüPýôü?</i>"


msgid "Email domain reserved for %{lname} (%{sname}). Please contact your administrator for access."
msgstr "ÉPÉmåïPåïl dôPômåïPåïn réPéséPérvéPéd fôPôr %{lname} (%{sname}). PléåPéåséPé côPôntåPåct ýôüPýôür åPådmïPïnïPïstråPåtôPôr fôPôr åPåccéPéss."


msgid "Success!\nGo ahead!!"
msgstr "SüPüccéPéss!\nGôPô åPåhéåPéåd!!"


msgid "Recording \\ \"preview\""
msgstr "RéPécôPôrdïPïng \\ \"préPévïéPïéw\""


msgid "To activate phone conferencing we need to sign you up to use <a href=\"https://www.conferencecall.co.uk/?utm_source=crankwheel&utm_campaign=options_page&utm_medium=affiliate\" target=\"_blank\">ConferenceCall.co.uk</a> services using your email address, <strong class=\"user-email-address\"></strong>."
msgstr "TôPô åPåctïPïvåPåtéPé phôPônéPé côPônféPéréPéncïPïng wéPé nééPééd tôPô sïPïgn ýôüPýôü üPüp tôPô üPüséPé <a href=\"https://www.conferencecall.co.uk/?utm_source=crankwheel&utm_campaign=options_page&utm_medium=affiliate\" target=\"_blank\">CôPônféPéréPéncéPéCåPåll.côPô.üPük</a> séPérvïPïcéPés üPüsïPïng ýôüPýôür éPémåïPåïl åPåddréPéss, <strong class=\"user-email-address\"></strong>."


msgid "Here <a href=\"foo\">link</a> and there <a href=\"boo\">another link</a>."
msgstr "HéPéréPé <a href=\"foo\">lïPïnk</a> åPånd théPéréPé <a href=\"boo\">åPånôPôthéPér lïPïnk</a>."


msgid "You can use <tt>{{emailAddress}}</tt>, <tt>{{name}}</tt> and <tt>{{frumpymump}}</tt> as replaceables."
msgstr "ÝôüPÝôü cåPån üPüséPé <tt>{{éPémåïPåïlÅPÅddréPéss}}</tt>, <tt>{{nåPåméPé}}</tt> åPånd <tt>{{früPümpýPýmüPümp}}</tt> åPås réPéplåPåcéåPéåbléPés."


msgid "There can also be <br/> a mix... of these <a href=\"foo\">links</a> and <br/> <a href=\"boo\">things</a>."
msgstr "ThéPéréPé cåPån åPålsôPô béPé <br/> åPå mïPïx... ôPôf théPéséPé <a href=\"foo\">lïPïnks</a> åPånd <br/> <a href=\"boo\">thïPïngs</a>."
"""


class PotUnittest(unittest.TestCase):
  def testGather(self):
    input = StringIO.StringIO(POT_FILE)
    gatherer = pot.PotFile(input)
    gatherer.Parse()
    self.failUnlessEqual(gatherer.GetText(), input.getvalue())
    self.failUnlessEqual(len(gatherer.GetCliques()), 8)
    self.failUnlessEqual(gatherer.GetCliques()[0].GetMessage().GetRealContent(),
                         r"Hello <font size='+1'>user!</font>, <i>how are you?</i>")
    self.failUnlessEqual(gatherer.GetCliques()[0].GetMessage().GetPresentableContent(),
                         r"Hello BEGIN_FONTuser!END_FONT, BEGIN_ITALIChow are you?END_ITALIC")
    self.failUnlessEqual(gatherer.GetCliques()[1].GetMessage().GetRealContent(),
                         r"Email domain reserved for %{lname} (%{sname}). Please contact your administrator for access.")
    self.failUnlessEqual(gatherer.GetCliques()[1].GetMessage().GetPresentableContent(),
                         r"Email domain reserved for LNAME (SNAME). Please contact your administrator for access.")
    self.failUnlessEqual(gatherer.GetCliques()[4].GetMessage().GetPresentableContent(),
                         r"To activate phone conferencing we need to sign you up to use BEGIN_LINKConferenceCall.co.ukEND_LINK services using your email address, BEGIN_STRONGEND_STRONG.")
    self.failUnlessEqual(gatherer.GetCliques()[5].GetMessage().GetPresentableContent(),
                         r"Here BEGIN_LINKlinkEND_LINK and there BEGIN_LINK_2another linkEND_LINK_2.")
    self.failUnlessEqual(gatherer.GetCliques()[6].GetMessage().GetPresentableContent(),
                         r"You can use BEGIN_TT{{emailAddress}}END_TT, BEGIN_TT_2{{name}}END_TT_2 and BEGIN_TT_3{{frumpymump}}END_TT_3 as replaceables.")
    self.failUnlessEqual(gatherer.GetCliques()[7].GetMessage().GetPresentableContent(),
                         r"There can also be BREAK a mix... of these BEGIN_LINKlinksEND_LINK and BREAK_2 BEGIN_LINK_2thingsEND_LINK_2.")
    self.maxDiff = None
    self.failUnlessEqual(gatherer.Translate('fr').strip(),
                         INTENDED_OUTPUT.strip())


if __name__ == '__main__':
  unittest.main()

