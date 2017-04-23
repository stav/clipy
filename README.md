# Clipy

YouTube video downloader which includes an asynchronous Python backend server written using
`aiohttp` and a front end that requires a modern browser. The latest version of *Clipy* is
moving toward a web browser interface with the heavy lifting done by the server.

The previous version of *Clipy* used the command line heavily and that code is still available
in the `shell` branch.

## Requirements

### Server

* Python 3.6

### Client

* ES6 (ECMAScript 2015)

See also requirements.txt

## Install

You will probably need the development package of Python to install `pycares`:

	sudo apt-get install python-dev

Install dependencies:

	pip install -r requirements.txt

## Run the server:

	clipy$ python main.py

## Open the GUI:

Use a web browser: http://127.0.0.1:7070/

## Screen-shots

![Clipy user interface](http://104.237.140.142/clipy/screenshot_gui.png)

# Credits

* C logo: http://cdn.mysitemyway.com/etc-mysitemyway/icons/legacy-previews/icons/simple-red-square-icons-alphanumeric/128147-simple-red-square-icon-alphanumeric-letter-c.png
* Download code: Pafy
