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
Logging mechanisms using the [PostgreSQL](https://www.postgresql.org/)
"""

import time
import psycopg2

from . import (
    prep,
    unprep,
    compress_encrypt,
    decompress_decrypt,
    ENCRYPT_KEY,
)

from .. import base_context

CONNECTION = psycopg2.connect(**base_context.cs_postgres_options)


def _read_log(db_name, path, logname):
    c = CONNECTION.cursor()
    c.execute(
        "SELECT data FROM logs WHERE db_name=%s AND path=%s AND logname=%s ORDER BY id ASC",
        (db_name, "/".join(path), logname),
    )
    r = c.fetchone()
    while r is not None:
        yield unprep(r[-1])
        r = c.fetchone()
    c.close()


def read_log(db_name, path, logname):
    """
    Reads all entries of a log.

    **Parameters:**

    * `db_name`: the name of the database to read
    * `path`: the path to the page associated with the log
    * `logname`: the name of the log

    **Optional Parameters:**

    * `lock` (default `True`): whether the database should be locked during
        this read

    **Returns:** a list containing the Python objects in the log
    """
    return list(_read_log(db_name, path, logname))


def most_recent(db_name, path, logname, default=None):
    """
    Ignoring most of the log, grab the last entry.

    This code works by reading backward through the log until the separator is
    found, treating the piece of the file after the last separator as a log
    entry, and using `unprep` to return the associated Python object.

    **Parameters:**

    * `db_name`: the name of the database to read
    * `path`: the path to the page associated with the log
    * `logname`: the name of the log

    **Optional Parameters:**

    * `default` (default `None`): the value to be returned if the log contains
        no entries or does not exist
    * `lock` (default `True`): whether the database should be locked during
        this read

    **Returns:** a single Python object representing the most recent entry in
    the log.
    """
    c = CONNECTION.cursor()
    c.execute(
        "SELECT data FROM logs WHERE db_name=%s AND path=%s AND logname=%s ORDER BY id DESC LIMIT 1",
        (db_name, "/".join(path), logname),
    )
    r = c.fetchone()
    c.close()
    return unprep(bytes(r[-1])) if r is not None else default


def update_log(db_name, path, logname, new):
    """
    Adds a new entry to the end of the specified log.

    **Parameters:**

    * `db_name`: the name of the database to update
    * `path`: the path to the page associated with the log
    * `logname`: the name of the log
    * `new`: the Python object that should be added to the end of the log

    **Optional Parameters:**

    * `lock` (default `True`): whether the database should be locked during
        this update
    """
    c = CONNECTION.cursor()
    c.execute(
        "INSERT INTO logs (db_name, path, logname, updated, data) VALUES(%s, %s, %s, %s, %s)",
        (db_name, "/".join(path), logname, int(time.time()), prep(new)),
    )
    CONNECTION.commit()
    c.close()


def overwrite_log(db_name, path, logname, new):
    """
    Overwrites the entire log with a new log with a single (given) entry.

    **Parameters:**

    * `db_name`: the name of the database to overwrite
    * `path`: the path to the page associated with the log
    * `logname`: the name of the log
    * `new`: the Python object that should be contained in the new log

    **Optional Parameters:**

    * `lock` (default `True`): whether the database should be locked during
        this update
    """
    c = CONNECTION.cursor()
    c.execute("BEGIN WORK")
    c.execute(
        "DELETE FROM logs WHERE db_name=%s AND path=%s AND logname=%s",
        (db_name, "/".join(path), logname),
    )
    c.execute(
        "INSERT INTO logs (db_name, path, logname, updated, data) VALUES(%s, %s, %s, %s, %s)",
        (db_name, "/".join(path), logname, int(time.time()), prep(new)),
    )
    c.execute("COMMIT WORK")
    CONNECTION.commit()
    c.close()


def modify_most_recent(
    db_name,
    path,
    logname,
    default=None,
    transform_func=lambda x: x,
    method="update",
    connection=None,
):
    path = "/".join(path)
    c = CONNECTION.cursor()
    try:
        c.execute(
            "SELECT * FROM logs WHERE db_name=%s AND path=%s AND logname=%s ORDER BY id DESC LIMIT 1",
            (db_name, path, logname),
        )
        res = c.fetchone()
        if res:
            old_val = unprep(res[-1])
            id_ = res[0]
        else:
            method = "update"
            old_val = default
        new_val = prep(transform_func(old_val))
        if method == "update":
            c.execute(
                "INSERT INTO logs(db_name, path, logname, update, data) VALUES(%s, %s, %s, %s)",
                (db_name, path, logname, int(time.time()), new_val),
            )
        else:  # overwrite
            c.execute(
                "UPDATE logs SET data=%s,updated=%s WHERE id=%s",
                (new_val, int(time.time()), id_),
            )
        CONNECTION.commit()
    except:
        CONNECTION.rollback()
    finally:
        c.close()


def clear_old_logs(db_name, path, timestamp):
    c = CONNECTION.cursor()
    c.execute("DELETE FROM logs WHERE updated < %s", (timestamp,))
    CONNECTION.commit()
    c.close()


def initialize_database():
    c = CONNECTION.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS logs (id bigserial PRIMARY KEY, db_name text, path text, logname text, updated bigint, data bytea);"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS uploads (id char(96) PRIMARY KEY, info bytea, content bytea);"
    )
    CONNECTION.commit()
    c.close()
