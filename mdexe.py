#!/usr/bin/env python

import sys
import re
from subprocess import Popen, PIPE
import shlex
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter

re_start = re.compile("^```\s*([\w\d]+)")
re_end = re.compile("^```")

def canon_cmd(lang, cmd):
    if lang == "php":
        if "<?php" not in cmd[0]:
            cmd.insert(0, "<?php\n")
    return cmd

def exec_cmd(lang, cmd_base):
    print("\n## Example\n")
    cmd = "".join(canon_cmd(lang, cmd_base))
    if opt.show_script:
        if opt.show_markdown:
            print(f"```\n{''.join(cmd_base)}```\n")
        else:
            print("".join(cmd_base))
    with Popen(shlex.split(lang),
               stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True) as proc:
        output, errs = proc.communicate(input=cmd, timeout=5)
    if errs:
        print(errs)
    if output:
        if opt.show_markdown:
            print(f"```\n{output}```")
        else:
            print(output)

def canon_lang(keyword):
    if keyword in ["node", "js", "javascript"]:
        return "node"
    elif keyword in ["python", "sh", "bash", "zsh", "php"]:
        return keyword
    else:
        raise ValueError(f"INFO: ignore ```{keyword}, it doesn't registered.")

ap = ArgumentParser(
        description="execute code picked from markdown by key.",
        formatter_class=ArgumentDefaultsHelpFormatter)
ap.add_argument("input_file", nargs="*",
                help="specify a filename containing code snipet. "
                    "'-' means stdin.")
ap.add_argument("-s", action="store", dest="script_id",
                help="specify the script identifier, separated by comma.")
ap.add_argument("-A", action="store_true", dest="execute_all",
                help="specify to execute all snipets.")
ap.add_argument("-M", action="store_true", dest="show_markdown",
                help="show output in markdown.")
ap.add_argument("-S", action="store_true", dest="show_script",
                help="show original script.")
opt = ap.parse_args()

#
if not (opt.execute_all or opt.script_id):
    print("ERROR: either -s or -A is required to specify a snipet.")
    ap.print_help()
    exit(0)

if opt.script_id is None:
    script_id_list = []
else:
    script_id_list = [int(i) for i in opt.script_id.split(",")]

#
if opt.input_file:
    fd = open(opt.input_file)
else:
    fd = sys.stdin

f_snipet = False
script_id = 0
for line in fd:
    r = re_start.match(line)
    if r:
        f_snipet = True
        script_id += 1
        try:
            lang = canon_lang(r.group(1))
        except ValueError:
            continue
        snipet = [] # initialize
        continue
    r = re_end.match(line)
    if r and f_snipet is True:
        f_snipet = False
        if len(script_id_list) == 0 or script_id in script_id_list:
            exec_cmd(lang, snipet)
        snipet = []
        continue
    if f_snipet:
        snipet.append(line)

