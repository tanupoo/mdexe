#!/usr/bin/env python

import sys
import re
from subprocess import Popen, PIPE
import shlex
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter

re_start = re.compile("^```\s*([\w\d]+)(,\s*_lib)?")
re_end = re.compile("^```")

class ReadMarkdown:

    def __init__(self, input_file=None):
        if input_file is not None:
            fd = open(input_file)
        else:
            fd = sys.stdin
        #
        self.snipets = [] # {"lang":"code"}
        self.libs = []   # {"lang":"code"}
        in_snipet = False
        lang = None
        is_lib = False
        for line in fd:
            # find a start of a snipet.
            r = re_start.match(line)
            if r:
                if in_snipet is False:
                    in_snipet = True
                    lang = self._canon_lang(r.group(1))
                    if r.group(2):
                        is_lib = True
                    snipet = [] # initialize
                    continue
                else:
                    raise ValueError(
                            "ERROR: failed parsing quotaing mark to open")
            # find a end of a snipet.
            r = re_end.match(line)
            if r:
                if in_snipet is True:
                    if is_lib:
                        x = self.libs
                    else:
                        x = self.snipets
                    x.append({"lang":lang, "snipet":"".join(snipet)})
                    in_snipet = False
                    lang = None
                    is_lib = False
                    snipet = []
                    continue
                else:
                    raise ValueError(
                            "ERROR: failed parsing quotaing mark to close")
            # in snipet quote.
            if in_snipet is True:
                snipet.append(line)

    def _canon_cmd(self, lang, cmd):
        if lang == "php":
            if "<?php" not in cmd[0]:
                cmd.insert(0, "<?php\n")
        return cmd

    def _exec_cmd(self, id, lang, snipet, show_header=False):
        if show_header:
            print(f"## SNIPET_ID {id} Result: {lang}\n")
        cmd = "".join([x["snipet"] for x in self.libs if x["lang"] == lang])
        cmd += "".join(self._canon_cmd(lang, snipet))
        with Popen(shlex.split(lang),
                stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True) as proc:
            output, errs = proc.communicate(input=cmd, timeout=5)
        if errs:
            print(errs)
        if output:
            print(output)

    def _canon_lang(self, keyword):
        if keyword in ["node", "js", "javascript"]:
            return "node"
        elif keyword in ["sh", "bash", "zsh"]:
            return keyword
        elif keyword in ["python", "php"]:
            return keyword
        else:
            raise ValueError(f"INFO: ignore ```{keyword}, it doesn't registered.")

    def exec_snipets(self, snipet_ids=None, show_header=False):
        if len(snipet_ids) == 0 or snipet_ids is None:
            for i,x in enumerate(self.snipets):
                self._exec_cmd(i, x["lang"], x["snipet"], show_header)
        else:
            for i in snipet_ids:
                self._exec_cmd(i, self.snipets[i]["lang"],
                               self.snipets[i]["snipet"], show_header)

    def show_snipets(self, snipet_ids=None, show_header=True):
        #
        if len(snipet_ids) == 0 or snipet_ids is None:
            for i,x in enumerate(self.snipets):
                self.show_libs(x["lang"], show_header)
                self.print_snipet(i, x["lang"], x["snipet"], show_header)
        else:
            for i in snipet_ids:
                self.show_libs(self.snipets[i]["lang"], show_header)
                self.print_snipet(i, self.snipets[i]["lang"],
                                  self.snipets[i]["snipet"], show_header)

    def show_libs(self, lang, show_header=True):
        if len(self.libs) == 0:
            return
        if show_header:
            print(f"## LIBRARY: {lang}\n")
        for i,x in enumerate(self.libs):
            if x["lang"] == lang:
                print(f"{x['snipet']}\n")

    def print_snipet(self, id, lang, snipet, show_header=True):
        if show_header:
            print(f"## SNIPET_ID {id}: {lang}\n")
        print(f"{snipet}")

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
ap.add_argument("-s", action="store_true", dest="show_snipets",
                help="specify to show the snipets "
                    "even when the -x option is specified.")
ap.add_argument("-H", action="store_false", dest="show_header",
                help="with this option, disable to show each header.")
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
if (not opt.exec_snipets) or opt.show_snipets:
    md.show_snipets(snipet_ids, show_header=opt.show_header)
if opt.exec_snipets:
    md.exec_snipets(snipet_ids, show_header=opt.show_header)
