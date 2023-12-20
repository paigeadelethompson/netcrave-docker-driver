from fs.memoryfs import MemoryFS


@Singleton
class memory_filesystem_service():
    def new_filesystem(self, id):
        if self._state.get(id) is not None:
            raise NotImplementedError()
        self._state[id] = MemoryFS()

    def __init__(self):
        self._state = {}
