# Clipy

YouTube video downloader which includes an asynchronous Python backend server written using
`aiohttp` and a front end that requires a modern browser. The latest version of *Clipy* is
moving toward a web browser interface with the heavy lifting done by the server.

The previous version of *Clipy* used the command line heavily and that code is still available
in the `shell` branch.

## Requirements

### Server

* Python 3.6 (only)

### Client

* ES6+ (ECMAScript 2015)

See also requirements.txt

## Install

You will probably need the development package of Python to install `pycares`:

	sudo apt-get install python3.6-dev

Install dependencies:

	pip install -r requirements.txt

Install the application

	python3.6 setup.py install

## Run the server:

	clipy

	INFO:asyncio:<Server sockets=[<socket.socket fd=6, family=AddressFamily.AF_INET, type=2049, proto=6, laddr=('127.0.0.1', 7070)>]> is serving
	======== Running on http://127.0.0.1:7070 ========
	(Press CTRL+C to quit)

### Or running for development:

	python -Wdefault -m clipy.run

## Open the GUI:

Use a web browser: http://127.0.0.1:7070/

## Screen-shots

![Clipy user interface](http://104.237.140.142/clipy/screenshot_gui.png)

# Credits

* C logo: [mysitemyway](http://cdn.mysitemyway.com/etc-mysitemyway/icons/legacy-previews/icons/simple-red-square-icons-alphanumeric/128147-simple-red-square-icon-alphanumeric-letter-c.png)
* Download code: [Pafy](http://pythonhosted.org/Pafy/)
