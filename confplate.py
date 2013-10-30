#!/usr/bin/env python
#
# License:
#
# Config file generator based on Jinja2 templates
# Copyright (C) 2013  Jochen Bartl <jochenbartl@mail.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
from optparse import OptionParser
import logging
import os.path
import csv

from jinja2 import Environment, FileSystemLoader, StrictUndefined, meta

# FIXME Clean-up + hints on how to get PyGTK installed
# Only show warning if GUI is started intentionally
try:
    import pygtk
    pygtk.require("2.0")
    import gtk
except:
    #print 'PyGTK not installed'
    pass


VERSION = '0.1'


class ConfPlate(object):
    def __init__(self):
        self.templatepath = ""
        self.templatename = ""
        self.variables = {}

        # Logging
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
        # Logging
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


class Gui(object):
    def delete_event(self, widget, event, data=None):
        gtk.main_quit()

        return False

    def __init__(self):
        self.window = self.add_window()

        self.vbox = self.add_vbox(self.window)

        #self.button = self.add_button(self.vbox)
        #self.checkbutton = self.add_checkbutton(self.vbox)

        #self.vbox.pack_start(self.button, expand=False)
        #self.window.show_all()

        # Logging
        self.logger = logging.getLogger('TplGui')
        self.logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def set_variable_names(self, variables):

        for k in variables:
            hbox = gtk.HBox(False, 8)

            label = self.add_label(hbox)
            label.set_text(k)

            entry = self.add_entry(hbox)
            #entry.set_text(self.d[k])
            #entry.set_text('')
            self.vbox.add(hbox)

    def show(self):
        self.window.show_all()

    def add_window(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        #window.set_size_request(400, 400)
        window.connect("delete_event", self.delete_event)
        #window.set_border_width(8)

        return window

    def add_vbox(self, widget):
        vbox = gtk.VBox(False, 8)
        widget.add(vbox)

        return vbox

    def add_hbox(self, widget):
        hbox = gtk.HBox(False, 8)
        widget.add(hbox)

        return hbox

    def add_label(self, widget):
        label = gtk.Label()
        widget.add(label)

        return label

    def add_entry(self, widget):
        entry = gtk.Entry()
        widget.add(entry)

        return entry

    #def add_button(self, widget):
    #    button = gtk.Button(label="Colorize!")
    #    button.set_size_request(100, 100)
    #    button.connect("clicked", self.button_clicked_event)
    #    widget.pack_start(button, expand=False)

    #    return button


def show_usage_examples():
    print """Sorry, not yet"""




if __name__ == '__main__':
    optparser = OptionParser(usage="usage: %prog [options] template-file [template variables ...]")
    #optparser.add_option("-C", "--community", dest="community",
    #                        help="SNMP community", default="public")
    #optparser.add_option("-S", "--snmpversion", dest="snmpversion",
    #                        help="SNMP version (1, 2c)", default="2c")
    #optparser.add_option("-P", "--statspath", dest="statspath",
    #                        help="Path were statistic files are stored")
    optparser.add_option('', '--help-examples', dest='examples', action='store_true',
                            help='Show usage examples', default=False)
    optparser.add_option('-g', '--gui', dest='gui', action='store_true',
                            help='Start the GUI', default=False)
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
    # GUI
    #--------------------------------------------------------------------------
    if options.gui:
        # FIXME Tpl filename / path should be optional
        tpl = ConfPlate()
        tpl.templatepath = os.path.dirname(args[0])
        tpl.templatename = os.path.basename(args[0])

        tplvars = tpl.get_template_vars()

        # Any variables set on command line?
        # Time to read variables from CSV?

        tplgui = Gui()
        tplgui.set_variable_names(tplvars)
        tplgui.show()
        gtk.main()

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


