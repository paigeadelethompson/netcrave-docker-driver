FROM netcrave 

RUN apt --option Dpkg::Options::="--force-confold" --no-install-recommends -y install python3-poetry build-essential python3-dev

WORKDIR /tmp

RUN git clone https://github.com/paigeadelethompson/netcrave-docker-driver.git  /tmp

RUN poetry build 

RUN poetry install

RUN apt -y remove build-essential python3-dev 

RUN apt -y autoremove

RUN rm -rf /var/lib/{apt,dpkg,cache,log}/
