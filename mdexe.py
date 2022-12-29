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
from pydantic import BaseModel
from typing import List, Optional, Literal

re_start = re.compile("^```\s*([\w\d]+)")
re_ext_1 = re.compile("^#%(name:(.*)|lib(.*))")
re_ext_inc = re.compile("^#%inc:(.*)")
re_quote = re.compile("^```")

class Snipet(BaseModel):
    lang: str
    name: Optional[str] = None
    name2: Optional[str] = None
    lib: bool = False
    text: List[str] = []
    working: Literal[0, 1, 2] = 0
    id: str = 0

class ReadMarkdown:

    def __init__(self, input_file=None):
        if input_file is not None:
            fd = open(input_file)
        else:
            fd = sys.stdin

        """
        self.snipets:
            List[Snipet]
        """
        self.quotes = []

        # phase1: read the snipets anyway
        in_quote = False
        snipet_id = 1
        # take only text in the mean snipets.
        for line in fd:
            r = re_quote.match(line)
            if r:
                # means the end of snipet, OR other quote.
                if in_quote:
                    # found the end of a snipet.
                    in_quote = False
                    if not snipet.lib:
                        # assign id if not a lib.
                        snipet.id = str(snipet_id)
                        snipet_id += 1
                    self.quotes.append(snipet)
                else:
                    # not in quote.
                    r = re_start.match(line)
                    if r:
                        # found a start of a snipet.
                        in_quote = True
                        snipet = Snipet.parse_obj({
                                "lang": self._canon_lang(r.group(1))})
            elif in_quote:
                # in quote.
                r = re_ext_1.match(line)
                if r:
                    if r.group(1).startswith("name:"):
                        snipet.name = r.group(2).strip()
                    elif r.group(1).startswith("lib"):
                        snipet.lib = True
                        if r.group(3) and r.group(3).startswith(":"):
                            snipet.name2 = r.group(3)[1:].strip()
                else:
                    snipet.text.append(line)
        #
        if opt.debug:
            import json
            print("## phase1")
            for x in self.quotes:
                print(json.dumps(x.dict(), indent=4))

        # phase 2
        def get_snipet(name: str) -> Snipet:
            for s in self.quotes:
                if ((s.name and s.name == name) or
                    (s.name2 and s.name2 == name)):
                    return format_snipet(s)
            else:
                return None

        def format_snipet(snipet: Snipet) -> List[str]:
            if snipet.working == 2:
                return snipet.text
            elif snipet.working == 1:
                raise ValueError(f"{snipet.name} was read recursively.")
            # if snipet.working == 0
            snipet.working = 1
            #
            new_text = []
            for t in snipet.text:
                r = re_ext_inc.match(t)
                if r:
                    for i,n in enumerate(r.group(1).split(",")):
                        if i:
                            new_text.append("\n")
                        name = n.strip()
                        inc = get_snipet(name)
                        if inc:
                            new_text.extend(inc)
                        else:
                            raise ValueError(f"{name} doesn't exist.")
                else:
                    new_text.append(t)
            snipet.working = 2
            snipet.text = new_text
            return snipet.text

        for i,s in enumerate(self.quotes):
            format_snipet(s)
        #
        if opt.debug:
            import json
            print("## phase2")
            for x in self.quotes:
                print(json.dumps(x.dict(), indent=4))

    def _exec_cmd(self, lang, code_lines, envkeys, exec_file=False):
        if lang == "php":
            if "<?php" not in code_lines[0]:
                # XXX should be find()
                code_lines.insert(0, "<?php\n")
        code = "".join(code_lines)
        if exec_file:
            self._exec_tempfile(lang, code, envkeys)
        else:
            self._exec_pipeline(lang, code, envkeys)

    def _exec_tempfile(self, lang, cmd, envkeys):
        def reader(fd):
            data = os.read(fd, 1024)
            #print(data.decode(), end="", flush=True)
            return data
        with tempfile.NamedTemporaryFile("w") as tmp:
            tmp.write(cmd)
            tmp.flush()
            pty.spawn(shlex.split(f"{lang} {tmp.name}"), reader)

    def _exec_pipeline(self, lang, cmd, envkeys):
        with Popen(shlex.split(lang),
                stdin=PIPE, stdout=PIPE, stderr=PIPE,
                   text=True, env=envkeys) as proc:
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
                    code_lines.extend(m["snipet"])
                    break
            else:
                raise ValueError(f"ERROR: name={n} is not defined.")
        code_lines.extend(snipet["snipet"])
        return code_lines

    def get_snipet_by_id(self, id: int) -> Snipet:
        for s in self.quotes:
            if s.id == id:
                return s
        else:
            return None

    def print_header(self, tag, snipet, show_header):
        if show_header:
            print("\n"
                  f"## {tag}: ID:{snipet.id} LANG:{snipet.lang} "
                  f"NAME:{snipet.name}\n")

    def exec_snipets(self, snipet_ids, exec_file=False, envkeys=None,
                     unbuffered=True, show_header=False):
        if unbuffered:
            os.environ["PYTHONUNBUFFERED"] = "YES"
        if len(snipet_ids) == 0:
            snipet_ids = [s.id for s in self.quotes if s.id != 0]
        for i in snipet_ids:
            s = self.get_snipet_by_id(i)
            self.print_header("RESULT", s, show_header)
            self._exec_cmd(s.lang, s.text, envkeys, exec_file)

    def show_snipets(self, snipet_ids, show_header=True, show_lineno=True,
                     show_libs=False):
        if len(snipet_ids) == 0:
            snipet_ids = [s.id for s in self.quotes if s.id != 0]
        for i in snipet_ids:
            s = self.get_snipet_by_id(i)
            lineno = 0
            self.print_header("SNIPET", s, show_header)
            if show_lineno:
                for line in s.text:
                    lineno += 1
                    print(f"{lineno:02}: {line}", end="")
            else:
                print(f"{''.join(s.text)}")
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
                    "It takes the first snipet if the -i option is omitted AND the -x option is specified.")
ap.add_argument("-x", action="store_true", dest="exec_snipets",
                help="execute snipets specified the IDs seperated by a comma.")
ap.add_argument("-e", action="append", dest="_envkeys",
                help="specify KEY=VAL as an environment variable "
                "so that you can embed KEY into your document "
                "to execute with the VAL. "
                "It allows to be used multiple times.")
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
ap.add_argument("-d", action="store_true", dest="debug",
                help="enable debug mode.")
opt = ap.parse_args()

opt.envkeys = None
if opt._envkeys:
    opt.envkeys = {}
    for ek in opt._envkeys:
        if "=" not in ek:
            raise ValueError(f"ERROR: {ek} doesn't look key=val")
        opt.envkeys.update([(ek.split("="))])

md = ReadMarkdown(opt.input_file)
#
if opt.snipet_ids and "0" in opt.snipet_ids:
    print("ERROR: snipet ID must not be zero.")
    exit(-1)
if opt.exec_snipets:
    if opt.snipet_ids == "all":
        snipet_ids = []
    elif opt.snipet_ids is not None:
        snipet_ids = opt.snipet_ids.split(",")
    else:
        snipet_ids = ["1"]
else:
    if opt.snipet_ids == "all":
        snipet_ids = []
    elif opt.snipet_ids is not None:
        snipet_ids = opt.snipet_ids.split(",")
    else:
        snipet_ids = []

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
                    envkeys=opt.envkeys,
                    unbuffered=opt.unbuffered,
                    show_header=opt.show_header)
