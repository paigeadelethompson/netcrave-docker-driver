import random
import socketserver as SocketServer
from pyicap import *


class ThreadingSimpleServer(SocketServer.ThreadingMixIn, ICAPServer):
    pass

class ICAPHandler(BaseICAPRequestHandler):

    def echo_OPTIONS(self):
        self.set_icap_response(200)
        self.set_icap_header(b'Methods', b'REQMOD RESPMOD')
        self.set_icap_header(b'Service', b'netcrave-docker-icap')
        self.send_headers(False)

    def echo_RESPMOD(self):
        self.no_adaptation_required()
        
    def example_REQMOD(self):
        self.no_adaptation_required()

def main():
    port = 1344
    server = ThreadingSimpleServer(('192.0.0.22', port), ICAPHandler)
    try:
        while 1:
            server.handle_request()
    except KeyboardInterrupt:
        print("Finished")
