from systemd_service import Service

class service(Service):
    def __init__(self, name, *args, **kwargs):
        super(service, self).__init__(*args, **kwargs)
        self.name = name
        
    def create_service(self, after=None):
        if after:
            after = f'After={after}'
        else:
            after = ''
        systemd_script = f'''
        [Unit]
        Description="{self.name}"
        {after}
        StartLimitIntervalSec=5000
        StartLimitBurst=50

        [Service]
        Type=simple
        ExecStartPre=/usr/bin/env {self.name}-env
        ExecStart=/usr/bin/env {self.name}-daemon
        Restart=never

        [Install]
        WantedBy=multi-user.target
        '''

        self.stop()
        self.remove()
        
        with open(f"/etc/systemd/system/{self.name}.service", 'w') as file:
            file.write(systemd_script)
            
        self.reload()

