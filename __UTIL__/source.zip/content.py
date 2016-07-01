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

import os
import platform

from zipfile import ZipFile, ZIP_DEFLATED


def keep_file(full, base):
    # ignore compiled python files
    if base.endswith('.pyc') or base.endswith('.pycs'):
        return False
    # ignore vim temporary files and swap files
    if base.endswith('~') or base.endswith('.swp'):
        return False
    # ignore emacs temporary files
    if base.startswith('#') and base.endswith('#'):
        return False
    # ignore Mercurial backup files
    if base.endswith('.orig'):
        return False
    # ignore dotfiles
    if base.startswith('.'):
        return False
    # ignore config.py in catsoop root
    if full == os.path.join(cs_fs_root, 'catsoop', 'config.py'):
        return False
    return True

tmp = os.environ.get('TEMP',cs_fs_root) if platform.system() == 'Windows' else '/tmp'

cache_fname = os.path.join(tmp, '.catsoop-source-%s.zip' % hash(cs_fs_root))
regenerate = False
if not os.path.isfile(cache_fname):
    regenerate = True
else:
    source_modified = os.stat(cs_fs_root).st_mtime
    cache_modified = os.stat(cache_fname).st_mtime
    if source_modified > cache_modified:
        regenerate = True

if regenerate:
    with csm_filelock.FileLock(cache_fname) as flock:
        outfile = ZipFile(cache_fname, 'w', ZIP_DEFLATED)
        for root, dirs, files in os.walk(cs_fs_root):
            to_remove = set()
            for d in dirs:
                if d.startswith('.'):
                    to_remove.add(d)
            for d in to_remove:
                dirs.remove(d)
            for f in files:
                fullname = os.path.join(root, f)
                if keep_file(fullname, f):
                    name = fullname.replace(cs_fs_root, 'cat-soop')
                    outfile.write(fullname, name)
        outfile.close()

with csm_filelock.FileLock(cache_fname) as flock:
    with open(cache_fname, 'r') as f:
        response = f.read()

cs_handler = 'raw_response'
content_type = 'application/zip'