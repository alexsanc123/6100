# This file is part of CAT-SOOP
# Copyright (c) 2011-2016 Adam Hartz <hartz@mit.edu>

# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.

# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see
# <https://www.gnu.org/licenses/agpl-3.0-standalone.html>.


def get_logged_in_user(context):
    # certificates-based login
    env = context['cs_env']
    if 'SSL_CLIENT_S_DN_Email' not in env:
        return {'username': 'None'}
    else:
        email = env['SSL_CLIENT_S_DN_Email']
        return {'username': email.split('@')[0],
                'email': email,
                'name': env['SSL_CLIENT_S_DN_CN']}