# This file is part of CAT-SOOP
# Copyright (c) 2011-2019 by The CAT-SOOP Developers <catsoop-dev@mit.edu>
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
import time

OPCODE_TRACING_ENABLED = sys.version_info > (3, 7)
if OPCODE_TRACING_ENABLED and True:  # TODO: Add a flag here for enabling opcode counts
    def trace_closure(limit=float('inf')):
        executed_opcodes = 0
        limit_reached = False

        def tracer(frame, event, arg):
            nonlocal executed_opcodes, limit_reached
            frame.f_trace_opcodes = True
            if event == 'opcode':
                executed_opcodes += 1
                if executed_opcodes >= limit:
                    limit_reached = True
                    sys.exit(1)
            return tracer

        def get():
            return executed_opcodes

        def killed():
            return limit_reached

        names = {
            'tracer': tracer,
            'get': get,
            'killed': killed,
        }

        return lambda n: names[n]

    tracer = trace_closure()
    sys.settrace(tracer('tracer'))

class NoAnswerGiven:
    pass

results = {}
start_time = time.time()
try:
    import sft as test_module ## TODO: replace sft with module name
    ans = getattr(test_module, '_catsoop_answer', NoAnswerGiven)
    if ans is not NoAnswerGiven:  # we got a result back
        results['result'] = ans
finally:
    results['duration'] = time.time() - start_time
    sys.settrace(None)
    if OPCODE_TRACING_ENABLED:
        results['opcodes_executed'] = tracer('get')()
        results['opcode_limit_reached'] = tracer('killed')()
    print('---')
    print(results)
