import asyncio
from asyncio.base_events import Server
from functools import partial
from io import BytesIO
import logging
import os
import sys
from concurrent.futures import Executor, ThreadPoolExecutor
from contextlib import contextmanager
from tempfile import SpooledTemporaryFile
from typing import Any, Awaitable, IO, Callable, Dict, Generator, Iterable, List, Optional, Tuple
from wsgiref.util import is_hop_by_hop

from aiohttp.web import (
    Application,
    AppRunner,
    BaseSite,
    TCPSite,
    UnixSite,
    Request,
    Response,
    StreamResponse,
    HTTPRequestEntityTooLarge,
    middleware)

from aiohttp.web_response import CIMultiDict
from aiohttp_wsgi.utils import parse_sockname

WSGIEnviron = Dict[str, Any]
WSGIHeaders = List[Tuple[str, str]]
WSGIAppendResponse = Callable[[bytes], None]
WSGIStartResponse = Callable[[str, WSGIHeaders], Callable[[bytes], None]]
WSGIApplication = Callable[[WSGIEnviron, WSGIStartResponse], Iterable[bytes]]

logger = logging.getLogger(__name__)

async def _run_application(application: WSGIApplication, environ: WSGIEnviron) -> Response:
    # Response data.
    response_status: Optional[int] = None
    response_reason: Optional[str] = None
    response_headers: Optional[WSGIHeaders] = None
    response_body: List[bytes] = []
    log = logging.getLogger(__name__)
    # Run the application.
    app = application()
    try:
        if environ.get("SERVER_NAME") == "unix":
            request_uri = "/{request}".format(request = environ.get("HTTP_HOST"))
            callback = next((index.get("callback") for index in app.router if index.get("path") == request_uri))
            response_status, response_body, headers = await callback()
            response_headers = app.headers + headers
            return Response(
                status = response_status,
                reason = response_reason,
                headers = CIMultiDict(response_headers),
                body = b"".join(response_body))
    except Exception as ex:
        log.error(ex)

class WSGIHandler:
    """
    An adapter for WSGI applications, allowing them to run on :ref:`aiohttp <aiohttp-web>`.

    :param application: {application}
    :param str url_scheme: {url_scheme}
    :param io.BytesIO stderr: {stderr}
    :param int inbuf_overflow: {inbuf_overflow}
    :param int max_request_body_size: {max_request_body_size}
    :param concurrent.futures.Executor executor: {executor}
    """
    def __init__(
        self,
        application: WSGIApplication,
        *,
        # Handler config.
        url_scheme: Optional[str] = None,
        stderr: Optional[IO[bytes]] = None,
        inbuf_overflow: int = 524288,
        max_request_body_size: int = 1073741824,
        # asyncio config.
        executor: Optional[Executor] = None):
            assert callable(application), "application should be callable"
            self._application = application
            # Handler config.
            self._url_scheme = url_scheme
            self._stderr = stderr or sys.stderr
            assert isinstance(inbuf_overflow, int), "inbuf_overflow should be int"
            assert inbuf_overflow >= 0, "inbuf_overflow should be >= 0"
            assert isinstance(max_request_body_size, int), "max_request_body_size should be int"
            assert max_request_body_size >= 0, "max_request_body_size should be >= 0"
            if inbuf_overflow < max_request_body_size:
                self._body_io: Callable[[], IO[bytes]] = partial(SpooledTemporaryFile, max_size=inbuf_overflow)
            else:
                # Use BytesIO as an optimization if we'll never overflow to disk.
                self._body_io = BytesIO
            self._max_request_body_size = max_request_body_size
            # asyncio config.
            self._executor = executor

    def _get_environ(self, request: Request, body: IO[bytes], content_length: int) -> WSGIEnviron:
        # Resolve the path info.
        path_info = request.match_info["path_info"]
        script_name = request.rel_url.path[:len(request.rel_url.path) - len(path_info)]
        # Special case: If the app was mounted on the root, then the script name will
        # currently be set to "/", which is illegal in the WSGI spec. The script name
        # could also end with a slash if the WSGIHandler was mounted as a route
        # manually with a trailing slash before the path_info. In either case, we
        # correct this according to the WSGI spec by transferring the trailing slash
        # from script_name to the start of path_info.
        if script_name.endswith("/"):
            script_name = script_name[:-1]
            path_info = "/" + path_info
        # Parse the connection info.
        assert request.transport is not None
        server_name, server_port = parse_sockname(request.transport.get_extra_info("sockname"))
        remote_addr, remote_port = parse_sockname(request.transport.get_extra_info("peername"))
        # Detect the URL scheme.
        url_scheme = self._url_scheme
        if url_scheme is None:
            url_scheme = "http" if request.transport.get_extra_info("sslcontext") is None else "https"
        # Create the environ.
        environ = {
            "REQUEST_METHOD": request.method,
            "SCRIPT_NAME": script_name,
            "PATH_INFO": path_info,
            "RAW_URI": request.raw_path,
            # RAW_URI: Gunicorn's non-standard field
            "REQUEST_URI": request.raw_path,
            # REQUEST_URI: uWSGI/Apache mod_wsgi's non-standard field
            "QUERY_STRING": request.rel_url.raw_query_string,
            "CONTENT_TYPE": request.headers.get("Content-Type", ""),
            "CONTENT_LENGTH": str(content_length),
            "SERVER_NAME": server_name,
            "SERVER_PORT": server_port,
            "REMOTE_ADDR": remote_addr,
            "REMOTE_HOST": remote_addr,
            "REMOTE_PORT": remote_port,
            "SERVER_PROTOCOL": "HTTP/{}.{}".format(*request.version),
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": url_scheme,
            "wsgi.input": body,
            "wsgi.errors": self._stderr,
            "wsgi.multithread": True,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
            "asyncio.executor": self._executor,
            "aiohttp.request": request,
        }
        # Add in additional HTTP headers.
        for header_name in request.headers:
            header_name = header_name.upper()
            if not(is_hop_by_hop(header_name)) and header_name not in ("CONTENT-LENGTH", "CONTENT-TYPE"):
                header_value = ",".join(request.headers.getall(header_name))
                environ["HTTP_" + header_name.replace("-", "_")] = header_value
        # All done!
        return environ

    async def handle_request(self, request: Request) -> Response:
        # Check for body size overflow.
        if request.content_length is not None and request.content_length > self._max_request_body_size:
            raise HTTPRequestEntityTooLarge(
                max_size=self._max_request_body_size,
                actual_size=request.content_length)
        # Buffer the body.
        content_length = 0
        with self._body_io() as body:
            while True:
                block = await request.content.readany()
                if not block:
                    break
                content_length += len(block)
                if content_length > self._max_request_body_size:
                    raise HTTPRequestEntityTooLarge(
                        max_size=self._max_request_body_size,
                        actual_size=content_length,
                    )
                body.write(block)
            body.seek(0)
            # Get the environ.
            environ = self._get_environ(request, body, content_length)
            return await asyncio.create_task(
                _run_application(
                    self._application,
                    environ))

    __call__ = handle_request

def format_path(path: str) -> str:
    assert not path.endswith("/"), f"{path!r} name should not end with /"
    if path == "":
        path = "/"
    assert path.startswith("/"), f"{path!r} name should start with /"
    return path

Handler = Callable[[Request], Awaitable[StreamResponse]]
Middleware = Callable[[Request, Handler], Awaitable[StreamResponse]]

def static_cors_middleware(*, static: Iterable[Tuple[str, str]], static_cors: str) -> Middleware:
    @middleware
    async def do_static_cors_middleware(request: Request, handler: Handler) -> StreamResponse:
        response = await handler(request)
        for path, _ in static:
            if request.path.startswith(path):
                response.headers["Access-Control-Allow-Origin"] = static_cors
                break
        return response
    return do_static_cors_middleware


#@contextmanager
async def run_server(
    application: WSGIApplication,
    *,
    # asyncio config.
    threads: int = 4,
    # Server config.
    host: Optional[str] = None,
    port: int = 8080,
    # Unix server config.
    unix_socket: Optional[str] = None,
    unix_socket_perms: int = 0o600,
    # Shared server config.
    backlog: int = 1024,
    # aiohttp config.
    static: Iterable[Tuple[str, str]] = (),
    static_cors: Optional[str] = None,
    script_name: str = "",
    shutdown_timeout: float = 60.0,
    **kwargs: Any):
        assert threads >= 1, "threads should be >= 1"
        executor = ThreadPoolExecutor(threads)
        
        # Create aiohttp app.
        app = Application()
        
        # Add static routes.
        static = [(format_path(path), dirname) for path, dirname in static]
        for path, dirname in static:
            app.router.add_static(path, dirname)
        
        # Add the wsgi application. This has to be last.
        app.router.add_route(
            "*",
            f"{format_path(script_name)}{{path_info:.*}}",
            WSGIHandler(
                application,
                executor=executor,
                **kwargs
            ).handle_request,
        )
        
        # Configure middleware.
        if static_cors:
            app.middlewares.append(static_cors_middleware(
                static=static,
                static_cors=static_cors,
            ))
        
        
        # Start the app runner.
        runner = AppRunner(app)
        await asyncio.create_task(runner.setup())
        
        # Set up the server.
        if unix_socket is not None:
            site: BaseSite = UnixSite(runner, path=unix_socket, backlog=backlog, shutdown_timeout=shutdown_timeout)
        else:
            site = TCPSite(runner, host=host, port=port, backlog=backlog, shutdown_timeout=shutdown_timeout)
        
        await asyncio.create_task(site.start())
        
        # Set socket permissions.
        if unix_socket is not None:
            os.chmod(unix_socket, unix_socket_perms)
        
        # Report.
        assert site._server is not None
        assert isinstance(site._server, Server)
        assert site._server.sockets is not None
        
        server_uri = " ".join(
            "http://{}:{}".format(*parse_sockname(socket.getsockname()))
            for socket
            in site._server.sockets)
        
        logger.info("Serving on %s", server_uri)
        
        try:
            while True:
                await asyncio.sleep(1)
        finally:
            # Clean up unix sockets.
            for socket in site._server.sockets:
                sock_host, sock_port = parse_sockname(socket.getsockname())
                if sock_host == "unix":
                    os.unlink(sock_port)
            
            # Close the server.
            logger.debug("Shutting down server on %s", server_uri)
            
            await asyncio.create_task(site.stop())
            
            # Shut down app.
            logger.debug("Shutting down app on %s", server_uri)
            
            await asyncio.create_task(runner.cleanup())
            
            # Shut down executor.
            
            logger.debug("Shutting down executor on %s", server_uri)
            executor.shutdown()
            
            logger.info("Stopped serving on %s", server_uri)

async def serve(application: WSGIApplication, **kwargs: Any) -> None:  # pragma: no cover
    """
    Runs the WSGI application on :ref:`aiohttp <aiohttp-web>`, serving it until keyboard interrupt.

    :param application: {application}
    :param str url_scheme: {url_scheme}
    :param io.BytesIO stderr: {stderr}
    :param int inbuf_overflow: {inbuf_overflow}
    :param int max_request_body_size: {max_request_body_size}
    :param int threads: {threads}
    :param str host: {host}
    :param int port: {port}
    :param str unix_socket: {unix_socket}
    :param int unix_socket_perms: {unix_socket_perms}
    :param int backlog: {backlog}
    :param list static: {static}
    :param list static_cors: {static_cors}
    :param str script_name: {script_name}
    :param int shutdown_timeout: {shutdown_timeout}
    """
    await run_server(application, **kwargs)
