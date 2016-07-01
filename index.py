#!/usr/bin/env python3

# This file is part of CAT-SOOP
# Copyright (c) 2011-2016 Adam Hartz <hartz@mit.edu>

# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.

# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see
# <https://www.gnu.org/licenses/agpl-3.0-standalone.html>.

# index.py
# This file is the main CGI interface to CAT-SOOP

import os
import sys
import cgitb
import platform

import catsoop.dispatch as dispatch

cgitb.enable()

if platform.system() == 'Windows':
    import msvcrt
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)


def write(x):
    sys.stdout.write(x)
    sys.stdout.flush()


def _http_response(input_tuple):
    status, headers, content = input_tuple
    h = 'Status: %s %s\n' % (status[0], status[1])
    h += '\n'.join('%s: %s' % (i, j) for (i, j) in headers.iteritems())
    h += '\n'
    if len(headers) > 0:
        h += '\n'
    return h, content

if __name__ == '__main__':
    headers, content = _http_response(dispatch.main(os.environ))
    write(headers)
    if isinstance(content, str):
        write(content)
    else:
        for i in content:
            write(i)