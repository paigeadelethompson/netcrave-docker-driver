# IAmPaigeAT (paige@paige.bio) 2023

from werkzeug.serving import make_server
from threading import Thread
from netcrave_docker_util.ssl_context import ssl_context 

def http_servers(flask_application, bind_addresses = [("*", 8181, False, 0.5), ("*", 8443, True, 0.5)]):
    servers = []
    
    for host, port, tls, poll_rate in bind_addresses:
        if host.startswith("unix://"):
            srv = make_server(
                host        = host, 
                port        = 0, 
                app         = flask_application)
            servers.append({
                "ssl_context": None,
                "server": srv, 
                "thread": Thread(target = srv.serve_forever, args = ()) })
        elif tls:
            ctx = flask_application.get_ssl_context()
            srv = make_server(
                host        = host, 
                port        = port, 
                ssl_context = ctx, 
                app         = flask_application)
            servers.append({
                "ssl_context": ctx, 
                "server": srv, 
                "thread": Thread(target = srv.serve_forever, args = ()) })
        else:
            srv = make_server(
                host        = host, 
                port        = port, 
                app         = flask_application)
            servers.append({
                "server": srv, 
                "thread": Thread(target = srv.serve_forever, args = ()) })
    return servers
