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
Logging mechanisms using [PostgreSQL](https://www.postgresql.org/)
"""

import time
import uuid
import psycopg2

from datetime import datetime, timedelta

from . import (
    prep,
    unprep,
    compress_encrypt,
    decompress_decrypt,
    hash_db_info,
    WORKER_ID,
)

from .. import base_context


def _connect():
    return psycopg2.connect(**base_context.cs_postgres_options)


def setup_kwargs():
    return {"connection": _connect()}


def teardown_kwargs(kwargs):
    try:
        kwargs["connection"].close()
    except:
        pass


def read_log(db_name, path, logname, connection=None):
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
    db_name, path, logname = hash_db_info(db_name, path, logname)
    conn = _connect() if connection is None else connection
    with conn:
        with conn.cursor() as c:
            c.execute(
                "SELECT data FROM logs WHERE db_name=%s AND path=%s AND logname=%s ORDER BY updated ASC",
                (db_name, "/".join(path), logname),
            )
            res = c.fetchall()
    if connection is None:
        conn.close()
    return [unprep(bytes(entry[-1])) for entry in res]


def most_recent(db_name, path, logname, default=None, connection=None):
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
    db_name, path, logname = hash_db_info(db_name, path, logname)
    conn = _connect() if connection is None else connection
    with conn:
        with conn.cursor() as c:
            c = conn.cursor()
            c.execute(
                "SELECT data FROM logs WHERE db_name=%s AND path=%s AND logname=%s ORDER BY updated DESC LIMIT 1",
                (db_name, "/".join(path), logname),
            )
            r = c.fetchone()
    out = unprep(bytes(r[-1])) if r is not None else default
    if connection is None:
        conn.close()
    return out


def update_log(db_name, path, logname, new, connection=None):
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
    db_name, path, logname = hash_db_info(db_name, path, logname)
    conn = _connect() if connection is None else connection
    with conn:
        with conn.cursor() as c:
            c.execute(
                "SELECT pg_advisory_xact_lock(%s)",
                (hash((db_name, tuple(path), logname)),),
            )
            c.execute(
                "INSERT INTO logs (db_name, path, logname, updated, data) VALUES(%s, %s, %s, NOW(), %s)",
                (db_name, "/".join(path), logname, prep(new)),
            )
    if connection is None:
        conn.close()


def overwrite_log(db_name, path, logname, new, connection=None):
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
    db_name, path, logname = hash_db_info(db_name, path, logname)
    conn = _connect() if connection is None else connection
    with conn:
        with conn.cursor() as c:
            c.execute(
                "SELECT pg_advisory_xact_lock(%s)",
                (hash((db_name, tuple(path), logname)),),
            )
            c.execute(
                "DELETE FROM logs WHERE db_name=%s AND path=%s AND logname=%s",
                (db_name, "/".join(path), logname),
            )
            c.execute(
                "INSERT INTO logs (db_name, path, logname, updated, data) VALUES(%s, %s, %s, NOW(), %s)",
                (db_name, "/".join(path), logname, prep(new)),
            )
    if connection is None:
        conn.close()


def modify_most_recent(
    db_name,
    path,
    logname,
    default=None,
    transform_func=lambda x: x,
    method="update",
    connection=None,
):
    db_name, path, logname = hash_db_info(db_name, path, logname)
    conn = _connect() if connection is None else connection
    path = "/".join(path)
    with conn:
        with conn.cursor() as c:
            c.execute(
                "SELECT pg_advisory_xact_lock(%s)",
                (hash((db_name, tuple(path), logname)),),
            )
            c.execute(
                "SELECT * FROM logs WHERE db_name=%s AND path=%s AND logname=%s ORDER BY updated DESC FOR UPDATE LIMIT 1",
                (db_name, path, logname),
            )
            res = c.fetchone()
            if res:
                old_val = unprep(bytes(res[-1]))
                id_ = res[0]
            else:
                method = "update"
                old_val = default
            new_val = prep(transform_func(old_val))
            if method == "update":
                c.execute(
                    "INSERT INTO logs(db_name, path, logname, updated, data) VALUES(%s, %s, %s, NOW(), %s)",
                    (db_name, path, logname, new_val),
                )
            else:  # overwrite
                c.execute(
                    "UPDATE logs SET data=%s,updated=NOW() WHERE id=%s",
                    (new_val, id_),
                )
    if connection is None:
        conn.close()


def clear_old_logs(db_name, path, age, connection=None):
    db_name, path, _ = hash_db_info(db_name, path, "")
    conn = _connect() if connection is None else connection
    with conn:
        with conn.cursor() as c:
            c.execute(
                "DELETE FROM logs WHERE db_name=%s AND path=%s AND updated < %s",
                (
                    db_name,
                    "/".join(path),
                    datetime.now() - timedelta(seconds=age),
                ),
            )
    if connection is None:
        conn.close()


def initialize_database(connection=None):
    conn = _connect() if connection is None else connection
    with conn:
        with conn.cursor() as c:
            c.execute(
                "CREATE TABLE IF NOT EXISTS logs (id bigserial PRIMARY KEY, db_name text, path text, logname text, updated timestamp, data bytea);"
            )
            c.execute(
                "CREATE INDEX IF NOT EXISTS idx_logname ON logs (db_name, path, logname);"
            )
            c.execute(
                "CREATE TABLE IF NOT EXISTS uploads (id char(96) PRIMARY KEY, info bytea, content bytea);"
            )
            c.execute(
                "CREATE TABLE IF NOT EXISTS queues (id char(36) PRIMARY KEY, queuename text, status text, worker char(32), created timestamp, updated timestamp, data bytea);"
            )
            c.execute("CREATE INDEX IF NOT EXISTS idx_queuename ON queues(queuename);")
    if connection is None:
        conn.close()


def store_upload(id_, info, data, connection=None):
    conn = _connect() if connection is None else connection
    with conn:
        with conn.cursor() as c:
            c.execute("INSERT INTO uploads VALUES (%s, %s, %s)", (id_, info, data))
    if connection is None:
        conn.close()


def retrieve_upload(upload_id, connection=None):
    conn = _connect() if connection is None else connection
    with conn:
        with conn.cursor() as c:
            c.execute("SELECT info,content FROM uploads WHERE id=%s", (upload_id,))
            result = c.fetchone()
    if connection is None:
        conn.close()
    if result is None:
        return None
    return unprep(bytes(result[0])), decompress_decrypt(bytes(result[1]))


def queue_push(queuename, initial_status, data, connection=None):
    id = str(uuid.uuid4())
    query = "INSERT INTO queues (id, queuename, status, worker, created, updated, data) VALUES (%s,%s,%s,%s,NOW(),NOW(),%s) RETURNING *"
    conn = _connect() if connection is None else connection
    with conn:
        with conn.cursor() as c:
            c.execute(query, (id, queuename, initial_status, None, prep(data)))
    if connection is None:
        conn.close()
    return id


def queue_pop(queuename, old_status, new_status=None, connection=None):
    """
    Pop the oldest entry from the given queue with the given status, set its
    status to new_status and its worker to this worker, and return the entry.
    Returns None if no entry was found.  Otherwise returns the id and data
    associated with this queue entry.
    """
    query = "UPDATE queues SET status=%s,worker=%s,updated=NOW() WHERE id=(SELECT id FROM queues WHERE queuename=%s AND status=%s ORDER BY created ASC FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING *"
    conn = _connect() if connection is None else connection
    with conn:
        with conn.cursor() as c:
            c.execute(query, (new_status, WORKER_ID, queuename, old_status))
            res = c.fetchall()  # id, queuename, status, created, updated, data

            if new_status is None and res:
                # if we found something and we don't want to set a new state,
                # just delete it.
                c.execute("DELETE FROM queues WHERE id=%s", (res[0][0],))
    if connection is None:
        conn.close()
    if not res:
        return None
    else:
        return _prep_entries(res)[0]


def queue_update(queuename, id, new_data, new_status=None, connection=None):
    """
    Update the queue entry with the given id, optionally also updating the
    status.
    """
    if new_status:
        query = "UPDATE queues SET data=%s,status=%s,updated=NOW() WHERE id=%s AND queuename=%s RETURNING *"
        args = (prep(new_data), new_status, id, queuename)
    else:
        query = "UPDATE queues SET data=%s,updated=NOW() WHERE id=%s AND queuename=%s RETURNING *"
        args = (prep(new_data), id, queuename)
    conn = _connect() if connection is None else connection
    with conn:
        with conn.cursor() as c:
            c.execute(query, args)
            res = c.fetchall()
    if connection is None:
        conn.close()
    return _prep_entries(res)[0] if res else None


def queue_get(queuename, id, connection=None):
    conn = _connect() if connection is None else connection
    with conn:
        with conn.cursor() as c:
            c.execute(
                "SELECT * FROM queues WHERE id=%s AND queuename=%s", (id, queuename)
            )
            res = c.fetchall()
    if connection is None:
        conn.close()
    return _prep_entries(res)[0] if res else None


def queue_all_entries(queuename, status, connection=None):
    """
    Return the current queue contents, appropriately ordered
    """
    conn = _connect() if connection is None else connection
    with conn:
        with conn.cursor() as c:
            c.execute(
                f"SELECT * FROM queues WHERE queuename=%s AND status=%s ORDER BY created ASC",
                (queuename, status),
            )
            res = c.fetchall()
    if connection is None:
        conn.close()
    return _prep_entries(res)


def _prep_entries(entries):
    return [
        {
            "id": i[0],
            "queuename": i[1],
            "status": i[2],
            "worker": i[3],
            "created": i[4],
            "updated": i[5],
            "data": unprep(bytes(i[6])),
        }
        for i in entries
    ]
