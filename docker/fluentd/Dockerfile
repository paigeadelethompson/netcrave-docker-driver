FROM netcrave

ADD .env /opt/conf/.env

ARG TEMPLATE_ROOT

ADD $TEMPLATE_ROOT /opt/conf/templates

RUN /usr/bin/netcrave-template

RUN apt -y install curl sudo

RUN curl -fsSL https://toolbelt.treasuredata.com/sh/install-debian-bookworm-fluent-package5-lts.sh | sh

RUN rm -rf /opt/conf

CMD fluentd
