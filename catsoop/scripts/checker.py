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
import sys
import time
import shutil
import signal
import logging
import tempfile
import traceback
import collections
import multiprocessing

from datetime import datetime

import catsoop.base_context as base_context
import catsoop.lti as lti
import catsoop.auth as auth
import catsoop.cslog as cslog
import catsoop.loader as loader
import catsoop.language as language
import catsoop.dispatch as dispatch

from catsoop.process import set_pdeathsig

REAL_TIMEOUT = base_context.cs_checker_global_timeout

DEBUG = True

LOGGER = logging.getLogger("cs")

CHECKER = "checker"
QUEUED = "queued"
RUNNING = "running"
RESULTS = "results"

PROBLEMSTATE_QUEUE = multiprocessing.Queue


def log(msg):
    if not DEBUG:
        return
    dt = datetime.now()
    omsg = "[checker:%s]: %s" % (dt, msg)
    LOGGER.info(omsg)


def exc_message(context):
    exc = traceback.format_exc()
    exc = context["csm_errors"].clear_info(context, exc)
    return ('<p><font color="red"><b>CAT-SOOP ERROR:</b><pre>%s</pre></font>') % exc


def do_check(row):
    """
    Check submission, dispatching to appropriate question handler

    row: (dict) action to take, with input data
    """
    os.setpgrp()  # make this part of its own process group
    set_pdeathsig()()  # but make it die if the parent dies.  will this work?

    context = loader.generate_context(row["path"])
    context["cs_course"] = row["path"][0]
    context["cs_path_info"] = row["path"]
    context["cs_username"] = row["username"]
    context["cs_user_info"] = {"username": row["username"]}
    context["cs_user_info"] = auth.get_user_information(context)
    context["cs_now"] = datetime.fromtimestamp(row["time"])

    have_lti = ("cs_lti_config" in context) and ("lti_data" in row)
    if have_lti:
        lti_data = row["lti_data"]
        lti_handler = lti.lti4cs_response(
            context, lti_data
        )  # LTI response handler, from row['lti_data']
        log("lti_handler.have_data=%s" % lti_handler.have_data)
        if lti_handler.have_data:
            log("lti_data=%s" % lti_handler.lti_data)
            if not "cs_session_data" in context:
                context["cs_session_data"] = {}
            context["cs_session_data"][
                "is_lti_user"
            ] = True  # so that course preload.py knows

    cfile = dispatch.content_file_location(context, row["path"])
    log(
        "Loading grader python code course=%s, cfile=%s" % (context["cs_course"], cfile)
    )
    loader.load_content(
        context, context["cs_course"], context["cs_path_info"], context, cfile
    )

    namemap = collections.OrderedDict()
    cnt = 0
    total_possible_npoints = 0
    for elt in context["cs_problem_spec"]:
        if isinstance(elt, tuple):  # each elt is (problem_context, problem_kwargs)
            m = elt[1]
            namemap[m["csq_name"]] = elt
            csq_npoints = m.get("csq_npoints", 0)
            total_possible_npoints += (
                csq_npoints  # used to compute total aggregate score pct
            )
            if DEBUG:
                question = elt[0]["handle_submission"]
                dn = m.get("csq_display_name")
                log("Map: %s (%s) -> %s" % (m["csq_name"], dn, question))
                log(
                    "%s csq_npoints=%s, total_points=%s"
                    % (dn, csq_npoints, elt[0]["total_points"]())
                )
            cnt += 1
    if DEBUG:
        log(
            "Loaded %d procedures into question namemap (total_possible_npoints=%s)"
            % (cnt, total_possible_npoints)
        )

    # now, depending on the action we want, take the appropriate steps

    names_done = set()
    for name in row["names"]:
        if name.startswith("__"):
            name = name[2:].rsplit("_", 1)[0]
        if name in names_done:
            continue
        names_done.add(name)
        question, args = namemap[name]
        if row["action"] == "submit":
            if DEBUG:
                log("submit name=%s, row=%s" % (name, row))
            try:
                handler = question["handle_submission"]
                if DEBUG:
                    log("handler=%s" % handler)
                resp = handler(row["form"], **args)
                score = resp["score"]
                msg = resp["msg"]
                extra = resp.get("extra_data", None)
            except Exception as err:
                resp = {}
                score = 0.0
                log("Failed to handle submission, err=%s" % str(err))
                log("Traceback=%s" % traceback.format_exc())
                msg = exc_message(context)
                extra = None

            if DEBUG:
                log("submit resp=%s, msg=%s" % (resp, msg))

            score_box = context["csm_tutor"].make_score_display(
                context, args, name, score, True
            )

        elif row["action"] == "check":
            try:
                msg = question["handle_check"](row["form"], **args)
            except:
                msg = exc_message(context)

            score = None
            score_box = ""
            extra = None

            if DEBUG:
                log("check name=%s, msg=%s" % (name, msg))

        row["score"] = score
        row["score_box"] = score_box
        row["response"] = language.handle_custom_tags(context, msg)
        row["extra_data"] = extra

        # store the results
        cslog.queue_update(row["id"], row, RESULTS)

        # now update the log appropriately
        def log_mutator(x):
            if row["action"] == "submit":
                x.setdefault("scores", {})[name] = row["score"]
            x.setdefault("score_displays", {})[name] = row["score_box"]
            x.setdefault("cached_responses", {})[name] = row["response"]
            x.setdefault("extra_data", {})[name] = row["extra_data"]

            if have_lti and lti_handler.have_data and row["action"] == "submit":
                aggregate_score = 0
                cnt = 0
                try:
                    for k, v in x[
                        "scores"
                    ].items():  # e.g. 'scores': {'q000000': 1.0, 'q000001': True, 'q000002': 1.0}
                        aggregate_score += float(v)
                        cnt += 1
                    if total_possible_npoints == 0:
                        total_possible_npoints = 1.0
                        LOGGER.error("[checker] total_possible_npoints=0 ????")
                    aggregate_score_fract = (
                        aggregate_score * 1.0 / total_possible_npoints
                    )  # LTI wants score in [0, 1.0]
                    log(
                        "Computed aggregate score from %d questions, aggregate_score=%s (fraction=%s)"
                        % (cnt, aggregate_score, aggregate_score_fract)
                    )
                    log(
                        "magic=%s sending aggregate_score_fract=%s to LTI tool consumer"
                        % (row["magic"], aggregate_score_fract)
                    )
                    score_ok = True
                except Exception as err:
                    LOGGER.error(
                        "[checker] failed to compute score for problem %s, err=%s"
                        % (x, err)
                    )
                    score_ok = False

                if score_ok:
                    try:
                        lti_handler.send_outcome(aggregate_score_fract)
                    except Exception as err:
                        LOGGER.error(
                            "[checker] failed to send outcome to LTI consumer, err=%s"
                            % str(err)
                        )
                        LOGGER.error("[checker] traceback=%s" % traceback.format_exc())
            return x

        cslog.modify_most_recent(
            row["username"],
            row["path"],
            "problemstate",
            default={},
            transform_func=log_mutator,
            method="overwrite",
        )


running = []

# if anything is in the "running" dir when we start, and it's owned by us,
# that's an error.  turn those back to queued to force them to run again (put
# them at the front of the queue).
for entry in cslog.queue_all_entries(CHECKER, RUNNING):
    if entry["worker"] == cslog.WORKER_ID:
        cslog.queue_update(entry["id"], entry["data"], QUEUED)


# and now actually start running
if DEBUG:
    log("starting main loop")
nrunning = None

while True:
    # check for dead processes
    dead = set()
    if DEBUG and not (
        len(running) == nrunning
    ):  # output debug message when nrunning changes
        nrunning = len(running)
        log("have %d running (%s)" % (nrunning, running))
    for i in range(len(running)):
        p = running[i]
        if not p.is_alive():
            log("    Process %s is dead" % p)
            if p.exitcode != 0:
                p._entry["data"]["score"] = 0.0
                p._entry["data"]["score_box"] = ""
                if p.exitcode < 0:  # this probably only happens if we killed it
                    p._entry["data"]["response"] = (
                        "<font color='red'><b>Your submission could not be checked "
                        "because the checker ran for too long.</b></font>"
                    )
                else:  # a python error or similar
                    p._entry["data"]["response"] = (
                        "<font color='red'><b>An unknown error occurred when "
                        "processing your submission</b></font>"
                    )
                queue_update(p._entry["data"]["id"], p._entry["data"], RESULTS)
            dead.add(i)
        elif time.time() - p._started > REAL_TIMEOUT:
            # kill this now, next pass through the loop will clean it up
            try:
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            except:
                pass
    if dead:
        log("Removing %s" % dead)
    for i in sorted(dead, reverse=True):
        running.pop(i)

    if base_context.cs_checker_parallel_checks - len(running) > 0:
        # otherwise, add an entry to running.
        new_entry = cslog.queue_pop(CHECKER, QUEUED, RUNNING)
        if new_entry is not None:
            new_entry["data"]["id"] = new_entry["id"]
            log("Starting checker with row=%s" % new_entry["data"])
            p = multiprocessing.Process(target=do_check, args=(new_entry["data"],))
            running.append(p)
            p.start()
            p._started = time.time()
            p._entry = new_entry
            log("Process pid = %s" % p.pid)

    time.sleep(0.1)
