from netcrave_docker_acme.http import run_acme, run_job_processor
from threading import Thread
import time


def main():
    t2 = Thread(target=run_acme)
    t3 = Thread(target=run_job_processor)

    t2.run()
    t3.run()

    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
