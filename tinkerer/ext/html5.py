"""
    html5
    ~~~~~

    Monkey-patch Sphinx HTML translator to emit HTML5.

    :copyright: Copyright 2011-2018 by Vlad Riscutia and contributors (see
    CONTRIBUTORS file)
    :license: FreeBSD, see LICENSE file.
"""

from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence
    from typing import Any, ClassVar

    from docutils.nodes import Element, Text

from docutils import nodes
from sphinx.writers.html import HTMLTranslator


def visit_desc_addname(self, node):
    '''
    Similar to Sphinx but using a <span> node instead of <tt>.
    '''
    self.body.append(self.starttag(node, 'span', '', CLASS='descclassname'))


def depart_desc_addname(self, node):
    '''
    Similar to Sphinx but using a <span> node instead of <tt>.
    '''
    self.body.append('</span>')


def visit_desc_name(self, node):
    '''
    Similar to Sphinx but using a <span> node instead of <tt>.
    '''
    self.body.append(self.starttag(node, 'span', '', CLASS='descname'))


def depart_desc_name(self, node):
    '''
    Similar to Sphinx but using a <span> node instead of <tt>.
    '''
    self.body.append('</span>')


def visit_literal(self, node):
    '''
    Similar to Sphinx but using a <span> node instead of <tt>.
    '''
    self.body.append(self.starttag(node, 'span', '',
                                   CLASS='docutils literal'))
    self.protect_literal_text += 1


def depart_literal(self, node):
    '''
    Similar to Sphinx but using a <span> node instead of <tt>.
    '''
    self.protect_literal_text -= 1
    self.body.append('</span>')



def depart_title(self, node) -> None:
    close_tag = self.context[-1]
    if (
        self.config.html_permalinks
        and self.builder.add_permalinks
        and node.parent.hasattr('ids')
        and node.parent['ids']
    ):
        # add permalink anchor
        if close_tag.startswith('</h'):
            self.add_permalink_ref(node.parent, _('Link to this heading'))
        elif close_tag.startswith('</a></h'):
            self.body.append(
                '</a><a class="headerlink" href="#%s" ' % node.parent['ids'][0]
                + 'title="{}">{}'.format(
                    _('Link to this heading'), self.config.html_permalinks_icon
                )
            )
        elif isinstance(node.parent, nodes.table):
            self.body.append('</span>')
            self.add_permalink_ref(node.parent, _('Link to this table'))
    elif isinstance(node.parent, nodes.table):
        self.body.append('</span>')

    #super().depart_title(node)
    HTMLTranslator._depart_title(self, node)


def patch_translator():
    '''
    Monkey-patch Sphinx translator to emit proper HTML5.
    '''
    HTMLTranslator.visit_desc_addname = visit_desc_addname
    HTMLTranslator.depart_desc_addname = depart_desc_addname
    HTMLTranslator.visit_desc_name = visit_desc_name
    HTMLTranslator.depart_desc_name = depart_desc_name
    HTMLTranslator.visit_literal = visit_literal
    HTMLTranslator.depart_literal = depart_literal

    #HTMLTranslator._depart_title = HTMLTranslator.depart_title
    #HTMLTranslator.depart_title = depart_title