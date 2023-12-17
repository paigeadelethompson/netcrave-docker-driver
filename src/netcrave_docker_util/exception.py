class unknown(Exception):
    def __init__(self, msg, ex = None, additional_artifacts =None, *args, **kwargs):
        super(unknown, self).__init__(*args, **kwargs)
        self._artifacts = additional_artifacts
        self._msg = msg 
        self._inner = ex
        
    def artifacts(self):
        return self._artifacts
    
    def __str__(self):
        return """
            {inner}
            {msg}            
            """.format(msg = self._msg, inner = self._inner)
