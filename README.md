# Clipy

YouTube video downloader which includes an asynchronous Python backend server written using
`aiohttp` and a front end that requires a modern browser. The latest version of *Clipy* is
moving toward a web browser interface with the heavy lifting done by the server.

The previous version of *Clipy* used the command line heavily and that code is still available
in the `shell` branch.

Evenually the async downloading work should be wrapped up nicely in a Python module that the Clipy
client just imports and calls.

## Requirements

### Server

* Python 3.6 (only)

### Client

* ES6+ (ECMAScript 2015) modern browser

See also requirements.txt

## Install

First clone this repository.

You will need a terminal in the repository directory with the file ``setup.py``.

### Setup

	python3.6 setup.py install

You may need the development package of Python to install `pycares`:

	sudo apt-get install python3.6-dev

## Run

Open a terminal and run the following:

	clipyd & sleep 2; clipy

This will run the Clipy server as a background process and wait two seconds for it to start and then
it will open a web browser and requst the home page.

## Screen-shots

![Clipy user interface](http://104.237.140.142/clipy/screenshot_gui.png)

## Downloads

Videos will be downloaded to the ``videos`` directory under the repository.

## Server

You can shutdown the server using the button in the browser or from the command line:

	pkill clipyd

# Credits

* C logo: [mysitemyway](http://cdn.mysitemyway.com/etc-mysitemyway/icons/legacy-previews/icons/simple-red-square-icons-alphanumeric/128147-simple-red-square-icon-alphanumeric-letter-c.png)
* Download code: [Pafy](http://pythonhosted.org/Pafy/)
