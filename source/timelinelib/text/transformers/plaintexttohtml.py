# Copyright (C) 2009, 2010, 2011, 2012, 2013, 2014, 2015  Rickard Lindberg, Roger Lindberg
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


from markdown import markdown

from timelinelib.text.transformers.defaulttransformer import DefaultTextTransformer


class PlainTextToHtml(DefaultTextTransformer):

    def __init__(self):
        pass

    def transform(self, text):
        html_text = super(PlainTextToHtml, self).transform(text)
        try:
            return markdown(html_text)
        except:
            replacements = (("<", "&lt;"),
                            (">", "&gt;"))
            for target, replacement in replacements:
                html_text = html_text.replace(target, replacement)
            return html_text