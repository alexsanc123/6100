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

import os
import sys
import json
import uuid
import time
import pickle
import shutil
import signal
import logging
import tempfile
import traceback
import subprocess
import collections
import multiprocessing

from datetime import datetime
import urllib.parse, urllib.request

CATSOOP_LOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if CATSOOP_LOC not in sys.path:
    sys.path.append(CATSOOP_LOC)

import catsoop.base_context as base_context
import catsoop.lti as lti
import catsoop.auth as auth
import catsoop.util as util
import catsoop.cslog as cslog
import catsoop.loader as loader
import catsoop.language as language
import catsoop.dispatch as dispatch

from catsoop.process import set_pdeathsig

CHECKER_DB_LOC = os.path.join(base_context.cs_data_root, "_logs", "_checker")
COURSES_LOC = os.path.join(base_context.cs_data_root, "courses")
RUNNING = os.path.join(CHECKER_DB_LOC, "running")
QUEUED = os.path.join(CHECKER_DB_LOC, "queued")
RESULTS = os.path.join(CHECKER_DB_LOC, "results")
ACTIONS = os.path.join(CHECKER_DB_LOC, "actions")
STAGING = os.path.join(CHECKER_DB_LOC, "staging")

for i in (RUNNING, QUEUED, RESULTS, ACTIONS, STAGING):
    os.makedirs(i, exist_ok=True)

REAL_TIMEOUT = base_context.cs_checker_global_timeout

DEBUG = True

LOGGER = logging.getLogger("cs")


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
    for elt in context["cs_problem_spec"]:
        if isinstance(elt, tuple):  # each elt is (problem_context, problem_kwargs)
            namemap[elt[1]["csq_name"]] = elt

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

        # make temporary file to write results to
        magic = row["magic"]
        temploc = os.path.join(STAGING, "results.%s" % magic)
        with open(temploc, "wb") as f:
            f.write(context["csm_cslog"].prep(row))
        # move that file to results, close the handle to it.
        newloc = os.path.join(RESULTS, magic[0], magic[1], magic)
        os.makedirs(os.path.dirname(newloc), exist_ok=True)
        shutil.move(temploc, newloc)
        try:
            os.close(_)
        except:
            pass
        # then remove from running
        os.unlink(os.path.join(RUNNING, row["magic"]))
        # finally, update the appropriate log
        cm = context["csm_cslog"].log_lock(
            [row["username"], *row["path"], "problemstate"]
        )
        with cm as lock:
            x = context["csm_cslog"].most_recent(
                row["username"], row["path"], "problemstate", {}, lock=False
            )
            if row["action"] == "submit":
                x.setdefault("scores", {})[name] = row["score"]
            x.setdefault("score_displays", {})[name] = row["score_box"]
            x.setdefault("cached_responses", {})[name] = row["response"]
            x.setdefault("extra_data", {})[name] = row["extra_data"]
            context["csm_cslog"].overwrite_log(
                row["username"], row["path"], "problemstate", x, lock=False
            )

            # update LTI tool consumer with new aggregate score
            if have_lti and lti_handler.have_data and row["action"] == "submit":
                lti.update_lti_score(lti_handler, x, namemap)


def clear_remote(r):
    del REMOTE_URLS[r]
    del REMOTE_COURSES[r]
    del REMOTE_ALL_COURSES[r]
    del REMOTE_ALIVE_TIME[r]

    # clean up processes before removing
    for magic in REMOTE_PROCESSES[r][0]:
        old_loc = os.path.join(RUNNING, magic)
        new_loc = os.path.join(QUEUED, "0_%s" % magic)
        if os.path.isfile(old_loc):
            shutil.move(old_loc, new_loc)
    del REMOTE_PROCESSES[r]


if __name__ == "__main__":
    running = []

    # if anything is in the "running" dir when we start, that's an error.  turn
    # those back to queued to force them to run again (put them at the front of the
    # queue).
    for f in os.listdir(RUNNING):
        shutil.move(os.path.join(RUNNING, f), os.path.join(QUEUED, "0_%s" % f))

    # and now actually start running
    if DEBUG:
        log("starting main loop")

    REMOTE_URLS = {}  # checker_id
    REMOTE_PROCESSES = (
        {}
    )  # checker_id: [{magic: (row, time_started), ...}, max_processes]
    REMOTE_COURSES = (
        {}
    )  # checker_id: set of courses that the checker is ready to check for
    REMOTE_ALL_COURSES = (
        {}
    )  # checker_id: set of all courses the checker reported being OK to check for
    REMOTE_ALIVE_TIME = {}  # checker_id: last time heard from

    COURSE_GIT_HASHES = {}  # current head

    while True:
        # clear out remotes that we haven't heard from in a while
        t = time.time()
        to_remove = set()
        for remote, last_seen in REMOTE_ALIVE_TIME.items():
            if t - last_seen > 60:
                to_remove.add(remote)
        for r in to_remove:
            clear_remote(r)

        # update current state of git repos for subjects
        for course in sorted(os.listdir(COURSES_LOC)):
            full_path = os.path.realpath(os.path.join(COURSES_LOC, course))
            try:
                COURSE_GIT_HASHES[course] = (
                    subprocess.check_output(
                        ["git", "rev-parse", "HEAD"],
                        stderr=subprocess.PIPE,
                        cwd=full_path,
                    )
                    .strip()
                    .decode("utf-8")
                )
            except:
                pass

        # once we have the state, ask each remote to update itself
        # this can also cause us to remove checkers entirely if we can't talk to
        # them
        to_remove = set()
        for course, hash_ in COURSE_GIT_HASHES.items():
            for remote, remote_courses in REMOTE_COURSES.items():
                if (
                    course in REMOTE_ALL_COURSES[remote]
                    and remote_courses.get(course, None) != hash_
                ):
                    data = util.remote_checker_encode(
                        {"action": "update_course", "course": course, "hash": hash_}
                    )
                    try:
                        req = urllib.request.Request(REMOTE_URLS[remote], data=data)
                        resp = json.loads(urllib.request.urlopen(req, timeout=3).read())
                        assert resp["ok"]
                    except:
                        raise
                        to_remove.add(remote)
        for r in to_remove:
            clear_remote(r)

        # now, handle actions
        for action in sorted(os.listdir(ACTIONS)):
            full_path = os.path.join(ACTIONS, action)
            with open(full_path, "rb") as f:
                action = pickle.load(f)
            os.unlink(full_path)
            t = action["action"]
            if t == "hello":
                new_id = uuid.uuid4().hex
                data = util.remote_checker_encode({"action": "connected", "id": new_id})
                try:
                    req = urllib.request.Request(action["url"], data=data)
                    resp = json.loads(urllib.request.urlopen(req, timeout=3).read())
                    assert resp["ok"]
                except Exception as e:
                    # no response back, or something like that; just ignore this...
                    continue
                to_remove = {
                    remote
                    for remote in REMOTE_URLS
                    if REMOTE_URLS[remote] == action["url"]
                }
                for r in to_remove:
                    clear_remote(r)
                REMOTE_URLS[new_id] = action["url"]
                REMOTE_PROCESSES[new_id] = [{}, action["parallel_checks"]]
                REMOTE_COURSES[new_id] = action["courses"]
                REMOTE_ALL_COURSES[new_id] = set(action["courses"])
                REMOTE_ALIVE_TIME[new_id] = time.time()
            else:
                id_ = action["id"]
                if id_ not in REMOTE_URLS:
                    data = util.remote_checker_encode({"action": "unknown", "id": id_})
                    try:
                        req = urllib.request.Request(action["url"], data=data)
                        resp = urllib.request.urlopen(req).read(timeout=3)
                    except:
                        continue
                else:
                    REMOTE_ALIVE_TIME[id_] = time.time()
                    if t == "courses_updated":
                        for course, hash_ in action["courses"]:
                            if hash_ == COURSE_GIT_HASHES[course]:
                                REMOTE_COURSES[id_][course] = hash_
                    elif t == "goodbye":
                        del REMOTE_URLS[id_]
                        del REMOTE_PROCESSES[id_]
                        del REMOTE_COURSES[id_]
                        del REMOTE_ALL_COURSES[id_]
                        del REMOTE_ALIVE_TIME[id_]
                    elif t == "check_done":
                        running = REMOTE_PROCESSES[id_][0]
                        try:
                            row = action["row"]
                            magic = row["magic"]
                            try:
                                name = row["name"]
                            except:
                                name = None
                            try:
                                _ = running.pop(magic)
                            except:
                                pass
                            # if we get here, this existed, and we should add it to results
                            old_loc = os.path.join(RUNNING, magic)
                            if not os.path.isfile(old_loc):
                                continue
                            new_loc = os.path.join(RESULTS, magic[0], magic[1], magic)
                            os.makedirs(os.path.dirname(new_loc), exist_ok=True)
                            with open(new_loc, "wb") as f:
                                f.write(cslog.prep(row))
                            os.unlink(old_loc)

                            if name is not None:
                                cm = cslog.log_lock(
                                    [row["username"], *row["path"], "problemstate"]
                                )
                                with cm as lock:
                                    x = cslog.most_recent(
                                        row["username"],
                                        row["path"],
                                        "problemstate",
                                        {},
                                        lock=False,
                                    )
                                    if row["action"] == "submit":
                                        x.setdefault("scores", {})[name] = row["score"]
                                    x.setdefault("score_displays", {})[name] = row[
                                        "score_box"
                                    ]
                                    x.setdefault("cached_responses", {})[name] = row[
                                        "response"
                                    ]
                                    x.setdefault("extra_data", {})[name] = row[
                                        "extra_data"
                                    ]
                                    cslog.overwrite_log(
                                        row["username"],
                                        row["path"],
                                        "problemstate",
                                        x,
                                        lock=False,
                                    )

                                    # update LTI tool consumer with new aggregate score
                                    have_lti = "lti_data" in row
                                    if have_lti:
                                        context = loader.generate_context(row["path"])
                                        lti_handler = lti.lti4cs_response(
                                            context, row["lti_data"]
                                        )  # LTI response handler, from row['lti_data']

                                    if (
                                        have_lti
                                        and lti_handler.have_data
                                        and row["action"] == "submit"
                                    ):
                                        lti.update_lti_score(lti_handler, x, namemap)
                        except:
                            pass

        # check for processes that have been running for too long with no results
        # coming back, purge them and add to results (maybe the checker died or
        # something?)
        t = time.time()
        for remote in REMOTE_PROCESSES:
            to_kill = set()
            for magic, (row, started) in REMOTE_PROCESSES[remote][0].items():
                if t - started > REAL_TIMEOUT:
                    to_kill.add(magic)
                    row["response"] = (
                        "<font color='red'><b>Your submission could not be checked "
                        "because the checker ran for too long.</b></font>"
                    )
                    newloc = os.path.join(RESULTS, magic[0], magic[1], magic)
                    with open(newloc, "wb") as f:
                        f.write(cslog.prep(row))
                    os.unlink(os.path.join(RUNNING, row["magic"]))
            for magic in to_kill:
                del REMOTE_PROCESSES[remote][0][magic]

        # finally, look through queued requests and send one off to a checker if we
        # have one
        waiting = sorted(os.listdir(QUEUED))
        for first in waiting:
            qfn = os.path.join(QUEUED, first)
            with open(qfn, "rb") as f:
                try:
                    row = cslog.unprep(f.read())
                except Exception as err:
                    LOGGER.error(
                        "[checker] failed to read queue log file %s, error=%s, traceback=%s"
                        % (qfn, err, traceback.format_exc())
                    )
                    # error reading? try the next queued entry
                    continue
            _, magic = first.split("_")
            row["magic"] = magic

            # send a request for a worker to start it
            course = row["path"][0]
            to_remove = set()
            for remote in REMOTE_PROCESSES:
                if (
                    course in REMOTE_COURSES[remote]
                    and len(REMOTE_PROCESSES[remote][0]) < REMOTE_PROCESSES[remote][1]
                ):
                    data = util.remote_checker_encode(
                        {"action": "do_check", "row": row, "id": remote}
                    )
                    try:
                        req = urllib.request.Request(REMOTE_URLS[remote], data=data)
                        resp = json.loads(urllib.request.urlopen(req, timeout=3).read())
                        assert resp["ok"]
                    except:
                        to_remove.add(remote)
                        continue
                    shutil.move(
                        os.path.join(QUEUED, first), os.path.join(RUNNING, magic)
                    )
                    REMOTE_PROCESSES[remote][0][magic] = (row, time.time())
                    break
            else:
                # if we didn't find a checker, continue on to the next queued entry
                for r in to_remove:
                    clear_remote(r)
                continue

            # if we're here, we found a checker.  get out of our loop over queued
            # entries
            for r in to_remove:
                clear_remote(r)
            break

        # sleep for a little while before looping again
        time.sleep(0.3)
