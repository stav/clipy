"""
    18.5.1.12. Executor

        Call a function in an Executor (pool of threads or pool of processes).
        By default, an event loop uses a thread pool executor (ThreadPoolExecutor).

        BaseEventLoop.run_in_executor(executor, callback, *args)

        Arrange for a callback to be called in the specified executor.

        The executor argument should be an Executor instance. The default
        executor is used if executor is None.

    18.5.1.14. Debug mode

        BaseEventLoop.set_debug(enabled: bool)

        Set the debug mode of the event loop.

        New in version 3.4.2.

    18.5.1.17. Example: Hello World (callback)

        import asyncio

        def print_and_repeat(loop):
            print('Hello World')
            loop.call_later(2, print_and_repeat, loop)

        loop = asyncio.get_event_loop()
        loop.call_soon(print_and_repeat, loop)
        try:
            loop.run_forever()
        finally:
            loop.close()

    18.5.3.1.1. Example: “Hello World” coroutine

        import asyncio

        @asyncio.coroutine
        def greet_every_two_seconds():
            while True:
                print('Hello World')
                yield from asyncio.sleep(2)

        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(greet_every_two_seconds())
        finally:
            loop.close()

    18.5.3.1.2. Example: Chain coroutines

        import asyncio

        @asyncio.coroutine
        def compute(x, y):
            print("Compute %s + %s ..." % (x, y))
            yield from asyncio.sleep(1.0)
            return x + y

        @asyncio.coroutine
        def print_sum(x, y):
            result = yield from compute(x, y)
            print("%s + %s = %s" % (x, y, result))

        loop = asyncio.get_event_loop()
        loop.run_until_complete(print_sum(1, 2))
        loop.close()

    18.5.1.18. Example: Set signal handlers for SIGINT and SIGTERM

        import os
        import asyncio
        import functools
        import signal

        def ask_exit(signame):
            print("got signal %s: exit" % signame)
            loop.stop()

        loop = asyncio.get_event_loop()
        for signame in ('SIGINT', 'SIGTERM'):
            loop.add_signal_handler(getattr(signal, signame),
                                    functools.partial(ask_exit, signame))

        print("Event loop running forever, press CTRL+c to interrupt.")
        print("pid %s: send SIGINT or SIGTERM to exit." % os.getpid())
        try:
            loop.run_forever()
        finally:
            loop.close()

    18.5.2.4. Event loop policies and the default policy

        The default policy defines context as the current thread, and manages
        an event loop per thread that interacts with asyncio. The module-level
        functions get_event_loop() and set_event_loop() provide convenient
        access to event loops managed by the default policy.

    18.5.3.4.1. Example: Future with run_until_complete()

        # Example combining a Future and a coroutine function:
        import asyncio

        @asyncio.coroutine
        def slow_operation(future):
            yield from asyncio.sleep(1)
            future.set_result('Future is done!')

        loop = asyncio.get_event_loop()
        future = asyncio.Future()
        loop.create_task(slow_operation(future))
        loop.run_until_complete(future)
        print(future.result())
        loop.close()

    18.5.3.4.2. Example: Future with run_forever()

        # Using the Future.add_done_callback() method to describe the flow:
        import asyncio

        @asyncio.coroutine
        def slow_operation(future):
            yield from asyncio.sleep(1)
            future.set_result('Future is done!')

        def got_result(future):
            print(future.result())
            loop.stop()

        loop = asyncio.get_event_loop()
        future = asyncio.Future()
        loop.create_task(slow_operation(future))
        future.add_done_callback(got_result)
        try:
            loop.run_forever()
        finally:
            loop.close()

    18.5.3.5. Task

        class asyncio.Task(coro, *, loop=None)

        Schedule the execution of a coroutine: wrap it in a future. A task is a
        subclass of Future. Don’t create directly Task instances: use the
        BaseEventLoop.create_task() method.

    18.5.5.1. Stream functions

        asyncio.open_connection(host=None, port=None, *, loop=None, limit=None, **kwds)

            A wrapper for create_connection() returning a (reader, writer) pair.

            This function is a coroutine.

        asyncio.open_unix_connection(path=None, *, loop=None, limit=None, **kwds)

            A wrapper for create_unix_connection() returning a (reader, writer) pair.

            This function is a coroutine.

    18.5.5.6. Example

        # Simple example querying HTTP headers of the URL passed on the command line:
        import asyncio
        import urllib.parse
        import sys

        @asyncio.coroutine
        def print_http_headers(url):
            url = urllib.parse.urlsplit(url)
            reader, writer = yield from asyncio.open_connection(url.hostname, 80)
            query = ('HEAD {url.path} HTTP/1.0\r\n'
                     'Host: {url.hostname}\r\n'
                     '\r\n').format(url=url)
            writer.write(query.encode('latin-1'))
            while True:
                line = yield from reader.readline()
                if not line:
                    break
                line = line.decode('latin1').rstrip()
                if line:
                    print('HTTP header> %s' % line)

        url = sys.argv[1]
        loop = asyncio.get_event_loop()
        task = asyncio.async(print_http_headers(url))
        loop.run_until_complete(task)
        loop.close()

    18.5.6.3. Create a subprocess: low-level API using subprocess.Popen

        Run subprocesses asynchronously using the subprocess module.

    18.5.6.6. Example

        # Implement a function similar to subprocess.getstatusoutput(), except
        # that it does not use a shell. Get the output of the “python -m platform”
        # command and display the output:
        import asyncio
        import os
        import sys
        from asyncio import subprocess

        @asyncio.coroutine
        def getstatusoutput(*args):
            proc = yield from asyncio.create_subprocess_exec(*args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            try:
                stdout, _ = yield from proc.communicate()
            except:
                proc.kill()
                yield from proc.wait()
                raise
            exitcode = yield from proc.wait()
            return (exitcode, stdout)

        loop = asyncio.get_event_loop()
        coro = getstatusoutput(sys.executable, '-m', 'platform')
        exitcode, stdout = loop.run_until_complete(coro)
        if not exitcode:
            stdout = stdout.decode('ascii').rstrip()
            print("Platform: %s" % stdout)
        else:
            print("Python failed with exit code %s:" % exitcode, flush=True)
            sys.stdout.buffer.write(stdout)
            sys.stdout.buffer.flush()
        loop.close()

    18.5.8.2. Concurrency and multithreading

        An event loop runs in a thread and executes all callbacks and tasks in
        the same thread. While a task is running in the event loop, no other
        task is running in the same thread. But when the task uses yield from,
        the task is suspended and the event loop executes the next task.

        To schedule a callback from a different thread, the
        BaseEventLoop.call_soon_threadsafe() method should be used. Example to
        schedule a coroutine from a different thread:

            loop.call_soon_threadsafe(asyncio.async, coro_func())

        Most asyncio objects are not thread safe. You should only worry if you
        access objects outside the event loop. For example, to cancel a future,
        don’t call directly its Future.cancel() method, but:

            loop.call_soon_threadsafe(fut.cancel)

        To handle signals and to execute subprocesses, the event loop must be
        run in the main thread.

        The BaseEventLoop.run_in_executor() method can be used with a thread
        pool executor to execute a callback in different thread to not block
        the thread of the event loop.

    18.5.8.3. Handle blocking functions correctly

        Blocking functions should not be called directly. For example, if a
        function blocks for 1 second, other tasks are delayed by 1 second which
        can have an important impact on reactivity.

        For networking and subprocesses, the asyncio module provides high-level
        APIs like protocols.

        An executor can be used to run a task in a different thread or even in
        a different process, to not block the thread of the event loop. See the
        BaseEventLoop.run_in_executor() method.

    18.5.8.4. Logging

        The asyncio module logs information with the logging module in the logger 'asyncio'.
"""
