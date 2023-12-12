FROM netcrave 

ADD .env /opt/conf/.env

ARG TEMPLATE_ROOT

ADD $TEMPLATE_ROOT /opt/conf/templates

RUN /usr/bin/netcrave-template

RUN apt --option Dpkg::Options::="--force-confold" --no-install-recommends -y install frr tini

RUN rm -rf /opt/conf

ENTRYPOINT ["/usr/bin/tini", "--"]

COPY ./docker/frr/docker-start /usr/lib/frr/docker-start

RUN chmod +x /usr/lib/frr/docker-start

RUN mkdir -p /var/run/frr/

RUN chown -R frr /var/run/frr

CMD ["/usr/lib/frr/docker-start"]
