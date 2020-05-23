cs_auth_required = False
cs_long_name = "CAT-SOOP Website"

TOR_STRING = lambda n: ("torsocks %s" % n) if "onion" in cs_url_root else n

cs_footer = """The content of this page is Copyright &copy; 2016-2020 by the CAT-SOOP Developers.<br/>
This content is licensed under the <a href="BASE/_util/license" target="_blank">GNU Affero General Public License, version 3</a>, as is CAT-SOOP itself.<br/>
The original form of this content is source code in the CAT-SOOP specification format.<br/>
The source code is available in the <code>website</code> directory of the Git repository at the following address:<br/>
<code>git://%s/catsoop.git</code>.<br/><hr width="300" style="background-color:#000000;border-color:#000000" />""" % (
    cs_url_root.split("/", 2)[2]
)
