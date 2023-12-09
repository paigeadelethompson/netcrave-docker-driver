from netcrave_docker_davfs.http import run_volume_driver
from threading import Thread
import time

def main():
    run_volume_driver()
    
if __name__ == '__main__':
    main()
