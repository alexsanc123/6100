# TODO: Remove this
import pprint

import pytest

from .. import loader
from .. import tutor
from .. import cslog
from ..dispatch import content_file_location
from catsoop.__HANDLERS__.default import default

import json
from bs4 import BeautifulSoup
import shutil

TEST_PAGE_PATH = ["test_course", "questions"]


def generate_test_context(test_form):
    """
    Generates a test context based on test_form.

    **Parameters:**

    * `test_form`: a dictionary containing, at the minimum, a proposed action and other data regarding the propsed action

        Examples:

            test_form = {"action": "view"}  # to view a page
            test_form = {
                            "names": '["q000008"]',
                            "data": '{"q000008": "5"}',
                            "action": "submit",
                        }  # to submit a specific value to a specific question

    **Returns:** a processed context that is ready for handling
    """
    context = loader.generate_context(TEST_PAGE_PATH)
    context["cs_user_info"] = {
        "username": "test_user",
        "permissions": ["view", "submit"],
    }
    cfile = content_file_location(context, TEST_PAGE_PATH)
    loader.load_content(context, TEST_PAGE_PATH[0], TEST_PAGE_PATH[1:], context, cfile)

    context["cs_session_data"] = {}
    context["cs_form"] = test_form

    default.pre_handle(context)

    return context


def mock_submit(question_name, submit_value, action):
    submit_form = {
        "names": json.dumps([question_name]),
        "data": json.dumps({question_name: submit_value}),
        "action": "submit",
    }

    submit_context = generate_test_context(submit_form)

    handler = tutor.handler(submit_context, "default", False)

    handler_fn = "handle_check" if action == "check" else "handle_submit"
    handler[handler_fn](submit_context)

    return (
        cslog.most_recent(
            submit_context["cs_user_info"]["username"], TEST_PAGE_PATH, "problemstate"
        ),
        handler,
    )


def check_render(question_name, handler, last_submit, check_soup):
    # def check_render(question_name, handler, last_submit, expected_content):
    view_ctx = generate_test_context({"action": "view"})

    all_questions = [
        elem for elem in view_ctx["cs_problem_spec"] if isinstance(elem, tuple)
    ]
    rendered = handler["render_question"](
        all_questions[int(question_name[1:])], view_ctx, last_submit
    )

    soup = BeautifulSoup(rendered, "html.parser")

    pprint.pprint(soup)

    # return expected_content in soup.text
    return check_soup(soup)


@pytest.fixture(autouse=True)
def setup():
    test_log_path = "/tmp/catsoop_test/_logs/_courses/test_course/test_user/questions"
    # test_log_path = os.path.join(context["cs_data_root"], "_logs")
    shutil.rmtree(test_log_path, ignore_errors=True)


def test_question_8():
    # TODO: what should we do with scores in the problemstate after check? If not deleted, will display the previous score prior to checking after refreshing the page
    test_question_name = "q000008"
    last_submit_1, submit_handler_1 = mock_submit(
        question_name=test_question_name,
        submit_value="sqrt(cos(omega)+j*sin(omega))",
        action="submit",
    )
    last_check_1, check_handler_1 = mock_submit(
        question_name=test_question_name,
        submit_value="5",
        action="check",
    )

    expected_last_submit_1 = {
        # "last_processed": {
        #     test_question_name: {"data": "sqrt(cos(omega)+j*sin(omega))", "type": "raw"}
        # },
        "last_submit": {
            test_question_name: {"data": "sqrt(cos(omega)+j*sin(omega))", "type": "raw"}
        },
        "last_submit_id": {},
        "nsubmits_used": {test_question_name: 1},
        "score_displays": {
            test_question_name: "<span "
            'style="color:rgb(0,200,0);font-weight:bolder;">100.00%</span>'
        },
        # "scores": {test_question_name: True}, # TODO
    }

    expected_last_check_1 = {
        "last_check": {test_question_name: {"data": "5", "type": "raw"}},
        # "last_processed": {test_question_name: {"data": "5", "type": "raw"}},
        "last_submit": {
            test_question_name: {"data": "sqrt(cos(omega)+j*sin(omega))", "type": "raw"}
        },
        "last_submit_id": {},
        "nsubmits_used": {test_question_name: 1},
        "score_displays": {test_question_name: ""},
        # "scores": {},  # TODO
    }

    assert expected_last_submit_1.items() <= last_submit_1.items()  # is a subset of
    assert expected_last_check_1.items() <= last_check_1.items()

    assert check_render(
        question_name=test_question_name,
        handler=check_handler_1,
        last_submit=last_check_1,
        # expected_content="Please remember to submit your response after checking.",
        check_soup=lambda x: "Please remember to submit your response after checking."
        in x.text
        # and x.find("input", {"id": test_question_name}).attrs["value"] == "",
    )

    last_submit_2, submit_handler_2 = mock_submit(
        question_name=test_question_name,
        submit_value="10",
        action="submit",
    )

    expected_last_submit_2 = {
        "last_check": {test_question_name: {"data": "5", "type": "raw"}},
        # "last_processed": {test_question_name: {"data": "10", "type": "raw"}},
        "last_submit": {test_question_name: {"data": "10", "type": "raw"}},
        "last_submit_id": {},
        "nsubmits_used": {test_question_name: 2},
        "score_displays": {
            test_question_name: "<span "
            'style="color:rgb(200,0,0);font-weight:bolder;">0.00%</span>'
        },
        # "scores": {test_question_name: False},  # TODO: Why does this go to False?
    }

    assert expected_last_submit_2.items() <= last_submit_2.items()
    assert check_render(
        question_name=test_question_name,
        handler=submit_handler_2,
        last_submit=last_submit_2,
        # expected_content="Please remember to submit your response after checking.",
        check_soup=lambda x: "Please remember to submit your response after checking."
        not in x.text
        # and x.find("input", {"id": test_question_name}).attrs["value"]
        # == "10",  # confirm that the message disappears
    )
