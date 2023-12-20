# IAmPaigeAT (paige@paige.bio) 2023

from netcrave_docker_util.http_handler import handler


class acme_service(handler):
    def __init__(self):
        super().__init__()
        self.add_route(
            "POST",
            "/.well-known/acme-challenge/",
            self.well_known_acme_challenge)

    async def well_known_acme_challenge(self, request):
        raise NotImplementedError()
