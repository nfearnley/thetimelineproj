# Copyright (C) 2009, 2010  Rickard Lindberg, Roger Lindberg
#
# This file is part of Timeline.
#
# Timeline is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Timeline is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Timeline.  If not, see <http://www.gnu.org/licenses/>.


import locale


def ex_msg(e):
    """Return exception error string."""
    try:
        return str(e)
    except UnicodeEncodeError:
        if len(e.args) == 1:
            return e.args[0]
        else:
            # Exceptions raised by Timeline (the only ones that might be
            # unicode) should always contain a single unicode message. So we
            # should never end up here.
            return ""


def version_str_to_tuple(version_str):
    """
    >>> version_str_to_tuple("0.4.44.3")
    (0, 4, 44, 3)
    """
    return tuple([int(x) for x in version_str.split(".")])


def local_to_unicode(local_string):
    """Try to convert a local string to unicode."""
    encoding = locale.getdefaultlocale()[1]
    if encoding is None:
        # TODO: What should we do here?
        return u"ERROR"
    else:
        try:
            return local_string.decode(encoding)
        except Exception:
            # TODO: What should we do here?
            return u"ERROR"
