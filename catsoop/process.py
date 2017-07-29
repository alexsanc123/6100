# This file is part of CAT-SOOP
# Copyright (c) 2011-2017 Adam Hartz <hartz@mit.edu>
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
import time
import ctypes
import signal
import threading
import subprocess
import multiprocessing


libc = ctypes.CDLL("libc.so.6")
def set_pdeathsig(sig = signal.SIGTERM):
    def callable():
        return libc.prctl(1, sig)
    return callable


class PKiller(threading.Thread):
    def __init__(self, proc, timeout):
        threading.Thread.__init__(self)
        self.proc = proc
        self.timeout = timeout
        self.going = True

    def run(self):
        if isinstance(self.proc, subprocess.Popen):
            self.run_subproc()
        else:
            self.run_multiproc()

    def run_multiproc(self):
        end = time.time() + self.timeout
        while (time.time() < end):
            time.sleep(0.1)
            if (not self.proc.is_alive()) or (not self.going):
                return
        if self.going:
            try:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
            except:
                pass

    def run_subproc(self):
        end = time.time() + self.timeout
        while (time.time() < end):
            time.sleep(0.1)
            if (self.proc.poll() is not None) or (not self.going):
                return
        if self.going:
            try:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
            except:
                pass

