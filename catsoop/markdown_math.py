# This file is part of CAT-SOOP
# Copyright (c) 2011-2020 by The CAT-SOOP Developers <catsoop-dev@mit.edu>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""CAT-SOOP Math Mode Extension for PyMarkdown"""

from markdown.extensions import Extension
from markdown.inlinepatterns import HtmlInlineProcessor, SimpleTextInlineProcessor

_nodoc = {
    "Extension",
    "HtmlInlineProcessor",
    "SimpleTextInlineProcessor",
    "absolute_import",
    "unicode_literals",
}

_MATH_RE = r"(?:^|(?<!\\))\$(?P<body>(?:\\\$|[^$])*)\$"
_DMATH_RE = r"\$\$(?P<body>.*?)\$\$"
_DMATHENV_RE = r"\\begin\s*{(?P<env>(?:equation|eqnarray|align)\*?)}(?P<body>(?s).*?)\\end\s*{(?P=env)}"
_ESCAPED_DOLLAR_RE = r"(?<!\\)\\(\$)"


class RawHtmlInlineProcessor(HtmlInlineProcessor):
    """A subclass of `catsoop.thirdparty.markdown.inlinepattern.HtmlInlineProcessor`
    used to store raw inline html and return a placeholder."""

    def __init__(self, endtag, *args, **kwargs):
        self._hz_tag = endtag
        HtmlInlineProcessor.__init__(self, *args, **kwargs)

    def handleMatch(self, m, data):
        groups = m.groupdict()
        body = self.unescape(groups["body"])
        env = groups.get("env", "")
        rawhtml = "<%(tag)s%(env)s>%(body)s</%(tag)s>" % {
            "tag": self._hz_tag,
            "body": body,
            "env": ' env="%s"' % env if env else "",
        }
        place_holder = self.md.htmlStash.store(rawhtml)
        return place_holder, m.start(0), m.end(0)


class MathExtension(Extension):
    """The CAT-SOOP math extension to Markdown."""

    def extendMarkdown(self, md):
        """ Modify inline patterns."""
        md.inlinePatterns.register(
            RawHtmlInlineProcessor("displaymath", _DMATHENV_RE, md),
            "catsoop_denvmath",
            203,
        )
        md.inlinePatterns.register(
            RawHtmlInlineProcessor("displaymath", _DMATH_RE, md), "catsoop_dmath", 183
        )
        md.inlinePatterns.register(
            RawHtmlInlineProcessor("math", _MATH_RE, md), "catsoop_math", 182
        )
        md.inlinePatterns.register(
            SimpleTextInlineProcessor(_ESCAPED_DOLLAR_RE), "catsoop_emath", 181
        )
