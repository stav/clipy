import os

import pafy
import pyperclip
from evdev import InputDevice, list_devices, categorize, ecodes

# print()
# print('Accessible event devices:')
# for dev in map(InputDevice, list_devices()):
#     print( '%-20s %-32s %s' % (dev.fn, dev.name, dev.phys) )

download_dir = os.path.expanduser('~')

kb = '/dev/input/event3'
shifted = controlled = False
SHIFT = ('KEY_LEFTSHIFT', 'KEY_RIGHTSHIFT')
CTRL = ('KEY_LEFTCTRL', 'KEY_RIGHTCTRL')
KEY = 'KEY_D'

dev = InputDevice(kb)

print()
print('Keyboard found on:', dev)
print(dev.capabilities(verbose=True))

for event in dev.read_loop():
    if event.type == ecodes.EV_KEY:
        ce = categorize(event)
        print(ce)

        if ce.keycode in SHIFT:
            shifted = True if ce.keystate is ce.key_down else False

        if ce.keycode in CTRL:
            controlled = True if ce.keystate is ce.key_down else False

        if shifted and controlled and ce.keycode == KEY and ce.keystate is ce.key_up:
            url = pyperclip.paste().strip()

            try:
                video = pafy.new(url)
                best = video.getbest(preftype="mp4")
                print('engaged:', '\n%s\n%s' % (video.title, best))
                path = '%s.%s' % (os.path.join(download_dir, best.title), best.extension)
                best.download(filepath=path)

            except (OSError, ValueError, FileNotFoundError) as e:
                print(e)
