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

# Driver components and dependency 
- Nearly everything will depend on CockroachDB (postgresql-based) it's a good database with good security mechanisms.

# Getting started / Development

- settings are isolated to a dotenv file, see `dotenv.example` and copy it to `.env` in the root directory of the repository

from the root directory of this repository:
- `docker-compose build`
- ` docker-compose up --no-start`


# Future items under consideration (not this release scope)
- authorization plugin; access to the docker daemon and resource controls defined by an identity (with ory / openid)
- multi-tenancy; vrf ownership / tenant id based on openid
