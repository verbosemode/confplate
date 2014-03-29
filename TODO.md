# TODO

## ConfPlate core
* API clean-up
* Document methods
* Implement types for variables
  - Allows to give hints to the UI on how to display / verify user input
  - http://packetlife.net/blog/2013/jul/26/lessons-learned-writing-custom-config-builder/
  - Maybe Jinja filters can be abused for that

## CLI
* Catch exceptions and display user-friendly error messages
  - jinja2.exceptions.TemplateSyntaxError, ...
  - Error message should include template name and line number if possible
  - User should not see Python error messages
  - Make it possible to create a debug log
* Replace optparse with argparse

## Tests

## PyPi support for easy installation

## Web interface
* Based on Flask
