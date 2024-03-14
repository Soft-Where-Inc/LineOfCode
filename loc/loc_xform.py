#!/usr/bin/python3
################################################################################
# loc_xform.py
# SPDX-License-Identifier: Apache-2.0
################################################################################
"""
Helper module to encode (fileindex / line #) pair to LOC-ID and to decode LOC-ID
# to constituent fileindex / line #.
"""

# LOC-encoding numbers. -HARD-Dependency on what's generated in loc.h
LOC_NBITS_FILES = 15
LOC_NBITS_LINES = 16
LOC__MASK_LINES = 0xffff

###############################################################################
# Minimalist encode / decode routines live here
#
def loc_encode(file_index:int, line_num:int) -> int:
    """
    Encode a pair of (file-index, line#) and return a LOC-ID.
    """
    return (file_index << LOC_NBITS_LINES) | line_num
#
def loc_decode(loc_id:int) -> (int, int):
    """
    Crack open a LOC ID and return a pair (file-index, line#)
    """
    file_index = loc_id >> LOC_NBITS_LINES
    line_num = loc_id & LOC__MASK_LINES
    return (file_index, line_num)
