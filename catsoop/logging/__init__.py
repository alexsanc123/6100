# This file is part of CAT-SOOP
# Copyright (c) 2011-2017 Adam Hartz <hartz@mit.edu>
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

from . import sqlite
from . import catsoopdb

_db_type_map = {
    'catsoopdb': catsoopdb,
    'sqlite': sqlite,
}

def get_logger(context):
    db_type = context.get('cs_log_type', 'catsoopdb')
    logging_module = _db_type_map.get(db_type, None)
    if logging_module is None:
        raise NameError('No such logger: %s' % db_type)
    return logging_module
