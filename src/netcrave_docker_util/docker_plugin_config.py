# IAmPaigeAT (paige@paige.bio) 2023

async def create_configuration(
    desc,
    socket_path,
    plugin_type=[
        "docker.volumedriver/1.0",
        "docker.networkdriver/1.0",
        "docker.ipamdriver/1.0",
        "docker.authz/1.0",
        "docker.logdriver/1.0",
        "docker.metricscollector/1.0"]):
    return {
        'Description': desc,
        'Documentation': 'https://github.com/paigeadelethompson/netcrave-docker-driver',
        'Interface': {
            'Socket': socket_path,
            'Types': plugin_type},
        'Network': {
            'Type': 'host'}}
