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
"""CAT-SOOP Math Mode Extension for Mistletoe"""

import re

from mistletoe import Document
from mistletoe.span_token import SpanToken
from mistletoe.html_renderer import HTMLRenderer


class Math(SpanToken):
    pattern = re.compile(r"(?:^|(?<!\\))\$(?P<body>(?:\\\$|[^$])*)\$")
    parse_inner = False

    def __init__(self, match):
        self.body = match.group("body")


class DisplayMath(SpanToken):
    pattern = re.compile(r"\$\$(?P<body>.*?)\$\$", re.MULTILINE | re.DOTALL)
    parse_inner = False
    precedence = SpanToken.precedence + 2

    def __init__(self, match):
        self.body = match.group("body")


class DisplayMathEnv(SpanToken):
    pattern = re.compile(
        r"\\begin\s*{(?P<env>(?:equation|eqnarray|align)\*?)}(?P<body>(?s).*?)\\end\s*{(?P=env)}",
        re.MULTILINE | re.DOTALL,
    )
    parse_inner = False
    precedence = SpanToken.precedence + 1

    def __init__(self, match):
        self.body = match.group("body")
        self.env = match.group("env")


class EscapedDollar(SpanToken):
    pattern = re.compile(r"(?<!\\)\\(\$)")


class CatsoopRenderer(HTMLRenderer):
    def __init__(self):
        HTMLRenderer.__init__(self, DisplayMathEnv, DisplayMath, Math, EscapedDollar)

    def render_math(self, token):
        return f"<math>{token.body}</math>"

    def render_display_math(self, token):
        return f"<displaymath>{token.body}</displaymath>"

    def render_display_math_env(self, token):
        return f'<displaymath env="{token.env}">{token.body}</displaymath>'


def markdown(x):
    with CatsoopRenderer() as renderer:
        return renderer.render(Document(x))
