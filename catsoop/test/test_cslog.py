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
import math
import time
import glob
import pickle
import random
import shutil
import hashlib
import unittest
import subprocess
import multiprocessing

from .. import base_context
from .. import loader
from ..test import CATSOOPTest

from .. import cslog as cslog_base

from ..cslog import fs as cslog_fs

# -----------------------------------------------------------------------------


class _Base:
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
        # enough, then the whole log should be deleted.
        path3 = ["test_subject", "some", "page3"]
        names = "test1", "test2", "test3"
        for n in names:
            for i in range(3):
                self.cslog.update_log(user, path3, n, i)
            self.assertEqual(self.cslog.read_log(user, path3, n), list(range(3)))

        time.sleep(1)
        self.cslog.clear_old_logs(user, path3, 1)
        for n in names:
            self.assertEqual(self.cslog.read_log(user, path3, n), [])

    def test_logging_stress(self):
        pass

    def test_logging_uploads(self):
        content = "hello 🐈".encode("utf-8")
        h = hashlib.sha256(content).hexdigest()
        id_, info, data = cslog_base.prepare_upload("testuser", content, "cat.txt")
        self.cslog.store_upload(id_, info, data)

        ret_info, ret_data = self.cslog.retrieve_upload(id_)
        self.assertEqual(ret_info, self.cslog.unprep(info))
        self.assertEqual(ret_data, content)

        self.assertEqual(self.cslog.retrieve_upload(id_[::-1]), None)

    def test_logging_encryption(self):
        # TODO: write this.
        # this will need to be overridden for each subclass, since the
        # specifics of the encryption are going to depend on the details of how
        # things are stored (though there will be some things in common)
        assert False

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
            p.start()
            procs.append(p)
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
            p.start()
            procs.append(p)

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

        for i in range(200):
            p = multiprocessing.Process(target=update, args=(i, ids))
            p.start()
            procs.append(p)

        for p in procs:
            p.join()

        allids = set()
        for i in range(200):
            with open("/tmp/catsoop_test_%s" % i, "rb") as f:
                new = pickle.load(f)
                self.assertEqual(len(new), 100)
                allids |= new

        self.assertEqual(allids, set(ids))
        self.assertEqual({self.cslog.queue_get("test", i)["data"] for i in ids}, {7})


class Test_cslog_fs(CATSOOPTest, _Base):
    def setUp(self,):
        CATSOOPTest.setUp(self)

        context = {}
        loader.load_global_data(context)
        self.cslog = cslog_fs

        _logs_dir = os.path.join(context["cs_data_root"], "_logs")
        shutil.rmtree(_logs_dir, ignore_errors=True)  # start with fresh logs each time


initdb = shutil.which("initdb")
postgres = shutil.which("postgres")
if initdb is None:
    # debian puts initdb in a weird spot...
    try:
        initdb = glob.glob("/usr/lib/postgresql/*/bin/initdb")[0]
        postgres = glob.glob("/usr/lib/postgresql/*/bin/postgres")[0]
    except:
        pass
try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    from ..cslog import postgres as cslog_postgres
except:
    psycopg2 = None


@unittest.skipIf(
    initdb is None or postgres is None,
    "skipping PostgreSQL tests: cannot create dummy database for testing",
)
@unittest.skipIf(psycopg2 is None, "skipping PostgreSQL tests: please install psycopg2")
class Test_cslog_postgres(CATSOOPTest, _Base):
    db_loc = "/tmp/catsoop_psql"
    port = 60037

    def setUp(self,):
        CATSOOPTest.setUp(self)
        context = {}

        loader.load_global_data(context)
        self.cslog = cslog_postgres
        cslog_postgres.base_context.cs_postgres_options = {
            "host": "localhost",
            "port": self.port,
            "user": "catsoop",
            "password": "catsoop",
        }

        # set up the database (inspired by https://github.com/tk0miya/testing.postgresql)
        shutil.rmtree(self.db_loc, ignore_errors=True)

        os.makedirs(os.path.join(self.db_loc, "tmp"))

        p = subprocess.Popen(
            [
                initdb,
                "-U",
                "postgres",
                "-A",
                "trust",
                "-D",
                os.path.join(self.db_loc, "data"),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        p.communicate()

        # start postgres server
        self.p = subprocess.Popen(
            [
                postgres,
                "-p",
                str(self.port),
                "-D",
                os.path.join(self.db_loc, "data"),
                "-k",
                os.path.join(self.db_loc, "tmp"),
                "-h",
                "127.0.0.1",
                "-F",
                "-c",
                "logging_collector=off",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(0.1)

        # create database structure
        conn = psycopg2.connect(host="localhost", port=self.port, user="postgres")
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        c = conn.cursor()
        c.execute("CREATE DATABASE catsoop;")
        c.execute("CREATE USER catsoop WITH ENCRYPTED PASSWORD 'catsoop';")
        c.execute("GRANT ALL PRIVILEGES ON DATABASE catsoop TO catsoop;")
        c.close()
        conn.close()
        self.port += 1  # ugh this is gross

        self.cslog.initialize_database()

    def tearDown(self):
        self.p.kill()
        self.p.communicate()


if __name__ == "__main__":
    unittest.main()
