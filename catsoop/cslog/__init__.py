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
Logging mechanisms

From a high-level perspective, CAT-SOOP's logs are sequences of Python objects.

A log is identified by a `db_name` (typically a username), a `path` (a list of
strings starting with a course name), and a `logname` (a string).

This package provides functions for interacting with and modifying those logs.
In particular, it provides ways to retrieve the Python objects in a log, or to
add new Python objects to a log.
"""

import os
import ast
import sys
import lzma
import uuid
import base64
import pickle
import struct
import hashlib
import importlib

from collections import OrderedDict
from datetime import datetime, timedelta

_nodoc = {
    "FileLock",
    "SEP_CHARS",
    "get_separator",
    "good_separator",
    "modify_most_recent",
    "NoneType",
    "OrderedDict",
    "datetime",
    "timedelta",
    "COMPRESS",
    "Cipher",
    "ENCRYPT_KEY",
    "ENCRYPT_PASS",
    "RawFernet",
    "compress_encrypt",
    "decompress_decrypt",
    "default_backend",
    "log_lock",
    "prep",
    "sep",
    "unprep",
}


from .. import time
from .. import util
from .. import base_context
from filelock import FileLock

importlib.reload(base_context)

COMPRESS = base_context.cs_log_compression

ENCRYPT_KEY = None
ENCRYPT_PASS = os.environ.get("CATSOOP_PASSPHRASE", None)
if ENCRYPT_PASS is not None:
    with open(
        os.path.join(os.path.dirname(os.environ["CATSOOP_CONFIG"]), "encryption_salt"),
        "rb",
    ) as f:
        SALT = f.read()
    ENCRYPT_KEY = hashlib.pbkdf2_hmac(
        "sha256", ENCRYPT_PASS.encode("utf8"), SALT, 100000, dklen=32
    )


def compress_encrypt(x):
    if COMPRESS:
        x = lzma.compress(x)
    if ENCRYPT_KEY is not None:
        x = util.simple_encrypt(ENCRYPT_KEY, x)
    return x


def prep(x):
    """
    Helper function to serialize a Python object.
    """
    return compress_encrypt(pickle.dumps(x, 4))


def decompress_decrypt(x):
    if ENCRYPT_KEY is not None:
        x = util.simple_decrypt(ENCRYPT_KEY, x)
    if COMPRESS:
        x = lzma.decompress(x)
    return x


def unprep(x):
    """
    Helper function to deserialize a Python object.
    """
    return pickle.loads(decompress_decrypt(x))


def _e(x, person):
    p = hashlib.sha512(person.encode("utf-8")).digest()[:9]
    return base64.urlsafe_b64encode(
        hashlib.blake2b(x.encode("utf-8"), person=b"catsoop%s" % p).digest()
    ).decode("utf-8")


def hash_db_info(db_name, path, logname):
    if ENCRYPT_KEY is not None:
        seed = path[0] if path else db_name
        path = [_e(p, seed + repr(path[:ix])) for ix, p in enumerate(path)]
        db_name = _e(db_name, seed + repr(path))
        logname = _e(logname, seed + repr(path))
    return db_name, path, logname


def prepare_upload(username, data, filename):
    hstring = hashlib.sha256(data).hexdigest()
    info = {
        "filename": filename,
        "username": username,
        "time": time.detailed_timestamp(time.now()),
        "hash": hstring,
    }
    return "%s%s" % (uuid.uuid4().hex, hstring), prep(info), compress_encrypt(data)


try:
    with open("/etc/machine-id", "rb") as f:
        WORKER_ID = hashlib.blake2b(
            f.read(), key=b"catsoop_checker", person=b"=(o_O)=", digest_size=16
        ).hexdigest()
except:
    WORKER_ID = None

_store = base_context.cs_log_storage_backend
exec(
    """from .%s import (
    setup_kwargs,
    teardown_kwargs,
    read_log,
    most_recent,
    update_log,
    overwrite_log,
    modify_most_recent,
    initialize_database,
    clear_old_logs,
    store_upload,
    retrieve_upload,
    queue_push,
    queue_pop,
    queue_get,
    queue_update,
    queue_all_entries,
)"""
    % base_context.cs_log_storage_backend
)
