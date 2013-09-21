Problems
========

This page describes problems that timeline solves, and also problems it does
not intent to solve. It explains why timeline exists and what it does.

Timeline display
----------------

In the very beginning, timeline was created because Rickard was frustrated with
regular calendars. He found it difficult to get a sense of when events occurred
in time. Especially events far apart that would not fit in a calendar view. He
thought that presenting events on a timeline where he could quickly zoom in and
out and move around to show different views would help.

So, the core task of timeline is to **display and navigate events on a
timeline**. It has done that since version 0.1.0 which was released on 11 April
2009. Excerpt from the README:

    The Timeline Project aims to create a cross-platform application for
    displaying and navigating information on a timeline. The main goal is that
    it should be easy to quickly display different periods in time with
    different kinds of information on the timeline.

Implications
^^^^^^^^^^^^

If you have data that you would like to display on a timeline, timeline should
be able to do it.

Edit events
-----------

If timeline only displayed events, it would be cumbersome to edit them. You
would have to edit them in one program, then open timeline to view them.
Therefore, timeline can also edit the events that it displays.

However, read-only timelines have always existed, indicating that the very core
task is displaying events on a timeline, and not editing events. But being able
to edit events from within timeline makes it usable in more situations.

* Drag to resize
* ...

Problems related to event storage
---------------------------------

* Own file format
* Different backends

Problems related to being an application
----------------------------------------

* Availability: Cross-platform
* Binary packages
* Translation of strings

Problems that timeline does not solve
-------------------------------------

* Printing
