#!/usr/bin/python

from dotenv import load_dotenv;
import os, sys;
from pathlib import Path
import jinja2
from itertools import islice
from itertools import chain

for index in chain.from_iterable([["{}/{}".format(
    x, a) for a in z if a.endswith(".jinja2")] for x, y, z in os.walk(
    "/opt", topdown=True, onerror=None, followlinks=False) if len(z) > 0]):

    cur_path = Path(next(islice(Path(index).parents, 1)))
    out_path = Path("/") / Path("/".join(islice(cur_path.parts, 4, None)))
    
    #out_path = Path("/") / Path("/".join([cur_path.parts[4:])) ### XXX FIXME doesn't trim the path down correctly, 
                                          # if TEMPLATE_ROOT build arg isnt set, but maybe that's ok

    print("current path: {}".format(cur_path))
    print("output path: {}".format(out_path))

    out_path.mkdir(parents = True, exist_ok = True)

    templateLoader = jinja2.FileSystemLoader(searchpath = cur_path)
    templateEnv = jinja2.Environment(loader = templateLoader)

    template_file = Path(list(Path(index).parts).pop())
    out_file = Path(template_file.name.replace(".jinja2", ""))

    print("template file name: {}".format(template_file))

    template = templateEnv.get_template(str(template_file))

    load_dotenv("/opt/conf/.env")
    outputText = template.render(os.environ)

    print("output file name: {}".format(out_file))
    print("full output path: {}".format(out_path / out_file))

    open(out_path / out_file, 'w+').write(outputText)

    print("saved")
