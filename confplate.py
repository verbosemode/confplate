#!/usr/bin/env python
#
# Config file generator based on Jinja2 templates
#
# License:
#
# The MIT License (MIT)
# 
# Copyright (c) 2013 Jochen Bartl <jochenbartl@mail.de>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import sys
from optparse import OptionParser
import logging
import os.path
import csv

from jinja2 import Environment, FileSystemLoader, StrictUndefined, meta

VERSION = '0.1'

class ConfPlate(object):
    def __init__(self):
        self.templatepath = ""
        self.templatename = ""
        self.variables = {}

        self.logger = logging.getLogger('ConfPlate')
        self.logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def parse_var_types(self, tplvars):
        """
        TODO do we really need data types???
        """

        d = {}
        vartypes = ['STRING', 'BOOL']

        for v in tplvars:
            e = v.split('_')

            if len(e) > 1 and e[-1] in vartypes:
                d[''.join(e[0:-1])] = e[-1].lower()
            else:
                d[v] = 'STRING'

        return sorted(d)

    def get_template_vars(self, ignorevars=[]):
        env = Environment(loader=FileSystemLoader(self.templatepath), undefined=StrictUndefined)

        tplsrc = env.loader.get_source(env, self.templatename)[0]
        ast = env.parse(tplsrc)
        tplvars = meta.find_undeclared_variables(ast)

        # TODO Option for returing data unordered?
        return sorted([e for e in tplvars if not e in ignorevars])

    def get_unset_template_vars(self, ignorevars=[]):
        """
        Return a list of variables that have no assigned value
        """

        tplvars = self.get_template_vars()

        return [e for e in tplvars if not e in self.variables]

    def render_template(self):
        env = Environment(loader=FileSystemLoader(self.templatepath), undefined=StrictUndefined)
        tpl = env.get_template(self.templatename)

        return tpl.render(self.variables)

    def set_variables(self, variables, unset=''):
        """
        Set template variables and return a list with unused variables
        """

        tplvars = self.get_template_vars()
        l = []

        for e in tplvars:
            if not e in variables and len(unset) > 0:
                self.variables[e] = unset
            elif not e in variables:
                l.append(e)
            else:
                self.variables[e] = variables[e]

        return l

    def get_vardicts_from_csv(self, filename):
        l = []

        with open(filename, 'r') as f:
            reader = csv.DictReader(f)

            for row in reader:
                l.append(row)

        return l


class Cli(object):
    def __init__(self):
        self.logger = logging.getLogger('Cli')
        self.logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def cli_vars_to_dict(self, tplvars):
        """
        Converts a list of variables and values in the format NAME=VALUE
        into a dictionary.
        """

        d = {}
        failed = []

        for v in tplvars:
            try:
                varname, varval = v.split('=')
            except ValueError:
                failed.append(v)
                continue

            d[varname] = varval

        return d, failed

    def list_template_vars(self, tpl):

        tplvars = tpl.get_template_vars()
        tplvars = tpl.parse_var_types(tplvars)

        print "\nVariables used in template %s\n" % (tpl.templatename)

        for v in tplvars:
            # TODO No support for data types yet
            #print "\t* %s\t\t(%s)" % (v, tplvars[v])
            print "\t%s" % v

        print '\n'

    def list_unset_vars(self, variables):
        sys.stderr.write("\nThe following variables are not set\n\n")

        for v in variables:
            # TODO No support for data types yet
            #print "\t* %s\t\t(%s)" % (v, tplvars[v])
            sys.stderr.write("\t%s\n" % v)

        sys.stderr.write("\nPlease specify them or use the -f/--force option to replace unset variables with the string UNSET\n\n")

    def interactive_mode(self, tpl):
        tplvars = tpl.get_template_vars()
        d = {}

        for v in tplvars:
            try:
                s = raw_input("%s: " % v)
            except KeyboardInterrupt:
                print 'Mhkay, you have pressed Ctrl+c. We will have to start all over again...Bye, Bye'
                sys.exit(1)

            d[v] = s

        return d


def show_usage_examples():
    print """Sorry, not yet"""

if __name__ == '__main__':
    optparser = OptionParser(usage="usage: %prog [options] template-file [template variables ...]")
    optparser.add_option('', '--help-examples', dest='examples', action='store_true',
                            help='Show usage examples', default=False)
    optparser.add_option('-l', '--list-variables', dest='listvariables', action='store_true',
                            help='List template variables', default=False)
    optparser.add_option('-f', '--force', dest='force', action='store_true',
                            help='Replace unset variables with UNSET and continue', default=False)
    optparser.add_option('-i', '--input-csv', dest='inputcsv',
                            help='Read variables from a CSV file')
    #optparser.add_option('-D', '--debug', dest='debug', action='store_true',
    #                        help='Enable debug mode', default=False)

    (options, args) = optparser.parse_args()

    #if options.debug:
    #    logger.setLevel(logging.DEBUG)

    #--------------------------------------------------------------------------
    # Show usage examples 
    #--------------------------------------------------------------------------
    if options.examples:
        show_usage_examples()
        sys.exit(0)

    #--------------------------------------------------------------------------
    # Argument error handling
    #--------------------------------------------------------------------------
    if not len(args) > 0:
        optparser.print_help()
        sys.exit(-1)
    else:
        if not os.path.exists(args[0]):
            sys.stderr.write("Template file \"%s\" does not exist!\n" % args[0])
            sys.exit(-1)

    #--------------------------------------------------------------------------
    # List template variables
    #--------------------------------------------------------------------------
    if options.listvariables:
        tpl = ConfPlate()
        tpl.templatepath = os.path.dirname(args[0])
        tpl.templatename = os.path.basename(args[0])

        cli = Cli()
        cli.list_template_vars(tpl)

        sys.exit(0)

    #--------------------------------------------------------------------------
    # Render template
    #--------------------------------------------------------------------------
    tpl = ConfPlate()
    tpl.templatepath = os.path.dirname(args[0])
    tpl.templatename = os.path.basename(args[0])

    cli = Cli()

    # Read variables from CSV file
    if options.inputcsv:
        i = 1

        csvfilename = options.inputcsv

        if not os.path.exists(csvfilename):
            sys.stderr.write("CSV input file \"%s\" does not exist!\n" % csvfilename)
            sys.exit(-1)

        tplvarlist = tpl.get_vardicts_from_csv(csvfilename)

        for e in tplvarlist:
            if options.force:
                tpl.set_variables(e, unset='UNSET')
                print tpl.render_template()
            else:
                unsetvars = tpl.set_variables(e)

                print tpl.render_template()

            if len(unsetvars) > 0:
                print "CSV row %i" % i
                cli.list_unset_vars(unsetvars)
                sys.exit(-1)

        sys.exit(0)

    # Read variables from cmdline
    if len(args) > 1:
        tplvars, failed = cli.cli_vars_to_dict(args[1:])

        if len(failed) > 0:
            sys.stderr.write("\nUnabled to parse the following variables\n\n")

            for e in failed:
                sys.stderr.write("\t%s\n" % e)

            sys.stderr.write("\nVariable/Value pairs are separated by the equals sign\n\n")
            sys.stderr.write("Example:\n\n\tIP_ADDRESS=192.0.2.5 NETMASK=255.255.255.0 DOMAIN=example.net\n\n")
            sys.exit(-1)

        if options.force:
            tpl.set_variables(tplvars, unset='UNSET')
        else:
            unsetvars = tpl.set_variables(tplvars)

            if len(unsetvars) > 0:
                cli.list_unset_vars(unsetvars)
                sys.exit(-1)

        print tpl.render_template()

        sys.exit(0)

    # Interactive mode: Prompt user for variables
    else:
        # Useless, but every good program needs a 'force' parameter
        if options.force:
            tpl.set_variables({}, unset='UNSET')
        else:
            tplvars = cli.interactive_mode(tpl)
            tpl.set_variables(tplvars)

        print
        print tpl.render_template()

        sys.exit(0)
