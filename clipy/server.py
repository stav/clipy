"""
Clipy YouTube video downloader local server

Run server::

    $ python clipy/server.py
"""
import os
import sys
import asyncio

import clipy.youtube

DATA_DIR = '/home/stav/Workspace/clipy/data'


class YoutubeServer:

    def __init__(self):
        self.server = None # encapsulates the server sockets
        self.clients = {} # task -> (reader, writer)

    def _accept_client(self, client_reader, client_writer):
        # start a new Task to handle this specific client connection
        task = asyncio.Task(self._handle_client(client_reader, client_writer))
        self.clients[task] = (client_reader, client_writer)

        def client_done(task):
            print("client task done:", task, file=sys.stderr)
            del self.clients[task]

        task.add_done_callback(client_done)

    @asyncio.coroutine
    def _handle_client(self, client_reader, client_writer):
        print()
        while True:
            data = (yield from client_reader.readline()).decode("utf-8")

            if not data: # an empty string means the client disconnected
                break

            print('Got data: {}'.format(data.strip()))
            video_id = yield from clipy.youtube.get_video_id(data)
            print('Got video_id: {}'.format(video_id))

            if video_id:
                if os.path.exists(os.path.join(DATA_DIR, video_id)):
                    print('exists!')
                    with open(os.path.join(DATA_DIR, video_id)) as fd:
                        response = fd.read()
                        client_writer.write(response.encode("utf-8"))

                    # This enables us to have flow control in our connection.
                    yield from client_writer.drain()

    def start(self, loop):
        self.server = loop.run_until_complete(
            asyncio.streams.start_server(self._accept_client,
                                         '127.0.0.1', 8888,
                                         loop=loop))

    def stop(self, loop):
        if self.server is not None:
            self.server.close()
            loop.run_until_complete(self.server.wait_closed())
            self.server = None


loop = asyncio.get_event_loop()
server = YoutubeServer()
server.start(loop)
print('serving')

try:
    loop.run_forever()
except KeyboardInterrupt:
    print("exit")
finally:
    server.stop(loop)
    loop.close()
