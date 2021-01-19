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
Logging mechanisms using the filesystem

On disk, each log is a file containing one or more entries, where each entry
consists of:

* 8 bytes representing the length of the entry
* a binary blob (pickled Python object, potentially encrypted and/or
    compressed)
* the 8-byte length repeated
"""

import os
import glob
import time
import uuid
import base64
import pickle
import shutil
import struct
import hashlib
import contextlib

from collections import OrderedDict
from datetime import datetime, timedelta

from filelock import FileLock

from .. import time as cstime
from .. import base_context

from . import (
    prep,
    unprep,
    compress_encrypt,
    decompress_decrypt,
    hash_db_info,
    WORKER_ID,
)


@contextlib.contextmanager
def passthrough():
    yield


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
            "%s.log" % logname,
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


def clear_old_logs(db_name, path, expire):
    """
    Clear logs older than the given value.  Primarily used for session handling
    """
    db_name, path, _ = hash_db_info(db_name, path, "")
    directory = os.path.dirname(get_log_filename(db_name, path, "test"))
    try:
        logs = os.listdir(directory)
    except:
        return
    for log in logs:
        fullname = os.path.join(directory, log)
        try:
            if os.stat(fullname).st_mtime < time.time() - expire:
                os.unlink(fullname)
        except:
            pass


def store_upload(id_, info, data):
    dir_ = os.path.join(base_context.cs_data_root, "_logs", "_uploads", id_)
    os.makedirs(dir_, exist_ok=True)
    with open(os.path.join(dir_, "info"), "wb") as f:
        f.write(info)
    with open(os.path.join(dir_, "content"), "wb") as f:
        f.write(data)


def retrieve_upload(id_):
    dir_ = os.path.join(base_context.cs_data_root, "_logs", "_uploads", id_)
    try:
        with open(os.path.join(dir_, "info"), "rb") as f:
            info = unprep(f.read())
        with open(os.path.join(dir_, "content"), "rb") as f:
            data = decompress_decrypt(f.read())
        return info, data
    except FileNotFoundError:
        return None


def _queue_location(queuename):
    return os.path.join(base_context.cs_data_root, "_logs", "_queues", queuename)


def _get_statuses(queuename):
    return os.listdir(_queue_location(queuename))


def _get_staging_filename(id):
    return os.path.join(_queue_location(""), "_staging", id)


def _new_queue_filename(queuename, status, created, updated, id):
    basename = f"{created}_{updated}_{id}"
    return os.path.join(_queue_location(queuename), status, basename)


def _get_entries(queuename, status):
    try:
        root = os.path.join(_queue_location(queuename), status)
        return {f: os.path.join(root, f) for f in os.listdir(root)}
    except:
        return {}


def queue_push(queuename, initial_status, data):
    now = time.time()
    id = str(uuid.uuid4())
    staging_name = _get_staging_filename(id)
    final_name = _new_queue_filename(queuename, initial_status, now, now, id)
    os.makedirs(os.path.dirname(staging_name), exist_ok=True)
    with open(staging_name, "wb") as f:
        pickle.dump(
            {
                "id": id,
                "worker": None,
                "data": prep(data),
            },
            f,
            4,
        )
    os.makedirs(os.path.dirname(final_name), exist_ok=True)
    os.rename(staging_name, final_name)
    return id


def queue_pop(queuename, old_status, new_status=None):
    for shortname, fullname in sorted(_get_entries(queuename, old_status).items()):
        try:
            # try moving to staging area; that's our indication that we
            # actually got an entry
            created, updated, id = shortname.split("_")
            staging_name = _get_staging_filename(id)
            os.rename(fullname, staging_name)
        except:
            continue

        # if we get here, we moved this to staging, so it belongs to us.
        # load the data first:

        with open(staging_name, "rb") as f:
            entry = pickle.load(f)
        entry["queuename"] = queuename
        entry["status"] = old_status
        entry["worker"] = WORKER_ID
        entry["created"] = float(created)
        entry["updated"] = float(updated)

        # want to set a new status, go for it.  otherwise, we'll just delete
        # this entry from the queue.
        if new_status is None:
            shutil.rmtree(staging_name, ignore_errors=True)
        else:
            now = time.time()
            entry["updated"] = now
            entry["status"] = new_status
            with open(staging_name, "wb") as f:
                pickle.dump(entry, f, 4)
            new_name = _new_queue_filename(queuename, new_status, created, now, id)
            os.makedirs(os.path.dirname(new_name), exist_ok=True)
            os.rename(staging_name, new_name)

        entry["data"] = unprep(entry["data"])  # unprep the data for the thing we return
        return entry
    return None


def queue_update(queuename, id, new_data, new_status=None):
    for i in range(100):
        try:
            cur_name = glob.glob(
                os.path.join(_queue_location(queuename), "*", f"*_{id}")
            )[0]
            staging_name = _get_staging_filename(id)
            os.rename(cur_name, staging_name)
            break
        except:
            time.sleep(0.001)
            continue
    else:
        return None

    status = cur_name.split(os.sep)[-2]
    created, updated, _ = os.path.basename(cur_name).split("_")

    with open(staging_name, "rb") as f:
        entry = pickle.load(f)

    entry["worker"] = WORKER_ID
    entry["data"] = prep(new_data)
    with open(staging_name, "wb") as f:
        pickle.dump(entry, f, 4)

    new_status = new_status or status
    new_name = _new_queue_filename(queuename, new_status, created, updated, id)
    os.makedirs(os.path.dirname(new_name), exist_ok=True)
    os.rename(staging_name, new_name)

    entry["queuename"] = queuename
    entry["status"] = new_status
    entry["created"] = float(created)
    entry["updated"] = float(updated)
    entry["data"] = new_data  # return the enprepped data here
    return entry


def queue_get(queuename, id):
    try:
        filename = glob.glob(os.path.join(_queue_location(queuename), "*", f"*_{id}"))[
            0
        ]
        with open(filename, "rb") as f:
            entry = pickle.load(f)

        entry["queuename"] = queuename
        entry["status"] = filename.split(os.sep)[-2]

        created, updated, _ = os.path.basename(filename).split("_")
        entry["created"] = float(created)
        entry["updated"] = float(updated)

        entry["data"] = unprep(entry["data"])

        return entry
    except:
        raise
        return None


def queue_all_entries(queuename, status):
    out = []
    for shortname, fullname in sorted(_get_entries(queuename, status).items()):
        with open(fullname, "rb") as f:
            entry = pickle.load(f)

        entry["queuename"] = queuename
        entry["status"] = status

        created, updated, _ = shortname.split("_")
        entry["created"] = float(created)
        entry["updated"] = float(updated)

        entry["data"] = unprep(entry["data"])

        out.append(entry)
    return out
