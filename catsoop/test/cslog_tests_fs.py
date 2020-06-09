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
"""
Small suite of tests for cslog using the filesystem
"""

import os
import shutil
import math
import random
import unittest

from .. import loader
from ..test import CATSOOPTest

# -----------------------------------------------------------------------------


class _Base:
    def test_queue_ops(self):
        # add a couple of queue entries
        vals = [4, 8, 15, 16, 23, 42]
        ids = [self.cslog.queue_push("testqueue", "something", v) for v in vals]

        # check that the queue order is right
        entries = self.cslog.queue_all_entries("testqueue", "something")
        self.assertEqual([i["data"] for i in entries], vals)

        # read each entry
        for id_, v in zip(ids, vals):
            entry = self.cslog.queue_get("testqueue", id_)
            self.assertEqual(entry["id"], id_)
            self.assertEqual(entry["data"], v)
            self.assertEqual(entry["status"], "something")
            self.assertEqual(entry["created"], entry["updated"])

        # pop one entry into a different category
        x = self.cslog.queue_pop("testqueue", "something", "something_else")
        self.assertEqual(x["data"], 4)
        self.assertEqual(x["status"], "something_else")
        self.assertNotEqual(x["created"], x["updated"])

        # check that the queue order is right
        entries = self.cslog.queue_all_entries("testqueue", "something")
        self.assertEqual([i["data"] for i in entries], vals[1:])
        entries = self.cslog.queue_all_entries("testqueue", "something_else")
        self.assertEqual([i["data"] for i in entries], [4])

        # pop from nonexistent, make sure we get None
        self.assertEqual(self.cslog.queue_pop("testqueue", "nope", "something"), None)
        self.assertEqual(self.cslog.queue_pop("testq", "something", "something"), None)

        # let's update some entries
        x = self.cslog.queue_update("testqueue", ids[2], "cat")
        y = self.cslog.queue_update(
            "testqueue", ids[3], "dog", new_status="something_else"
        )

        # try updating nonexistent one
        self.assertEqual(self.cslog.queue_update("testqueue", "ABCDEFG", 20), None)

        # pop one entry away entirely (8 should still be at the front of the queue, then 'cat')
        self.assertEqual(self.cslog.queue_pop("testqueue", "something")["data"], 8)

        # check that we have what we expect
        entries = self.cslog.queue_all_entries("testqueue", "something")
        self.assertEqual([i["data"] for i in entries], ["cat", 23, 42])
        entries = self.cslog.queue_all_entries("testqueue", "something_else")
        self.assertEqual([i["data"] for i in entries], [4, "dog"])

    def test_queue_load(self):
        # can we spin up a bunch of processes here and have them hit the queue hard?
        # how to test for inacuuracies in push/pop?
        pass


class Test_cslog_fs(CATSOOPTest, _Base):
    def setUp(
        self,
    ):  # this is gross, but it's a way to make sure we get a filesystem-based checker
        CATSOOPTest.setUp(self)
        context = {}

        def mock_load_global_data(into, check_values=True):
            ret = loader.load_global_data(into, check_values)
            into["cs_logging_backend"] = "fs"
            return ret

        mock_load_global_data(context)
        self.cslog = context["csm_cslog"]

        _logs_dir = os.path.join(context["cs_data_root"], "_logs")
        shutil.rmtree(_logs_dir, ignore_errors=True)  # start with fresh logs each time


if __name__ == "__main__":
    unittest.main()
