```nohighlight
\
/    /\__/\
\__=(  o_O )=
(__________)
 |_ |_ |_ |_
```

[![Build Status](https://catsoop.mit.edu/jenkins/buildStatus/icon?job=catsoop%2Fcatsoop%2Fdev)](https://catsoop.mit.edu/jenkins/job/catsoop/job/catsoop/job/dev/)
[![PyPI: Latest Version](https://img.shields.io/pypi/v/catsoop.svg)](https://pypi.org/project/catsoop/)
[![License: AGPLv3+](https://img.shields.io/pypi/l/catsoop.svg)](https://catsoop.mit.edu/git/catsoop/catsoop/raw/branch/master/LICENSE)

## CAT-SOOP

* Web Site: <https://catsoop.mit.edu>
* IRC: `#catsoop` on OFTC (`irc.oftc.net`)
* Community Forum: <https://catsoop.mit.edu/community>
* Development Portal: <https://catsoop.mit.edu/git>


CAT-SOOP is a flexible, programmable learning management system originally
developed primarily for use in MIT's 6.01 (Introduction to Electrical
Engineering and Computer Science via Robotics).

CAT-SOOP is free/libre software, available under the terms of the GNU Affero
General Public License, version 3+.  Please note that the terms of this license
apply to the CAT-SOOP system itself, but not to any course material hosted on a
CAT-SOOP instance, unless explicitly stated otherwise.


### INSTALLING

To install, run:
```nohighlight
$ pip3 install catsoop
```

Or, from a clone of the repository, run:
```nohighlight
$ make install
```

To generate a config.py file, run:
```nohighlight
$ catsoop configure
```

If you are setting up a public-facing copy of CAT-SOOP (as opposed to a local
copy for debugging purposes), see the instructions at
<https://catsoop.mit.edu/website/docs/installing/server_configuration>

To start the server, run:
```nohighlight
$ catsoop start
```

To run all the unit tests:
```nohighlight
$ make test
```


### HACKING

See <https://catsoop.mit.edu/website/docs/contributing/hacking>


### INCLUDED SOFTWARE

CAT-SOOP incorporates pieces of third-party software.  Licensing information
for the original programs is available in the `LICENSE.included_software` file.
The CAT-SOOP distribution also includes several pieces of third-party software.
Licensing information for these programs is included in this distribution, in
the `LICENSE.bundled_software` file.
