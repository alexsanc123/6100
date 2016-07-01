# Version 9.0.0 (current progress)

_Next planned release.  Currently under development._

**Added:**

* Added back the `catsoopdb` format (last seen in
    [version 4.0.1](https://gitlab.com/adqm/cat-soop/blob/master/CHANGELOG.md#version-401)),
    with improvements to prevent collisions and a few bugfixes.
* Added [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) to the
    distribution.

**Changed:**

* CAT-SOOP is now _only_ compatible with Python version 3.5+.  Python 2
    compatibility was dropped intentionally, but versions 3.0.0 <= x < 3.5 are
    not supported because CAT-SOOP does some strange things with imports.
* Renamed `gb.py` -> `base_context.py` to more accurately reflect its usage.
* Moved `main.template` and `base.css` to `old.template` and `old.css`,
    respectively, to make room for new (more modern) style.
* Modified the `login` authentication type to use Python's built-in
    implementation of PBKDF2.  Also included the option to tune the number
    of iterations used with PBKDF2, and increased the default number of
    iterations from 50,000 to 250,000.
* Changed the way authentication is handled in AJAX requests, in preparation
    for including the public-facing API.

**Deprecated:**

**Removed:**

**Fixed:**

* Pre-compiled CAT-SOOP (`.pycs`) files' names now include the Python
    implementation's cache tag, so that the same course can be migrated to a
    CAT-SOOP instance running on a different version of Python without issue.
* Fixed a bug whereby an empty entry in a multiplechoice question (`--`) was
    interpreted as being the last element in the `csq_options` list.

**Security:**

# Version 8.0.0

**Added:**

* `<label>` and `<ref>` tags are now available, for easier referencing of
    sections within a CAT-SOOP page.
* Answers and explanations can now be automatically viewed in certain
    situations (running out of submissions, earning 100% score).
* Added a check for non-ASCII characters in input, and an error message to be
    displayed in this case.
* Most CAT-SOOP options related to the default handler can now be specified as
    functions that return the appropriate value, rather than the value itself,
    which allows them to be set in a way that depends on the current context.
* Added a way to compute stats about a particular page (for use in making
    gradebooks).
* Question types can now have multiple form fields by having names starting with
    `__QNAME_`, where `QNAME` is the name of the question.
* The `multiplechoice` question type has two new modes which allow for arbitrary
    formatting (including math) in the options: `checkbox`, which allows
    multiple answers to be selected; and `radio`, which allows only one answer
    to be selected.
* Added the `cs_debug` function, which can be used to log arbitrary information
    to a file during execution of a `preload` or `content` file.
* Resources can now be loaded from arbitrarily-named files
    (e.g., `<root>/path/to/foo.md` instead of `<root>/path/to/foo/content.md`)
* In the `pythoncode` question type, it is now possible to hide the code
    associated with test cases.
* Added `data_uri` module from
    [https://gist.github.com/zacharyvoase/5538178](https://gist.github.com/zacharyvoase/5538178)
    for better handling of file uploads
* Users can now log in with their e-mail addresses instead of their usernames
    when using the `login` authentication type.
* Permissions can now be specified directly via `cs_permissions`, instead of
    exclusively via roles.
* The `pythoncode` question type can now handle Python 3 code.
* Handlers and question types can now have viewable pages inside them, viewable
    at `<url_root>/__HANDLER__/default/page_name`
* Every page footer now links to both the terms of the license, and also to the
    "download source" link.
* Added a module for sending e-mails, primarily for use in the `login`
    authentication type.
* [MathJax](https://www.mathjax.org/) is now included directly, rather than loaded from their CDN.

**Changed:**

* Functions inside of question types no longer need to manually load default
    values; values from the `defaults` variable are automatically used when not
    specified inside the `<question>` tag.
* The `login` authentication type was much improved, including the option to
    send confirmation e-mails, change passwords, and recover lost passwords; and
    to customize the types of e-mail addresses that are accepted.
* Improved error reporting in the `login` question type.
* The `cs_post_load` hook now executes before the page's handler is invoked,
    and a new hook `cs_post_handle` was introduced, which is called after the
    handler is invoked.
* CAT-SOOP's handling of HTML tags is now case-insensitive.
* The "view as" page was updated to show more accurately what the user in
    question would see.
* Many options related to the default handler (primarily related to which
    actions should be allowed) are now specified on a per-question basis rather
    than a per-page basis.
* Locking a user out of a problem has been separated from viewing the answer to
    that question.
* Improved rendering in the `expression` question type.
* `name_map` is now stored as an ordered dictionary.
* Results from the `pythonic` question type are now evaluated in the question's
    scope, rather than in the question type's scope.
* The number of rows to be displayed in the ACE interface for coding questions
    is now customizable.
* Answers in the `smallbox` and `bigbox` question types are no longer wrapped in
    `<tt></tt>`
* Markdown and/or custom XML, depending on the source type used, is now
    interpreted inside of answers and explanations (including math rendering).
* All CAT-SOOP modules are now available inside of the source files for handlers
    and question types.
* The `cs_scripts` string is now injected into the template after jQuery, katex,
    MathJax, and cs_math have been loaded.
* Modified the generation of per-user random seeds to (eventually) allow for
    re-generating of random seeds.
* Moved much of the Javascript code from the default handler to separate files.
* Moved WSGI file and changed the way imports are handled in order to make sure
    everything can access the CAT-SOOP modules/subpackages.
* Moved handling of `csq_prompt` out of individual question types and into the
    default handler to avoid duplicating code.
* Removed logo image from main page.
* `cs_source_format` is now inferred (rather than specified explicitly).
* In question type specifications, `handle_submission` now returns a dictionary
    instead of a tuple.
* Restructured authentication types to make adding more types in the future
    easier.

**Fixed:**

* Fixed a bug whereby `$` characters could not be escaped with `\`.
* Fixed issues with certain tags' internals being parsed as Markdown
    (`script`, `pre`, `question`, etc).
* Trying to access a resource that doesn't exist on disk now gives a 404 error
    instead of crashing.
* Fixed several bugs related to uploading multiple files in a single submission
* Spaces are now allowed in question names.
* CAT-SOOP no longer crashes on a malformed `<question>`, but rather displays an
    error message.
* Fixed an issue with intermittent WSGI failures by re-trying failed actions.
* Updated MathJax to version 2.6.1 to fix a rendering issue in Chrome.
* Updated the URL of the default Python sandbox to reflect changes in the
    CAT-SOOP web site.
* Improved handling of query strings and fragment identifiers when rewriting
    URLs.
* Improved handling of implicit multiplication in the `expression` question
    type.
* Added unary `+` to Python syntax in the `expression` question type.
* `cslog.most_recent` now returns the default value when the log file does not
    exist, instead of crashing.
* Fixed handling of temporary files on Windows hosts.
* Fixed validation of user information when registering under the `login`
    authenatication type.
* Fixed several bugs with manual grading, reported from 6.02.
* Log files are no longer created when trying to read from a nonexistent log.
* Mercurial temporary files (`*.orig`) are now ignored in the zip generated when
    downloading the source.
* `<pre>` tags are now used instead of `<tt>` for wrapping answers in the
    `pythoncode` question type.
* Fixed an issue in the `pythoncode` sanboxes whereby `0 MEMORY` limit actually
    allowed 0 bytes of heap storage, rather than unlimited.
* Prevent a crash if `<cs_data_root>/courses` does not exist.
* Modified to always use the local `markdown` package, even if one is installed
    globally, to make sure Markdown extensions are loaded properly.
* Buttons are now re-enabled on page load, to prevent an issue whereby buttons
    would remain disabled after a refresh on Firefox.

**Security:**

* Smarter hashing ([PBKDF2](https://en.wikipedia.org/wiki/PBKDF2)) is now used
    for the `login` authentication mode.
* Closed a XSS vulnerability in the `pythoncode` question type.
* Closed a security hole in session handling that allowed for arbitrary code
    execution under certain circumstances by validating session ids and
    modifying the way session data are stored.
* Logs can no longer be accessed/created outside of the appropriate `__LOGS__`
    directories.

# Version 7.1.1

**Fixed:**

* Fixed an issue that prevented the last question on each page from being
    displayed.

# Version 7.1.0

**Added:**

* Included python-markdown from
    [https://pypi.python.org/pypi/Markdown](https://pypi.python.org/pypi/Markdown)
* Added the option to grade questions manually, from 6.02 fall 2015.
* Added a `richtext` question type, which allows for formatting of text using
    CAT-SOOP-flavored Markdown.
* Added the `fileupload` question type, which allows users to upload arbitrary
    files.
* Added checks for valid configuration options.

**Changed:**

* Rewrote the `expression` question type to use PLY for parsing, and included
    a default syntax for expressions that is more approachable to users not
    familiar with Python.

# Version 7.0.1

**Fixed:**

* Fixed a syntax error in the `expression` question type.

# Version 7.0.0

**Added:**

* Included [KaTeX](https://khan.github.io/KaTeX/).
* Added three new handlers: `passthrough`, which displays `cs_content` without
    modification; `raw_response`, which allows sending a raw HTTP response; and
    `redirect`, for redirecting to other resources easily.
* Added support for [Markdown](https://daringfireball.net/projects/markdown/) as
    an alternative source format, and included
    [python-markdown](https://pypi.python.org/pypi/Markdown) in the
    distribution.
* Question type specifications can now include an arbitrary action (beyond
    saving/submitting) that will be executed when a user presses a new button.
* Added support for streaming content (via returning a generator instead of a
    string), and for automatic streaming of large static files.
* Added support for inline (runnable by users) test cases in `pythoncode`
    question types.
* Added `cs_util` resources: `time`, which yields the current time (according to
    the server) for synchronization purposes; `source.zip`, which downloads a
    zip archive containing the CAT-SOOP source code; and `license`, which
    contains the text of CAT-SOOP's license.
* Added a `string` mode to the `pythonic` question type, which allows the answer
    to be specified as a string to be evaluated.  Also added the `csq_code_pre`
    variable to this question type, for setting up the environment into which
    `csq_soln` will be evaluated in string mode.

**Changed:**

* Math rendering now uses KaTeX (fast, but limited support) when possible, and
    falls back to MathJax (slow, but more support) when necessary.
* "Special" CAT-SOOP variables are now prefixed with `cs_` (for page-specific
    values) or `csq_` (for question-specific values) to prevent accidental
    shadowing
* Changed nomenclature: "activity type" -> "handler"
* Complete rewrite of default handler.
* Reorganization of sandboxing for Python code.
* `gb.py` should no longer be changed; rather, global configuration values
    should be overwritten via `config.py` (which is loaded into `gb.py`)
* Improved handling of footnotes.

**Removed:**

* Removed `jquery_typing` plugin, which is no longer needed for `expression`
    questions.

**Fixed:**

* Fixed bug with newline handling in CGI interface.
* Fixed bugs related to static files when using the CGI interface running on
    Windows hosts.
* The default theme now handles resizing of the containing window more smoothly.

**Style:**

* Embraced [PEP8](https://www.python.org/dev/peps/pep-0008/) style.

# Version 6.0.0

**Added:**

* Added `post_load` hook, which is executed after the `content` file is
    executed.
* Added support for XML as an additional source format, and set it to be the
    default format.
* Change names `EARLY_LOAD.py` -> `preload.py` and
    `LATE_LOAD.py` -> `content.xml`
* Added the `pythonliteral` question type, which behaves much like `pythonic`,
    but requires that the submission be a literal value (rather than the result
    of a more complicated expression).

**Changed:**

* Modified handling of footnotes.
* File containing user information should now end in `.py` (e.g., `username.py`
    instead of `username`).
* Reorganized `python...` question types to properly inherit from one another to
    avoid duplicate code.

**Removed:**

* The `problem` activity type was removed, in favor of `ajaxproblem`.

**Fixed:**

* Fixed an issue where `'last_submit'` was keeping information only about the
    most recent submission overall, instead of the most recent submission for
    each question.
* The `__LOGS__` directory will now be created if it does not exist, rather than
    crashing CAT-SOOP.

**Security:**

* Error messages now show less information, to avoid displaying sensitive
    information.

# Version 5.0.0

**Added:**

* Added support for footnotes via `<footnote>`
* Added support for page organization via `<section>`, `<subsection>`, etc.
* The ability to save and submit are now controllable via special variables in
    the `problem` activity type.
* Added a warning message upon clicking the 'view solution' button to indicate
    that users will not be able to submit after doing so.  Also maintained the
    ability to bypass this check, for things like automatically submitting at
    the end of a timed exercise.
* Added the `handout` activity type, which allows for showing a static file, but
    with access controls (releasing after a particular date, only viewable by
    particular role, etc).
* Added support for displaying explanations in addition to answers in particular
    question types.

**Changed:**

* Logs are now stored in [SQLite](https://www.sqlite.org/) databases.
* The logo in the main page is now displayed as text, rather than as an image.
* Buttons in `ajaxproblem` question types are now disabled before processing the
    request, to avoid multiple identical submissions from mis-clicks.

**Removed:**

* Removed `catsoopdb` format, in favor of SQLite.

**Fixed:**

* Renamed `logging.py` to `cslog.py` to prevent accidentically importing
    Python's built-in `logging` module.
* Fixed rendering of math when viewing solution to an `expression` question.
* Scores are now properly handled in the `ajaxproblem` activity type.
* Fixed a bug with displaying the solution for `pythonic` question types whose
    solutions are tuples.
* Fixed a bug with displaying the solution for `pythonic` question types whose
    solutions are strings.
* Fixed a bug related to handling of dynamic pages in the `__BASE__` course.
* Fixed numerous `ajaxproblem` bugs.
* Improved detection of static files.

**Security:**

* Error messages no longer show information about the location of CAT-SOOP (or
    the course in question) on disk

# Version 4.0.1

**Fixed:**

* Fixed issue whereby a missing `EARLY_LOAD.py` would crash CAT-SOOP.
* Fixed bug with caching of static files.
* Fixed bug related to authenticating (in `login` mode) with

**Removed:**

* Removed rendering time from default template.

# Version 4.0.0

**Added:**

* Added the `ajaxproblem` activity type, which allows submitting individual
    questions without reloading the entire page.  Made `ajaxproblem` the default
    activity type.
* Added support for skipping ahead or behind by weeks in relative timestrings,
    using `+` or `-` (e.g., `M+:17:00` means _next_ Monday at 5pm).
* Solutions for individual students are now displayed when impersonating them.
* Source for pages is now cached in a `marshal`ed format, to prevent having to
    re-parse the source of pages that have not changed.
* Added support for authenticating via `login` (username and password) rather
    than via client certificate.
* Added support for per-user randomness (users see the same numbers upon
    returning to a page, but different users may see different numbers).
* Added documentation (via epydoc-compatible docstrings) throughout.
* CAT-SOOP now asks the browser to use cached versions of static files where
    appropriate.
* Allowed question types and activity types to be specified in the course rather
    than in the base system.

**Changed:**

* Changed internal nomenclature: `meta` -> `context` everywhere to represent the
    context in which a page is rendered.

**Removed:**

* Removed several references to `sicp-s2.mit.edu` in the code.

**Fixed:**

* Fixed impersonation glitch whereby permissions were inherited from the
    impersonatee.
* Fixed glaring bug with static file handling.
* Fixed inheritance bug in the `pythonic` question type.

**Security:**

# Version 3.1.0

**Added:**

* Added WSGI interface (and moved main function elsewhere so WSGI and CGI can
    share code).
* Questions are automatically given names if they were not explicitly given a
    name.
* Question types and activity types are now pre-compiled to avoid having to
    re-parse them on every load.

# Version 3.0.0

**Added:**

* `problem` activities now store due dates, to account for changes in due date
    after submitting.
* Added support for the [ACE](https://ace.c9.io/#nav=about) code editor in
    Python code questions.

**Changed:**

* Separated loading from `METADATA.py` into `EARLY_LOAD.py` and `LATE_LOAD.py`.
    `EARLY_LOAD` files are executed all the way down the source tree (for the
    sake of inheritance, as with `METADATA.py`), but only the `LATE_LOAD.py`
    associated with the leaf node is executed (to allow some code execution to
    be avoided when working down the tree).
* Moved/improved impersonation code.
* Refactored logging code.
* Refactored main control loop.

**Fixed:**

* Better sandboxing of Python code.
* Fixed an issue with `submitAs` control for questions with randomness.
* Fixed handling of paths on Windows hosts.
* Modified `expression` question type to be compatible with Python 2.6.
* Several bug fixes in `pythoncode` question type.

**Security:**

* Prune out `..` and `.` from URLs to avoid escaping the CAT-SOOP tree.

# Version 2.0.0

_Complete re-write.  First version used in 6.01 (spring 2013).  First version
with any similarity to the current code._

# Version 1.0.0

_The original version, used in 6.003 fall 2011, and described in
[http://hdl.handle.net/1721.1/77086](http://hdl.handle.net/1721.1/770860),
which has very little relevance to later versions._