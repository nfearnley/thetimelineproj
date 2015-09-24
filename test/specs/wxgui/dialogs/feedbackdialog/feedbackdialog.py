# -*- coding: utf-8 -*-
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


from mock import Mock

from timelinelib.utilities.encodings import to_unicode
from timelinelib.wxgui.dialogs.feedbackdialog.feedbackdialogcontroller import FeedbackDialogController
from timelinelib.wxgui.dialogs.feedbackdialog.feedbackdialog import FeedbackDialog
from timelinetest import UnitTestCase
from timelinetest.utils import create_dialog


class describe_feedback_dialog(UnitTestCase):

    def setUp(self):
        self.view = Mock(FeedbackDialog)
        self.controller = FeedbackDialogController(self.view)
        self.webbrowser = Mock()

    def test_it_can_be_created(self):
        with create_dialog(FeedbackDialog, None, "info", "this was fun", "very fun") as dialog:
            if self.HALT_GUI:
                dialog.ShowModal()

    def test_shows_parts_in_dialog(self):
        self.controller.on_init(self.webbrowser, info="info text", subject="subject text", body="body text")
        self.view.SetInfoText.assert_called_with("info text")
        self.view.SetSubjectText.assert_called_with("subject text")
        self.view.SetBodyText.assert_called_with("body text")

    def test_can_send_with_default(self):
        self.view.GetToText.return_value = "foo@example.com"
        self.view.GetSubjectText.return_value = "sub ject"
        self.view.GetBodyText.return_value = "bo dy"
        self.controller.on_init(self.webbrowser, info="", subject="", body="")
        self.controller.on_default_click(None)
        self.webbrowser.open.assert_called_with("mailto:foo%40example.com?subject=sub%20ject&body=bo%20dy")

    def test_can_send_unicode_characters(self):
        self.view.GetToText.return_value = "foo@example.com"
        self.view.GetSubjectText.return_value = "subject"
        self.view.GetBodyText.return_value = to_unicode("åäöÅÄÖ")
        self.controller.on_init(self.webbrowser, info="", subject="", body="")
        self.controller.on_default_click(None)
        self.webbrowser.open.assert_called_with("mailto:foo%40example.com?subject=subject&body=%C3%A5%C3%A4%C3%B6%C3%85%C3%84%C3%96")

    def test_can_send_with_gmail(self):
        self.view.GetToText.return_value = "foo@example.com"
        self.view.GetSubjectText.return_value = "sub ject"
        self.view.GetBodyText.return_value = "bo dy"
        self.controller.on_init(self.webbrowser, info="", subject="", body="")
        self.controller.on_gmail_click(None)
        self.webbrowser.open.assert_called_with("https://mail.google.com/mail/?compose=1&view=cm&fs=1&to=foo%40example.com&su=sub%20ject&body=bo%20dy")