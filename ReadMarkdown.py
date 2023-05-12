#!/usr/bin/env python

import sys
import re
from subprocess import Popen, PIPE, DEVNULL
import shlex
import tempfile
import pty
import os
from io import StringIO
from pydantic import BaseModel
from typing import List, Optional, Literal

re_quote = re.compile("^(```+)")
re_start = re.compile("^(```+)\s*([\w\d]+)")
re_ext_1 = re.compile("^#%(name:(.*)|lib(.*))")
re_ext_inc = re.compile("^#%inc:(.*)")

class Snipet(BaseModel):
    lang: str
    name: Optional[str] = None
    name2: Optional[str] = None
    lib: bool = False
    text: List[str] = []
    working: Literal[0, 1, 2] = 0
    id: str = 0

class ReadMarkdown:

    def __init__(self, input_file=None, text=None, debug=False):
        if input_file is not None:
            fd = open(input_file)
        elif text is not None:
            fd = StringIO(text)
        else:
            fd = sys.stdin

        """
        self.quotes:
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
                                "lang": self._canon_lang(r.group(2))})
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
        if debug:
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
        if debug:
            import json
            print("## phase2")
            for x in self.quotes:
                print(json.dumps(x.dict(), indent=4))

    def _exec_cmd(self, lang, code_lines, envkeys, exec_file=False):
        if lang == "php":
            if "<?php" not in code_lines[0]:
                # XXX should be find()
                code_lines.insert(0, "<?php\n")
        elif "awk" in lang:
            # overwrite
            lang = f"{lang} -f"
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
        elif keyword in ["perl"]:
            return keyword
        elif keyword in ["awk", "gawk", "nawk"]:
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

    def get_snipet_ids(self, include_lib=False):
        if include_lib:
            return [s.id for s in self.quotes]
        else:
            return [s.id for s in self.quotes if not s.lib]

