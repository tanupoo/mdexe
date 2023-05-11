#!/usr/bin/env python

from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter
from ReadMarkdown import ReadMarkdown

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
                    "It takes the first snipet if the -i option is omitted "
                    "AND the -x option is specified.")
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
if len(snipet_ids) > 0:
    for i in snipet_ids:
        if i not in md.get_snipet_ids():
            print(f"ERROR: snipet ID {i} doesn't exist.")
            exit(-1)

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
