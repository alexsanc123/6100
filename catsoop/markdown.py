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
"""CAT-SOOP Extensions for Mistletoe"""

import re

from mistletoe import Document
from mistletoe.span_token import SpanToken, tokenize_inner
from mistletoe.block_token import BlockToken, tokenize
from mistletoe.html_renderer import HTMLRenderer


# Math


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


# Admonitions


class Admonition(BlockToken):
    classes = ["note", "tip", "info", "warning", "error"]
    start_regex = re.compile(r"!!!(?P<header>.*)")

    def __init__(self, match):
        self.type, title, raw_lines = match
        self.title = tokenize([title])
        self.children = tokenize(raw_lines)
        print(self.title, self.children)

    @classmethod
    def start(cls, line):
        match = cls.start_regex.match(line)
        if not match:
            return False

        cls.indent = None

        header = (match.group("header") or "").strip()
        try:
            type_, title = header.split(":", 1)
            if type_.lower() not in cls.classes:
                type_ = "note"
                title = header
        except ValueError:
            if header.lower() in cls.classes:
                type_ = header
                title = ""
            else:
                type_ = "note"
                title = header.strip()

        cls.type, cls.title = type_.lower(), title
        return True

    @classmethod
    def read(cls, lines):
        out_lines = []
        next(lines)  # consume the starting line (with !!!)
        line = lines.peek()
        while line is not None:
            print(repr(line))
            if cls.indent is None:
                try:
                    cls.indent = re.match("^\s*", line).group(0)
                except AttributeError:
                    # None as return type from match?  no indent, move on
                    break

            # if there is no indent on the following line, break here
            if not cls.indent:
                break

            if line.strip():
                # nonempty line.
                if not line.startswith(cls.indent):
                    break
                else:
                    out_lines.append(line[len(cls.indent) :])
            else:
                out_lines.append(line)

            # move on to the next line
            next(lines)
            line = lines.peek()

        return cls.type, cls.title, out_lines


class CatsoopRenderer(HTMLRenderer):
    def __init__(self):
        HTMLRenderer.__init__(
            self, Admonition, DisplayMathEnv, DisplayMath, Math, EscapedDollar
        )

    def render_admonition(self, token):
        print("WTF", repr(token))
        if token.title:
            rendered_title = '<div class="admonition-title">%s</div>' % "".join(
                self.render_inner(i) for i in token.title
            )
        else:
            rendered_title = ""
        rendered_body = "".join(self.render(i) for i in token.children)
        return f'<div class="admonition admonition-{token.type}">{rendered_title}\n\n{rendered_body}\n</div>'

    def render_math(self, token):
        return f"<math>{token.body}</math>"

    def render_display_math(self, token):
        return f"<displaymath>{token.body}</displaymath>"

    def render_display_math_env(self, token):
        return f'<displaymath env="{token.env}">{token.body}</displaymath>'


def markdown(x):
    with CatsoopRenderer() as renderer:
        return renderer.render(Document(x))