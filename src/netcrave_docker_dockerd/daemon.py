from pathlib import Path
import subprocess
from threading import Thread 
from netcrave_docker_dockerd.setup_environment import setup_environment

class service():
    def __init__(self):
        pass
    
    def start(self):
        try:
            self.composer, self.ca, self.ndb = setup_environment()
            #Thread(target = lambda: subprocess.run
        except Exception as ex:
            raise ex
    
    def create_service(self):
        systemd_script = """
            [Unit]
            Description="Netcrave internal Docker daemon"
            
            StartLimitIntervalSec=60000

            [Service]
            Type=simple
            ExecStartPre=/usr/bin/env netcrave-dockerd-environment
            ExecStart=/usr/bin/env netcrave-dockerd-daemon
            Restart=never

            [Install]
            WantedBy=multi-user.target
            """
            
        if not Path("/etc/systemd/system/netcrave-dockerd-daemon.service").exists():
            with open("/etc/systemd/system/netcrave-dockerd-daemon.service", 'w') as file:
                file.write(systemd_script)
            
            result = subprocess.run(["/usr/bin/env", "systemctl", "daemon-reload"])
            
            if result.returncode != 0:
                Path("/etc/systemd/system/netcrave-dockerd-daemon.service").unlink()
                raise Exception("failed to reload systemd")
        else:
            raise Exception("service already installed")
            
                
            
    
