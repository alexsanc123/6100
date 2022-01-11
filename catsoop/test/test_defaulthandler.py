import pytest

from .. import loader
from .. import tutor
from .. import cslog
from ..dispatch import content_file_location

def test_submit():
    page_path = ['test_course', 'questions']
    ctx = loader.generate_context(page_path)
    ctx['cs_user_info'] = {
        'username': 'test_user',
        'permissions': ['view', 'submit'],
    }
    cfile = content_file_location(ctx, page_path)
    loader.load_content(ctx, page_path[0], page_path[1:], ctx, cfile)
    first_question = None
    for i in ctx['cs_problem_spec']:
        if isinstance(i, tuple):
            first_question = i
            break
    print(first_question[1]['csq_name'])
    handler = tutor.handler(ctx, 'default', False)

    handler['handle_submission'](ctx, ...)

    last_submit = cslog.most_recent(ctx['cs_user_info']['username'], page_path, 'problemstate')

    rendered = handler['render_question'](...)
    assert last_submitted_value in rendered
