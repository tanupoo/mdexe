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

re_start = re.compile("^```\s*([\w\d]+)(,\s*_lib)?")
re_quote = re.compile("^```")

class ReadMarkdown:

    def __init__(self, input_file=None):
        if input_file is not None:
            fd = open(input_file)
        else:
            fd = sys.stdin
        #
        self.quotes = { "snipet": [], "lib": [], "other": [] } # {"lang":"code"}
        quote_type = None # "snipet", "lib", "other"
        #
        in_quote = False
        lang = None
        for line in fd:
            r = re_quote.match(line)
            if r:
                if not in_quote:
                    # found a start of a quote.
                    text_lines = [] # initialize
                    in_quote = True
                    r = re_start.match(line)
                    if r:
                        if quote_type is None:
                            lang = self._canon_lang(r.group(1))
                            if r.group(2):
                                quote_type = "lib"
                            else:
                                quote_type = "snipet"
                        else:
                            raise ValueError(
                                    "ERROR: quote mark mismatch to open.")
                    else:
                        quote_type = "other"
                else:
                    # found a end of a quote.
                    in_quote = False
                    if quote_type in ["snipet", "lib", "other"]:
                        self.quotes[quote_type].append({"lang":lang,
                                                "snipet":text_lines})
                        quote_type = None
                        lang = None
                        text_lines = []
                    else:
                        raise ValueError(
                                "ERROR: quote mark mismatch to close.")
            # in quote.
            elif quote_type is not None:
                text_lines.append(line)

    def _canon_cmd(self, lang, text_lines):
        if lang == "php":
            if "<?php" not in cmd[0]:
                text_lines.insert(0, "<?php\n")
        return "".join(text_lines)

    def get_lib(self, lang):
        m = "".join(["".join(x["snipet"]) for x in self.quotes["lib"]
                        if x["lang"] == lang])
        if len(m) > 0:
            #return m + "\n"
            return m # XXX
        else:
            return m

    def _exec_cmd(self, id, lang, text_lines,
                  exec_file=False, show_header=False):
        if not lang:
            print("ERROR: lang is not defined.")
            return
        if show_header:
            print(f"\n## SNIPET_ID {id} Result: {lang}\n")
        cmd = self.get_lib(lang) + self._canon_cmd(lang, text_lines)
        if exec_file:
            self._exec_tempfile(lang, cmd)
        else:
            self._exec_pipeline(lang, cmd)

    def _exec_tempfile(self, lang, cmd):
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

    def exec_snipets(self, snipet_ids=None, exec_file=False, unbuffered=True,
                     show_header=False):
        if unbuffered:
            os.environ["PYTHONUNBUFFERED"] = "YES"
        qlist = self.quotes["snipet"]
        if len(snipet_ids) == 0 or snipet_ids is None:
            for i,x in enumerate(qlist):
                self._exec_cmd(i, x["lang"], x["snipet"],
                               exec_file, show_header)
        else:
            for i in snipet_ids:
                self._exec_cmd(i, qlist[i]["lang"], qlist[i]["snipet"],
                               exec_file, show_header)

    def show_snipets(self, snipet_ids=None, show_header=True, show_lineno=True):
        qlist = self.quotes["snipet"]
        if len(snipet_ids) == 0 or snipet_ids is None:
            for i,x in enumerate(qlist):
                opts = {
                    "lang": x["lang"],
                    "show_header": show_header,
                    "show_lineno": show_lineno,
                    "lineno": 0,
                    }
                self.show_libs(opts)
                self.print_snipet(i, x["snipet"], opts)
        else:
            for i in snipet_ids:
                opts = {
                    "lang": qlist[i]["lang"],
                    "show_header": show_header,
                    "show_lineno": show_lineno,
                    "lineno": 0,
                    }
                self.show_libs(opts)
                self.print_snipet(i, qlist[i]["snipet"], opts)
        sys.stdout.flush()

    def show_libs(self, opts):
        qlist = self.quotes["lib"]
        if len(qlist) == 0:
            return
        if opts["show_header"]:
            print(f"\n## LIBRARY: {opts['lang']}\n")
        for i,x in enumerate(qlist):
            if x["lang"] == opts["lang"]:
                if opts["show_lineno"]:
                    for line in x["snipet"]:
                        opts["lineno"] += 1
                        print(f"{opts['lineno']:02}: {line}")
                else:
                    print(f"{''.join(x['snipet'])}\n")

    def print_snipet(self, id, text_lines, opts):
        if opts["show_header"]:
            print(f"\n## SNIPET_ID {id}: {opts['lang']}\n")
        if opts["show_lineno"]:
            for line in text_lines:
                opts["lineno"] += 1
                print(f"{opts['lineno']:02}: {line}", end="")
        else:
            print(f"{''.join(text_lines)}")

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
ap.add_argument("-S", action="store_false", dest="show_snipets",
                help="disable to show the snipet ")
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
    md.show_snipets(snipet_ids, show_header=opt.show_header,
                    show_lineno=opt.show_lineno)
if opt.exec_snipets:
    md.exec_snipets(snipet_ids, exec_file=opt.exec_file,
                    unbuffered=opt.unbuffered,
                    show_header=opt.show_header)
