# Python YouTube downloader
# 1. start script
# 2. copy youtube url into clipboard
# 3. press ctrl-d to start downloading

import sys

import pygtk
pygtk.require('2.0')
import gtk
import keybinder
import notify2  # https://pypi.python.org/pypi/notify2

sys.path.insert(0, '/srv/_platforms/pafy')
import pafy  # https://github.com/np1/pafy
# https://github.com/rg3/youtube-dl  Small command-line program to download videos from YouTube.com
# https://github.com/Zulko/moviepy  Python module for script-based movie editing

download_dir = "/home/stav/Videos/clpclp/"

def clip():
    summary = 'ClipClip'
    text = gtk.clipboard_get().wait_for_text().strip()
    engaged = False
    if '//www.youtube.com/' in text:
        engaged = True
        video = pafy.new(text)
        best = video.getbest(preftype="mp4")
        summary += ' video engaged (%s)' % video.length
        text += '\n%s\n%s' % (video.title, best)
        print 'engaged:', text

    notify2.Notification(summary, text).show()

    if engaged:
        myfilename = download_dir + best.title + "." + best.extension
        best.download(filepath=myfilename)

    #gtk.main_quit()

if __name__ == '__main__':
    notify2.init("Clipy")
    notify2.Notification('Clipy', 'started\n%s' % download_dir).show()
    keybinder.bind("<Ctrl>D", clip)
    gtk.main()
