FROM netcrave 

ADD .env /opt/conf/.env

ARG TEMPLATE_ROOT

ADD $TEMPLATE_ROOT /opt/conf/templates

RUN /usr/bin/netcrave-template

RUN apt --option Dpkg::Options::="--force-confold" --no-install-recommends -y install haproxy 

RUN rm -rf /opt/conf

RUN mkdir /ctl_socket

ARG ADMIN_SOCKET_ADDR

CMD haproxy -W -S /run/sock.haproxy -f /etc/haproxy/haproxy.cfg
