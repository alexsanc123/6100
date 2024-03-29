# Current Developments

_Work toward next release. Currently under development._

**ADDED:**

* Added the ability for users to specify that they prefer light text on a dark background

* `<python>` tags can now be exited using `sys.exit()`, with non-zero "return codes" causing the output to be ignored

* Added additional arguments to the callback function for `ajaxrequest` in the `default` handler

* The `pythoncode` question type now listens to the `csq_show_check` flag

* Added the `download` and `filename` options to the `raw_response` handler to allow making the responses downloadable (thanks to Shen Shen)

* Updates to the question info cache can now be avoided by setting `cs_update_questions_cache = False`

**CHANGED:**

* Suppressed some warnings coming from BeautifulSoup

* Changed default session duration to fourteen days instead of two

* Changed location of lock files to (hopefully) prevent the size of the locks directory from growing out of control

* Javascript files are now located at `/js/` instead of `/scripts/`

* `<chapter>`, `<section>`, `<subsection>`, and `<subsubsection>` tags have been replaced with `<catsoop-chapter>`, `<catsoop-section>`, etc; and a conversion script has been provided

* Moved the default `'remote'` Python sandbox and improved the error message when the sandbox is offline.

**DEPRECATED:**

**REMOVED:**

**FIXED:**

* Fixed a crash from `render_escaped_dollar` method not existing (triggered by mistletoe update?)

* Fixed multiple issues with `-c` flag and `CATSOOP_CONFIG` environment variable

* Fixed incorrect help text for `catsoop logedit` command

* Fixed an old bug where submitting an asynchronously-checked question while another submission is queued for that same question caused confused results
    to be displayed

* Fixed a potential bug in the `pythoncode` question type when decoding submitted files containing a BOM

* An empty string is no longer considered to be a well-formed response to a `pythonic` question

* Fixed a potential bug with the length calculation in the `raw_response` header when `response` was given as a string containing unicode characters (thanks to Shen Shen)

* Fixed a display issue causing a "hamburger" to appear on narrow screens even with no menu items present

* Replaced the `<showhide>` implementation so as to avoid broken rendering of `<details>` tags in Chromium/Chrome

* Code blocks within responses to question submissions are now properly highlighted

* Fixed a regression that caused the `'timeout'` option in `pythoncode` test cases to be ignored

**SECURITY:**

**ACCESSIBILITY:**

* Changed `"radio"` and `"checkbox"` multiplechoice renderers to use fieldsets and to properly associate labels with inputs

* Improved screen-reader-friendliness of solution displays for the `"checkbox"` multiplechoice renderer

* Improved code displays (with and without line numbers) to make them more usable with a screen reader

* Automatically set ARIA labels for built-in question types based on `csq_prompt` (and added the ability to specify a `csq_preamble` that is not included as part of the ARIA label).

* Switched from KaTeX to MathJax for math rendering, for better screen reader support

* Improved keyboard-oriented navigation and screen-reader support for the navigation breadcrumbs and the top menu

* Improved accessibility of modal dialogs from the `cs_modal` javascript function

**DOCUMENTATION:**

**VENDORED SOFTWARE:**

* Removed [KaTeX](https://katex.org/) from the distribution

* Included [MathJax](https://www.mathjax.org/) (v3.2.2) in the distribution


# Version 2022.9.0

**ADDED:**

* Added `cs_log_lock_location` to control where locks for log files are written

* Added `csq_renderer` option to `pythonic` qtype, to allow choosing between `"bigbox"` and `"smallbox"` renderers

* The `pythonic` qtype now respects the `csq_check_function` variable (which can still be overridden by specifying check functions for individual tests)

* Questions with a "Check" button now have a "Revert to Prior Submission" button (thanks to Evan Rubel)

* Added `cs_wsgi_server_worker_max_requests` option to provide `--max-requests` option to uWSGI, to force workers to be killed and restarted after that
    many requests

**CHANGED:**

* catsoop now requires Python 3.7 or newer

* `cs_local_python_import` now raises a more meaningful exception when the given filename is incorrect

* Replaced hacky import mechanism for custom question types with access to `cs_local_python_import`

* Questions with a "Check" button no longer also have a "Save" button (thanks to Evan Rubel)

* Added error reporting on failed `<include>` tags (thanks to Shen Shen)

* Changed default message for when users are not logged in

* Due to build issues on some platforms, catsoop no longer depends on uWSGI unless `[server]` is specified when installing

* `tutor.init_random` now uses randomly-generated random seeds again

**FIXED:**

* Fixed an issue with autolocking and auto answer viewing

* Fixed an issue with `checkoff` question type not understanding who has permissions to submit checkoffs

* Fixed an issue with storage of manual grades

* Fixed an error with certain LTI integrations

* Fixed an incorrect check for whether the target(s) of `<include>` tags are within the tree (thanks to Shen Shen)

* Fixed an issue with `checker_local`'s multiprocessing on MacOS

* Every page now loads the CodeMirror base code, to fix an error caused by multiple code-like questions using different CodeMirror modes but bringing in a completely fresh `codemirror.js` for each one (overriding the old modes)

* Replaced [deprecated `asyncio.get_event_loop`](https://github.com/python/cpython/issues/83710) function in `reporter.py` script

**REMOVED:**

* Removed the ability to use other machines as remote checkers

**SECURITY:**

* Don't allow fresh logins on user settings pages

* `cs_auth_type` is now only read from `config.py` (course-level `preload.py` files cannot change it)

**VENDORED SOFTWARE:**

* Upgraded [Codemirror](https://codemirror.net/) to v5.65.6 (upgrating to Codemirror v6 will happen in a later catsoop version)

* Upgraded [KaTeX](https://katex.org/) to v0.16.0

* Upgraded [Twemoji](https://twemoji.twitter.com/) to v14.0.2


# Version 2021.9.0

**ADDED:**

* File uploads in the built-in question types now support dragging-and-dropping files (in addition to the normal file-chooser setup)

* Logging of page views (in the `problemactions` log) can now be enabled by setting `cs_log_page_views = True`

* Allow running via `python3 -m catsoop` in addition to `catsoop`

* Added experimental support for running checkers on separate machines from the web server

* Added a `delete_log` function to the `cslog` module for deleting an entire log

* Added a "user settings" page for managing user information, API tokens, look-and-feel, and more

* Unauthenticated users now receive the `"Unauthenticated"` role, which can be used to control permissions

* Added a way to impersonate a user while preserving their permissions, via the `preserve_permissions` query string parameter

**CHANGED:**

* On the main page, links are now shown even to courses that can't be properly loaded, so that the underlying issue is easier to find (clicking on the link shows a more detailed error message)

* Auto-generated `csq_name` fields now increment only for questions that don't have names specified (reverts a bad change from 2020.9.0)

* The `pythonic` and `pythonliteral` question types now allow checking for valid formatting

* Reverted changes to `cslog` module and how the checker queue process works

* Logs now store information about file uploads in a more intuitive format

* `cs_upload_management` provides a way to control where uploaded files are stored (directly in the database, or as separate files)

* Changed the location of the default remote sandbox for running Python code

* Replaced `csq_grading_mode="legacy"` with `csq_autograder_async` flag, and made synchronous checking the default

**REMOVED:**

* Removed PostgreSQL as a logging mechanism

**FIXED:**

* Fixed issue with reporter websocket connection being lost frequently

* Fixed a crash related to `multiprocessing` on MacOS with Python 3.8

* Fixed an issue with rendering inline code blocks split across multiple lines of Markdown

* Attempted fix for rendering of the catsoop logo in the footer on iOS/Safari

* Fixed a potential race condition in `cslog.most_recent`

**SECURITY:**

* Logs are now encrypted by default

* Removed information about the Python version from the default footer

* Prevented lock file locations from leaking information when logs are encrypted

* Switched to using the `secrets` module to generate secure tokens

* API tokens are no longer generated automatically for users, and they are no longer present in the source of exercises

* OpenID Connect auth type now implements PKCE

**VENDORED SOFTWARE:**

* Upgraded [Codemirror](https://codemirror.net/) to v5.62.2

* Upgraded [KaTeX](https://katex.org/) to version 0.13.16

* Upgraded [Twemoji](https://twemoji.twitter.com/) to v13.1.0


# Version 2021.2.0

**ADDED:**

* Added information about the Python version to the default footer

* Added ability to easily change the Javascript callback functions invoked after taking an action using the built-in action buttons

* Javascript callback functions now take a second parameter, the name(s) of the question(s) that were affected by the action

**FIXED:**

* Fixed the color of the "callout" box for the checking queue

* Fixed broken `tutor.read_checker_result`

* Updated the `cert` auth type to work with NGINX

**SECURITY:**

* Fixed an XSS vulnerability in the default handler


# Version 2020.9.0

**ADDED:**

* Added ability to conditionally show or hide HTML elements via the `cs-show-if` and `cs-hide-if` attributes

* Added support for showing line numbers next to code snippets by adding `-lines` to the end of the language specified for a code block

* Added ability to avoid running children's preloads into `cs_children`, by setting `cs_load_children = False`

* Added support for using LTI with Canvas, and added support for customizing the username inferred from LTI data, via `lti_username_function` in `cs_lti_config`

* Added support for PostgreSQL as an alternative backend for storing logs

* Added the ability to customize the text shown on the button in `<showhide>` tags, via the `summary` attribute

* Added support for Markdown "callouts", similar to [Markdeep's "admonitions"](https://casual-effects.com/markdeep/features.md.html#basicformatting/admonitions)

* Added support for syntax highlighting of inline code elements

* Added the `ldap3` authentication type for login using an LDAPv3 server (thanks to Halvard Hummel)

* Added the `sso` authentication type for authentication using an arbitrary third-party single-sign-on provider

* Added support for sharing KaTeX macros across calls to `catsoop.render_math`

* Added support for using `:short_name:` syntax to reference emoji, which can be included as images or as unicode characters; and added emoji images from [Twemoji](https://twemoji.twitter.com/) as the default images

**CHANGED:**

* Auto-generated `csq_name` fields increment for every question, even those that have names specified

* Switched to [mistletoe](https://github.com/miyuchina/mistletoe) for handling Markdown (CommonMark) instead of [Python-Markdown](https://python-markdown.github.io/)

* Some small changes to the way code is displayed on catsoop pages to improve readability

* Logging, upload management, and queue management are now unified within the `cslog` module

* Changed default ports from `6010` and `6011` to `7667` and `7668` to avoid a conflict with X11, and modified the `catsoop configure` command to ask about the port numbers

* Replaced `js_files` in question types with `extra_headers`, which allows injecting arbitrary strings into the header (which allows specifying not
    only Javascript files but also stylesheets)

* Removed [Ace](https://ace.c9.io/) in favor of [CodeMirror](https://codemirror.net/) as the default web-based code editor

* Upgraded [KaTeX](https://katex.org/) to v0.12.0

* Upgraded [highlight.js](https://highlightjs.org/) to version 10.0.2

* `cslog` now uses pickle protocol 4 by default (rather than the highest possible protocol), to make sure that all supported Python versions can read logs produced by any other supported version

**REMOVED:**

* Removed slow/broken code for logging in via e-mail instead of username when using the `login` auth type

* `cs_upload_management` is no longer relevant, as uploads are now handled via a standard interface in `cslog`

* Custom authentication types can no longer be specified at the course level

* Removed the choice of where file uploads are stored (`cs_upload_management` is no longer recognized)

* Removed [MathJax](https://www.mathjax.org/) from the distribution

**FIXED:**

* Show an error message when two questions would have the same name

* Fixed an issue with using cached results in the `pythoncode` question type

* Fixed issues with incorrect scores being sent to LTI consumers

* OpenID Connect auth type now properly checks JWT issuer

* Fixed issue with `number` question type not accepting negative inputs (thanks to Abdullah Negm)

**SECURITY:**

* Closed an XSS vulnerability by escaping the URL on 404 error pages


# Version 2020.2.0

**ADDED:**

* Added support for top-level math environments without `$` or `$$`: `equation`, `equation*`, `align`, `align*`, `eqnarray`, `eqnarray*`

* Added support for drawing SVG diagrams using ASCII art (ported from [Markdeep](https://casual-effects.com/markdeep))

**CHANGED:**

* Upgraded [KaTeX](https://katex.org/) to v0.11.1

* Replaced Fernet encryption with simpler encryption scheme based on `libsodium`

**FIXED:**

* Fixed an issue with `<showhide>` tags that prevented them from properly handling arbitrary contents (at the expense of nested showhide tags)

* Fixed alignment of first line within `<pre><code>` tags

* Fixed issue with `csq_rerender` ignoring prompts (thanks to Valerie Richmond)


# Version 2019.9.6

**FIXED:**

* BACKPORT: Fixed an issue whereby submitting a `multiplechoice` question using the `'radio'` renderer would cause an error if no option was selected (thanks to Kade Phillips)


# Version 2019.9.5

**FIXED:**

* BACKPORT: Fixed long-standing issue whereby certain students could not log in due to cookies being parsed incorrectly by `SimpleCookie`


# Version 2019.9.4

**FIXED:**

* Fixed issue whereby having the logs on a different filesystem from `/tmp` could cause the checker to crash


# Version 2019.9.3

**FIXED:**

* Fixed several lingering references to the `util` module, which has been renamed to `user`


# Version 2019.9.2

**FIXED:**

* Fixed an issue preventing question types with multiple boxes (e.g., `multiexpression`) from pre-populating those boxes with values from the last submission


# Version 2019.9.1

**FIXED:**

* Multiple fixes for the `'remote'` Python sandbox

**CHANGED:**

* The version codename is now displayed when running `catsoop --version` and in the default footer


# Version 2019.9.0

**ADDED:**

* Checking functions for `pythoncode` questions can now optionally return a tuple `(score, message)` or a dictionary `{'score': score, 'msg': message}` to display an additional message in response to a test case

* Added `cs_local_python_import` function to the context of a page load, which takes a string containing a filename (with extension, relative to the current page's directory) and returns a corresponding Python module object

* Added `.catsoop` as a content file extension, parsed using the same parser as content files with the `.md` extension

* Added rudimentary support for syntax highlighting of `.catsoop` files in Vim

* Added `cs_ui_config_flags`, including option to automatically view explanations when viewing answers, and to highlight the 'View Explanation' button

* Added `cs_user_config`, including option to specify which variable should be used for grouping when managing groups

* Added `csq_result_as_string` option to `pythoncode` question type, allowing the result to come back as a string (useful for custom types as return values from `pythoncode` or `pythonic` question types, where evaluation would otherwise fail)

* Added `logread`, `logwrite`, and `logedit` commands for working with log entries in a human-readable format

* Plugins can now start scripts when catsoop is started; scripts in `cs_data_root/plugins/autostart/` that end with `.py` will be run when `catsoop start` is invoked

* Added nicer names for URL fragments of sections and updated the `<tableofcontents/>` generator to use these when linking to sections

* Added option to show permalinks next to section headers (enabled by setting `cs_show_section_permalinks=True`)

* The `cs_content_header` text now has the CSS class `cs_content_header`

* Items in the top menu in the default theme now have the CSS class `cs_top_menu_item`

**CHANGED:**

* Question names can no longer begin with an underscore (`_`)

* Plugins should now be stored in `cs_data_root/plugins` rather than in `cs_fs_root/__PLUGINS__`

* URLs starting with `_plugin` now point to the proper location

* File locks are now stored with a `.lock` extension, to avoid potential collisions with directory names

* Renamed `loader.do_early_load` to `loader.do_preload` and `loader.do_late_load` to `loader.load_content` to hopefully remove the last of the "early load" and "late load" terminology

* Changed the name of the `util` module to `user` to better reflect its purpose

* Upgraded [KaTeX](https://katex.org/) to v0.11.0

* Changed the solution display for the `richtext` question type

* `util.read_user_file` now does not raise an exception if there is an error in a user's file; rather, it always returns a dictionary, but includes error information in the case of an error

* Logs are now stored in a binary format in order to improve the efficiency of reading/writing log entries

* The configuration script for production instances now uses uWSGI by default, and it asks about the number of processes to use for uWSGI and for the checker

**REMOVED:**

* Removed several deprecated features:

    * `__MEDIA__` can no longer be used as a name for directories containing static files;  `__STATIC__` should be used instead

    * `csm_tools` no longer points to utility functions from third-party libraries; use `csm_thirdparty` instead

    * `cs_print` has been removed; use `print` instead

    * `csq_multiplechoice_renderer` and `csq_multiplechoice_soln_mode` variables for `multiplechoice` questions have been renamed to `csq_renderer` and `csq_soln_mode`, respectively

    * `cs_score_message` has been removed as a special variable; use `csq_score_message` instead

    * `loader.spoof_early_load` has been renamed to `loader.generate_context`

* Removed `circuit` question type, which has not been used by anyone for a long time and may no longer work with catsoop updates

**FIXED:**

* The `print` function can now be used to add content to the page when using the Python source format

* `loader.generate_context` no longer breaks when given an empty path

* Reverted changes to `language` module from version 14.x.x

* Scores and messages are now logged in `problemactions` for questions in `'legacy'` grading mode (checker IDs are still logged for questions using the asynchronous checker)

* Fixed an issue whereby `set()` could not be accepted as an answer to a `pythonic` or `pythonliteral` question

* Fix for malformed HTML in `multiexpression` question output

* Fix for "preview" in `richtext` question type

* Fixed an issue related to complex numbers in the `expression` question type

* Implemented a fix for the long-standing issue with empty lines in `<showhide>` tags escaping out of them

* Fixed an issue with the checker process, whereby submissions would forever be marked as `'running'` if they experienced an error during page load or when looking up the question to submit

* Fixed the lack of decompression of uploaded files when downloaded via the 'Download Most Recent Submission' link

* Fixed an issue that caused the contents of `<ref>` tags to be ignored

* Fixed several issues with the `openid_connect` authentication mode to make it more general (thanks for input from Max Goldman)

* `"divider"` can once again be used as an element in `cs_top_menu` drop-downs


# Version 14.0.3

**FIXED:**

* Fix for issue with multiple blank lines in output from `pythoncode` questions


# Version 14.0.2

**FIXED:**

* Fix for a UI issue with the alignment of the timer when used in an iframe

* Fixed an issue with the `post_load` hook not being able to affect page content

* Fixed the LTI behavior by passing form POSTs through if the session is already LTI authenticated

* Fixed a regression from `language.py` changes that prevented content after the last question on a page from being rendered

* Fixed a regression from `language.py` that prevented footnotes from being shown in most cases

* Various fixes for Python unicode handling


# Version 14.0.1

FIXED:

* Fix for a problem with unicode characters in the `pythoncode` question type when using the `'ace'` interface

* Fixed an issue with older Pythons by using an `OrderedDict` to store `cs_internal_qinfo` in `language.py`


# Version 14.0.0

**ADDED:**

* Added the `dummy` question type, which can be used as a placeholder for a question that should be removed (but without affecting automatically-generated csq_names for questions that follow)

* Added support for using CAT-SOOP as an LTI Tool Provider (thanks to Ike Chuang)

* Added a few unit tests (thanks to Ike Chuang)

* Added `cs_debug_logger`, an instance of `logging.Logger`, for debugging (thanks to Ike Chuang)

* Added `'do_rlimits'` key to the `'python'` sandbox, which can be used to disable setting resource limits (workaround for Cygwin issue)

* Several additional features were added to pythoncode questions:

    * `pythoncode check` functions now have a lot of additional information available to them, beyond the value that was returned (including stdout, stderr, information about any exceptions that were raised, and information about timing)

    * Added the option to selectively show/hide stderr (`test['show_stderr']`)

    * Added the option to count the number of executed opcodes, and to set timeouts based on number of executed opcodes

    * Added the `csq_test_defaults` option to provide default per-test-case options within a single question

* Brought back breadcrumbs in the default theme

* The CAT-SOOP source distribution now includes the [Ace](https://ace.c9.io/) code editor

* Added `cs_custom_tags` for specifying custom tags for a course

**CHANGED:**

* Upgraded [KaTeX](https://katex.org/) to v0.10.0

* Updated CAT-SOOP to use [Python-Markdown](https://python-markdown.github.io/) version 3+

* Replaced default favicon with one that does not have the letters "CS" in it

* Modified the default theme to ensure the body of a page is always at least 900px wide

* CAT-SOOP now exists as a proper Python package (thanks to Ike Chuang)

* Moved file locks to a subdirectory of `cs_data_root`

* Sessions are now stored in `cs_data_root/_sessions` instead of `cs_data_root/__SESSIONS__`

* Logs are now stored in `cs_data_root/_logs` instead of `cs_data_root/__LOGS__`

* Improved display of test case results for `pythoncode` questions

* Per-test-case sandbox options for `pythoncode` questions are now specified via `test['sandbox_options']`

* The run_code function for Python sandboxes now returns a dictionary, rather than a 3-tuple

* Changed the structure of JS web labels for LibreJS to make it clearer which parts of a page's Javascript are explicitly licensed under AGPLv3

**FIXED:**

* `js_files` now preserves the order of its arguments

* Fixed an issue with Microsoft Edge not accepting button presses

* Fixed an issue with the default handler's timer not properly synchronizing with the server's time

* Fixed an type issue related to `mpmath` objects in `numpy` arrays

* Fixed confusing results from `pythonic` question type by making sure that the submission constitutes a single Python expression

* Fixed a bug in the `pythonic` and `pythonliteral` question types so that answers with leading whitespace are allowed

* Fixed a bug whereby non-JSON-serializable objects in someone's `__USERS__` file would break the `get_user_information` API endpoint

* Fixed an issue with `expression` question types, whereby if all values were specified in `csq_names`, the question would use the specified values, likely `int`s or `float`s (instead of `mpmath.mpf`s) to represent them, occasionally causing correct answers to be marked as incorrect due to a loss of precision

* Fixed an issue with the Python sandbox's `sandbox_run_code` by making it respect `csq_sandbox_options`

* Fixed bugs with multiple functions in the `catsoop.check` module

* Fixed bug in `cs_ajax.js` related to submitting manual grades

* Fixed an issue with proper display of whitespace in `pythoncode` questions' inputs/outputs

* Fixed an issue that caused `'last_submit'` values in logs to be updated too soon (before checking to see if a submission was allowed)

* Fixed an issue that caused bare content files starting with `_` or `.` to be web-accessible

* Fixed the `'permissions'` field in `cs_user_info` to make sure it is always a `set`

* Fixed the 'Show/Hide Detailed Results' button in the `pythoncode` question type to have the same styling as other buttons

* Fixed a bug with `catsoop.modal` Javascript that caused an error if `cancel` was set to `false`

* Fixes for reporting line numbers in `<python>` tags

**DOCUMENTATION:**

* The CAT-SOOP web site is now included in the distribution, and includes a new page to automatically generate API documentation


# Version 13.0.0

**ADDED:**

* Added the `<tableofcontents/>` tag, which produces a table of contents for a page

* Added support for question types to have a `js_files` function that returns a list of Javsacript files that should be loaded before rendering the question

* The decimal precision of numbers in the `expression` question type can now be altered via the `csq_precision` variable

* Added the `multiexpression` question type for questions about multiple related expressions

* Made CAT-SOOP work properly with [LibreJS](https://www.gnu.org/software/librejs/)

* Added support for Python sandboxing via [bubblewrap](https://github.com/projectatomic/bubblewrap)

* The `cs_question_type_defaults` variable can be used to set default values of variables for specific question types

* The `catsoop.check` module is now available; it provides access to a small library of common check functions (to be used as `csq_check_function` or similar)

* CAT-SOOP can now optionally encrypt log entries; keys are specified via `cs_log_encryption_passphrase` and `cs_log_encryption_salt`

* CAT-SOOP can now optionally compress log entries by setting `cs_log_compression = True`

* Added support for Python 3.7

**CHANGED:**

* Upgraded [KaTeX](https://katex.org/) to v0.10.0-rc.1

* Updated [MathJax](https://www.mathjax.org/) to version 2.7.5

* Updated [highlight.js](https://highlightjs.org/) to version 9.12.0

* The location and format in which uploaded files are stored on disk has changed

* The URL format for static files has changed (from `__STATIC__` to `_static`)

* The URL format for utilities has changed (from `cs_util` to `_util`)

* `csq_threshold` and `csq_ratio_check` have been replaced with `csq_ratio_threshold` and `csq_absolute_threshold` in the `expression` question type; the more lenient of the two thresholds is used, and the default behavior is the same as before

**DEPRECATED:**

* The special directory name `__MEDIA__` has been renamed to `__STATIC__` to better reflect its purpose; `__MEDIA__` will be removed in a future version, so use `__STATIC__` instead

* The `catsoop.tools` library was renamed to `catsoop.thirdparty` to better reflect its contents; the `csm_tools` pointer to these libraries will be removed in a future version, so use `csm_thirdparty` instead

    * Many of the libraries themselves were also removed and so should now be imported directly, rather than accessed via `csm_thirdparty`

* `print` should now be used instead of `cs_print` to inject page content from within `<python>` tags; `cs_print` will be removed in a future version

* The `csq_multiplechoice_renderer` and `csq_multiplechoice_soln_mode` variables have been renamed to `csq_renderer` and `csq_soln_mode`; the old names still work but will be removed in a future version

**REMOVED:**

* Removed [jQuery](https://jquery.com/), [Bootstrap](https://getbootstrap.com/), and [SweetAlert2](https://sweetalert2.github.io/) (replaced with vanilla JS/CSS)

* Removed `cs_util/process_theme` and removed dependence on outside fonts

* Removed many bundled third-party applications in favor of installation via `pip`

* `cs_login_aes_key_location` has been removed; the `cs_log_encryption*` variables should be used instead

**FIXED:**

* Fixed a bug that assigned the wrong `qtype` variable to question types that inherit from other question types

* Fixed an issue with error reporting when trying to log a tuple that contains an element that can't be logged

* Fixed an issue that caused CAT-SOOP's main page to crash if a course with a malformed `preload.py` was present

* Removed some redundant calls to `cslog.most_recent` from the default handler to improve efficiency

* Fixed multiple instances of improper handling of questions with multiple boxes

* Fixed a bug related to improper handling of internal links with trailing slashes

* "Log In" and "Log Out" no longer discard the query string associated with the current page (thanks to Jeremy Wright)

* Fixed the `'check'` action so that it respects `csq_grading_mode` and checks to see whether checking is allowed before actually running the check

**SECURITY:**

* Prevent submissions from being able to access materials defined in `csq_code_pre` from `pythoncode` questions


# Version 12.1.1

FIXED:

* Fixed an issue with unintentional ["broadcasting"](https://numpy.org/doc/stable/user/basics.broadcasting.html) of `numpy` arrays in certain `expression` questions

* Fixed an issue that prevented `datetime` and `timedelta` objects from being logged


# Version 12.1.0

**ADDED:**

* Added questions' types and grading modes to the `question_info` cache

* `datetime` and `timedelta` objects (from the [`datetime`](https://docs.python.org/3/library/datetime.html) module) are now allowed in log entries

**CHANGED:**

* The automatic source code download no longer saves cached copies, to avoid accidentally filling small disks

* Upgraded [KaTeX](https://katex.org/) to v0.9.0

* Upgraded [SweetAlert2](https://sweetalert2.github.io/) to version 7.15.1

* Upgraded [MathJax](https://www.mathjax.org/) to version 2.7.3

* Upgraded [PLY](https://www.dabeaz.com/ply/) to version 3.11

**REMOVED:**

* `'questions'` is no longer a valid key `for tutor.compute_page_stats`, as it is redundant with `'question_info'`

**FIXED:**

* Fixed an issue where invalid question names were failing silently

* Prevented scroll bars from showing up in the CAT-SOOP logo at the bottom of the page

* The `question_info` cache is now checked/updated after the `pre_handle` plugin is executed, rather than after

* `expression` questions now support implicit multiplication by `j` (the imaginary unit)

* Fixed an issue that caused scores in the `problemstate` log to be overwritten with `None` when the "check" button was used

* Entering an empty expression and entering an invalid expression to a `pythonic` question now produce the same error message

* Fixed a bug where API token was not being properly set when impersonating a user

* In the `default` handler, ensure `handle_check` creates all `problemstate` fields if they don't already exist

* The checker script is now aware of the `cs_now` variable

* Fixed an issue that caused a misleading error message when the remote Python sandbox couldn't be reached

* Fixed a misleading error message about how to install [`jose`](https://pypi.org/project/python-jose/) when using the `openid_connect` authentication type

* Fixed a broken link after an error message when using the `openid_connect` authentication type

**SECURITY:**

* Prevented `as_role` from affecting the `'role'` field in `cs_user_info` if the user does not have the `'impersonate'` permission


# Version 12.0.0

**ADDED:**

* Added a cache of question information, to avoid having to fake a page load to get question information in `tutor.compute_page_stats`

**CHANGED:**

* CAT-SOOP can optionally be configured to use uWSGI, and the options for configuring the WSGI server have changed

* Logs are now stored in plain-text files, as opposed to binary log file

* Page views are no longer logged in the `problemactions` log

* Upgraded [KaTeX](https://katex.org/) to v0.9.0-beta1

* `'question_points'` is no longer a valid key in `tutor.compute_page_stats`; `'question_info'` should be used instead

**FIXED:**

* Fixed a bug with rendering of scores when manual grades are submitted


# Version 11.1.2

**ADDED:**

* Added "Log In" / "Log Out" to top menu by default, and gave authentication types the ability to populate that menu

**CHANGED:**

* Separated WSGI server into separate process, and allow `cs_wsgi_server_port` to be a list to start multiple servers (for load balancing)

* Updated `wsgi.py` so that it can be used by an external WSGI server (such as uWSGI)

* `csq_nosubmit_message` is now sent only on an actual submission (not when viewing the page), so that the submit button still appears when loading pages with `cs_nosubmit_message` set

* Buttons are now always created under `'view'` mode in the `default` handler

* `cs_nosubmit_message` was replaced with `csq_nosubmit_message` (specific to each question)

**FIXED:**

* Fixed an issue where checker results were stored in an invalid location in the case of some errors

* Fixed an issue with the checker updating scores for problems that don't yet have a `problemstate` log

* Fixed key generation for AES encryption in `login` authentication mode

* Fixed a bug with changing password in `login` authentication mode

* Fixed a bug with client-side password hashing so that the hash is now a proper PBKDF2 hash of the given password

* The `'last_submit_time'` and `'last_submit_times'` entries in the `problemstate` log are now only updated if the submission was successful

* Fixed a bug whereby some compound expressions were treated as literals in the `pythonliteral` question type

* Fixed a bug with rendering of `<` and `>` in the `richtext` question type

* Fixed an issue with empty `<python>` tags

* Fixed a broken link in the OpenID Connect login page


# Version 11.1.1

**ADDED:**

* Added the `'legacy'` grading mode, which does not use the asynchronous checker

**CHANGED:**

* Separated checker results into subdirectories to prevent a single directory growing too large

* Helper scripts are now launched using `sys.executable` rather than a hard-coded `python3`

* Checks run through the asynchronous checker now cache their results in the `problemstate` directory to avoid having to do a double-lookup

* Attempts at improved error reporting throughout CAT-SOOP

**REMOVED:**

* Removed the `PKiller` class, which is no longer used anywhere

**FIXED:**

* Temporary workaround for automatic scrolling to location of anchor

* Fixed a bug with username/password-based access to the `get_user_information` API endpoint

* Fixed a bug with the names of uploaded files

**SECURITY:**

* The current session ID and API token are now filtered from error messages

**DOCUMENTATION:**

* Added (hopefully) meaningful docstrings to almost everything in the codebase


# Version 11.1.0

**ADDED:**

* Added [cheroot](https://github.com/cherrypy/cheroot) as a `catsoop.tools` package

* Added [websockets](https://github.com/aaugustin/websockets) as a `catsoop.tools` package

**CHANGED:**

* cheroot is now used instead of uWSGI

* File names for uploaded files now include the `csq_name` of the question they were uploaded for

**FIXED:**

* Fixed an issue whereby the Python sandbox could leave handles to deleted files open (eventually leading to an error from having too many files open)

* Changed the Python sandbox to use `sys.executable` (instead of hard-coded path to an assumed location of a Python interpreter) when `csq_python_interpreter` is not set

**SECURITY:**

* File names for uploaded files now include a hash of their contents to limit the feasibility of a brute-force attack to grab a different user's files


# Version 11.0.5

**ADDED:**

* Added the `get_upload` utility for downloading uploaded files

* Added `'extra_data'` field to checker results

* Added `tutor.read_checker_result` helper for reading checker results

* Added `csq_npoints` as an option to the `pythoncode` question type; if specified, it overrides any point values assigned to the individual test cases

**CHANGED:**

* Changed the default checker used for multiple-choice-multiple-answer problems

* The `fileupload` question type now uses `get_upload` to download user files, rather than a data URI

* Made changes to make sure that files are always closed after being opened

**FIXED:**

* Fixed a potential race condition in the `pythoncode` question type

* Fixed an issue with the `expression` question type, where overzealous type checking led to some correct answers being marked as incorrect

* Fixed issues with the circuit simulator question type that prevented an AC analysis from being run interactively, causing incorrect AC results to be sent to the checker

* Changes to make sure that reasonable fonts are used (particularly in `<pre>`, `<code>`, and `<tt>`) even if our fonts are not loaded

* Some small temporary fixes to AC analysis in the circuit simulator for the `circuit` question type

**SECURITY:**

* Fixed an issue whereby `get_upload` could be used to read arbitrary files from disk via a carefully constructed request (thanks to Max Justicz for reporting)


# Version 11.0.4

**FIXED:**

* Fixed an issue with matrix comparison in `expression` question type

* Fixed a typo in `handout` handler


# Version 11.0.3

**FIXED:**

 * Use <https://github.com/aaugustin/websockets> for websocket connections

**REMOVED:**

* Removed the included simple websockets implementation

* Remove more traces of the abandoned queue


# Version 11.0.2

**FIXED:**

* Moving a file from running to `results` in the checker is now implemented as an atomic operation, to avoid the potential for corrupted results files


# Version 11.0.1

**FIXED:**

* Changes to the way the reporter process handles websocket connections


# Version 11.0.0

**ADDED:**

* Added script to migrate SQLite logs (and checker) to new format

**CHANGED:**

* Logs are now, once again, stored in catsoopdb format; no other options

* The checker's state is now stored via the filesystem, rather than through SQLite

* File upload paths are now stored relative to `cs_data_root` to make moving between systems easier; old (absolute) paths still work, but the system will now store relative paths

* Results from completed checks are now loaded in a way that avoids requiring a websocket connection

* The checker and reporter are now two separate processes

**FIXED:**

* Fixed serious bug (deadlock) with checker script / logging

* Fixed HTML rendering of `pythoncode` question type


# Version 10.4.0

**ADDED:**

* Added a means of viewing a page with different (lower) permissions by spoofing your role (the `as_role` query string argument)

* Added a `dummy` auth type to make authentication on local testing setups easier

* Added preliminary support for running on MacOS and Windows (Cygwin) hosts by fixing a number of Mac-specific issues

* The score display can now be changed on a per-problem basis via `csq_score_message`

**CHANGED:**

* `pycs`-compiled files are now stored in `<cs_data_root>/_cached` to avoid polluting the course itself

* The body of the CAT-SOOP default template is now slightly wider

* Local Python sandboxes now write their stdout and stderr to files instead of relying on low-level hacks involving pipes

* Upgraded [KaTeX](https://katex.org/) to v0.8.2

* Updated [Python-Markdown](https://python-markdown.github.io/) to version 2.6.9

* The magic variable controlling the checker's location is now `cs_checker_websocket` instead of `cs_websocket_location` (which is now ambiguous)

* Added more options to modify the styling of the "login required" page

* Cross/check images are now preceded by a newline

**DEPRECATED:**

* `cs_score_message` has been deprecated in favor of `csq_score_message`; `cs_score_message` will be removed in a future version

**REMOVED:**

* Removed lots of unused imports, unused local variables, etc, thanks to pyflakes

**FIXED:**

* Fixed a race condition related to clearing expired session data

* Fixed serious bug (deadlock) with checker script / logging

* Modified the way `PKiller` kills processes to avoid a potential race condition

* Fixed several breaking issues with the grouping mechanism related to the version 10 changes

* Fixed a bug that prevented WHDW from loading students' scores

* Fixed a bug that caused some `<showhide>` tags' buttons to affect other `<showhide>` elements on the page instead of themselves

* Fixed an issue with error reporting in the `openid_connect` auth type

* Fixed an issue with the `login` authentication type that caused false negatives when checking passwords from different browsers

* Fixed an issue with broken loading of uploaded files from the database

* Fixed an issue that caused an error message not to be shown when `cs_form` was not defined

* Replaced a lingering instance of `xrange`

* Questions with the `checkoff` question type now render as totally empty if the description and name are empty, rather than as a single colon

**SECURITY:**

* `nohup.out` files are now ignored when generating the `.zip` files of the CAT-SOOP source


# Version 10.3.0

**CHANGED:**

* Moved all logs to one central location to make backups easier


# Version 10.2.2

**REMOVED:**

* Removed several calls to the deprecated `cs_print` from the default "main" page

* Removed "Acknowledgments" section from the default "main" page

**FIXED:**

* Removed an extraneous `print` statement from the `default` handler

* Remove HTML formatting from course name in `source.zip` downloads


# Version 10.2.1

**CHANGED:**

* Prevented the creation of extra directories when reading nonexistent logs

**REMOVED:**

* Removed the defunct `checker_reporter.js` script

**FIXED:**

* Fixed a number of issues with sessions

* Fixed an issue with serializing Python `set`s for logging


# Version 10.2.0

**ADDED:**

* Added more options to modify the styling of the "login required" box

**CHANGED:**

* Submission  IDs are no longer visible by default, though they can be made visible with `cs_show_submission_id`

* Logs once again use SQLite instead of RethinkDB

**REMOVED:**

* Removed RethinkDB completely

**FIXED:**

* Updated the location of the default `remote` sandbox


# Version 10.1.0

**ADDED:**

* `cs_user_info` and `cs_username` are now always defined, even on pages that don't require authentication

**CHANGED:**

* The built-in `print` function can now be used instead of `cs_print` to inject page content from within `<python>` tags

**DEPRECATED:**

* `print` should now be used instead of `cs_print` to inject page content from within `<python>` tags; `cs_print` will be removed in a future version

**FIXED:**

* Fixed issue with clearing session data

* Fixed an issue with question types' `init` functions being called with incorrect arguments


# Version 10.0.1

**CHANGED:**

* RethinkDB is now used to store session data, as opposed to the file-based storage used in the past

* Slight changes to the way version numbers are displayed in the default template

**FIXED:**

* Fixed multiple large issues with manually-graded submissions

* Fixed multiple large issues with the `fileupload` question type


# Version 10.0.0

**ADDED:**

* Added the dot product operator to `expression` question type

* Added `process.py`, containing some common operations relating to process management

* Added support for storing uploaded files on disk rather than in the database directly

**CHANGED:**

* RethinkDB is now a hard dependency

* The API for logging functions was changed, to avoid a special character as a separator

* Submissions are now handled asynchronously, and results are retrieved via web sockets

* Markdown no longer outputs `<em>` or `<strong>`, preferring `<i>` and `<b>` to improve browser compatibility

* Many images are now included in pages as data URI's rather than being loaded from a separate request

* Changed the password hashing scheme for the login authentication type to one based on <https://blogs.dropbox.com/tech/2016/09/how-dropbox-securely-stores-your-passwords/>

* Re-styled buttons throughout the system

**REMOVED:**

* Removed CSS-only spinner, replaced with data URI for image in the base context

* Removed images for check/cross/favicon, replaced with data URI's in the base context

* Removed SQLite and catsoopdb as backends for logging

**FIXED:**

* Improved the Javascript code responsible for making sure the top menu doesn't block text when moving around a page

* Errors in the registration form now prevent submitting the form


# Version 9.4.3

**ADDED:**

* Added the `circuit` question type

* Added support for nonscalar values in `expression` questions

**FIXED:**

* Changed exponentiation to be right-associative in the `expression` question type

* Fixed a bug with rendering implicit multiplication in `expression` questions

* Fixed a bug with rendering of chained exponentiation in `expression` questions

* Fixed a bug with order of operations when using the Python syntax in `expression` questions


# Version 9.4.2

**ADDED:**

* Added the `<section*>` family of tags, for unnumbered sections

* Added the `<include>` tag, to include the contents of another file

* Added the ability to add an additional message to the default page via `cs_main_page_text`

**FIXED:**

* Fixed an issue whereby expressions utilizing binary subtraction were not properly parenthesized in the "Check Syntax" rendering of `expression` questions


# Version 9.4.1

**FIXED:**

* Fixed an issue with rendering of certain test cases in the `pythoncode` question type

* Modified the handling of streams in the Python sandbox to avoid buffers filling up

* Modified error message handling in the Python sandbox to avoid long-running regex searches


# Version 9.4.0

**ADDED:**

* Added support for custom "submissions not allowed" messages via `cs_nosubmit_message`

* Added the `cs_now` variable to page load contexts

* Added the `'code_pre'` option to tests in the `pythoncode` question type, for code to be run before submitted code

**CHANGED:**

* Code is now licensed under the [GNU Affero General Public License, v3+](https://www.gnu.org/licenses/agpl-3.0.html), and the footer text has been updated to reflect this change

* `cs_nsubmits_message` was replaced by `csq_nsubmits_message`

* Updated [MathJax](https://www.mathjax.org/) to version 2.7.1, and updated it to use a future-proof renderer

* Updated [PLY](https://www.dabeaz.com/ply/) to version 3.10

* Updated [Python-Markdown](https://python-markdown.github.io/) to version 2.6.8

* Updated [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) to version 4.6.0

* Fixed several issues with rendering of `pythoncode` question types

* Updated the "Formatting Help" page of the `richtext` question type

**REMOVED:**

* Removed large pieces of the default MathJax install because they will not be used

**FIXED:**

* Fixed broken "home" link for pages in the `cs_util` "pseudo-course"

* Fixed issue with HTML tags not rendering inside of `<section>` tags

* Fixed error messages for expressions that can't be parsed in the `expression` question type

* Fixed a crash when the `<cs_data_root>/courses` directory did not exist or was not writeable by the web server

* Fixed a bug with HTML tags being ignored inside `<ref>` tags


# Version 9.3.0

**ADDED:**

* `default` handler now logs scores of all questions in the `problemactions` log during `'submit'` actions

* Added the `csq_always_show_tests` option to `pythoncode` questions, to enable/disable the "Show/Hide Detailed Results" button

* New plugin infrastructure

* `catsoop.ajaxrequest` now accepts a callback function that can be executed once the request has completed

* More options for rendering pages (`'content_only'` and `'raw_html'`)

**CHANGED:**

* Code is now released under version 2 of the Soopycat License

* Math expressions are now rerendered in all responses to AJAX calls

* Updated [KaTeX](https://katex.org/) to v0.7.0

* Updated [MathJax](https://www.mathjax.org/) to version 2.7.0

* Python syntax highlighting updated

* Several improvements to WHDW and stats displays (thanks to Jeremy Kaplan)

**REMOVED:**

* Errors related to evaluating the expression are no longer displayed in the `pythonic` question type

**FIXED:**

* Allowed `pythonic` question type to accept tuples without parentheses

* Fixed issue with `expression` question type that causes errors with `csq_ratio_check = True` when `csq_soln == 0`

* Switched to different CDN for loading Ace editor code

* Fixed an issue related to automatic locking when no answers have been viewed

* Fixed a regression related to rendering the answers to `multiplechoice` questions using the `'checkbox'` renderer

* Fixed a regression related to answer checking in `multiplechoice` questions

* Fixed issue related to handling empty `<python>` or `<question>` tags

* Fixed issue related to incorrectly filtering user information when generating API tokens

* Fixed issues with type errors from decoding data URI's in the `pythoncode` and `fileupload` question types

* Fixed several issues related to invalid HTML output in response to `pythoncode` submission

* Fixed `source.zip` generation to be more pedantic about when to re-build the file

* Fixed rendering of questions via `'rerender'` in the default handler

* Fixed problem with trying to render a template from a context where not all variables are defined

* Fixed rendering of check/cross images in `expression` question type

* Manual grading interface now displays more relevant feedback to the grader after submission (exactly the score and comments as the student will see them)

* Fixed the display of answers to `pythoncode` questions so that syntax highlights properly

* Fixed issue with processes not being properly closed with the Python sandbox

**SECURITY:**

* Fixed a regression that opened a XSS vulnerability in `pythoncode` questions

**DOCUMENTATION:**

* Use American spellings in documentation


# Version 9.2.0

**ADDED:**

* Added `render_single_question` to the default handler, for rendering a single question's contents

* Added ability to customize how e-mail address is created from available information when using OpenID Connect

* Added the ability to override `get_group`'s section lookup and instead use the specified section

* Added `'stats'` and `'whdw'` (Who Has Done What) actions to the default handler

**CHANGED:**

* Better checks and display for `checkoff` question type

* Improved error handling in the `pythonic` question type

* Improved the formatting of HTML in the `pythoncode` question type to prevent BeautifulSoup from modifying it too much

* `None` is now a special category that is skipped when assigning groups

* Improved formatting of answers to `pythoncode` questions

* Cells in HTML tables are no longer automatically center-aligned

* Removed confusing answer display from `checkoff` question type

**FIXED:**

* Fixed a bug with `cs_path_info` not being defined in certain situations

* Fixed the stylesheet so that pages can be printed again

* Fixed a bug with reporting error messages related to malformed questions

* Fixed a type error in `list_groups` that prevented students' sections from being determined correctly

* Brought the `richtext` question type up to speed with current CAT-SOOP

* Brought the `multiplechoice` question type up to speed with current CAT-SOOP

* Brought the `handout` handler up to speed with current CAT-SOOP and improved its error reporting

* Fixed a regression that rendered `pythonliteral` questions unusable

* Fixed a typo in `dispatch` that broke proper 404 handling of `handout`

* Fixed a regression with the permissions check for the "Save" button

* Several fixes for the `fileupload`, `richtext`, and `pythoncode` question types

* Prevented a misleading error message from being displayed when automatically viewing answers on a timed exercise

* Several fixes for `catsoop.tools.data_uri`

* Fixed a bug that prevented per-user randomness from functioning as expected

* Updated automatic source downloader to use `spoof_early_load`, fixing a bug

* Fixed a typo in the `checkoff` question type


# Version 9.1.0

**ADDED:**

* Added `catsoop.path_info` to javascript (for groups)

* Added `cs_pre_handle` for normal use and `pre_handle.py` for plugins as another place to inject custom behavior during page loads

* The state of the context is now stored after every `preload.py` file in the chain has been executed (in `cs_loader_states`), to allow, e.g., looking up parents' names

* Added "breadcrumbs" to the default theme

* Fleshed out the interactive group management page

**CHANGED:**

* Navigational menu entries can now optionally be specified in a more straightforward (Pythonic) manner

* `csq_names` are now automatically assigned as part of the XML parsing step, rather than in the default handler

* Changed "Are you sure you want to view the answer" dialog to use [SweetAlert2](https://limonte.github.io/sweetalert2/)

* Nicer-looking tables in default theme

* Added a more complete message to the "log in" box for OpenID Connect

**FIXED:**

* Fixed bug with `cs_view_without_auth` flag

* Fixed bug with listing groups

* Fixed bug with file locking stemming from a change in 9.0.0

* `cs_post_load` and plugins' post-load hooks now fire at the right time (after `<python>` tags are evaluated)

* Fixed bug with additional files in the Python sandbox

* Fixed several bugs related to HTML parsing/display

* Internal Server Errors in AJAX callbacks now display an error message

* Fixed a bug that prevented saving entries to questions

* Fixed a bug that prevented reading user information from the `__USERS__` directory from `catsoop.util.read_user_file`

**SECURITY:**

* Logins are no longer carried over between courses (user must log in to each course separately)


# Version 9.0.0

**ADDED:**

* Added back the catsoopdb format (last seen in version 4.0.1), with improvements to prevent collisions and a few bugfixes

* Added [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) to the distribution

* Included [Bootstrap](http://getbootstrap.com/) in the distribution and updated the default theme to use it (also moved `main.template` and `base.css` to `old.template` and `old.css`, respectively, to make room for new style)

* Added the `cs_base_color` variable, for switching the main color of the default theme

* Added syntax highlighting to code blocks, via [highlight.js](https://highlightjs.org/)

    * If no language is explicitly specified for syntax highlighting, the value stored in `cs_default_code_language` will be used (default is no syntax highlighting; explicitly setting that value to `None` will cause highlight.js to guess the appropriate language for each block)

* Added support for authentication via [OpenID Connect](http://openid.net/connect/)

* Added support for default courses via `cs_default_course`

* Added the `list_questions` and `get_state` API endpoints to the default handler

* Added an easier way to spoof context loading with `loader.spoof_early_load`

* Added `cslog.modify_most_recent`, which updates the most recent log entry atomically

* Added method for sending e-mail to a CAT-SOOP user from the API without knowing their e-mail address

* Added support for input checks and ratio checking (rather than absolute error checking) to the `expression` question type

* Added `number` question type for single numbers (or simple fractions)

* Added `__PLUGINS__` directory for plugins which work in ways other than defining a new question type or handler (ability to affect the context before or after preload, before or after content load, and after handler is invoked)

**CHANGED:**

* CAT-SOOP is now only compatible with Python version 3.5+

    * Python 2 compatibility was dropped intentionally, but versions 3.0.0 <= x < 3.5 are not supported because CAT-SOOP does some strange things with imports

* CAT-SOOP no longer runs on Windows hosts

* Drastically improved inheritance for question types (requiring far less manual work) via `tutor.qtype_inherit`

* CAT-SOOP XML parsing is now largely handled by BeautifulSoup instead of by regular expressions

* Renamed `gb.py` -> `base_context.py` to more accurately reflect its usage

* Modified the `'login'` authentication type to use Python's new built-in implementation of PBKDF2

* Changed the way authentication is handled in AJAX requests, in preparation for including the public-facing API

* Themes are now run through a pre-processor that handles `<python>` and `<printf>` tags (including `@{...}` syntax)

* Passwords (in all forms) are now hashed both before and after being sent to the server (passwords are now never sent in plain-text)

* Navigation links should now be held in `cs_top_menu` instead of `cs_navigation`

* `<ref>` tags can now take the relevant label as `label="x"` in addition to just as `x`

* Improved error pages shown on 404 File Not Found

* Default permissions now include the `'view'` permission

* Modified the default "loading" spinner to use CSS instead of an image

* `csq_check_function` can now return a dictionary mapping `'score'` to the score and `'msg'` to a message to be returned, eliminating the need for `csq_msg_function` when it is more convenent to compute the score and message at the same time; alternatively, it can return a tuple `(score, message)`

* `csq_msg_function`, if used, can now optionally take a second argument representing the solution (the message doe not need to be computed from the submission alone)

* Replaced `"response"` field with `"message"` in JSON returned by the default handler's AJAX calls, to avoid duplicate use of `"response"`

* Easter Egg: the CAT-SOOP cat in the footer changes slightly when displaying a 404 or 500 error message

* Improved error reporting in `pythonic` question type

**FIXED:**

* Tracebacks in CAT-SOOP error messages now actually show useful information

* Pre-compiled CAT-SOOP (`.pycs`) files' names now include the Python implementation's cache tag, so that the same course can be migrated to a CAT-SOOP instance running on a different version of Python without issue

* Fixed a bug whereby an empty entry in a multiplechoice question (`--`) was interpreted as being the last element in the `csq_options` list and so could be marked as a correct answer

* Missing files/directories are now always handled as 404 errors, rather than 500

* Fixed a bug resulting from a nonexistent `courses` directory

* The `cs_post_load` hook is now invoked at a time when `cs_content` is still relevant

* Fixed bug with `expression` question type erroring when using multiple values for a variable

* Prevented PLY from writing its parsing tables to disk

**SECURITY:**

* Included the option to tune the number of iterations used with PBKDF2, and increased the default number of iterations from 50,000 to 250,000

* Minimum password length in the login authentication type is now 8 instead of 5, per the NIST recommendation at <https://pages.nist.gov/800-63-3/sp800-63b.html>


# Version 8.0.0

**ADDED:**

* `<label>` and `<ref>` tags are now available for easier referencing of sections within a CAT-SOOP page

* Answers and explanations can now be automatically viewed in certain situations (running out of submissions, earning 100% score)

* Added a check for non-ASCII characters in input, and an error message to be displayed in this case

* Most CAT-SOOP options related to the default handler can now be specified as functions that return the appropriate value, rather than the value itself, which allows them to be set in a way that depends on the current context

* Added a way to compute stats about a particular page (for use in making gradebooks)

* Question types can now have multiple form fields by having names starting with `__QNAME__`, where `QNAME` is the name of the question

* The `multiplechoice` question type has two new modes which allow for arbitrary formatting (including math) in the options: `'checkbox'`, which allows multiple answers to be selected; and `'radio'`, which allows only one answer to be selected

* Added the `cs_debug` function, which can be used to log arbitrary information to a file during execution of a preload or content file

* Resources can now be loaded from arbitrarily-named files (e.g., `<root>/path/to/foo.md` instead of `<root>/path/to/foo/content.md`)

* In the `pythoncode` question type, it is now possible to hide the code associated with test cases

* Added `data_uri` module from <https://gist.github.com/zacharyvoase/5538178> for better handling of file uploads

* Users can now log in with their e-mail addresses instead of their usernames when using the `'login'` authentication type

* Permissions can now be specified directly via `cs_permissions`, instead of exclusively via roles

* The `pythoncode` question type can now handle Python 3 code

* Handlers and question types can now have viewable pages inside them, viewable at, for example, `<url_root>/__HANDLER__/default/page_name`

* Every page footer now links to both the terms of the license, and also to the "download source" link

* Added a module for sending e-mails, primarily for use in the `'login'` authentication type

* [MathJax](https://www.mathjax.org/) is now served directly, rather than loaded from their CDN

**CHANGED:**

* Functions inside of question types no longer need to manually load default values; values from the defaults variable are automatically used when not
    specified inside the `<question>` tag

* The `'login'` authentication type was much improved, including the option to send confirmation e-mails, change passwords, and recover lost passwords; and to customize the types of e-mail addresses that are accepted

* Improved error reporting in the `'login'` auth type

* The `cs_post_load` hook now executes before the page's handler is invoked, and a new hook `cs_post_handle` was introduced, which is called after the handler is invoked

* CAT-SOOP's handling of HTML tags is now case-insensitive

* The "view as" page was updated to show more accurately what the user in question would see

* Many options related to the `default` handler (primarily related to which actions should be allowed) are now specified on a per-question basis rather than a per-page basis

* Locking a user out of a problem has been separated from viewing the answer to that question

* Improved rendering in the `expression` question type

* `name_map` is now stored as an ordered dictionary

* Results from the `pythonic` question type are now evaluated in the question's scope, rather than in the question type's scope

* The number of rows to be displayed in the ACE interface for coding questions is now customizable

* Answers in the `smallbox` and `bigbox` question types are no longer wrapped in `<tt></tt>`

* Markdown and/or custom XML, depending on the source type used, is now interpreted inside of answers and explanations (including math rendering)

* All CAT-SOOP modules are now available inside of the source files for handlers and question types

* The `cs_scripts` string is now injected into the template after jQuery, KaTeX, MathJax, and `cs_math` have been loaded

* Modified the generation of per-user random seeds to (eventually) allow for re-generating of random seeds

* Moved much of the Javascript code from the default handler to separate files

* Moved WSGI file and changed the way imports are handled in order to make sure everything can access the CAT-SOOP modules/subpackages

* Moved handling of `csq_prompt` out of individual question types and into the default handler to avoid duplicating code

* Removed logo image from main page

* `cs_source_format` is now inferred (rather than specified explicitly)

* In question type specifications, `handle_submission` now returns a dictionary instead of a tuple

* Restructured authentication types to make adding more types in the future easier

* Section labels are now rendered as id's of the associated headers

**FIXED:**

* Fixed a bug whereby `$` characters could not be escaped with backslash

* Fixed issues with certain tags' internals being parsed as Markdown (`<script>`, `<pre>`, `<question>`, etc)

* Trying to access a resource that doesn't exist on disk now gives a 404 error instead of crashing

* Fixed several bugs related to uploading multiple files in a single submission

* Spaces are now allowed in question names

* CAT-SOOP no longer crashes on a malformed `<question>`, but rather displays an error message

* Fixed an issue with intermittent WSGI failures by re-trying failed actions

* Updated [MathJax](https://www.mathjax.org/) to version 2.6.1 to fix a rendering issue in Chrome

* Updated the URL of the default Python sandbox to reflect changes in the CAT-SOOP web site

* Improved handling of query strings and fragment identifiers when rewriting URLs

* Improved handling of implicit multiplication in the `expression` question type

* Added unary `+` to Python syntax in the `expression` question type

* `cslog.most_recent` now returns the default value when the log file does not exist, instead of crashing

* Fixed handling of temporary files on Windows hosts

* Fixed validation of user information when registering under the `'login'` authenatication type

* Fixed several bugs with manual grading, reported from 6.02

* Log files are no longer created when trying to read from a nonexistent log

* Mercurial temporary files (`.orig`) are now ignored in the zip generated when downloading the source

* `<pre>` tags are now used instead of `<tt>` for wrapping answers in the `pythoncode` question type

* Fixed an issue in the `pythoncode` sanboxes whereby a `MEMORY` limit of 0 actually allowed 0 bytes of heap storage, rather than unlimited

* Prevent a crash if `<cs_data_root>/courses` does not exist

* Modified to always use the local `markdown` package even if one is installed globally, to make sure Markdown extensions are loaded properly

* Buttons are now re-enabled on page load, to prevent an issue whereby buttons would remain disabled after a refresh on Firefox

**SECURITY:**

* [PBKDF2](https://en.wikipedia.org/wiki/PBKDF2) is now used for password hashing in the `'login'` authentication mode

* Closed a XSS vulnerability in the `pythoncode` question type

* Closed a security hole in session handling that allowed for arbitrary code execution under certain circumstances by validating session ids and modifying the way session data are stored

* Logs can no longer be accessed/created outside of the appropriate `__LOGS__` directories


# Version 7.1.1

**FIXED:**

* Fixed an issue that prevented the last question on each page from being displayed


# Version 7.1.0

**ADDED:**

* Added the option to grade questions manually, from 6.02 fall 2015

* Added a `richtext` question type, which allows for formatting of text using CAT-SOOP-flavored Markdown

* Added the `fileupload` question type, which allows users to upload arbitrary files

* Added checks for valid configuration options

**CHANGED:**

* Rewrote the `expression` question type to use [PLY](https://ply.readthedocs.io) for parsing, and included a default syntax for expressions that is more approachable to users not familiar with Python


# Version 7.0.1

**FIXED:**

* Fixed a syntax error in the `expression` question type


# Version 7.0.0

**ADDED:**

* Included [KaTeX](https://khan.github.io/KaTeX/)

* Added three new handlers:

    * `passthrough` displays `cs_content` without modification

    * `raw_response`, which allows sending a raw HTTP response

    * `redirect` redirects to other locations

* Added support for [Markdown](https://daringfireball.net/projects/markdown/) as an alternative source format and included [Python-Markdown](https://pypi.python.org/pypi/Markdown) in the distribution

* Question type specifications can now include an arbitrary action (beyond saving/submitting) that will be executed when a user presses a new button

* Added support for streaming content (via returning a generator instead of a string) and for automatic streaming of large static files

* Added support for inline (runnable by users) test cases in `pythoncode` question types

* Added `cs_util` resources:

    * `time`  gives the current time (according to the server) for synchronization purposes

    * `source.zip` gives a zip archive containing the CAT-SOOP source code

    * `license` gives the text of CAT-SOOP's license

* Added a `'string'` mode to the pythonic question type, which allows the answer to be specified as a string to be evaluated

* Added the `csq_code_pre` variable to this question type, for setting up the environment into which `csq_soln` will be evaluated in string mode

**CHANGED:**

* Math rendering now uses [KaTeX](https://katex.org) (fast, but limited support) when possible and falls back to [MathJax](https://www.mathjax.org) (slow, but more support) when necessary

* "Special" CAT-SOOP variables are now prefixed with `cs_` (for page-specific values) or `csq_` (for question-specific values) to prevent accidental shadowing

* Changed nomenclature: "activity types" are now "handlers"

* Complete rewrite of `default` handler

* Reorganization of sandboxing for Python code

* `gb.py` should no longer be changed; rather, global configuration values should be overwritten via `config.py` (which is loaded into `gb.py`)

* Improved handling of footnotes

**REMOVED:**

* Removed `jquery_typing` plugin, which is no longer needed for `expression` questions

**FIXED:**

* Fixed bug with newline handling in CGI interface

* Fixed bugs related to static files when using the CGI interface running on Windows hosts

* The `default` theme now handles resizing of the containing window more smoothly


# Version 6.0.0

**ADDED:**

* Added `post_load` hook, which is executed after the content file is executed

* Added support for XML as an additional source format, and set it to be the default format

* Change names: `EARLY_LOAD.py` is now `preload.py` and `LATE_LOAD.py` is now `content.xml`

* Added the `pythonliteral` question type, which behaves much like `pythonic` but requires that the submission be a literal value (rather than the result of a more complicated expression)

**CHANGED:**

* Modified handling of footnotes

* File containing user information should now end in .py (e.g., `username.py` instead of just `username`)

* Reorganized python question types to properly inherit from one another to avoid duplicate code

**REMOVED:**

* The `problem` activity type was removed, in favor of `ajaxproblem`

**FIXED:**

* Fixed an issue where `last_submit` was keeping information only about the most recent submission overall, instead of the most recent submission for each question

* The `__LOGS__` directory will now be created if it does not exist, rather than crashing CAT-SOOP

**SECURITY:**

* Error messages now show less information, to avoid displaying sensitive information


# Version 5.0.0

**ADDED:**

* Added support for footnotes via `<footnote>`

* Added support for page organization via `<section>`, `<subsection>`, etc

* The ability to save and submit are now controllable via special variables in the `problem` activity type

* Added a warning message upon clicking the 'view solution' button to indicate that users will not be able to submit after doing so; also maintained the ability to bypass this check, for things like automatically submitting at the end of a timed exercise

* Added the `handout` activity type, which allows for showing a static file, but with access controls (releasing after a particular date, only viewable by particular role, etc)

* Added support for displaying explanations in addition to answers in particular question types

**CHANGED:**

* Logs are now stored in [SQLite](https://www.sqlite.org/) databases

* The logo in the main page is now displayed as text, rather than as an image

* Buttons in `ajaxproblem` question types are now disabled before processing the request, to avoid multiple identical submissions from mis-clicks

**REMOVED:**

* Removed catsoopdb format in favor of SQLite

**FIXED:**

* Renamed `logging.py` to `cslog.py` to prevent accidentically importing Python's built-in `logging` module

* Fixed rendering of math when viewing solution to an `expression` question

* Scores are now properly handled in the `ajaxproblem` activity type

* Fixed a bug with displaying the solution for `pythonic` question types whose solutions are tuples

* Fixed a bug with displaying the solution for `pythonic` question types whose solutions are strings

* Fixed a bug related to handling of dynamic pages in the `__BASE__` course

* Fixed numerous `ajaxproblem` bugs

* Improved detection of static files

**SECURITY:**

* Error messages no longer show information about the location of CAT-SOOP (or the course in question) on disk


# Version 4.0.1

**FIXED:**

* Fixed issue whereby a missing `EARLY_LOAD.py` would crash CAT-SOOP

* Fixed bug with caching of static files

* Fixed bug related to authenticating in `'login'` mode

**REMOVED:**

* Removed rendering time from `default` template


# Version 4.0.0

**ADDED:**

* Added the `ajaxproblem` activity type, which allows submitting individual questions without reloading the entire page and made `ajaxproblem` the default activity type

* Added support for skipping ahead or behind by weeks in relative timestrings, using `+` or `-` (e.g., M+:17:00 means _next_ Monday at 5pm)

* Solutions for individual students are now displayed when impersonating them

* Source for pages is now cached in a marshaled format, to prevent having to re-parse the source of pages that have not changed

* Added support for authenticating via login (username and password) rather than via client certificate

* Added support for per-user randomness (users see the same numbers upon returning to a page, but different users may see different numbers)

* Added documentation (via `epydoc`-compatible docstrings) throughout

* CAT-SOOP now asks the browser to use cached versions of static files where appropriate

* Allowed question types and activity types to be specified in the course rather than in the base system

**CHANGED:**

* Changed internal nomenclature: `meta` is now `context` everywhere to represent the context in which a page is rendered

**REMOVED:**

* Removed several references to `sicp-s2.mit.edu` in the code

**FIXED:**

* Fixed impersonation glitch whereby permissions were inherited from the impersonated user

* Fixed glaring bug with static file handling

* Fixed inheritance bug in the `pythonic` question type


# Version 3.1.0

**ADDED:**

* Added WSGI interface (and moved main function elsewhere so WSGI and CGI can share code)

* Questions are automatically given names if they were not explicitly given a name

* Question types and activity types are now pre-compiled to avoid having to re-parse them on every load


# Version 3.0.0

**ADDED:**

* `problem` activities now store due dates, to account for changes in due date after submitting

* Added support for the [ACE](https://ace.c9.io/) code editor in `pythoncode` questions

**CHANGED:**

* Separated loading from `METADATA.py` into `EARLY_LOAD.py` and `LATE_LOAD.py`;  `EARLY_LOAD` files are executed all the way down the source tree (for the sake of inheritance, as with `METADATA.py`), but only the `LATE_LOAD.py` associated with the leaf node is executed (to allow some code execution to be avoided when working down the tree)

* Moved/improved impersonation code

* Refactored logging code

* Refactored main control loop

**FIXED:**

* Better sandboxing of Python code

* Fixed an issue with `submitAs` control for questions with randomness

* Fixed handling of paths on Windows hosts

* Modified `expression` question type to be compatible with Python 2.6

* Several bug fixes in `pythoncode` question type

**SECURITY:**

* Prune out `'..'` and `'.'` from URLs to avoid escaping the CAT-SOOP tree


# Version 2.0.0

Complete re-write.  First version used in 6.01 (spring 2013).  First version with any similarity to the current code


# Version 1.0.0

The original version, used in 6.003 fall 2011, and described in <http://dspace.mit.edu/handle/1721.1/77086>.  This version has _very little_ in common with later versions
