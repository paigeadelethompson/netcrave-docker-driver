ARG DEBIAN_RELEASE

FROM debian:$DEBIAN_RELEASE

ENV DEBIAN_FRONTEND noninteractive

RUN apt update

RUN apt -y --no-install-recommends install python-is-python3 python3-pip python3-dotenv python3-jinja2 curl git

ADD docker/netcrave/template.py /usr/bin/netcrave-template

RUN chmod +x /usr/bin/netcrave-template
