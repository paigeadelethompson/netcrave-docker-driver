
class service():
    '''
    '''

    def __init__(self):
        self.headers = [
            ("Content-Type", "application/vnd.docker.plugins.v1.2+json")]

    def activate(self, request):
        pass

    def get_capabilities(self, request):
        pass

    def get_default_address_spaces(self, request):
        # anything tagged default
        pass

    def request_pool(self, request):
        # get scope by tag and/or interpolate
        pass

    def release_pool(self, request):
        # toggle allocation status
        pass

    def request_address(self, request):
        # get scope by tag and/or interpolate
        pass

    def release_address(self, request):
        # toggle allocation status
        pass
