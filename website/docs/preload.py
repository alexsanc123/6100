import os
import subprocess

from datetime import datetime

cs_long_name = "Documentation"

docs_loc = os.path.join(cs_data_root, "courses", cs_course, "docs")
cs_title = "Documentation | CAT-SOOP"

cs_top_menu = [
    {
        "text": "Navigation",
        "link": [
            {"link": "COURSE", "text": "CAT-SOOP Home"},
            {"link": "COURSE/docs", "text": "Docs Home"},
            {"link": "COURSE/docs/about", "text": "About"},
            {"link": "COURSE/docs/installing", "text": "Installing"},
            {"link": "COURSE/docs/authoring", "text": "Authoring"},
            {"link": "COURSE/docs/extending", "text": "Extending"},
            {"link": "COURSE/docs/contributing", "text": "Contributing"},
            {"link": "COURSE/docs/api?p=catsoop", "text": "API"},
        ],
    }
]


def callout(note, header, style):
    return """<div class="callout callout-%s">
<h4>%s</h4>
%s
</div>""" % (
        style,
        header,
        csm_language._md_format_string(globals(), note),
    )


def note(x):
    print(callout(x, "Note", "info"))
    return ""


def warning(x):
    print(callout(x, "Warning", "danger"))
    return ""


def doublecheck(x):
    print(callout(x, "Double Check", "warning"))
    return ""


def aside(x):
    print(callout(x, "Aside", "warning"))
    return ""


todo = """!!! warning: This Page Needs Attention
    Contributions to documentation are more than welcome!
    You can post suggestions, questions, or other feedback to the <a
    href="/community" target="_blank">community forum</a>.  If you don't want
    to create an account there, you can post by sending e-mail to
    `community@catsoop.mit.edu`."""
