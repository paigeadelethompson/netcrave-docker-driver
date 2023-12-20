# IAmPaigeAT (paige@paige.bio) 2023

import sys
from pathlib import Path


class unknown(Exception):
    def __init__(
            self,
            msg,
            ex=None,
            additional_artifacts=None,
            back_trace=sys.exc_info(),
            *args,
            **kwargs):
        super(unknown, self).__init__(*args, **kwargs)
        exc_type, exc_value, exc_traceback = back_trace
        self._artifacts = additional_artifacts
        self._msg = msg
        self._inner = ex
        self._details = {
            'filename': Path(exc_traceback.tb_frame.f_code.co_filename).name,
            'lineno': exc_traceback.tb_lineno,
            'name': exc_traceback.tb_frame.f_code.co_name,
            'type': exc_type.__name__,
            'message': exc_value.message}

    def artifacts(self):
        return self._artifacts

    def __str__(self):
        return (
            """{file} {line} {name} {type} {message}""".format(
                filename=self._details.get("filename"),
                line=self._details.get("lineno"),
                name=self._details.get("name"),
                type=self._details.get("type"),
                message=self._details.get("message")))
