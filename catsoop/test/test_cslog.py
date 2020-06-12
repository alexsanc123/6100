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
Common Test Cases for all CSLog Backends
"""

import os
import math
import time
import pickle
import random
import shutil
import hashlib
import unittest
import multiprocessing

from collections import Counter

from ..test import CATSOOPTest

from .. import cslog as cslog_base


# -----------------------------------------------------------------------------


class CSLogBackend:
    def test_logging_basic_ops(self):
        user = "testuser"
        path1 = ["test_subject", "some", "page"]
        name = "problemstate"
        self.cslog.update_log(user, path1, name, "HEY")
        self.assertEqual(self.cslog.most_recent(user, path1, name, {}), "HEY")

        self.cslog.update_log(user, path1, name, "HELLO")
        self.assertEqual(self.cslog.read_log(user, path1, name), ["HEY", "HELLO"])

        for i in range(50):
            self.cslog.update_log(user, path1, name, i)

        self.assertEqual(
            self.cslog.read_log(user, path1, name), ["HEY", "HELLO"] + list(range(50))
        )
        self.assertEqual(self.cslog.most_recent(user, path1, name), 49)

        self.cslog.overwrite_log(user, path1, name, 42)
        self.assertEqual(self.cslog.read_log(user, path1, name), [42])

        self.cslog.modify_most_recent(user, path1, name, transform_func=lambda x: x + 9)
        self.assertEqual(self.cslog.read_log(user, path1, name), [42, 51])

        self.cslog.modify_most_recent(user, path1, name, transform_func=lambda x: x + 8)
        self.assertEqual(self.cslog.read_log(user, path1, name), [42, 51, 59])

        self.cslog.modify_most_recent(
            user, path1, name, transform_func=lambda x: x + 7, method="overwrite"
        )
        self.assertEqual(self.cslog.most_recent(user, path1, name), 66)
        self.assertTrue(len(self.cslog.read_log(user, path1, name)) < 4)

        path2 = ["test_subject", "some", "page2"]

        def _transform(x):
            x["cat"] = "miau"
            return x

        self.cslog.modify_most_recent(
            user, path2, name, transform_func=_transform, default={}
        )
        self.assertEqual(self.cslog.most_recent(user, path2, name), {"cat": "miau"})

        # we'll leave it up to the logging backend whether they delete the
        # _whole_ log if it hasn't been updated since the given time, or
        # whether they only delete the old entries.
        #
        # because of this, this test is lame, as it tests only the (lame)
        # guarantee we should have: that if _all_ entreis in a log are old
        # enough, then the whole log should be deleted (and that logs on a
        # different path are unaffected)
        path3 = ["test_subject", "some", "page3"]
        names = "test1", "test2", "test3"
        users = "user1", "user2"
        for user in users:
            for n in names:
                for i in range(3):
                    self.cslog.update_log(user, path3, n, i)
                self.assertEqual(self.cslog.read_log(user, path3, n), [0, 1, 2])
            for n in names:
                for i in range(3):
                    self.cslog.update_log(user, path2, n, i)
                self.assertEqual(self.cslog.read_log(user, path2, n), [0, 1, 2])

        time.sleep(1)
        self.cslog.clear_old_logs(users[0], path3, 1)
        for n in names:
            self.assertEqual(self.cslog.read_log(users[0], path3, n), [])
            self.assertEqual(self.cslog.read_log(users[1], path3, n), [0, 1, 2])
        for n in names:
            self.assertEqual(self.cslog.read_log(users[0], path2, n), [0, 1, 2])
            self.assertEqual(self.cslog.read_log(users[1], path2, n), [0, 1, 2])

    def test_logging_stress_update(self):
        user = "testuser"
        path1 = ["test_subject", "some", "page"]
        name = "problemstate"

        procs = []

        def append_a_bunch():
            for i in range(100):
                self.cslog.update_log(user, path1, name, i)

        for i in range(50):
            p = multiprocessing.Process(target=append_a_bunch, args=())
            procs.append(p)

        for p in procs:
            p.start()

        for p in procs:
            p.join()  # wait for updaters to finish

        entries = self.cslog.read_log(user, path1, name)
        self.assertEqual(len(entries), 5000)
        self.assertEqual(dict(Counter(entries)), {i: 50 for i in range(100)})

    def test_logging_stress_overwrite(self):
        user = "testuser"
        path1 = ["test_subject", "some", "page"]
        name = "problemstate"

        procs = []

        self.cslog.update_log(user, path1, name, 8)

        def overwrite_a_bunch():
            for i in range(100):
                self.cslog.overwrite_log(user, path1, name, 7)

        for i in range(50):
            p = multiprocessing.Process(target=overwrite_a_bunch, args=())
            procs.append(p)

        for p in procs:
            p.start()

        for p in procs:
            p.join()  # wait for updaters to finish

        entries = self.cslog.read_log(user, path1, name)
        self.assertEqual(entries, [7])

    def test_logging_stress_modify(self):
        user = "testuser"
        path1 = ["test_subject", "some", "page"]
        name = "problemstate"

        procs = []

        self.cslog.update_log(user, path1, name, 0)

        def modify_a_bunch():
            for i in range(500):
                self.cslog.modify_most_recent(
                    user,
                    path1,
                    name,
                    transform_func=lambda x: x + 1,
                    method="overwrite",
                )

        for i in range(50):
            p = multiprocessing.Process(target=modify_a_bunch, args=())
            procs.append(p)

        for p in procs:
            p.start()

        for p in procs:
            p.join()  # wait for updaters to finish

        entries = self.cslog.read_log(user, path1, name)
        self.assertEqual(entries, [25000])

    def test_logging_uploads(self):
        content = "hello 🐈".encode("utf-8")
        h = hashlib.sha256(content).hexdigest()
        id_, info, data = cslog_base.prepare_upload("testuser", content, "cat.txt")
        self.cslog.store_upload(id_, info, data)

        ret_info, ret_data = self.cslog.retrieve_upload(id_)
        self.assertEqual(ret_info, self.cslog.unprep(info))
        self.assertEqual(ret_data, content)

        self.assertEqual(self.cslog.retrieve_upload(id_[::-1]), None)

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
        self.assertEqual(x["data"], "cat")
        self.assertEqual(x["status"], "something")
        self.assertEqual(y["data"], "dog")
        self.assertEqual(y["status"], "something_else")

        # try updating nonexistent one
        self.assertEqual(self.cslog.queue_update("testqueue", "ABCDEFG", 20), None)
        self.assertEqual(self.cslog.queue_update("testq", x["id"], 20), None)

        # pop one entry away entirely (8 should still be at the front of the queue, then 'cat')
        self.assertEqual(self.cslog.queue_pop("testqueue", "something")["data"], 8)

        # check that we have what we expect
        entries = self.cslog.queue_all_entries("testqueue", "something")
        self.assertEqual([i["data"] for i in entries], ["cat", 23, 42])
        entries = self.cslog.queue_all_entries("testqueue", "something_else")
        self.assertEqual([i["data"] for i in entries], [4, "dog"])

    def _pushes(self, n, size, offset=0, queue="test", status="stage1"):
        orig_len = len(self.cslog.queue_all_entries(queue, status))

        procs = []

        def pushstuff(n):
            for i in range(size):
                self.cslog.queue_push(queue, status, size * n + i + offset)

        for i in range(n):
            p = multiprocessing.Process(target=pushstuff, args=(i,))
            p.start()
            procs.append(p)

        # we'll need to wait for everyone to finish!
        for p in procs:
            p.join()

        self.assertEqual(
            len(self.cslog.queue_all_entries(queue, status)), n * size + orig_len
        )

    def test_queue_stress_pop(self):
        # first, push one entry on
        self.cslog.queue_push("test", "stage1", -1)

        # now push a bunch of stuff and make sure it all makes it in
        self._pushes(10, 100)
        self._pushes(20, 100, 1000)

        # now pop one thing off, this should be the first.
        self.assertEqual(self.cslog.queue_pop("test", "stage1")["data"], -1)

        # now pop a bunch of stuff off and make sure we get the right results
        # back
        procs = []

        def popstuff(n):
            mystage = "stage%d" % (2 + n)
            o = -1
            while o is not None:
                o = self.cslog.queue_pop("test", "stage1", mystage)

        for i in range(20):
            p = multiprocessing.Process(target=popstuff, args=(i,))
            procs.append(p)
        for p in procs:
            p.start()
        for p in procs:
            p.join()
        all_entries = []
        for i in range(20):
            this_entries = self.cslog.queue_all_entries("test", "stage%d" % (2 + i))
            all_entries.extend(this_entries)
        self.assertEqual({i["data"] for i in all_entries}, set(range(3000)))
        self.assertEqual(self.cslog.queue_all_entries("test", "stage1"), [])

    def test_queue_stress_poptonowhere(self):
        self._pushes(10, 100)
        ids = [i["id"] for i in self.cslog.queue_all_entries("test", "stage1")]

        procs = []

        def popout(n):
            out = set()
            o = -1
            while o is not None:
                o = self.cslog.queue_pop("test", "stage1")
                if o is not None:
                    out.add(o["id"])
            with open("/tmp/catsoop_test_%s" % n, "wb") as f:
                pickle.dump(out, f)

        for i in range(100):
            p = multiprocessing.Process(target=popout, args=(i,))
            procs.append(p)
        for p in procs:
            p.start()
        for p in procs:
            p.join()

        allids = set()
        for i in range(100):
            with open("/tmp/catsoop_test_%s" % i, "rb") as f:
                new = pickle.load(f)
                allids |= new

        self.assertEqual(allids, set(ids))
        self.assertEqual(self.cslog.queue_all_entries("test", "stage1"), [])

    def test_queue_stress_update(self):
        self._pushes(10, 10)
        ids = [i["id"] for i in self.cslog.queue_all_entries("test", "stage1")]

        procs = []

        def update(n, ids):
            mystage = "stage%s" % (2 + n)
            out = set()
            o = -1
            random.shuffle(ids)
            for i in ids:
                o = self.cslog.queue_update("test", i, 7, mystage)
                if o is not None:
                    out.add(o["id"])
            with open("/tmp/catsoop_test_%s" % n, "wb") as f:
                pickle.dump(out, f)

        for i in range(100):
            p = multiprocessing.Process(target=update, args=(i, ids))
            p.start()
            procs.append(p)

        for p in procs:
            p.join()

        allids = set()
        for i in range(100):
            with open("/tmp/catsoop_test_%s" % i, "rb") as f:
                new = pickle.load(f)
                self.assertEqual(len(new), 100)
                allids |= new

        self.assertEqual(allids, set(ids))
        self.assertEqual({self.cslog.queue_get("test", i)["data"] for i in ids}, {7})
