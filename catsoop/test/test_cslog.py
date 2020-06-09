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
import glob
import shutil
import math
import time
import random
import unittest
import subprocess
import multiprocessing

from .. import base_context
from .. import loader
from ..test import CATSOOPTest

from ..cslog import fs as cslog_fs

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
        self.assertEqual(x["data"], "cat")
        self.assertEqual(x["status"], "something")
        self.assertEqual(y["data"], "dog")
        self.assertEqual(y["status"], "something_else")

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
        procs = []

        # first, push a bunch of stuff and make sure it all makes it in
        def pushstuff(n):
            for i in range(100):
                self.cslog.queue_push("test", "stage1", 100 * n + i)

        self.cslog.queue_push("test", "stage1", -1)
        for i in range(20):
            p = multiprocessing.Process(target=pushstuff, args=(i,))
            p.start()
            procs.append(p)

        # we'll need to wait for everyone to finish!
        for p in procs:
            p.join()

        self.assertEqual(len(self.cslog.queue_all_entries("test", "stage1")), 2001)

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
        self.assertEqual({i["data"] for i in all_entries}, set(range(2000)))
        self.assertEqual(self.cslog.queue_all_entries("test", "stage1"), [])


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
