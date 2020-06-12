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

import os
import glob
import time
import shutil
import unittest
import subprocess

from .. import loader
from .. import base_context
from ..test import CATSOOPTest
from .test_cslog import CSLogBackend

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
class TestPostgres(CATSOOPTest, CSLogBackend):
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
