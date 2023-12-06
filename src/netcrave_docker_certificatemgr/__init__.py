from netcrave_docker_certificatemgr.http import run_volume_driver, run_dav, run_acme, await_acme_challenge_response
from threading import Thread
import time

def main():
    t1 = Thread(target=run_volume_driver)
    t2 = Thread(target=run_acme)
    t3 = Thread(target=await_acme_challenge_response)
    t4 = Thread(target=run_dav)
    
    t1.run()
    t2.run()
    t3.run()
    t4.run()
    
    while True:
        time.sleep(1)
    
if __name__ == '__main__':
    main()
