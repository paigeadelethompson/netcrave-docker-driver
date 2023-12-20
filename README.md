# WIP 

A plugin to expand the functionality of Docker 

- Better networking; using NetNS, and VRF for sufficient network isolation and egress/ingress reachability
- Schema defined IP address allocation with support for IPv4 and IPv6 
- Tag-based network assignment for containers (container networks are defined by egress / ingress tags) 
- A DNS server that automatically creates A / AAAA records for the internal plane; additional records can be defined in labels
- A volume driver based on WebDAV that provides certificates (additionally certificates issued from ACME)
- HAProxy as an ingress controller (backends are dynamically configured using DNS SRV resource records and haproxyctl.)
- Squid proxy for caching and ICAP (internet content adaptation protocol) for building web application firewalls
- End to end encryption and reliable data at rest encryption are extremely important and emphasized
- Clustering; with or without docker swarm; networking is handled by FRR/iBGP

# OS dependencies
- libfuse3-dev
- python3-poetry 
- build-essential 
- python3-dev 
- libfuse3-dev
- python-is-python3 

# Driver components and dependency 
- Nearly everything will depend on CockroachDB (postgresql-based) it's a good database with good security mechanisms.

# Getting started / Development

- `apt install python-is-python3 python3-poetry`
- `git clone https://github.com/paigeadelethompson/netcrave-docker-driver.git`
- `poetry install`

- Docker and the container runtimes need to be installed to /opt/netcrave and can be done in one command: 
```
export DEBUG=1
sudo poetry run netcrave-docker-install --runtimes
```
- With Docker and associated runtimes installed,  start the daemon:
```
export DEBUG=1
sudo poetry run netcrave-docker-daemon
```

This will automatically create the directories, and default configuration files as well as start and supervise `dockerd` and `containerd`

- To reset the state:
- `rm -rf /srv/netcrave/ ; rm -rf /etc/netcrave/ ; rm -rf /srv/_netcrave/ rm -rf /run/_netcrave ; ip netns delete _netcrave`

# Future items under consideration (not this release scope)
- authorization plugin; access to the docker daemon and resource controls defined by an identity (with ory / openid)
- multi-tenancy; vrf ownership / tenant id based on openid
