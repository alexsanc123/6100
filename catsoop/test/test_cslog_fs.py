# This file is part of CAT-SOOP
# Copyright (c) 2011-2021 by The CAT-SOOP Developers <catsoop-dev@mit.edu>
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
"""
Small suite of tests for cslog using the filesystem
"""

import os
import shutil

from .. import loader
from ..test import CATSOOPTest
from .test_cslog import CSLogBackend

from ..cslog import fs as cslog_fs


class TestFS(CATSOOPTest, CSLogBackend):
    def setUp(
        self,
    ):
        CATSOOPTest.setUp(self)

        context = {}
        loader.load_global_data(context)
        self.cslog = cslog_fs

        _logs_dir = os.path.join(context["cs_data_root"], "_logs")
        shutil.rmtree(_logs_dir, ignore_errors=True)  # start with fresh logs each time
