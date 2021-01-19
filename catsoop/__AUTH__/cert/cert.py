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


def get_logged_in_user(context):
    # certificates-based login
    action = context["cs_form"].get("loginaction", None)
    session = context["cs_session_data"]

    logintype = context["csm_auth"].get_auth_type_by_name(context, "login")
    _get_base_url = logintype["_get_base_url"]

    # if the user is trying to log out, do that.
    if action == "logout":
        context["cs_session_data"] = {}
        return {"cs_reload": True}
    elif "username" in session:
        uname = session["username"]
        return {
            "username": uname,
            "name": session.get("name", uname),
            "email": session.get("email", uname),
        }
    elif action is None:
        if context.get("cs_view_without_auth", True):
            old_postload = context.get("cs_post_load", None)

            def new_postload(context):
                if old_postload is not None:
                    old_postload(context)
                if "cs_login_box" in context:
                    lbox = context["cs_login_box"](context)

                else:
                    lbox = LOGIN_BOX % (_get_base_url(context),)
                context["cs_content"] = "%s\n\n%s" % (lbox, context["cs_content"])

            context["cs_post_load"] = new_postload
            return {}
        else:
            context["cs_handler"] = "passthrough"
            context["cs_content_header"] = "Please Log In"
            if "cs_login_page" in context:
                context["cs_content"] = context["cs_login_page"](context)
            else:
                context["cs_content"] = LOGIN_PAGE % (_get_base_url(context),)
            return {"cs_render_now": True}
    elif action == "login":
        env = context["cs_env"]
        cert_var = context.get("cs_cert_env_var", "SSL_CLIENT_S_DN")
        cert_sep = context.get("cs_cert_separator", ",")
        cert_data = {}
        for i in env[cert_var].split(cert_sep):
            try:
                k, v = i.split("=")
                cert_data[k] = v
            except:
                pass
        if "cs_cert_check" in context and not context["cs_cert_check"](cert_data):
            return {}
        if "cs_cert_function" in context:
            info = context["cs_cert_function"](cert_data)
        else:
            email = cert_data.get("emailAddress", None)
            if email is None:
                return {}
            info = {
                "username": email.split("@")[0],
                "email": email,
                "name": cert_data.get("CN", email),
            }
            session.update(info)
            return info
    else:
        raise Exception("Unknown action: %r" % action)


LOGIN_PAGE = """
<div id="catsoop_login_box">
Access to this page requires logging in with a certificate.  Please <a
href="%s?loginaction=login">Log In</a> to continue.
</div>
"""

LOGIN_BOX = """
<div class="response" id="catsoop_login_box">
<b><center>You are not logged in.</center></b><br/>
If you are a current student, please <a href="%s?loginaction=login">Log
In</a> with a certificate for full access to the web site.
</div>
"""
