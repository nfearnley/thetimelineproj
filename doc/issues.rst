Issues
======

On this page we collect problems that users are having with timeline, and also
describe possible solutions.

Website is out of date
----------------------

Problem: When we update the doc in the repository, those changes are not
immediately reflected on the website. A manual step is required to upload the
latest doc to the website.

Possible solution: Have the `Jenkins job
<https://jenkins.rickardlindberg.me/job/timeline-doc/>`_ update the website on
a successful build.

TypeError: not all arguments converted during string formatting
---------------------------------------------------------------

**crash-report**

Reported 16 November 2014::

    Traceback (most recent call last):
      File "timelinelib\wxgui\dialogs\categoryeditor.pyc", line 132, in _btn_ok_on_click
      File "timelinelib\editors\category.pyc", line 55, in save
      File "timelinelib\wxgui\dialogs\categoryeditor.pyc", line 88, in handle_invalid_name
    TypeError: not all arguments converted during string formatting

    Timeline version: 1.4.1
    System version: Windows, nele-notebook, XP, 5.1.2600, x86, x86 Family 6 Model 15 Stepping 13, GenuineIntel
    Python version: 2.7.6 (default, Nov 10 2013, 19:24:18) [MSC v.1500 32 bit (Intel)]
    wxPython version: 2.8.12.1 (msw-unicode)

Sorting of categories is incorrect when using non-english characters
--------------------------------------------------------------------

**known-limitation**

The sorting isn't correct for å and ä. ä comes before å. Is it possible to fix
that?

The problem with unicode is that it has no knowledge about an alphabet. I am
note sure how Python does the comparison, but it seems like the English
alphabet is correctly sorted. Maybe with the exception that upper case are
sorted before lower case?

This is a difficult problem. Even if we can sort by a particular alphabet
(which I think is not supported by Python at the moment), how do we choose
which alphabet? Maybe getting the locale from the user's computer is one
option.

Using an extended calendar causes some problems
-----------------------------------------------

Some are discussed here:

http://groups.google.com/group/wx-users/browse_thread/thread/6eead92c421b81f8

Another comment from a user:

I think that the year 0 dont exist... between 1 bc and 1ad like (...5 4 3 2 1 1
2 3 4 5...) the same for "Century 0" please take in mind this...

"Year zero" does not exist in the widely used Gregorian calendar or in its
predecessor, the Julian calendar. Under those systems, the year 1 BC is
followed by AD 1.

http://en.wikipedia.org/wiki/0_%28year%29

Another comment from a user:

One suggestion I have is to change AD/BC to BCE/CE.  It's becoming the accepted
standard since many do not practice a Christian faith, and those of us who do
can find through research that Jesus wasn't actually born in the 0 year.

Another comment from a user:

There is a concept called epochs used to denote different periods in time.
Perhaps that is something we should incorporate in timeline.

Or we should just make the gregorian calendar work better when extended.

Can't zoom wider than 1200 years
--------------------------------

Timeline should not be able to zoom wider than 1200 years. But unfortunately,
this happens sometimes, and a period larger than 1200 years gets written to the
``.timeline`` file.

When this happens, you can no longer open the file.

This is a bug in timeline that we should fix. But there is a workaround that
you can use to fix the problem yourself.

The ``.timeline`` file is actually just an xml file. In there, somewhere around
the bottom of the file, you should find this section::

    <displayed_period>
      <start>2013-09-28 00:10:06</start>
      <end>2013-10-09 20:34:55</end>
    </displayed_period>

If you open the ``.timeline`` file in a text editor and change the start and
end dates to be a period less than 1200 years, you should be able to open your
file again.

Make sure that you save the file with UTF-8 encoding.
