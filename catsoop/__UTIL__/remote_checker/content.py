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

import sys
import hmac
import json
import time
import uuid
import base64
import pickle
import hashlib


def decode_remote_checker_message():
    return csm_util.remote_checker_decode(cs_form["payload"])


# our dumping ground for results from here
action = os.path.join(
    cs_data_root,
    "_logs",
    "_checker",
    "actions",
    "%d_%s" % (time.time(), uuid.uuid4().hex),
)

res = decode_remote_checker_message()
if res is not None:
    with open(action, "wb") as f:
        f.write(res)
    ok = True
else:
    ok = False

cs_handler = "raw_response"
content_type = "application/json"
response = json.dumps({"ok": ok})
