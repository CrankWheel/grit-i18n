#!/usr/bin/env python

from grit import clique
from grit import exception
from grit import lazy_re
from grit import util
from grit import tclib

from grit.gather import interface

import json

class DodTemplate(interface.GathererBase):
  '''Represents a document or message in the template format used by
  Total Recall for HTML documents.'''

  def __init__(self, *args, **kwargs):
    super(DodTemplate, self).__init__(*args, **kwargs)
    self.have_parsed_ = False
    self.original_text_ = ''
    self.original_tree_ = {}

  def GetText(self):
    '''Returns the original text of the HTML document'''
    return self.text_

  def ProcessString(self, is_gather, output, prefix, tree):
    clique = self.uberclique.MakeClique(tclib.Message(text=tree, description=prefix))
    if is_gather:
      output = output.append(clique)
      return tree
    else:
      msg = clique.MessageForLanguage(self.lang_, self.pseudo_if_not_available_, self.fallback_to_english_)
      out = ''
      for content in msg.GetContent():
        if isinstance(content, tclib.Placeholder):
          out += content.GetOriginal()
        else:
          # We escape " characters to increase the chance that attributes
          # will be properly escaped.
          out += content
      return out

  def ProcessDict(self, is_gather, output, prefix, tree):
    new_dict = {}
    for key in tree:
      if key != 'type' and key != 'id':
        new_dict[key] = self.ProcessElement(is_gather, output, prefix + key + ' ', tree[key])
      else:
        new_dict[key] = tree[key]
    return new_dict

  def ProcessList(self, is_gather, output, prefix, tree):
    new_list = []
    for index in range(len(tree)):
      new_list.append(self.ProcessElement(is_gather, output, prefix + '[%d] ' % index, tree[index]))
    return new_list

  # If is_gather is True, this fills 'output' with the cliques it finds in the
  # tree. A deep copy of the tree is also returned but probably ignored.
  #
  # If it is false, original strings in 'tree' are replaced with translations
  # and a deep copy of the tree with translations applied is returned.
  def ProcessElement(self, is_gather, output, prefix, tree):
    if type(tree) == type({}):
      return self.ProcessDict(is_gather, output, prefix, tree)
    elif type(tree) == type([]):
      return self.ProcessList(is_gather, output, prefix, tree)
    elif type(tree) in [type(''), type(u'')]:
      return self.ProcessString(is_gather, output, prefix, tree)

  def GetCliques(self):
    '''Returns the message cliques for each translateable message in the
    document.'''
    cliques = []
    self.ProcessElement(True, cliques, '', self.original_tree_)
    return cliques

  def Translate(self, lang, pseudo_if_not_available=True,
                skeleton_gatherer=None, fallback_to_english=False):
    if not self.have_parsed_:
      raise exception.NotReady()
    self.lang_ = lang
    self.pseudo_if_not_available_ = pseudo_if_not_available
    self.fallback_to_english_ = fallback_to_english
    tree = self.ProcessElement(False, [], '', self.original_tree_)
    return json.dumps(tree, sort_keys=True, indent=2)

  def Parse(self):
    if self.have_parsed_:
      return
    self.have_parsed_ = True

    text = self._LoadInputFile()
    # Ignore the BOM character if the document starts with one.
    if text.startswith(u'\ufeff'):
      text = text[1:]
    self.original_text_ = text
    self.original_tree_ = json.loads(text)
