#!/usr/bin/env python
################################################################################
# gen_filenames_defines.py
################################################################################
"""
# Script to go through the code line of any code base and generate a list
# of filenames, and a list of mnemonics to identify each file. This mnemonic
# becomes the filename-index in downstream processing.
#
# This script is written somewhat generically so that it can be included
# as part of the src/ Makefile system of most C/C++ code bases.
"""

import sys

###############################################################################
# main() driver
###############################################################################
def main():
    """
    Shell to call do_main() with command-line arguments.
    """
    do_main(sys.argv[1:])

###############################################################################
# def do_main(args) -> bool:
def do_main(args):
    """
    Main driver to search through the code base looking for source files.
    """

    retval = False

    if len(sys.argv) < 2:
        print("Usage: %s <root src-dir>" % (sys.argv[0]))

        print("Example: %s $HOME/Code/myProject/" % (sys.argv[0]))
        sys.exit(1)

    # shut pylint up
    for arg in args:
        print (arg)

    return retval

###############################################################################
# Start of the script: Execute only if run as a script
###############################################################################
if __name__ == "__main__":
    main()
