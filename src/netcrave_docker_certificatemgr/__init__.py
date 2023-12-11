from netcrave_docker_certificatemgr.http import run_cert_mgr, run_job_processor

from threading import Thread
import time

def main():
    run_cert_mgr()
    
if __name__ == '__main__':
    main()
