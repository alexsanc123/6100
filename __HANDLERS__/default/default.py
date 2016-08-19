# This file is part of CAT-SOOP
# Copyright (c) 2011-2016 Adam Hartz <hartz@mit.edu>

# This program is free software: you can redistribute it and/or modify it under
# the terms of the Soopycat License, version 1.

# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the Soopycat License for more details.

# You should have received a copy of the Soopycat License along with this
# program.  If not, see <https://smatz.net/soopycat>.

import os
import re
import json
import random
import string
import traceback
import collections

_prefix = 'cs_defaulthandler_'


def _n(n):
    return "%s%s" % (_prefix, n)


def _unknown_handler(action):
    return lambda x: 'Unknown Action: %s' % action


def _get(context, key, default, cast=lambda x: x):
    v = context.get(key, default)
    return cast(v(context) if isinstance(v, collections.Callable) else v)


def handle(context):
    # set some variables in context
    pre_handle(context)

    mode_handlers = {'view': handle_view,
                     'submit': handle_submit,
                     'check': handle_check,
                     'save': handle_save,
                     'viewanswer': handle_viewanswer,
                     'clearanswer': handle_clearanswer,
                     'viewexplanation': handle_viewexplanation,
                     'copy': handle_copy,
                     'copy_seed': handle_copy_seed,
                     'activate': handle_activate,
                     'lock': handle_lock,
                     'unlock': handle_unlock,
                     'grade': handle_grade,
                     'passthrough': lambda c: '',
                     'new_seed': handle_new_seed,
                     'list_questions': handle_list_questions,
                     'get_state': handle_get_state,
                     'manage_groups': manage_groups,
                     }

    action = context[_n('action')]
    return mode_handlers.get(action, _unknown_handler(action))(context)


def handle_list_questions(context):
    types = {k: v[0]['qtype'] for k,v in context[_n('name_map')].items()}
    order = list(context[_n('name_map')])
    return make_return_json(context, {'order': order, 'types': types}, [])


def handle_get_state(context):
    ll = context[_n('last_log')]
    for i in ll:
        if isinstance(ll[i], set):
            ll[i] = list(ll[i])
    return make_return_json(context, ll, [])


def handle_copy_seed(context):
    if context[_n('impersonating')]:
        impersonated = context[_n('uname')]
        uname = context[_n('real_uname')]
        course = context['cs_course']
        logname = '.'.join(['random.seed'] + context['cs_path_info'])
        stored = context['csm_cslog'].most_recent(course, impersonated,
                                                  logname, None)
        context['csm_cslog'].update_log(course, uname, logname, stored)
    return handle_save(context)


def _new_random_seed(n=100):
    try:
        return os.urandom(n)
    except:
        return ''.join(random.choice(string.ascii_letters) for i in range(n))


def handle_new_seed(context):
    uname = context[_n('uname')]
    course = context['cs_course']
    logname = '.'.join(['random.seed'] + context['cs_path_info'])
    context['csm_cslog'].update_log(course, uname, logname, _new_random_seed())

    # Rerender the questions
    names = context[_n('question_names')]
    outdict = {}
    for name in names:
        outdict[name] = {'rerender': 'Please refresh the page'}

    return make_return_json(context, outdict)


def handle_activate(context):
    submitted_pass = context[_n('form')].get('activation_password', '')
    if submitted_pass == context[_n('activation_password')]:
        newstate = dict(context[_n('last_log')])
        newstate['activated'] = True

        course = context['cs_course']
        uname = context[_n('uname')]
        logname = context[_n('logname_state')]
        context['csm_cslog'].overwrite_log(course, uname, logname, newstate)
        context[_n('last_log')] = newstate
    return handle_view(context)


def handle_copy(context):
    if context[_n('impersonating')]:
        context[_n('uname')] = context[_n('real_uname')]
        ll = context['csm_cslog'].most_recent(context['cs_course'],
                                              context[_n('uname')],
                                              context[_n('logname_state')], {})
        context[_n('last_log')] = ll
    return handle_save(context)


def handle_activation_form(context):
    context['cs_content_header'] = 'Problem Activation'
    out = '<form method="POST">'
    out += ('\nActivation Password: '
            '<input type="text" '
            'name="activation_password" '
            'value="" />'
            '\n&nbsp;'
            '\n<input type="submit" '
            'name="action" '
            'value="Activate" />')
    if 'admin' in context[_n('perms')]:
        pwd = context[_n('activation_password')]
        out += ('\n<p><u>Staff:</u> password is '
                '<tt><font color="blue">%s</font></tt>') % pwd
    out += '</form>'

    p = context[_n('perms')]
    if 'submit' in p or 'submit_all' in p:
        log_action(context, {'action': 'show_activation_form'})

    return out


def handle_view(context):
    # base function: display the problem
    uname = context[_n('uname')]
    perms = context[_n('perms')]

    lastlog = context[_n('last_log')]
    lastsubmit = lastlog.get('last_submit', {})

    if (_get(context, 'cs_auth_required', True, bool) and
            'view' not in perms and 'view_all' not in perms):
        return 'You are not allowed to view this page.'

    if (_get(context, 'cs_require_activation', False, bool) and
            not lastlog.get('activated', False)):
        return handle_activation_form(context)

    due = context[_n('due')]
    timing = context[_n('timing')]

    if timing == -1 and ('view_all' not in perms):
        reltime = context['csm_time'].long_timestamp(context[_n('rel')])
        reltime = reltime.replace(';', ' at')
        return ('This page is not yet available.  '
                'It will become available on %s.') % reltime

    if 'submit' in perms or 'submit_all' in perms:
        # only log an entry for users who can submit
        log_action(context, {'action': 'view',
                             'score': lastlog.get('score', 0.0)})

    page = ''
    num_questions = len(context[_n('name_map')])
    if (num_questions > 0 and _get(context, 'cs_show_due', True, bool) and
            context.get('cs_due_date', 'NEVER') != 'NEVER'):
        duetime = context['csm_time'].long_timestamp(due)
        page += ('<tutoronly><center>'
                 'The questions below are due on %s.'
                 '<br/>--<br/></center></tutoronly>') % duetime

    for elt in context['cs_problem_spec']:
        if isinstance(elt, str):
            page += elt
        else:
            # this is a question
            page += render_question(elt, context, lastsubmit)

    page += default_javascript(context)
    page += default_timer(context)
    return page


def get_manual_grading_entry(context, name):
    pg_name = context[_n('logname_grades')]
    uname = context['cs_user_info'].get('username', 'None')
    log = context['csm_cslog'].read_log(context['cs_course'], uname, pg_name)
    out = None
    for i in log:
        if i['qname'] == name:
            out = i
    return out


def make_score_display(context, name, score, assume_submit=False):
    _, args = context[_n('name_map')][name]
    if not _get(args, 'csq_show_score', True, bool):
        if name in context[_n('last_log')].get('scores', {}) or assume_submit:
            return 'Submission received.'
        else:
            return ''
    gmode = _get(args, 'csq_grading_mode', 'auto', str)
    if gmode == 'manual':
        log = get_manual_grading_entry(context, name)
        if log is not None:
            score = log['score']
    if score is None:
        if name in context[_n('last_log')].get('scores', {}) or assume_submit:
            return 'Grade not available.'
        else:
            return ''
    c = context.get('cs_make_score_display', None)
    try:
        return c(score)
    except:
        colorthing = 255 * score
        r = max(0, 200 - colorthing)
        g = min(200, colorthing)
        s = score * 100
        return ('<span style="color:rgb(%d,%d,0);font-weight:bolder;">'
                '%.02f%%</span>') % (r, g, s)


def handle_clearanswer(context):
    names = context[_n('question_names')]
    timing = context[_n('timing')]
    due = context[_n('due')]
    lastlog = context[_n('last_log')]
    answerviewed = context[_n('answer_viewed')]
    explanationviewed = context[_n('explanation_viewed')]

    newstate = dict(lastlog)
    newstate['timestamp'] = context['cs_timestamp']
    if 'last_submit' not in newstate:
        newstate['last_submit'] = {}

    outdict = {}  # dictionary containing the responses for each question
    for name in names:
        out = {}

        error = clearanswer_msg(context, context[_n('perms')], name)
        if error is not None:
            out['error_msg'] = error
            outdict[name] = out
            continue

        q, args = context[_n('name_map')][name]

        out['clear'] = True
        outdict[name] = out

        answerviewed.discard(name)
        explanationviewed.discard(name)

    newstate['answer_viewed'] = answerviewed
    newstate['explanation_viewed'] = explanationviewed

    # update problemstate log
    course = context['cs_course']
    uname = context[_n('uname')]
    logname = context[_n('logname_state')]
    context['csm_cslog'].overwrite_log(course, uname, logname, newstate)

    # log submission in problemactions
    duetime = context['csm_time'].detailed_timestamp(due)
    log_action(context, {'action': 'viewanswer',
                         'names': names,
                         'score': newstate.get('score', 0.0),
                         'response': outdict,
                         'due_date': duetime})

    return make_return_json(context, outdict)


def explanation_display(x):
    return '<hr /><p><b>Explanation:</b></p>%s' % x


def handle_viewexplanation(context):
    names = context[_n('question_names')]
    timing = context[_n('timing')]
    due = context[_n('due')]
    lastlog = context[_n('last_log')]
    explanationviewed = context[_n('explanation_viewed')]
    loader = context['csm_loader']
    language = context['csm_language']

    newstate = dict(lastlog)
    newstate['timestamp'] = context['cs_timestamp']
    if 'last_submit' not in newstate:
        newstate['last_submit'] = {}

    outdict = {}  # dictionary containing the responses for each question
    for name in names:
        out = {}

        error = viewexp_msg(context, context[_n('perms')], name)
        if error is not None:
            out['error_msg'] = error
            outdict[name] = out
            continue

        q, args = context[_n('name_map')][name]
        exp = explanation_display(args['csq_explanation'])
        out['explanation'] = language.source_transform_string(context, exp)
        outdict[name] = out

        explanationviewed.add(name)

    newstate['explanation_viewed'] = explanationviewed

    # update problemstate log
    course = context['cs_course']
    uname = context[_n('uname')]
    logname = context[_n('logname_state')]
    context['csm_cslog'].overwrite_log(course, uname, logname, newstate)

    # log submission in problemactions
    duetime = context['csm_time'].detailed_timestamp(due)
    log_action(context, {'action': 'viewanswer',
                         'names': names,
                         'score': newstate.get('score', 0.0),
                         'response': outdict,
                         'due_date': duetime})

    return make_return_json(context, outdict)


def handle_viewanswer(context):
    names = context[_n('question_names')]
    timing = context[_n('timing')]
    due = context[_n('due')]
    lastlog = context[_n('last_log')]
    answerviewed = context[_n('answer_viewed')]
    loader = context['csm_loader']
    language = context['csm_language']

    newstate = dict(lastlog)
    newstate['timestamp'] = context['cs_timestamp']
    if 'last_submit' not in newstate:
        newstate['last_submit'] = {}

    outdict = {}  # dictionary containing the responses for each question
    for name in names:
        out = {}

        error = viewanswer_msg(context, context[_n('perms')], name)
        if error is not None:
            out['error_msg'] = error
            outdict[name] = out
            continue

        q, args = context[_n('name_map')][name]

        # if we are here, no errors occurred.  go ahead with checking.
        ans = q['answer_display'](**args)
        out['answer'] = language.source_transform_string(context, ans)
        outdict[name] = out

        answerviewed.add(name)

    newstate['answer_viewed'] = answerviewed

    # update problemstate log
    course = context['cs_course']
    uname = context[_n('uname')]
    logname = context[_n('logname_state')]
    context['csm_cslog'].overwrite_log(course, uname, logname, newstate)

    # log submission in problemactions
    duetime = context['csm_time'].detailed_timestamp(due)
    log_action(context, {'action': 'viewanswer',
                         'names': names,
                         'score': newstate.get('score', 0.0),
                         'response': outdict,
                         'due_date': duetime})

    return make_return_json(context, outdict)


def handle_lock(context):
    names = context[_n('question_names')]
    timing = context[_n('timing')]
    due = context[_n('due')]
    lastlog = context[_n('last_log')]
    locked = context[_n('locked')]

    newstate = dict(lastlog)
    newstate['timestamp'] = context['cs_timestamp']
    if 'last_submit' not in newstate:
        newstate['last_submit'] = {}

    outdict = {}  # dictionary containing the responses for each question
    for name in names:
        q, args = context[_n('name_map')][name]
        outdict[name] = {}
        locked.add(name)

        # automatically view the answer if the option is set
        if 'lock' in _get_auto_view(args) and q.get('allow_viewanswer', True) and _get(args, 'csq_allow_viewanswer', True, bool):
            c = dict(context)
            c[_n('question_names')] = [name]
            o = json.loads(handle_viewanswer(c)[2])
            ll = context['csm_cslog'].most_recent(
                context['cs_course'], context.get('cs_username', 'None'),
                context[_n('logname_state')], {})
            newstate['answer_viewed'] = ll.get('answer_viewed', set())
            newstate['explanation_viewed'] = ll.get('explanation_viewed',
                                                    set())
            outdict[name].update(o[name])

    newstate['locked'] = locked

    # update problemstate log
    course = context['cs_course']
    uname = context[_n('uname')]
    logname = context[_n('logname_state')]
    context['csm_cslog'].overwrite_log(course, uname, logname, newstate)

    # log submission in problemactions
    duetime = context['csm_time'].detailed_timestamp(due)
    log_action(context, {'action': 'lock',
                         'names': names,
                         'score': newstate.get('score', 0.0),
                         'response': outdict,
                         'due_date': duetime})

    return make_return_json(context, outdict)


def handle_grade(context):
    names = context[_n('question_names')]
    perms = context[_n('perms')]

    newentries = []
    outdict = {}
    for name in names:
        if name.endswith('_grading_score') or name.endswith(
                '_grading_comments'):
            continue
        error = grade_msg(context, perms, name)
        if error is not None:
            outdict[name] = {'error_msg': error}
            continue
        q, args = context[_n('name_map')][name]
        npoints = float(q['total_points'](**args))
        try:
            f = context[_n('form')]
            rawscore = f.get('%s_grading_score' % name, '')
            comments = f.get('%s_grading_comments' % name, '')
            score = float(rawscore)
        except:
            outdict[name] = {'error_msg': 'Invalid score: %s' % rawscore}
            continue
        newentries.append({'qname': name,
                           'grader': context[_n('real_uname')],
                           'score': score / npoints,
                           'comments': comments,
                           'timestamp': context['cs_timestamp']})
        outdict[name] = {
            'score_display': make_score_display(context, name, None),
            'message': "<b>Grader's Comments:</b><br/><br/>%s" % comments,
            'score': score,
        }

    # update problemstate log
    course = context['cs_course']
    uname = context[_n('uname')]
    logname = context[_n('logname_grades')]
    for i in newentries:
        context['csm_cslog'].update_log(course, uname, logname, i)

    # log submission in problemactions
    log_action(context, {'action': 'grade',
                         'names': names,
                         'scores': newentries,
                         'grader': context[_n('real_uname')]})

    return make_return_json(context, outdict, names=list(outdict.keys()))


def handle_unlock(context):
    names = context[_n('question_names')]
    timing = context[_n('timing')]
    due = context[_n('due')]
    lastlog = context[_n('last_log')]
    locked = context[_n('locked')]

    newstate = dict(lastlog)
    newstate['timestamp'] = context['cs_timestamp']
    if 'last_submit' not in newstate:
        newstate['last_submit'] = {}

    outdict = {}  # dictionary containing the responses for each question
    for name in names:
        q, args = context[_n('name_map')][name]
        outdict[name] = {}
        locked.remove(name)

    newstate['locked'] = locked

    # update problemstate log
    course = context['cs_course']
    uname = context[_n('uname')]
    logname = context[_n('logname_state')]
    context['csm_cslog'].overwrite_log(course, uname, logname, newstate)

    # log submission in problemactions
    duetime = context['csm_time'].detailed_timestamp(due)
    log_action(context, {'action': 'unlock',
                         'names': names,
                         'score': newstate.get('score', 0.0),
                         'response': outdict,
                         'due_date': duetime})

    return make_return_json(context, outdict)


def handle_save(context):
    names = context[_n('question_names')]
    timing = context[_n('timing')]
    due = context[_n('due')]

    lastlog = context[_n('last_log')]

    newstate = dict(lastlog)
    newstate['timestamp'] = context['cs_timestamp']
    if 'last_submit' not in newstate:
        newstate['last_submit'] = {}

    outdict = {}  # dictionary containing the responses for each question
    saved_names = []
    for name in names:
        out = {}
        question, args = context[_n('name_map')].get(name)
        sub = context[_n('form')].get(name, '')

        if sub == "":  # don't overwrite things with blank strings
            outdict[name] = {}
            continue

        saved_names.append(name)

        # if we are here, no errors occurred.  go ahead with checking.
        newstate['last_submit'][name] = sub

        rerender = question.get('always_rerender', False)
        if rerender is True:
            out['rerender'] = question['render_html'](newstate['last_submit'],
                                                      **args)
        elif rerender:
            out['rerender'] = rerender

        out['score_display'] = ''
        out['response'] = ''
        outdict[name] = out

        # cache responses
        newstate['%s_score_display' % name] = out['score_display']
        newstate['%s_message' % name] = out['message']

    # update problemstate log
    if len(saved_names) > 0:
        course = context['cs_course']
        uname = context[_n('uname')]
        logname = context[_n('logname_state')]
        context['csm_cslog'].overwrite_log(course, uname, logname, newstate)

        # log submission in problemactions
        duetime = context['csm_time'].detailed_timestamp(due)
        subbed = {n: context[_n('form')].get(n, '') for n in saved_names}
        log_action(context, {'action': 'save',
                             'names': saved_names,
                             'submitted': subbed,
                             'score': newstate.get('score', 0.0),
                             'response': outdict,
                             'due_date': duetime})

    return make_return_json(context, outdict)


def handle_check(context):
    names = context[_n('question_names')]
    timing = context[_n('timing')]
    due = context[_n('due')]

    lastlog = context[_n('last_log')]
    namemap = context[_n('name_map')]

    newstate = dict(lastlog)
    newstate['timestamp'] = context['cs_timestamp']
    if 'last_submit' not in newstate:
        newstate['last_submit'] = {}

    outdict = {}  # dictionary containing the responses for each question
    for name in names:
        out = {}
        sub = context[_n('form')].get(name, '')

        # if we are here, no errors occurred.  go ahead with checking.
        newstate['last_submit'][name] = sub
        question, args = namemap[name]

        try:
            response = question['handle_check'](context[_n('form')], **args)
        except:
            response = exc_message(context)

        out['score_display'] = ''
        out['message'] = context['csm_language'].handle_custom_tags(context,
                                                                    response)

        rerender = question.get('always_rerender', False)
        if rerender is True:
            out['rerender'] = question['render_html'](newstate['last_submit'],
                                                      **args)
        elif rerender:
            out['rerender'] = rerender

        outdict[name] = out

        # cache responses
        newstate['%s_score_display' % name] = out['score_display']
        newstate['%s_message' % name] = out['message']

    # update problemstate log
    course = context['cs_course']
    uname = context[_n('uname')]
    logname = context[_n('logname_state')]
    context['csm_cslog'].overwrite_log(course, uname, logname, newstate)

    # log submission in problemactions
    duetime = context['csm_time'].detailed_timestamp(due)
    subbed = {n: context[_n('form')].get(n, '') for n in names}
    log_action(context, {'action': 'check',
                         'names': names,
                         'submitted': subbed,
                         'score': newstate.get('score', 0.0),
                         'response': outdict,
                         'due_date': duetime})

    return make_return_json(context, outdict)


def handle_submit(context):
    names = context[_n('question_names')]
    due = context[_n('due')]

    lastlog = context[_n('last_log')]
    nsubmits_used = context[_n('nsubmits_used')]
    answer_viewed = context[_n('answer_viewed')]
    scores = lastlog.get('scores', {})

    namemap = context[_n('name_map')]
    timing = context[_n('timing')]

    newstate = dict(lastlog)

    newstate['last_submit_time'] = context['cs_timestamp']
    newstate['last_submit_times'] = newstate.get('last_submit_times', {})
    newstate['timestamp'] = context['cs_timestamp']
    if 'last_submit' not in newstate:
        newstate['last_submit'] = {}

    names_done = set()
    outdict = {}  # dictionary containing the responses for each question
    for name in names:
        if name.startswith('__'):
            name = name[2:].rsplit('_', 1)[0]
        if name in names_done:
            continue


        names_done.add(name)
        newstate['last_submit_times'][name] = context['cs_timestamp']
        out = {}
        sub = context[_n('form')].get(name, '')

        error = submit_msg(context, context[_n('perms')], name)
        if error is not None:
            out['error_msg'] = error
            outdict[name] = out
            continue

        # if we are here, no errors occurred.  go ahead with checking.
        nsubmits_used[name] = nsubmits_used.get(name, 0) + 1
        newstate['last_submit'][name] = sub

        question, args = namemap[name]

        grading_mode = _get(args, 'csq_grading_mode', 'auto', str)
        if grading_mode == 'auto':
            try:
                resp = question['handle_submission'](context[_n('form')], **
                                                     args)
                scores[name] = resp['score']
                msg = resp['msg']
            except:
                resp = {}
                scores[name] = 0.0
                msg = exc_message(context)
        elif grading_mode == 'manual':
            resp = {}
            msg = 'Submission received for manual grading.'
            scores[name] = None
        else:
            resp = {}
            scores[name] = 0.0
            msg = '<font color="red">Unknown grading mode: %s.  Please contact staff.</font>' % grading_mode

        out['score_display'] = make_score_display(
            context, name, scores[name],
            assume_submit=True)
        out['message'] = context['csm_language'].handle_custom_tags(context,
                                                                    msg)
        out['score'] = scores[name]

        rerender = resp.get('rerender', False) or question.get(
            'always_rerender', False)
        if rerender is True:
            out['rerender'] = question['render_html'](newstate['last_submit'],
                                                      **args)
        elif rerender:
            out['rerender'] = rerender

        outdict[name] = out

        if resp.get('lock', False):
            c = dict(context)
            c[_n('question_names')] = [name]
            o = json.loads(handle_lock(c)[2])
            ll = context['csm_cslog'].most_recent(
                context['cs_course'], context.get('cs_username', 'None'),
                context[_n('logname_state')], {})
            newstate['locked'] = ll.get('locked', set())
            outdict[name].update(o[name])

        # auto view answer if the option is set
        if 'submit_all' not in context[_n('orig_perms')]:
            x = nsubmits_left(context, name)
            if (question.get('allow_viewanswer', True) and (((out['score'] == 1 and 'perfect' in _get_auto_view(args)) or
                 (x[0] == 0 and 'nosubmits' in _get_auto_view(args))) and
                    _get(args, 'csq_allow_viewanswer', True, bool))):
                # this is a hack...
                c = dict(context)
                c[_n('question_names')] = [name]
                o = json.loads(handle_viewanswer(c)[2])
                ll = context['csm_cslog'].most_recent(
                    context['cs_course'], context.get('cs_username', 'None'),
                    context[_n('logname_state')], {})
                newstate['answer_viewed'] = ll.get('answer_viewed', set())
                newstate['explanation_viewed'] = ll.get('explanation_viewed',
                                                        set())
                outdict[name].update(o[name])

        # cache responses
        newstate['%s_score_display' % name] = out['score_display']
        newstate['%s_message' % name] = out['message']

    # update score
    if any(scores[i] is None for i in scores):
        newstate['score'] = None
    else:
        num = 0.0
        denom = 0.0
        for n in namemap:
            q, args = namemap[n]
            d = q['total_points'](**args)

            denom += d
            num += scores.get(n, 0.0) * d
            newstate['score'] = 0.0 if num == denom == 0.0 else num / denom
    context[_n('nsubmits_used')] = newstate['nsubmits_used'] = nsubmits_used
    newstate['scores'] = scores

    # update problemstate log
    course = context['cs_course']
    uname = context[_n('uname')]
    logname = context[_n('logname_state')]
    context['csm_cslog'].overwrite_log(course, uname, logname, newstate)

    # log submission in problemactions
    duetime = context['csm_time'].detailed_timestamp(due)
    subbed = {n: context[_n('form')].get(n, '') for n in names}
    log_action(context, {'action': 'submit',
                         'names': names,
                         'submitted': subbed,
                         'score': newstate['score'],
                         'response': outdict,
                         'due_date': duetime})

    return make_return_json(context, outdict)


def manage_groups(context):
    # displays the screen to admins who are adjusting groups
    perms = context['cs_permissions']
    #if 'groups' not in perms and 'admin' not in perms:
    #    return 'You are not allowed to view this page.'
    form = context['cs_form']
    # show the main partnering page
    section = context['cs_user_info'].get('section', None)
    default_section = context.get('cs_default_section', 1)
    all_sections = context.get('cs_sections', [])
    if len(all_sections) == 0:
        all_sections = {default_section: 'Default Section'} 
    if section is None:
        section = default_section  
    hdr = ('Group Assignments for %s, Section '
           '<span id="cs_groups_section">%s</span>')
    hdr %= (context['cs_original_path'], section)
    context['cs_content_header'] = hdr

    # menu for choosing section to display 
    out = 'Show Current Groups for Section: <select name="section" id="section">'
    for i in sorted(all_sections):
        s = ' selected' if i == section else ''
        out += '<option value="%s"%s>%s</a>' % (i, s, i)
    out += '</select>&nbsp;<a class="btn btn-catsoop" id="cs_groups_show">Go</a>'
    
    # empty table that will eventually be populated with groups
    out += ('<p><h4>Groups:</h4>'
            '<table id="cs_groups_table" border="1" align="center">'
            '<tr><td>Loading...</td></tr>'
            '</table>')

    # create partnership from two students
    out += ('<p><h4>Make New Partnership:</h4>'
            'Student 1: <select name="cs_groups_name1" id="cs_groups_name1">'
            '</select>&nbsp;'
            'Student 2: <select name="cs_groups_name2" id="cs_groups_name2">'
            '</select>&nbsp;'
            '<a class="btn btn-catsoop" id="cs_groups_newpartners">Partner Students</a>'
            '</p>')

    # add a student to a group
    out += ('<p><h4>Add Student to Group:</h4>'
            'Student: <select name="cs_groups_nameadd" id="cs_groups_nameadd">'
            '</select>&nbsp;'
            'Group: <select name="cs_groups_groupadd" id="cs_groups_groupadd">'
            '</select>&nbsp;'
            '<a class="btn btn-catsoop" id="cs_groups_addtogroup">Add to Group</a></p>')


    # randomly assign all partners.  this needs to be sufficiently scary...
    out += ('<p><h4>Randomly assign groups</h4>'
            'Number per group:&nbsp;'
            '<select name="cs_groups_numberpergroup" '
            'id="cs_groups_numberpergroup">')
    for i in range(10):
        s = ' selected' if i == 2 else ''
        out += '<option value="%s"%s>%s</option>' % (i, s, i)
    out += '</select>'
    out += '<br/>'
    return out + default_javascript(context)


def update_groups(context):
    # actually handles the updating of a groupship
    perms = context['cs_permissions']
    if 'groups' not in perms and 'admin' not in perms:
        return 'You are not allowed to view this page.'


def clearanswer_msg(context, perms, name):
    namemap = context[_n('name_map')]
    timing = context[_n('timing')]
    ansviewed = context[_n('answer_viewed')]
    i = context[_n('impersonating')]
    _, qargs = namemap[name]
    error = None
    if ('submit' not in perms and 'submit_all' not in perms):
        error = ('You are not allowed undo your viewing of '
                 'the answer to this question.')
    elif name not in ansviewed:
        error = "You have not viewed the answer for this question."
    elif name not in namemap:
        error = ('No question with name %s.  '
                 'Please refresh before submitting.') % name
    elif 'submit_all' not in perms:
        if timing == -1 and not i:
            error = 'This question is not yet available.'
        if not qargs.get('csq_allow_submit_after_answer_viewed', False):
            error = ('You are not allowed to undo your viewing of '
                     'the answer to this question.')
    return error


def viewexp_msg(context, perms, name):
    namemap = context[_n('name_map')]
    timing = context[_n('timing')]
    ansviewed = context[_n('answer_viewed')]
    expviewed = context[_n('explanation_viewed')]
    _, qargs = namemap[name]
    error = None
    if ('submit' not in perms and 'submit_all' not in perms):
        error = 'You are not allowed to view the answer to this question.'
    elif name not in ansviewed:
        error = 'You have not yet viewed the answer for this question.'
    elif name in expviewed:
        error = 'You have already viewed the explanation for this question.'
    elif name not in namemap:
        error = ('No question with name %s.  '
                 'Please refresh before submitting.') % name
    elif ('submit_all' not in perms) and timing == -1:
        error = 'This question is not yet available.'
    elif not _get(qargs, 'csq_allow_viewexplanation', True, bool):
        error = 'Viewing explanations is not allowed for this question.'
    else:
        q, args = namemap[name]
        if 'csq_explanation' not in args:
            error = 'No explanation supplied for this question.'
    return error


def viewanswer_msg(context, perms, name):
    namemap = context[_n('name_map')]
    timing = context[_n('timing')]
    ansviewed = context[_n('answer_viewed')]
    i = context[_n('impersonating')]
    _, qargs = namemap[name]
    error = None

    if not _.get('allow_viewanswer', True):
        error = 'You cannot view the answer to this type of question.'
    elif ('submit' not in perms and 'submit_all' not in perms):
        error = 'You are not allowed to view the answer to this question.'
    elif name in ansviewed:
        error = 'You have already viewed the answer for this question.'
    elif name not in namemap:
        error = ('No question with name %s.  '
                 'Please refresh before submitting.') % name
    elif 'submit_all' not in perms:
        if timing == -1 and not i:
            error = 'This question is not yet available.'
        elif not _get(qargs, 'csq_allow_viewanswer', True, bool):
            error = 'Viewing the answer is not allowed for this question.'
    return error


def save_msg(context, perms, name):
    namemap = context[_n('name_map')]
    timing = context[_n('timing')]
    i = context[_n('impersonating')]
    _, qargs = namemap[name]
    error = None
    if not _.get('allow_save', True):
        error = 'You cannot save this type of question.'
    elif 'submit' not in perms and 'submit_all' not in perms:
        error = 'You are not allowed to check answers to this question.'
    elif name not in namemap:
        error = ('No question with name %s.  '
                 'Please refresh before submitting.') % name
    elif 'submit_all' not in perms:
        if timing == -1 and not i:
            error = 'This question is not yet available.'
        elif name in context[_n('locked')]:
            error = 'You are not allowed to save for this question.'
        elif (not _get(qargs, 'csq_allow_submit_after_answer_viewed', False,
                       bool) and name in context[_n('answer_viewed')]):
            error = 'You are not allowed to save to this question after viewing the answer.'
        elif timing == 1 and _get(context, 'cs_auto_lock', False, bool):
            error = ('You are not allowed to save after the '
                     'deadline for this question.')
        elif not _get(qargs, 'csq_allow_save', True, bool):
            error = 'Saving is not allowed for this question.'
    return error


def check_msg(context, perms, name):
    namemap = context[_n('name_map')]
    timing = context[_n('timing')]
    i = context[_n('impersonating')]
    _, qargs = namemap[name]
    error = None
    if 'submit' not in perms and 'submit_all' not in perms:
        error = 'You are not allowed to check answers to this question.'
    elif name not in namemap:
        error = ('No question with name %s.  '
                 'Please refresh before submitting.') % name
    elif namemap[name][0].get('handle_check', None) is None:
        error = 'This question type does not support checking.'
    elif 'submit_all' not in perms:
        if timing == -1 and not i:
            error = 'This question is not yet available.'
        elif name in context[_n('locked')]:
            error = 'You are not allowed to check answers to this question.'
        elif (not _get(qargs, 'csq_allow_submit_after_answer_viewed', False,
                       bool) and name in context[_n('answer_viewed')]):
            error = 'You are not allowed to check answers to this question after viewing the answer.'
        elif timing == 1 and _get(context, 'cs_auto_lock', False, bool):
            error = ('You are not allowed to check after the '
                     'deadline for this problem.')
        elif not _get(qargs, 'csq_allow_check', True, bool):
            error = 'Checking is not allowed for this question.'
    return error


def grade_msg(context, perms, name):
    namemap = context[_n('name_map')]
    _, qargs = namemap[name]
    if 'grade' not in perms:
        return 'You are not allowed to grade exercises.'


def submit_msg(context, perms, name):
    if name.startswith('__'):
        name = name[2:].rsplit('_', 1)[0]
    namemap = context[_n('name_map')]
    timing = context[_n('timing')]
    i = context[_n('impersonating')]
    _, qargs = namemap[name]
    error = None
    if not _.get('allow_submit', True):
        error = 'You cannot submit this type of question.'
    if (not _.get('allow_self_submit', True)) and 'real_user' not in context['cs_user_info']:
        error = 'You cannot submit this type of question yourself.'
    elif 'submit' not in perms and 'submit_all' not in perms:
        error = 'You are not allowed to submit answers to this question.'
    elif name not in namemap:
        error = ('No question with name %s.  '
                 'Please refresh before submitting.') % name
    elif 'submit_all' not in perms:
        # don't allow if...
        if timing == -1 and not i:
            # ...the problem has not yet been released
            error = 'This question is not yet open for submissions.'
        elif _get(context, 'cs_auto_lock', False, bool) and timing == 1:
            # ...the problem auto locks and it is after the due date
            error = ('Submissions are not allowed after the '
                     'deadline for this question')
        elif name in context[_n('locked')]:
            error = 'You are not allowed to submit to this question.'
        elif (not _get(qargs, 'csq_allow_submit_after_answer_viewed', False,
                       bool) and name in context[_n('answer_viewed')]):
            # ...the answer has been viewed and submissions after
            #    viewing the answer are not allowed
            error = ('You are not allowed to submit to this question '
                     'because you have already viewed the answer.')
        elif not _get(qargs, 'csq_allow_submit', True, bool):
            # ...submissions are not allowed
            error = 'Submissions are not allowed for this question.'
        elif (not _get(qargs, 'csq_grading_mode', 'auto', str) == 'manual' and
              get_manual_grading_entry(context, name) is not None):
            # ...prior submission has been graded
            error = 'You are not allowed to submit after a previous submission has been graded.'
        else:
            # ...the user does not have enough checks left
            nleft, _ = nsubmits_left(context, name)
            if nleft <= 0:
                error = ('You have used all of your allowed '
                         'submissions for this question.')
    return error


def log_action(context, log_entry):
    course = context['cs_course']
    uname = context[_n('uname')]
    logname = context[_n('logname_actions')]
    entry = {'action': context[_n('action')],
             'timestamp': context['cs_timestamp'],
             'ip': context['cs_ip'],
             'user_info': context['cs_user_info'],
             'form': context['cs_form']}
    entry.update(log_entry)
    context['cs_debug'](uname, entry)
    context['csm_cslog'].update_log(course, uname, logname, entry)


def make_return_json(context, ret, names=None):
    names = context[_n('question_names')] if names is None else names
    names = set(i[2:].rsplit('_', 1)[0] if i.startswith('__') else i
                for i in names)
    for name in names:
        ret[name]['nsubmits_left'] = nsubmits_left(context, name)[1],
        ret[name]['buttons'] = make_buttons(context, name)
    content = json.dumps(ret, separators=(',', ':'))
    length = str(len(content))
    retcode = ('200', 'OK')
    headers = {'Content-type': 'application/json', 'Content-length': length}
    return retcode, headers, content


def render_question(elt, context, lastsubmit):
    q, args = elt
    name = args['csq_name']
    lastlog = context[_n('last_log')]
    answer_viewed = context[_n('answer_viewed')]
    out = '\n<!--START question %s -->' % (name)
    if q.get('indiv', True) and args.get('csq_indiv', True):
        out += '\n<div class="question question-%s" id="cs_qdiv_%s" style="position: static">' % (q['qtype'], name)

    out += '\n<div id="%s_rendered_question">\n' % name
    out += context['csm_language'].source_transform_string(context, args.get(
        'csq_prompt', ''))
    out += q['render_html'](lastsubmit, **args)
    out += '\n</div>'

    out += '<div>'
    out += (('\n<span id="%s_buttons">' % name) + make_buttons(context, name) +
            "</span>")
    out += ('\n<div id="%s_loading" class="loader" style="display:none;">'
            '</div>') % name
    out += (('\n<span id="%s_score_display">' % args['csq_name']) +
            make_score_display(context, name, lastlog.get('scores', {}).get(
                name, None)) + '</span>')
    out += (('\n<div id="%s_nsubmits_left" class="nsubmits_left">' % name) +
            nsubmits_left(context, name)[1] + "</div>")
    out += '</div>'

    if name in answer_viewed:
        answerclass = ' class="solution"'
        showanswer = True
    elif context[_n('impersonating')]:
        answerclass = ' class="impsolution"'
        showanswer = True
    else:
        answerclass = ''
        showanswer = False
    out += '\n<div id="%s_solution_container"%s>' % (args['csq_name'],
                                                     answerclass)
    out += '\n<div id="%s_solution">' % (args['csq_name'])
    if showanswer:
        ans = q['answer_display'](**args)
        out += '\n'
        out += context['csm_language'].source_transform_string(context, ans)
    out += '\n</div>'
    out += '\n<div id="%s_solution_explanation">' % name
    if (name in context[_n('explanation_viewed')] and
            args.get('csq_explanation', '') != ''):
        exp = explanation_display(args['csq_explanation'])
        out += context['csm_language'].source_transform_string(context, exp)
    out += '\n</div>'
    out += '\n</div>'

    out += '\n<div id="%s_message">' % args['csq_name']

    gmode = _get(args, 'csq_grading_mode', 'auto', str)
    ll = context[_n('last_log')].get('%s_message' % name, '')
    if gmode == 'manual':
        q, args = context[_n('name_map')][name]
        lastlog = get_manual_grading_entry(context, name) or {}
        lastscore = lastlog.get('score', '')
        lastcomments = lastlog.get('comments', '')
        tpoints = q['total_points'](**args)
        comments = (get_manual_grading_entry(context, name) or
                    {}).get('comments')
        try:
            score_output = lastscore * tpoints
        except:
            score_output = ""

        if comments is not None:
            ll = '<b>Score:</b> %s (out of %s)<br><br><b>Grader\'s Comments:</b><br/>%s' % (
                score_output, tpoints, comments)
    out += ll + "</div>"
    if q.get('indiv', True) and args.get('csq_indiv', True):
        out += '\n</div>'
    out += '\n<!--END question %s -->\n' % args['csq_name']
    return out


def nsubmits_left(context, name):
    nused = context[_n('nsubmits_used')].get(name, 0)
    q, args = context[_n('name_map')][name]

    if not q.get('allow_submit', True) or not q.get('allow_self_submit', True):
        return 0, ''

    info = q.get('defaults', {})
    info.update(args)

    # look up 'nsubmits' in the question's arguments
    # (fall back on default in qtype)
    nsubmits = info.get('csq_nsubmits', None)
    if nsubmits is None:
        nsubmits = context.get('cs_nsubmits_default', float('inf'))

    perms = context[_n('orig_perms')]
    if 'submit' not in perms and 'submit_all' not in perms:
        return 0, ''
    nleft = max(0, nsubmits - nused)
    for (regex, nchecks) in context['cs_user_info'].get('nsubmits_extra', []):
        if re.match(regex, '.'.join(context['cs_path_info'][1:] + [name])):
            nleft += nchecks
    if nleft < float('inf'):
        msg = "<i>You have %d submission%s remaining.</i>" % (nleft, 's'
                                                              if nleft != 1
                                                              else '')
    else:
        msg = "<i>You have infinitely-many submissions remaining.</i>"

    if 'submit_all' in perms:
        msg = (
            "As staff, you are always allowed to submit.  "
            "If you were a student, you would see the following:<br/>%s") % msg

    return max(0, nleft), msg


def button_text(x, msg):
    if x is None:
        return msg
    else:
        return None


_button_map = {
    'submit': (submit_msg, 'Submit'),
    'save': (save_msg, 'Save'),
    'viewanswer': (viewanswer_msg, 'View Answer'),
    'clearanswer': (clearanswer_msg, 'Clear Answer'),
    'viewexplanation': (viewexp_msg, 'View Explanation'),
    'check': (check_msg, True),
}


def make_buttons(context, name):
    uname = context[_n('uname')]
    rp = context[_n('perms')]  # the real user's perms
    p = context[_n('orig_perms')]  # the impersonated user's perms, if any
    i = context[_n('impersonating')]
    q, args = context[_n('name_map')][name]
    nsubmits, _ = nsubmits_left(context, name)

    buttons = {'copy_seed': None, 'copy': None, 'new_seed': None}
    buttons['new_seed'] = ("New Random Seed" if 'submit_all' in p and
                           context.get('cs_random_inited', False) else None)
    abuttons = {
        'copy_seed': ('Copy Random Seed'
                      if context.get('cs_random_inited', False) else None),
        'copy': 'Copy to My Account',
        'lock': None,
        'unlock': None
    }
    for (b, (func, text)) in list(_button_map.items()):
        buttons[b] = button_text(func(context, p, name), text)
        abuttons[b] = button_text(func(context, rp, name), text)

    for d in (buttons, abuttons):
        if d['check']:
            d['check'] = q.get('checktext', 'Check')

    if name in context[_n('locked')]:
        abuttons['unlock'] = 'Unlock'
    else:
        abuttons['lock'] = 'Lock'

    aout = ''
    if i:
        for k in {'submit', 'check', 'save'}:
            if buttons[k] is not None:
                abuttons[k] = None
            elif abuttons[k] is not None:
                abuttons[k] += ' (as %s)' % uname
        for k in ('viewanswer', 'clearanswer', 'viewexplanation'):
            if buttons[k] is not None:
                abuttons[k] = None
            elif abuttons[k] is not None:
                abuttons[k] += ' (for %s)' % uname
        aout = '<div><b><font color="red">Admin Buttons:</font></b><br/>'
        for k in ('copy', 'copy_seed', 'check', 'save', 'submit', 'viewanswer',
                  'viewexplanation', 'clearanswer', 'lock', 'unlock'):
            x = {'b': abuttons[k], 'k': k, 'n': name}
            if abuttons[k] is not None:
                aout += (
                    '\n<button id="%(n)s_%(k)s" '
                    'class="%(k)s" '
                    'style="background-color: #FFD9D9; border-color: red;" '
                    'onclick="catsoop.%(k)s(\'%(n)s\');">'
                    '%(b)s</button>') % x
        # in manual grading mode, add a box and button for grading
        gmode = _get(args, 'csq_grading_mode', 'auto', str)
        if gmode == 'manual':
            lastlog = get_manual_grading_entry(context, name) or {}
            lastscore = lastlog.get('score', '')
            lastcomments = lastlog.get('comments', '')
            tpoints = q['total_points'](**args)
            try:
                output = lastscore * tpoints
            except:
                output = ""
            aout += ('<br/><b><font color="red">Grading:</font></b>'
                     '<table border="0" width="100%%">'
                     '<tr><td align="right" width="30%%">'
                     '<font color="red">Points Earned (out of %2.2f):</font>'
                     '</td><td><input type="text" value="%s" size="5" '
                     'style="border-color: red;" '
                     'id="%s_grading_score" '
                     'name="%s_grading_score" /></td></tr>'
                     '<tr><td align="right">'
                     '<font color="red">Comments:</font></td>'
                     '<td><textarea rows="5" id="%s_grading_comments" '
                     'name="%s_grading_comments" '
                     'style="width: 100%%; border-color: red;">'
                     '%s'
                     '</textarea></td></tr><tr><td></td><td>'
                     '<button class="grade" '
                     'style="background-color: #FFD9D9; '
                     'border-color: red;" '
                     'onclick="catsoop.grade(\'%s\');">'
                     'Submit Grade'
                     '</button></td></tr></table>') % (tpoints, output, name,
                                                       name, name, name,
                                                       lastcomments, name)
        aout += '</div>'

    out = ''
    for k in ('check', 'save', 'submit', 'viewanswer', 'viewexplanation',
              'clearanswer', 'new_seed'):
        x = {'b': buttons[k], 'k': k, 'n': name}
        if buttons[k] is not None:
            out += ('\n<button id="%(n)s_%(k)s" '
                    'class="%(k)s" '
                    'onclick="catsoop.%(k)s(\'%(n)s\');">'
                    '%(b)s</button>') % x
    return out + aout


def pre_handle(context):
    # enumerate the questions in this problem
    context[_n('name_map')] = collections.OrderedDict()
    qcount = 0
    for elt in context['cs_problem_spec']:
        if isinstance(elt, tuple):
            m = elt[1]
            if 'csq_name' not in m:
                m['csq_name'] = 'q%06d' % qcount
                qcount += 1
            context[_n('name_map')][m['csq_name']] = elt

    # who is the user (and, who is being impersonated?)
    user_info = context.get('cs_user_info', {})
    uname = user_info.get('username', 'None')
    real = user_info.get('real_user', user_info)
    context[_n('role')] = real.get('role', 'None')
    context[_n('section')] = real.get('section', None)
    context[_n('perms')] = real.get('permissions', [])
    context[_n('orig_perms')] = user_info.get('permissions', [])
    context[_n('uname')] = uname
    context[_n('real_uname')] = real.get('username', uname)
    context[_n('impersonating')] = (
        context[_n('uname')] != context[_n('real_uname')])

    # store release and due dates
    r = context[_n('rel')] = context['csm_tutor'].get_release_date(context)
    d = context[_n('due')] = context['csm_tutor'].get_due_date(context)
    n = context['csm_time'].from_detailed_timestamp(context['cs_timestamp'])
    context[_n('now')] = n
    context[_n('timing')] = -1 if n <= r else 0 if n <= d else 1

    if _get(context, 'cs_require_activation', False, bool):
        pwd = _get(context, 'cs_activation_password', 'password', str)
        context[_n('activation_password')] = pwd

    # determine the right log name to look up, and grab the most recent entry
    loghead = '.'.join(context['cs_path_info'][1:])
    ps_name = '%s.problemstate' % loghead
    pa_name = '%s.problemactions' % loghead
    pg_name = '%s.problemgrades' % loghead
    grp_name = '%s.group' % loghead
    ll = context['csm_cslog'].most_recent(context['cs_course'],
                                          uname,
                                          ps_name,
                                          {})
    context[_n('group')] = context['csm_cslog'].most_recent(context['cs_course'],
                                                            uname,
                                                            grp_name,
                                                            None)
    context[_n('all_groups')] = context['csm_cslog'].most_recent(context['cs_course'],
                                                                 uname,
                                                                 '%ss' % grp_name,
                                                                 {})
    context[_n('last_log')] = ll
    context[_n('logname_state')] = ps_name
    context[_n('logname_actions')] = pa_name
    context[_n('logname_grades')] = pg_name
    context[_n('logname_group')] = grp_name
    context[_n('logname_groups')] = '%ss' % grp_name
    context[_n('locked')] = ll.get('locked', set())
    context[_n('answer_viewed')] = ll.get('answer_viewed', set())
    context[_n('explanation_viewed')] = ll.get('explanation_viewed', set())
    context[_n('nsubmits_used')] = ll.get('nsubmits_used', {})

    # what is the user trying to do?
    context[_n('action')] = context['cs_form'].get('action', 'view').lower()
    if context[_n('action')] in ('view', 'activate',
                                 'passthrough', 'list_questions',
                                 'get_state', 'manage_groups'):
        context[_n('form')] = context['cs_form']
    else:
        names = context['cs_form'].get('names', "[]")
        context[_n('question_names')] = json.loads(names)
        context[_n('form')] = json.loads(context['cs_form']['data'])


def _get_auto_view(context):
    # when should we automatically view the answer?
    ava = context.get('csq_auto_viewanswer', False)
    if ava is True:
        ava = set(['nosubmits', 'perfect', 'lock'])
    elif isinstance(ava, str):
        ava = set([ava])
    elif not ava:
        ava = set()
    return ava


def default_javascript(context):
    namemap = context[_n('name_map')]
    if 'submit_all' in context[_n('perms')]:
        skip_alert = list(namemap.keys())
    else:
        skipper = 'csq_allow_submit_after_answer_viewed'
        skip_alert = [name for (name, (q, args)) in list(namemap.items())
                      if _get(args, skipper, False, bool)]
    out = '''
<script type="text/javascript" src="__HANDLER__/default/cs_ajax.js"></script>
<script type="text/javascript">
catsoop.all_questions = %(allqs)r;
catsoop.api_token = %(secret)s;
catsoop.this_path = %(path)r;
catsoop.course = %(course)s;
'''

    if len(namemap) > 0:
        out += '''catsoop.imp = %(imp)r;
catsoop.skip_alert = %(skipalert)s;
catsoop.viewans_confirm = "Are you sure?  Viewing the answer will prevent any further submissions to this question.  Press 'OK' to view the answer, or press 'Cancel' if you have changed your mind.";
'''
    out += '</script>'

    api_tok = 'null'
    given_tok = context.get('cs_user_info', {}).get('api_token', None)
    if given_tok is not None:
        api_tok = repr(given_tok)

    return out % {
        'skipalert': json.dumps(skip_alert),
        'allqs': list(context[_n('name_map')].keys()),
        'user': context[_n('real_uname')],
        'path': '/'.join([context['cs_url_root']] + context['cs_path_info']),
        'imp': context[_n('uname')] if context[_n('impersonating')] else '',
        'secret': api_tok,
        'course': repr(context['cs_course']) if context['cs_course'] else 'null',
    }


def default_timer(context):
    out = ''
    if not _get(context, 'cs_auto_lock', False, bool):
        return out
    if len(context[_n('locked')]) >= len(context[_n('name_map')]):
        return out
    if context[_n('now')] > context[_n('due')]:
        # view answers immediately if viewed past the due date
        out += '\n<script type="text/javascript">'
        out += "\ncatsoop.ajaxrequest(cs_all_questions,'lock');"
        out += '\n</script>'
        return out
    else:
        out += '\n<script type="text/javascript">'
        out += ("\ncatsoop.timer_now = %d;"
                "\ncatsoop.timer_due = %d;"
                "\ncatsoop.time_url = %r;") % (
                    context['csm_time'].unix(context[_n('now')]),
                    context['csm_time'].unix(context[_n('due')]),
                    context['cs_url_root'] + '/cs_util/time')
        out += '\n</script>'
        out += ('<script type="text/javascript" '
                'src="__HANDLER__/default/cs_timer.js"></script>')
    return out


def exc_message(context):
    exc = traceback.format_exc().decode('utf-8', 'ignore')
    exc = exc.encode('ascii', 'ignore')
    exc = context['csm_errors'].clear_info(context, exc)
    return ('<p><font color="red">'
            '<b>CAT-SOOP ERROR:</b>'
            '<pre>%s</pre></font>') % exc
