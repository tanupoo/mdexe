#!/usr/bin/env python

import sys
import re
from subprocess import Popen, PIPE, DEVNULL
import shlex
import tempfile
import pty
import os
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter

# <lang_name>
#
# <lang_name>,inc:<name1>[,<name2>[,...]]
#
# <lang_name>,name:<name1>
re_start = re.compile("^```\s*([\w\d]+)(\s*,\s*(\S.*))?")
re_quote = re.compile("^```")

class ReadMarkdown:

    def __init__(self, input_file=None):
        if input_file is not None:
            fd = open(input_file)
        else:
            fd = sys.stdin
        #
        """
        self.quotes:
            {
                "snipet": {
                    "lang": ...,
                    "name": None,
                    "inc": [...], # include lib(s) labeled by the name.
                    "snipet": ...,
                },
                "lib": {
                    "lang": ...,
                    "name": ...,
                    "inc": [],  # doesn't include any others.
                    "snipet": ...,
                },
                "other": { ... }
            }
        """
        self.quotes = { "snipet": [], "lib": [], "other": [] } # {"lang":"code"}
        in_quote = False
        quote_type = None
        lang = None
        text_lines = []
        name = None
        includes = []
        for line in fd:
            r = re_quote.match(line)
            if r:
                if not in_quote:
                    # found a start of a quote.
                    in_quote = True
                    r = re_start.match(line)
                    if r:
                        if quote_type is None:
                            lang = self._canon_lang(r.group(1))
                            # if r.group(3) exists, assumes it's a library.
                            # and r.group(3) is a name for this one.
                            if r.group(3) is None:
                                quote_type = "snipet"
                                name = None
                                includes = []
                            else:
                                if r.group(3).startswith("inc:"):
                                    quote_type = "snipet"
                                    name = None
                                    includes = r.group(3).replace("inc:","").split(",")
                                elif r.group(3).startswith("name:"):
                                    quote_type = "lib"
                                    name = r.group(3).replace("name:","")
                                    includes = []
                                else:
                                    raise ValueError("ERROR: "
                                                     "inc or name must be used.")
                        else:
                            raise ValueError("ERROR: "
                                             "quote mark mismatch to open.")
                    else:
                        quote_type = "other"
                        name = "__xxx"
                        includes = []
                else:
                    # found a end of a quote.
                    in_quote = False
                    if quote_type in ["snipet", "lib", "other"]:
                        self.quotes[quote_type].append({"lang":lang,
                                                        "name": name,
                                                        "inc": includes,
                                                        "snipet":text_lines})
                        quote_type = None
                        lang = None
                        text_lines = []
                        name = None
                        includes = []
                    else:
                        raise ValueError(
                                "ERROR: quote mark mismatch to close.")
            # in quote.
            elif quote_type is not None:
                text_lines.append(line)
        import json
        #print("xxx", json.dumps(self.quotes, indent=4))

    def _exec_cmd(self, lang, code_lines, exec_file=False):
        if lang == "php":
            if "<?php" not in code_lines[0]:
                # XXX should be find()
                code_lines.insert(0, "<?php\n")
        code = "".join(code_lines)
        if exec_file:
            self._exec_tempfile(lang, code)
        else:
            self._exec_pipeline(lang, code)

    def _exec_tempfile(self, lang, code):
        def reader(fd):
            data = os.read(fd, 1024)
            #print(data.decode(), end="", flush=True)
            return data
        with tempfile.NamedTemporaryFile("w") as tmp:
            tmp.write(cmd)
            tmp.flush()
            pty.spawn(shlex.split(f"{lang} {tmp.name}"), reader)

    def _exec_pipeline(self, lang, cmd):
        with Popen(shlex.split(lang),
                stdin=PIPE, stdout=PIPE, stderr=PIPE,
                   text=True) as proc:
            proc.stdin.write(cmd)
            proc.stdin.close()
            while True:
                output = proc.stdout.readline()
                print(output, end="", flush=True)
                errs = proc.stderr.read()
                if errs:
                    print(errs)
                if len(output) == 0:
                    break

    def _canon_lang(self, keyword):
        if keyword in ["node", "js", "javascript"]:
            return "node"
        elif keyword in ["sh", "bash", "zsh"]:
            return keyword
        elif keyword in ["php"]:
            return keyword
        elif keyword.startswith("python"):
            return keyword
        elif keyword in ["py"]:
            return "python"
        else:
            print(f"INFO: ignore ```{keyword}, it doesn't registered.")
            return None

    def make_code_lines(self, snipet_id):
        snipet = self.quotes["snipet"][snipet_id]
        code_lines = []
        for n in snipet["inc"]:
            for m in self.quotes["lib"]:
                if m["lang"] == snipet["lang"] and m["name"] == n:
                    if len(code_lines) > 0:
                        code_lines.append("\n")
                    code_lines.extend(m["snipet"])
                    break
            else:
                print(f"WARNING: name={n} doesn't exist.")
                continue
        if len(code_lines) > 0:
            code_lines.append("\n")
        code_lines.extend(snipet["snipet"])
        return code_lines

    def exec_snipets(self, snipet_ids, exec_file=False, unbuffered=True,
                     show_header=False):
        if unbuffered:
            os.environ["PYTHONUNBUFFERED"] = "YES"
        if len(snipet_ids) == 0:
            snipet_ids = range(len(self.quotes["snipet"]))
        for i in snipet_ids:
            code_lines = self.make_code_lines(i)
            snipet = self.quotes["snipet"][i]
            lang = snipet["lang"]
            if show_header:
                print(f"\n## SNIPET_ID {i}: {lang}\n")
            self._exec_cmd(lang, code_lines, exec_file)

    def show_snipets(self, snipet_ids, show_header=True, show_lineno=True,
                     show_libs=False):
        if len(snipet_ids) == 0:
            snipet_ids = range(len(self.quotes["snipet"]))
        for i in snipet_ids:
            code_lines = self.make_code_lines(i)
            snipet = self.quotes["snipet"][i]
            lang = snipet["lang"]
            lineno = 0
            if show_header:
                print(f"\n## SNIPET_ID {i}: {lang}\n")
            if show_lineno:
                for line in code_lines:
                    lineno += 1
                    print(f"{lineno:02}: {line}", end="")
            else:
                print(f"{''.join(code_lines)}")
        #
        sys.stdout.flush()

#
# main
#
ap = ArgumentParser(
        description="execute code picked from markdown by key.",
        formatter_class=ArgumentDefaultsHelpFormatter)
ap.add_argument("input_file", nargs="?",
                help="specify a filename containing code snipet. "
                    "'-' means stdin.")
ap.add_argument("-i", action="store", dest="snipet_ids",
                help="specify the snipet IDs separated by comma, OR 'all'. "
                    "It's required when the -x option is specified.")
ap.add_argument("-x", action="store_true", dest="exec_snipets",
                help="execute snipets specified the IDs seperated by a comma.")
ap.add_argument("-u", action="store_true", dest="unbuffered",
                help="specify unbuffered mode.")
ap.add_argument("-w", action="store_true", dest="toggle_show_libs",
                help="toggle to show libs.  "
                "default is true in exec mode, false in show mode.")
ap.add_argument("-S", action="store_false", dest="show_snipets",
                help="disable to show the snipet.")
ap.add_argument("-N", action="store_false", dest="show_lineno",
                help="disable to show the line number of the snipet.")
ap.add_argument("-H", action="store_false", dest="show_header",
                help="with this option, disable to show each header.")
ap.add_argument("-z", action="store_true", dest="exec_file",
                help="specify to execute the file "
                    "after it sets the snipet into the one.")
opt = ap.parse_args()

#
if opt.exec_snipets:
    if opt.snipet_ids == "all":
        snipet_ids = []
    elif opt.snipet_ids is not None:
        snipet_ids = [int(i) for i in opt.snipet_ids.split(",")]
    else:
        print("ERROR: Required the -i option if the -x option is specified.")
        exit(-1)
else:
    if opt.snipet_ids == "all":
        snipet_ids = []
    elif opt.snipet_ids is not None:
        snipet_ids = [int(i) for i in opt.snipet_ids.split(",")]
    else:
        snipet_ids = []

md = ReadMarkdown(opt.input_file)
if opt.show_snipets:
    if opt.exec_snipets:
        show_libs = False
    else:
        show_libs = True
    show_libs=not show_libs if opt.toggle_show_libs else show_libs
    md.show_snipets(snipet_ids, show_header=opt.show_header,
                    show_lineno=opt.show_lineno,
                    show_libs=show_libs)
if opt.exec_snipets:
    md.exec_snipets(snipet_ids, exec_file=opt.exec_file,
                    unbuffered=opt.unbuffered,
                    show_header=opt.show_header)
