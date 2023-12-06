from dnserver import DNSServer
from dnserver.load_records import Zone
from dnserver.main import Record
import os
import docker
import time 

# https://github.com/samuelcolvin/dnserver#dnserver
#zone = {"host": "", "type": "", "answer": "", }
#zone_types: 'A', 'AAAA', 'CAA', 'CNAME', 'DNSKEY', 'MX', 'NAPTR', 'NS', 'PTR', 'RRSIG', 'SOA', 'SRV', 'TXT', 'SPF'

class ZoneCustom(Zone):
    def __init__(self, zone_type='A', host=str(), answer=str()):
        self.host = host
        self.type = zone_type
        self.answer = answer
    def to_record(self):
        return Record(self)

DNS_DB = [] #[ZoneCustom("A", os.environ.get("DNSSERV_HOST_A"), os.environ.get("DNSSERV_A")).to_record()]

def get_dns_server():
    lp = os.environ.get("DNS_LISTEN_PORT") != None and os.environ.get("DNS_LISTEN_PORT") or 5353
    fwd = os.environ.get("DNS_FORWARDER") != None and os.environ.get("DNS_FORWARDER") or "1.1.1.1"
    server = DNSServer([index.to_record() for index in DNS_DB], lp, fwd)
    server.start()
    assert server.is_running
    return server

def main():
    #client = docker.DockerClient(base_url = path)
    get_dns_server()
    while True:
        time.sleep(1)

    
