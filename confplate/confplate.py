#!/usr/bin/env python3
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
import string
import re

from jinja2 import Environment, FileSystemLoader, StrictUndefined, meta

__VERSION__ = '0.1.4'


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

    def get_template_vars(self, ignorevars=[], sort=True, maxnestlevels=100):
        """Return a list of all variables found in the template


        Arguments:

            ignorevars  -- a list of variables that are removed from the output
            sort        -- True (default) or False if returned list should be sorted
            maxnestlevels -- a positve integer which defines how deep you can nest templates with includes
        """

        tplvars = []
        templates = []
        templatesseen = []
        nestlevels = 0

        env = Environment(loader=FileSystemLoader(self.templatepath), undefined=StrictUndefined)

        templates.append(self.templatename)
        templatesseen.append(self.templatename)

        while len(templates) > 0:
            tpl = templates.pop()
            nested = False

            tplsrc = env.loader.get_source(env, tpl)[0]
            ast = env.parse(tplsrc)

            for template in meta.find_referenced_templates(ast):
                if template in templatesseen:
                    raise Exception("Template loop detected: \"{}\" references \"{}\" which was seen earlier".format(tpl, template))
                else:
                    templates.append(template)
                    templatesseen.append(template)
                    nested = True

            for e in meta.find_undeclared_variables(ast):
                if not e in ignorevars and not e in tplvars:
                    tplvars.append(e)

            if nested and nestlevels >= maxnestlevels:
                raise Exception("Maximum template nesting depth of {} reached in template {}".format(maxnestlevels, template))
            else:
                nestlevels += 1

        if sort:
            return sorted(tplvars)
        else:
            return tplvars

    def get_unset_template_vars(self, ignorevars=[]):
        """Return a list of variables that have no assigned value

        Arguments:
            ignorevars  -- a list of variables that are removed from the output
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

    def get_vardicts_from_csv(self, filename, filterfield, filtervalue, filterfield2, filtervalue2):
        """
        Load variables from CSV. Filter if ff and fv are set.
        """
        l = []


        with open(filename, 'r') as f:
            reader = csv.DictReader(f)

            if (filterfield and filtervalue) and (filterfield2 and filtervalue2):
                for row in reader:
                    if (re.search(filtervalue,row[filterfield]) and re.search(filtervalue2,row[filterfield2])):
                        l.append(row)

            elif (filterfield and filtervalue):
                for row in reader:
                    if (re.search(filtervalue,row[filterfield])):
                        l.append(row)
                        
            else:
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

        print("\nVariables used in template %s\n" % (tpl.templatename))

        for v in tplvars:
            # TODO No support for data types yet
            #print("\t* %s\t\t(%s)" % (v, tplvars[v]))
            print("\t%s" % v)

        print('\n')

    def list_unset_vars(self, variables):
        sys.stderr.write('\nThe following variables are not set\n\n')

        for v in variables:
            # TODO No support for data types yet
            #print("\t* %s\t\t(%s)" % (v, tplvars[v]))
            sys.stderr.write("\t%s\n" % v)

        sys.stderr.write('\nPlease specify them or use the -f/--force option to replace unset variables with the string UNSET\n\n')

    def generate_csv_header(self, tpl, separator=','):
        """Print a CSV header to the commandline from variables found in a template

        Arguments:
            tpl       -- an instance of ConfPlate, which is already configured
                         with a path to a template
            separator -- a string specifying the separator between the column
                         headers. Defaults to a comma: ","
        """
        tplvars = tpl.get_template_vars()

        print(separator.join(tplvars))

    def interactive_mode(self, tpl):
        tplvars = tpl.get_template_vars()
        d = {}

        for v in tplvars:
            try:
                s = input("%s: " % v)
            except KeyboardInterrupt:
                print('Quitting interactive mode: You have pressed Ctrl + c')
                sys.exit(1)

            d[v] = s

        return d


def show_usage_examples():
    print('Sorry, not yet')


def main():
    optparser = OptionParser(usage="usage: %prog [options] template-file [template variables ...]")
    optparser.add_option('', '--help-examples', dest='examples', action='store_true',
                         help='Show usage examples', default=False)
    optparser.add_option('-l', '--list-variables', dest='listvariables', action='store_true',
                         help='List template variables', default=False)
    optparser.add_option('-f', '--force', dest='force', action='store_true',
                         help='Replace unset variables with UNSET and continue', default=False)
    optparser.add_option('-i', '--input-csv', dest='inputcsv',
                         help='Read variables from a CSV file')
    optparser.add_option('-g', '--generate-csv-header', dest='generatecsvheader', action='store_true',
                         help='Generate the CSV header for an input file based on a given template', default=False)
    optparser.add_option('-F', '--csv-field-separator', dest='csvfieldseparator', default=',',
                         help='Sets the field separator for the CSV header output')
    optparser.add_option('--ff','--filter-field', dest='filterfield',help='Filter CSV on value of field')
    optparser.add_option('--fv','--filter-value', dest='filtervalue',help='Value to match in FILTERFIELD (RegEx allowed)')
    optparser.add_option('--ff2','--filter-field2', dest='filterfield2',help='Filter CSV on value of field 2')
    optparser.add_option('--fv2','--filter-value2', dest='filtervalue2',help='Value to match in FILTERFIELD2 (RegEx allowed)')
    optparser.add_option('--nolf', dest='nolf',action='store_true',help='Omits LF between outputting CSV rows')
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
    # Generate CSV header template
    #--------------------------------------------------------------------------
    if options.generatecsvheader:
        tpl = ConfPlate()
        tpl.templatepath = os.path.dirname(args[0])
        tpl.templatename = os.path.basename(args[0])

        cli = Cli()
        cli.generate_csv_header(tpl, separator=options.csvfieldseparator)

        sys.exit(0)

    #--------------------------------------------------------------------------
    # Render template
    #--------------------------------------------------------------------------
    tpl = ConfPlate()
    tpl.templatepath = os.path.dirname(args[0])
    tpl.templatename = os.path.basename(args[0])

    cli = Cli()

    # Get filters
    filterfield = options.filterfield
    filtervalue = options.filtervalue
    filterfield2 = options.filterfield2
    filtervalue2 = options.filtervalue2
   
    if options.filterfield and not options.filtervalue:
        sys.stderr.write("You must specify a value to filter on with --fv if you have specified filter field with --ff\n")
        sys.exit(-1)

    if  options.filtervalue and not options.filterfield:
        sys.stderr.write("You must specify a field to filter on with --ff if you have specified filter value with --fv\n")
        sys.exit(-1)

    if options.filterfield2 and not options.filtervalue2:
        sys.stderr.write("You must specify a value to filter on with --fv2 if you have specified filter field with --ff2\n")
        sys.exit(-1)

    if  options.filtervalue2 and not options.filterfield2:
        sys.stderr.write("You must specify a field to filter on with --ff2 if you have specified filter value with --fv2\n")
        sys.exit(-1)

    # Read variables from CSV file
    if options.inputcsv:
        i = 1

        csvfilename = options.inputcsv

        if not os.path.exists(csvfilename):
            sys.stderr.write("CSV input file \"%s\" does not exist!\n" % csvfilename)
            sys.exit(-1)

        tplvarlist = tpl.get_vardicts_from_csv(csvfilename,filterfield,filtervalue,filterfield2,filtervalue2)

        for e in tplvarlist:
            if options.force:
                tpl.set_variables(e, unset='UNSET')
                if options.nolf:
                    # render without LF between CSV row outputs
                    print(tpl.render_template(),end='')
                else:
                    print(tpl.render_template())

            else:
                unsetvars = tpl.set_variables(e)
                if options.nolf:
                    # render without LF between CSV row outputs
                    print(tpl.render_template(),end='')
                else:
                    print(tpl.render_template())

                if len(unsetvars) > 0:
                    print("CSV row %i" % i)
                    cli.list_unset_vars(unsetvars)
                    sys.exit(-1)

        sys.exit(0)

    # Read variables from cmdline
    if len(args) > 1:
        tplvars, failed = cli.cli_vars_to_dict(args[1:])

        if len(failed) > 0:
            sys.stderr.write('\nUnabled to parse the following variables\n\n')

            for e in failed:
                sys.stderr.write("\t%s\n" % e)

            sys.stderr.write('\nVariable/Value pairs are separated by the equals sign\n\n')
            sys.stderr.write('Example:\n\n\tIP_ADDRESS=192.0.2.5 NETMASK=255.255.255.0 DOMAIN=example.net\n\n')
            sys.exit(-1)

        if options.force:
            tpl.set_variables(tplvars, unset='UNSET')
        else:
            unsetvars = tpl.set_variables(tplvars)

            if len(unsetvars) > 0:
                cli.list_unset_vars(unsetvars)
                sys.exit(-1)

        print(tpl.render_template())

        sys.exit(0)

    # Interactive mode: Prompt user for variables
    else:
        # Useless, but every good program needs a 'force' parameter
        if options.force:
            tpl.set_variables({}, unset='UNSET')
        else:
            tplvars = cli.interactive_mode(tpl)
            tpl.set_variables(tplvars)

        print(tpl.render_template())

        sys.exit(0)

if __name__ == '__main__':
    main()
