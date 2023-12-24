# IAmPaigeAT (paige@paige.bio) 2023

import json
import logging


def get():
    log = logging.getLogger(__name__)
    config = json.load(open("/etc/netcrave/_netcrave.json"))
    log.debug("loaded configuration file {}".format(config))
    return config


def get_default():
    return {'bip': '10.0.0.1/16',
            'containerd': '/run/netcrave/_netcrave/sock.containerd',
            'data-root': '/srv/netcrave/_netcrave/data',
            'default-address-pools': [{'base': '10.1.0.0/16',
                                       'size': 29}],
            'default-shm-size': '64K',
            'default-ulimits': {'nofile': {'Hard': 64,
                                           'Name': 'nofile',
                                           'Soft': 64}},
            'exec-root': '/srv/netcrave/_netcrave/state',
            'fixed-cidr-v6': 'fc00::/64',
            'group': '_netcrave',
            'hosts': ['unix:///run/netcrave/_netcrave/sock.dockerd'],
            'ip-forward': True,
            'ip-masq': False,
            'iptables': False,
            "default-runtime": "runc",
            "runtimes": {"kata-runtime": {"path": "/opt/netcrave/bin/kata-runtime"}},
            'ip6tables': False,
            'ipv6': True,
            'live-restore': True,
            'log-driver': 'json-file',
            'log-level': '',
            'log-opts': {'cache-disabled': 'false',
                         'cache-max-file': '2',
                         'cache-max-size': '64m',
                         'cache-compress': 'true',
                         'max-file': '4',
                         'max-size': '128m'},
            'mtu': 9000,
            'pidfile': '/srv/netcrave/_netcrave/docker.pid',
            'selinux-enabled': True,
            'shutdown-timeout': 64,
            'tls': True,
            'tlscacert': '/etc/netcrave/ssl/ca.pem',
            'tlscert': '/etc/netcrave/ssl/_netcrave.pem',
            'tlskey': '/etc/netcrave/ssl/_netcrave.key',
            'tlsverify': True,
            "userland-proxy": False}
