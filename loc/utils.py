#!/usr/bin/python3
################################################################################
# utils.py
# SPDX-License-Identifier: Apache-2.0
################################################################################
"""
Purpose: Utility helper methods used in different LOC Python scripts.
"""

import os
from inspect import currentframe

###############################################################################
# Minimalist helper routines live here
#
def dir_exists(dir_name):
    """
    Boolean, check if a directory exists.
    """
    try:
        os.stat(dir_name)
    except OSError as err:
        print("[" + fnl() + "] OS error: " + "{0}".format(err))
        return False
    return True

# ------------------------------------------------------------------------------
def lineno():
    """
    Return line number at calling function.
    """
    curr_frame = currentframe()
    return curr_frame.f_back.f_lineno

# ------------------------------------------------------------------------------
def fnl():
    """
    Return calling function's brief-name and line number
    Ref: https://stackoverflow.com/questions/35701624/pylint-w0212-protected-access
    ... on need for use of pylint disable directive.
    """
    curr_frame = currentframe()
    # pylint: disable=protected-access
    func_name = curr_frame.f_back.f_back.f_code.co_name
    # pylint: enable=protected-access
    line_num = curr_frame.f_back.f_back.f_lineno
    return func_name + ':' + str(line_num)
