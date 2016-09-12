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
from base64 import b64encode
import json


def _execfile(*args):
    fn = args[0]
    with open(fn) as f:
        c = compile(f.read(), fn, 'exec')
    exec(c, *args[1:])


def get_sandbox(context):
    base = os.path.join(context['cs_fs_root'], '__QTYPES__', 'pythoncode',
                        '__SANDBOXES__', 'base.py')
    _execfile(base, context)


def html_format(string):
    s = string.replace('&', '&amp;').replace('<', '&lt;').replace(
        '>', '&gt;').replace('\t', '    ').splitlines(False)
    jx = 0
    for ix, line in enumerate(s):
        for jx, char in enumerate(line):
            if char != ' ':
                break
        s[ix] = '&nbsp;' * jx + line[jx:]

    return '<br/>'.join(s)


defaults = {
    'csq_input_check': lambda x: None,
    'csq_code_pre': '',
    'csq_code_post': '',
    'csq_initial': 'pass  # Your code here',
    'csq_soln': 'print("Hello, World!")',
    'csq_tests': [],
    'csq_log_keypresses': True,
    'csq_variable_blacklist': [],
    'csq_import_blacklist': [],
    'csq_cpu_limit': 2,
    'csq_nproc_limit': 0,
    'csq_memory_limit': 32e6,
    'csq_interface': 'ace',
    'csq_rows': 14,
    'csq_font_size': 16,
}

test_defaults = {
    'npoints': 1,
    'code': "ans = 3",
    'variable': 'ans',
    'description': '',
    'include': False,
    'include_soln': False,
    'include_description': False,
    'grade': True,
    'show_description': True,
    'show_code': True,
    'check_function': lambda sub, soln: (sub == soln != '') * 1.0,
    'transform_output': lambda x: '<tt>%s</tt>' % (x, ),
}


def total_points(**info):
    bak = info['csq_tests']
    info['csq_tests'] = []
    for i in bak:
        info['csq_tests'].append(dict(test_defaults))
        info['csq_tests'][-1].update(i)
    return sum(i['npoints'] for i in info['csq_tests'])


checktext = 'Run Code'


def handle_check(submissions, **info):
    py3k = info.get('csq_python3', True)

    code = submissions[info['csq_name']]
    if info['csq_interface'] == 'upload':
        code = csm_tools.data_uri.DataURI(code[1]).data
    code = code.replace('\r\n', '\n')

    if py3k:
        _printer = "print('_catsoop_code_done_running')"
    else:
        _printer = "print '_catsoop_code_done_running'"

    code = '\n\n'.join([info['csq_code_pre'], code, _printer])

    get_sandbox(info)
    fname, out, err = info['sandbox_run_code'](
        info, code, info.get('csq_sandbox_options', {}))

    err = info['fix_error_msg'](fname, err,
                                info['csq_code_pre'].count('\n') + 2, code)

    complete = False
    if '_catsoop_code_done_running' in out:
        complete = True
        out = out.rsplit('_catsoop_code_done_running', 1)[0]

    trunc = False
    outlines = out.split('\n')
    if len(outlines) > 10:
        trunc = True
        outlines = outlines[:10]
    out = '\n'.join(outlines)
    if len(out) >= 5000:
        trunc = True
        out = out[:5000]
    if trunc:
        out += "\n\n...OUTPUT TRUNCATED..."

    timeout = False
    if (not complete) and ('SIGTERM' in err):
        timeout = True
        err = ("Your code did not run to completion, "
               "but no error message was returned."
               "\nThis normally means that your code contains an "
               "infinite loop or otherwise took too long to run.")

    msg = '<div class="response">'
    if not timeout:
        msg += '<p><b>'
        if complete:
            msg += ('<font color="darkgreen">'
                    'Your code ran to completion.'
                    '</font>')
        else:
            msg += ('<font color="red">'
                    'Your code did not run to completion.'
                    '</font>')
        msg += '</b></p>'
    if out != '':
        msg += "\n<p><b>Your code produced the following output:</b>"
        msg += "<br/><pre>%s</pre></p>" % html_format(out)
    if err != '':
        if not timeout:
            msg += "\n<p><b>Your code produced an error:</b>"
        msg += "\n<br/><font color='red'><tt>%s</tt></font></p>" % html_format(err)
    msg += '</div>'

    return msg


def handle_submission(submissions, **info):
    code = submissions[info['csq_name']]
    if info['csq_interface'] == 'upload':
        code = csm_tools.data_uri.DataURI(code[1]).data
    code = code.replace('\r\n', '\n')
    tests = [dict(test_defaults) for i in info['csq_tests']]
    for (i, j) in zip(tests, info['csq_tests']):
        i.update(j)
    show_tests = [i for i in tests if i['include']]
    if len(show_tests) > 0:
        code = code.rsplit('### Test Cases')[0]

    inp = info['csq_input_check'](code)
    if inp is not None:
        msg = ('<div class="response">'
               '<font color="red">%s</font>'
               '</div>') % inp
        return {'score': 0, 'msg': msg}

    bak = info['csq_tests']
    info['csq_tests'] = []
    for i in bak:
        new = dict(test_defaults)
        new.update(i)
        if new['grade']:
            info['csq_tests'].append(new)

    get_sandbox(info)

    score = 0
    msg = ('\n<br/><button onclick="$(\'#%s_result_showhide\').toggle()">'
           'Show/Hide Detailed Results</button>') % info['csq_name']
    msg += ('<div class="response" id="%s_result_showhide" '
            'style="display:none"><h2>Test Results:</h2>') % info['csq_name']
    count = 1
    for test in info['csq_tests']:
        out, err, log = info['sandbox_run_test'](info, code, test)
        if 'cached_result' in test:
            log_s = repr(test['cached_result'])
            err_s = 'Loaded cached result'
        else:
            out_s, err_s, log_s = info['sandbox_run_test'](
                info, info['csq_soln'], test)

        if count != 1:
            msg += "\n\n<p></p><hr/><p></p>\n\n"
        msg += "\n<center><h3>Test %02d</h3>" % count
        if test['show_description']:
            msg += "\n<i>%s</i>" % test['description']
        msg += "</center><p></p>"
        if test['show_code']:
            html_code = html_format(test['code'])
            msg += "\nThe test case was:<br/>\n<tt>%s</tt>" % html_code

        try:
            percentage = test['check_function'](log, log_s)
        except:
            percentage = 0.0
        imfile = None
        if percentage == 1.0:
            imfile = "check.png"
        elif percentage == 0.0:
            imfile = "cross.png"

        score += percentage * test['npoints']

        if imfile is None:
            image = ''
        else:
            image = "<img src='BASE/images/%s' />" % imfile

        if log_s != '' and test['show_code']:  # Our solution ran successfully
            msg += ("\n<p>Our solution produced the following "
                    "value for <tt>%s</tt>:") % test['variable']
            m = test['transform_output'](log_s)
            msg += "\n<br/><font color='blue'>%s</font></p>" % m
        elif log_s == '':
            msg += "\n<p><b>OOPS!</b> Our code produced an error:"
            e = html_format(err_s)
            msg += "\n<br/><font color='red'><tt>%s</tt></font></p>" % e

        if log != '' and test['show_code']:
            msg += ("\n<p>Your submission produced the following "
                    "value for <tt>%s</tt>:") % test['variable']
            m = test['transform_output'](log)
            msg += "\n<br/><font color='blue'>%s</font>%s</p>" % (m, image)
        elif log != '':
            msg += "\n<br/><center>%s</center></p>" % (image)

        if out != '' and test['show_code']:
            msg += "\n<p>Your code produced the following output:"
            msg += "<br/><pre>%s</pre></p>" % html_format(out)

        msg += '<p>'
        if err != '' and test['show_code']:
            msg += "\nYour submission produced an error:"
            e = html_format(err)
            msg += "\n<br/><font color='red'><tt>%s</tt></font></p>" % e
        elif err != '':
            msg += "\n<br/><center>%s</center></p>" % (image)

        count += 1

    msg += "\n</div>"
    tp = total_points(**info)
    overall = float(score) / tp if tp != 0 else 0
    msg = (('\n<br/>&nbsp;Your score on your most recent '
            'submission was: %01.02f%%') % (overall * 100)) + msg
    return {'score': overall, 'msg': msg}


def make_initial_display(info):
    init = info['csq_initial']
    tests = [dict(test_defaults) for i in info['csq_tests']]
    for (i, j) in zip(tests, info['csq_tests']):
        i.update(j)
    show_tests = [i for i in tests if i['include']]
    l = len(show_tests) - 1
    if l > -1:
        init += '\n\n\n### Test Cases:\n'
    get_sandbox(info)
    for ix, i in enumerate(show_tests):
        init += '\n# Test Case %d' % (ix + 1)
        if i['include_soln']:
            if 'cached_result' in i:
                log_s = cached_result
            else:
                out_s, err_s, log_s = info['sandbox_run_test'](
                    info, info['csq_soln'], i)
            init += ' (Should print: %s)' % log_s
        init += '\n'
        if i['include_description']:
            init += '# %s\n' % i['description']
        init += i['code']
        if info.get('csq_python3', True):
            init += '\nprint("Test Case %d:", %s)' % (ix + 1, i['variable'])
            if i['include_soln']:
                init += '\nprint("Expected:", %s)' % (log_s, )
        else:
            init += '\nprint "Test Case %d:", %s' % (ix + 1, i['variable'])
            if i['include_soln']:
                init += '\nprint "Expected:", %s' % (log_s, )
        if ix != l:
            init += '\n'
    return init


def render_html_textarea(last_log, **info):
    return tutor.question('bigbox')[0]['render_html'](last_log, **info)


def render_html_upload(last_log, **info):
    name = info['csq_name']
    init = last_log.get(name, (None, info['csq_initial']))
    if isinstance(init, str):
        fname = ''
    else:
        fname, init = init
    params = {
        'name': name,
        'init': str(init),
        'safeinit': init.replace('<', '&lt;'),
        'b64init': b64encode(make_initial_display(info).encode()),
        'dl': (' download="%s"' % info['csq_skeleton_name'])
        if 'csq_skeleton_name' in info else 'download',
        'dl2': (' download="%s"' % fname)
        if 'csq_skeleton_name' in info else 'download',
    }
    out = ''
    if info.get('csq_show_skeleton', True):
        out += ('''<a href="data:text/plain;base64,%(b64init)s" '''
                '''target="_blank"%(dl)s>Code Skeleton</a><br />''') % params
    if last_log.get(name, None) is not None:
        code = last_log[name]
        if isinstance(code, str):
            code = (None, "data:text/plain;base64,%s" % b64encode(code.encode()))
        out += ('''<a href="%s" '''
                '''target="_blank" id="%s_lastfile">'''
                '''Your Last Submission</a><br />''') % (code[1], name)
    out += '''<input type="file" id=%(name)s name="%(name)s" />''' % params
    return out


def render_html_ace(last_log, **info):
    name = info['csq_name']
    init = last_log.get(name, None)
    if init is None:
        init = make_initial_display(info)
    init = str(init.encode('utf-8', 'replace').decode('ascii', 'ignore'))
    fontsize = info['csq_font_size']
    params = {
        'name': name,
        'init': init,
        'safeinit': init.replace('<', '&lt;'),
        'height': info['csq_rows'] * (fontsize + 4),
        'fontsize': fontsize,
    }

    return '''
<div class="ace_editor_wrapper" id="container%(name)s">
<div id="editor%(name)s" name="editor%(name)s" class="embedded_ace_code">%(safeinit)s</div></div>
<input type="hidden" name="%(name)s" id="%(name)s" />
<input type="hidden" name="%(name)s_log" id="%(name)s_log" />
<script type="text/javascript" src="https://d1n0x3qji82z53.cloudfront.net/src-min-noconflict/ace.js"></script>
<script type="text/javascript">
    var log%(name)s = new Array();
    var editor%(name)s = ace.edit("editor%(name)s");
    editor%(name)s.setTheme("ace/theme/textmate");
    editor%(name)s.getSession().setMode("ace/mode/python");
    editor%(name)s.setShowFoldWidgets(false);
    editor%(name)s.setValue(%(init)r)
    $("#%(name)s").val(editor%(name)s.getValue());
    editor%(name)s.on("change",function(e){
        editor%(name)s.getSession().setUseSoftTabs(true);
        $("#%(name)s").val(editor%(name)s.getValue());
    });
    editor%(name)s.clearSelection()
    editor%(name)s.getSession().setUseSoftTabs(true);
    editor%(name)s.on("paste",function(txt){editor%(name)s.getSession().setUseSoftTabs(false);});
    editor%(name)s.getSession().setTabSize(4);
    editor%(name)s.setFontSize("%(fontsize)spx");
    $("#container%(name)s").height(%(height)s);
    $("#editor%(name)s").height(%(height)s);
    editor%(name)s.resize(true);
</script>''' % params


RENDERERS = {
    'textarea': render_html_textarea,
    'ace': render_html_ace,
    'upload': render_html_upload
}


def render_html(last_log, **info):
    renderer = info['csq_interface']
    if renderer in RENDERERS:
        return RENDERERS[renderer](last_log or {}, **info)
    return ("<font color='red'>"
            "Invalid <tt>pythoncode</tt> interface: %s"
            "</font>") % renderer


def answer_display(**info):
    out = ('Here is the solution we wrote:<p>'
           '<pre><code id="%s_soln_highlight" class="lang-python">%s</code></pre>'
           '<script type="text/javascript">hljs.highlightBlock($("#%s_soln_highlight")[0]);</script>') % (info['csq_name'], info['csq_soln'], info['csq_name'])
    return out
