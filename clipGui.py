#!/usr/bin/env python

import sys
import pygtk
pygtk.require('2.0')
import gtk, gobject
import keybinder
import notify2  # https://pypi.python.org/pypi/notify2
sys.path.insert(0, '/srv/_platforms/pafy')
import pafy  # https://github.com/np1/pafy


# Update the value of the progress bar so that we get
# some movement
def progress_timeout(pbobj):
    if pbobj.activity_check.get_active():
        pbobj.pbar.pulse()
    else:
        # Calculate the value of the progress bar using the
        # value range set in the adjustment object
        new_val = pbobj.pbar.get_fraction() + 0.01
        if new_val > 1.0:
            new_val = 0.0
        # Set the new value
        pbobj.pbar.set_fraction(new_val)

    # As this is a timeout function, return TRUE so that it
    # continues to get called
    return True


class ClpClp:

    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_resizable(True)
        window.connect("delete_event", self.delete_event)
        window.connect("destroy", self.destroy)
        window.set_title("Clp Clp")
        window.set_border_width(10)

        vbox = gtk.VBox(False, 5)
        vbox.set_border_width(10)
        window.add(vbox)
        vbox.show()

        box1 = gtk.VBox(False, 0)
        window.add(box1)
        box1.show()

        box2 = gtk.VBox(False, 10)
        box2.set_border_width(10)
        box1.pack_start(box2, True, True, 0)
        box2.show()

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        textview = gtk.TextView()
        textbuffer = textview.get_buffer()
        sw.add(textview)
        sw.show()
        textview.show()

        box2.pack_start(sw)
        textbuffer.set_text('asdf')

        hbox = gtk.HButtonBox()
        box2.pack_start(hbox, False, False, 0)
        hbox.show()

        # Create a centering alignment object
        align = gtk.Alignment(0.5, 0.5, 0, 0)
        vbox.pack_start(align, False, False, 5)
        align.show()

        # Create the ProgressBar
        self.pbar = gtk.ProgressBar()
        align.add(self.pbar)
        self.pbar.show()

        # Add a timer callback to update the value of the progress bar
        self.timer = gobject.timeout_add(100, progress_timeout, self)

        separator = gtk.HSeparator()
        vbox.pack_start(separator, False, False, 0)
        separator.show()
        table = gtk.Table(2, 2, False)
        vbox.pack_start(table, False, True, 0)
        table.show()

        # Add a check button to select displaying of the trough text
        check = gtk.CheckButton("Show text")
        table.attach(check, 0, 1, 0, 1, gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL, 5, 5)
        check.connect("clicked", self.toggle_show_text)
        check.show()

        # Add a check button to toggle activity mode
        self.activity_check = check = gtk.CheckButton("Activity mode")
        table.attach(check, 0, 1, 1, 2, gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL, 5, 5)
        check.connect("clicked", self.toggle_activity_mode)
        check.show()

        # Add a check button to toggle orientation
        check = gtk.CheckButton("Right to Left")
        table.attach(check, 0, 1, 2, 3, gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL, 5, 5)
        check.connect("clicked", self.toggle_orientation)
        check.show()

        # Add a button to exit the program
        button = gtk.Button("close")
        button.connect("clicked", self.destroy)
        vbox.pack_start(button, False, False, 0)
        button.set_flags(gtk.CAN_DEFAULT)
        button.grab_default()
        button.show()

        #self.button = gtk.Button("Hello World")
        #self.button.connect("clicked", self.asdf, None)
        #self.button.connect_object("clicked", gtk.Widget.destroy, self.window)
        #self.window.add(self.button)
        #self.button.show()

        window.show()

    def clip(self):
        summary = 'ClipClip'
        text = gtk.clipboard_get().wait_for_text().strip()
        engaged = False
        if text.startswith('http://www.youtube.com/'):
            engaged = True
            video = pafy.new(text)
            best = video.getbest(preftype="mp4")
            summary += ' video engaged (%s)' % video.length
            text += '\n%s\n%s' % (video.title, best)
            print 'engaged:', text

        notify2.Notification(summary, text).show()

        if engaged:
            myfilename = "/home/stav/Videos/clpclp/" + best.title + "." + best.extension
            best.download(filepath=myfilename)

        print "Hello World"

    def asdf(self, widget, data=None):
        progressbar = gtk.ProgressBar(adjustment=None)
        progressbar.set_fraction(0.4)
        progressbar.pulse()

    def delete_event(self, widget, event, data=None):
        # If you return FALSE in the "delete_event" signal handler,
        # GTK will emit the "destroy" signal. Returning TRUE means
        # you don't want the window to be destroyed.
        # This is useful for popping up 'are you sure you want to quit?'
        # type dialogs.
        print "delete event occurred"

        # Change FALSE to TRUE and the main window will not be destroyed
        # with a "delete_event".
        return False

    def destroy(self, widget, data=None):
        print "destroy signal occurred"
        gobject.source_remove(self.timer)
        self.timer = 0
        gtk.main_quit()

    # Callback that toggles the text display within the progress
    # bar trough
    def toggle_show_text(self, widget, data=None):
        if widget.get_active():
            self.pbar.set_text("some text")
        else:
            self.pbar.set_text("")

    # Callback that toggles the activity mode of the progress
    # bar
    def toggle_activity_mode(self, widget, data=None):
        if widget.get_active():
            self.pbar.pulse()
        else:
            self.pbar.set_fraction(0.0)

    # Callback that toggles the orientation of the progress bar
    def toggle_orientation(self, widget, data=None):
        if self.pbar.get_orientation() == gtk.PROGRESS_LEFT_TO_RIGHT:
            self.pbar.set_orientation(gtk.PROGRESS_RIGHT_TO_LEFT)
        elif self.pbar.get_orientation() == gtk.PROGRESS_RIGHT_TO_LEFT:
            self.pbar.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)


def main():
    notify2.init("ClipClip")
    clipr = ClpClp()
    keybinder.bind("<Ctrl>D", clipr.clip)
    gtk.main()
    return 0

if __name__ == "__main__":
    main()
