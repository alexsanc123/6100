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
Logging mechanisms using the filesystem

On disk, each log is a file containing one or more entries, where each entry
consists of:

* 8 bits representing the length of the entry
* a binary blob (pickled Python object, potentially encrypted and/or
    compressed)
* the 8-bit length repeated
"""

import os
import base64
import struct
import hashlib

from collections import OrderedDict
from datetime import datetime, timedelta

from filelock import FileLock

from .. import time
from .. import base_context

from . import (
    prep,
    unprep,
    compress_encrypt,
    decompress_decrypt,
    hash_db_info,
)


def setup_kwargs():
    return {}


def teardown_kwargs(kwargs):
    return


def log_lock(path):
    lock_loc = os.path.join(base_context.cs_data_root, "_locks", *path) + ".lock"
    os.makedirs(os.path.dirname(lock_loc), exist_ok=True)
    return FileLock(lock_loc)


def get_log_filename(db_name, path, logname):
    """
    Helper function, returns the filename where a given log is stored on disk.

    **Parameters:**

    * `db_name`: the name of the database to look in
    * `path`: the path to the page associated with the log
    * `logname`: the name of the log
    """
    db_name, path, logname = hash_db_info(db_name, path, logname)
    if path:
        course = path[0]
        return os.path.join(
            base_context.cs_data_root,
            "_logs",
            "_courses",
            course,
            db_name,
            *(path[1:]),
            "%s.log" % logname
        )
    else:
        return os.path.join(
            base_context.cs_data_root, "_logs", db_name, *path, "%s.log" % logname
        )


def _modify_log(fname, new, mode):
    os.makedirs(os.path.dirname(fname), exist_ok=True)
    entry = prep(new)
    length = struct.pack("<Q", len(entry))
    with open(fname, mode) as f:
        f.write(length)
        f.write(entry)
        f.write(length)


def update_log(db_name, path, logname, new, lock=True):
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
    fname = get_log_filename(db_name, path, logname)
    # get an exclusive lock on this file before making changes
    # look up the separator and the data
    cm = log_lock([db_name] + path + [logname]) if lock else passthrough()
    with cm:
        _modify_log(fname, new, "ab")


def overwrite_log(db_name, path, logname, new, lock=True):
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
    # get an exclusive lock on this file before making changes
    fname = get_log_filename(db_name, path, logname)
    cm = log_lock([db_name] + path + [logname]) if lock else passthrough()
    with cm:
        _modify_log(fname, new, "wb")


def _read_log(db_name, path, logname, lock=True):
    fname = get_log_filename(db_name, path, logname)
    # get an exclusive lock on this file before reading it
    cm = log_lock([db_name] + path + [logname]) if lock else passthrough()
    with cm:
        try:
            with open(fname, "rb") as f:
                while True:
                    try:
                        length = struct.unpack("<Q", f.read(8))[0]
                        yield unprep(f.read(length))
                    except EOFError:
                        break
                    f.seek(8, os.SEEK_CUR)
                return
        except:
            return


def read_log(db_name, path, logname, lock=True):
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
    return list(_read_log(db_name, path, logname, lock))


def most_recent(db_name, path, logname, default=None, lock=True):
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
    fname = get_log_filename(db_name, path, logname)
    if not os.path.isfile(fname):
        return default
    # get an exclusive lock on this file before reading it
    cm = log_lock([db_name] + path + [logname]) if lock else passthrough()
    with cm:
        with open(fname, "rb") as f:
            f.seek(-8, os.SEEK_END)
            length = struct.unpack("<Q", f.read(8))[0]
            f.seek(-length - 8, os.SEEK_CUR)
            return unprep(f.read(length))


def modify_most_recent(
    db_name,
    path,
    logname,
    default=None,
    transform_func=lambda x: x,
    method="update",
    lock=True,
):
    cm = log_lock([db_name] + path + [logname]) if lock else passthrough()
    with cm:
        old_val = most_recent(db_name, path, logname, default, lock=False)
        new_val = transform_func(old_val)
        if method == "update":
            updater = update_log
        else:
            updater = overwrite_log
        updater(db_name, path, logname, new_val, lock=False)
    return new_val


def initialize_database():
    """
    Initialize the log storage on disk
    """
    pass


def clear_old_logs(db_name, path, timestamp):
    """
    Clear logs whose updated timestamp is below the given value.  Primarily used for session handling
    """
    directory = os.path.dirname(get_log_filename(db_name, path, "test"))
    try:
        logs = os.listdir(directory)
    except:
        return
    for log in logs:
        fullname = os.path.join(directory, log)
        try:
            if os.stat(fullname).st_mtime < timestamp:
                os.unlink(fullname)
        except:
            pass


def store_upload(id_, info, data):
    dir_ = os.path.join(
        base_context.cs_data_root, "_logs", "_uploads", id_[0], id_[1], id_
    )
    os.makedirs(dir_, exist_ok=True)
    with open(os.path.join(dir_, "info"), "wb") as f:
        f.write(info)
    with open(os.path.join(dir_, "content"), "wb") as f:
        f.write(data)


def retrieve_upload(id_):
    dir_ = os.path.join(
        base_context.cs_data_root, "_logs", "_uploads", id_[0], id_[1], id_
    )
    with open(os.path.join(dir_, "info"), "rb") as f:
        info = unprep(f.read())
    with open(os.path.join(dir_, "content"), "rb") as f:
        data = decompress_decrypt(f.read())
    return info, data
