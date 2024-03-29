#!/usr/bin/env python3
################################################################################
# gen_loc_files.py
# SPDX-License-Identifier: Apache-2.0
################################################################################
"""
Script to go through the code line of any code base and generate a list
of filenames, and a list of mnemonics to identify each file. This mnemonic
becomes the filename-index in downstream processing.

This script is written somewhat generically so that it can be included
as part of the src/ Makefile system of most C/C++ code bases.

Outputs:
This script will generate the following files:
  loc.h           - LOC-interfaces header file, to be #include'd in files where
                    LOC* macros are used
  loc_tokens.h    - Header file listing tokens for all files processed
  loc_filenames.c - Contains definition of filename lookup array
  <product>_loc.c - .c file to be linked with loc_filenames.c to produce
                    product-specific helper decoder program.
"""

import sys
import os
import tempfile
import argparse
import subprocess as sp
import shutil

# Ref: https://stackoverflow.com/questions/3108285/in-python-script-how-do-i-set-pythonpath
# PYTHONPATH will become ".../LineOfCode" dir, to resolve loc package imports
LOC_THIS_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

# Ref: https://stackoverflow.com/questions/3108285/in-python-script-how-do-i-set-pythonpath
# pylint: disable-msg=wrong-import-position
sys.path.append(LOC_THIS_SCRIPT_DIR + '/..')

import loc.utils as locu

###############################################################################
# Global Variables: Used in multiple places. List here for documentation
###############################################################################

LOC_SCRIPT          = os.path.basename(__file__)
LOC_PKGSRC_DIR      = os.path.dirname(LOC_THIS_SCRIPT_DIR)
LOC_DBG_GENFILESDIR = '/tmp'

###############################################################################
# main() driver
###############################################################################
def main():
    """
    Shell to call do_main() with command-line arguments.
    """
    do_main(sys.argv[1:])

###############################################################################
def do_main(args) -> (bool, int, int, str):
    """
    Main driver to search through the code base looking for source files.
    """
    # pylint: disable-msg=too-many-locals
    # pylint: disable-msg=too-many-statements
    if len(sys.argv) < 2:
        print("Usage: %s <root src-dir>" % (sys.argv[0]))
        print("Example: %s $HOME/Code/myProject/" % (sys.argv[0]))
        sys.exit(1)

    # By default, .h / .c files will be generated in /tmp first.
    tmp_dir = tempfile.gettempdir() + '/'

    parsed_args = loc_parse_args(args)

    # Extract parsed cmdline flags into local variables
    src_root_dir     = parsed_args.src_root_dirname
    inc_dirname      = tmp_dir if parsed_args.inc_dirname is None else parsed_args.inc_dirname
    src_dirname      = tmp_dir if parsed_args.src_dirname is None else parsed_args.src_dirname
    loc_dirname      = tmp_dir if parsed_args.loc_dirname is None else parsed_args.loc_dirname
    verbose          = parsed_args.verbose
    gen_cflags       = parsed_args.gen_cflags
    gen_cflags_brief = parsed_args.gen_cflags_brief
    loc_debug        = parsed_args.debug_script
    dump_dup_files   = parsed_args.dump_dup_files

    loct_doth = "loc_tokens.h"
    loc_dotc = "loc_filenames.c"

    # Strip trailing '/' from dir-path-name, if so supplied
    if src_root_dir.endswith('/'):
        src_root_dir = os.path.dirname(src_root_dir)

    inc_dirname = os.path.abspath(inc_dirname)
    src_dirname = os.path.abspath(src_dirname)
    loc_dirname = os.path.abspath(loc_dirname) + '/'

    if loc_debug:
        print_loc_vars(tmp_dir, src_root_dir, inc_dirname, src_dirname)

    if loc_validate_args(src_root_dir, inc_dirname, src_dirname) is False:
        sys.exit(1)

    max_file_num = 0
    max_num_lines = 0
    file_w_max_num_lines = ""
    full_loct_doth = inc_dirname + '/' + loct_doth
    full_loc_dotc  = src_dirname + '/' + loc_dotc
    # -----------------------------------------------------------------------
    # The filename-index mnemonics will come out in the .h file, but the list
    # of file names array will come out in the .c file. Only after we source
    # the list of src files can we generate the .h tokens. Hence, both file
    # handles have to be working in tandem.
    with open(full_loct_doth, 'w', encoding="utf8") as doth_fh:
        gen_loc_file_banner_msg(doth_fh, src_root_dir, loct_doth)
        gen_doth_include_guards(doth_fh, loct_doth, True)

        with open(full_loc_dotc, 'w', encoding="utf8") as dotc_fh:
            gen_loc_file_banner_msg(dotc_fh, src_root_dir, loc_dotc)

            (max_file_num, max_num_lines, file_w_max_num_lines) \
                = gen_loc_generated_files(doth_fh, dotc_fh, src_root_dir,
                                          loc_dotc,
                                          dump_dup_files, verbose)

        gen_doth_include_guards(doth_fh, loct_doth, False)
        if verbose:
            fprintf(sys.stdout, 'Generated ' + full_loct_doth + '\n')
            fprintf(sys.stdout, 'Generated ' + full_loc_dotc + '\n')

    # -----------------------------------------------------------------------
    # Generate the main header file that other code consuming this LOC machinery
    # will need to include. Required macros and lookup stuff live in this file.
    loc_doth = "loc.h"
    full_loc_doth = inc_dirname + '/' + loc_doth
    with open(full_loc_doth, 'w', encoding="utf8") as doth_fh:
        gen_loc_file_banner_msg(doth_fh, src_root_dir, loc_doth)
        gen_doth_include_guards(doth_fh, loc_doth, True)

        gen_loc_interface_doth(doth_fh, loc_dotc)

        gen_doth_include_guards(doth_fh, loc_doth, False)
        if verbose:
            fprintf(sys.stdout, 'Generated ' + full_loc_doth + '\n')

    # -----------------------------------------------------------------------
    # Generate the LOC-decoding program, used as helper utility program
    src_root_base = os.path.basename(src_root_dir)
    loc_decode_bin = src_root_base + "_" + "loc"
    loc_decode_dotc = loc_decode_bin + ".c"

    # Even though generated .h/.c files may be in project's source-tree,
    # generate the compiled decoder binary always in /tmp, as we don't know
    # what the project's build-area dir-rules may be.
    full_loc_decode_dotc = tmp_dir + loc_decode_dotc

    with open(full_loc_decode_dotc, 'w', encoding="utf8") as loc_fh:
        gen_loc_file_banner_msg(loc_fh, src_root_dir, loc_decode_dotc)
        gen_loc_decoder(loc_fh, max_file_num, loc_doth, loc_dotc, loc_decode_dotc,
                        loc_decode_bin)

        if verbose:
            fprintf(sys.stdout, 'Generated ' + full_loc_decode_dotc + '\n')

    # Pick up the decoder's source from tmp but use the user-specified
    # dir-name for output LOC-binary location.
    cc_rc = gen_cc_loc_decoder(tmp_dir, loc_dirname, loc_decode_bin,
                               loc_decode_dotc,
                               full_loct_doth, full_loc_doth,
                               full_loc_dotc, loc_debug)
    if verbose:
        if cc_rc == 0:
            fprintf(sys.stdout, 'Generated ' + loc_dirname + loc_decode_bin + '\n')
        else:
            fprintf(sys.stderr, 'Failed to generate ' + loc_dirname + loc_decode_bin + '\n')

    if cc_rc != 0:
        sys.exit(1)

    if gen_cflags or gen_cflags_brief:
        gen_loc_cflags(gen_cflags_brief)

    return (True, max_file_num, max_num_lines, file_w_max_num_lines)
    # pylint: enable-msg=too-many-statements
    # pylint: enable-msg=too-many-locals

###############################################################################
# Argument Parsing routine
def loc_parse_args(args):
    """
    Command-line argument parser.

    For how-to re-work argument parsing so it's testable.
    """

    # pylint: disable-msg=line-too-long
    # Ref: https://stackoverflow.com/questions/18160078/how-do-you-write-tests-for-the-argparse-portion-of-a-python-module
    # pylint: enable-msg=line-too-long

    # ---------------------------------------------------------------
    # Start of argument parser, with inline examples text
    # Create 'parser' as object of type ArgumentParser
    parser  = argparse.ArgumentParser(description='Generate LOC interface .h and .c files',
                                      formatter_class=argparse.RawDescriptionHelpFormatter,
                                      epilog=r'''Examples:

- Basic usage:
    ''' + LOC_SCRIPT + ''' --src-root-dir < source code root-dir >
''')

    # Define arguments supported by this script
    parser.add_argument('--src-root-dir', dest='src_root_dirname'
                        , metavar='<src-root-dir>'
                        , required=True
                        , default=LOC_PKGSRC_DIR
                        , help='Source root dir name, default: ' + LOC_PKGSRC_DIR)

    parser.add_argument('--gen-cflags', dest='gen_cflags'
                        , action='store_true'
                        , default=False
                        , help='Generate suggested CFLAGS to run Make with.')

    parser.add_argument('--gen-cflags-brief', dest='gen_cflags_brief'
                        , action='store_true'
                        , default=False
                        , help='Generate the brief CFLAGS syntax to run Make with.')

    parser.add_argument('--gen-includes-dir', dest='inc_dirname'
                        , metavar='<include-files-dir>'
                        , default=None
                        , help='Include .h files dir name.'
                                + ' Generated .h files go here.'
                                + ' Default: ' + LOC_PKGSRC_DIR)

    parser.add_argument('--gen-source-dir', dest='src_dirname'
                        , metavar='<source-files-dir>'
                        , default=None
                        , help='Source files dir name, default: ' + LOC_PKGSRC_DIR
                                + ' Generated .c files go here.')

    parser.add_argument('--loc-decoder-dir', dest='loc_dirname'
                        , metavar='<LOC-decoder-binary-dir>'
                        , default=None
                        , help='Project-specific standalone LOC decoder binary'
                                + ' dir name, default: '
                                + tempfile.gettempdir())

    # ======================================================================
    # Debugging support
    parser.add_argument('--verbose', dest='verbose'
                        , action='store_true'
                        , default=False
                        , help='Show verbose progress messages')

    parser.add_argument('--debug', dest='debug_script'
                        , action='store_true'
                        , default=False
                        , help='Turn on debugging for script\'s execution')

    parser.add_argument('--dump-dup-filenames', dest='dump_dup_files'
                        , action='store_true'
                        , default=False
                        , help='Print list of duplicate file names found')

    parsed_args = parser.parse_args(args)

    if parsed_args is False:
        parser.print_help()

    return parsed_args


###############################################################################
def gen_loc_generated_files(doth_fh, dotc_fh, src_root_dir, loc_dotc,
                            dump_dup_files, verbose):
    """
    Function to drive the generation of the generated files:
        $TMPDIR/loc.h
        $TMPDIR/loc_filenames.c

    Walk the source directory tree under 'src_root_dir', identifying all .c
    files, and build a dictionary of file_names. The list of file names and
    the associated tokens are generated off a common listing of files built
    here. Hence, this function takes both doth_fh & dotc_fh as inputs.

    Arguments:
        dotc_fh          - File handle for generated .h file
        dotc_fh          - File handle for generated .c file
        src_root_dir     - Top-level source root-dir to run a 'find' for .c files
        loc_dotc         - Name of generated loc_filenames.c file
        dump_dup_files   - Boolean; Dump list of dup file names found
        verbose          - Boolean; Print verbose messages for debugging

    Returns: (number-of-files, max-num-lines-across-all-files,
              file-with-max-lines)
    """
    # pylint: disable-msg=too-many-arguments
    # pylint: disable-msg=too-many-locals

    # Hash on file's base name as key, mapping it to full-name w/dir-path
    file_names = {}
    file_lines = {} # of lines in the file

    # Hash to collect any duplicate filenames, that are renamed below
    dup_file_names = {}

    num_files = 0
    max_num_lines = 0
    file_w_max_num_lines = ""

    # Grab code-base source's root-dir. This way, if user runs this script with
    # '~/Code/<someProduct>', then we only store the file-names as:
    # <someProduct>/dir1/file1, <someProduct>/dir2/file2, and so on ...
    # src_root_base will be 'someProduct'
    src_root_base = os.path.basename(src_root_dir)

    # ########################################################################
    # Run 'find' on the source-tree rooted at src_root_dir, finding all .c files
    for root, dirs, files in os.walk(src_root_dir):
        # Ensure list of files is sorted, so we get a consistent numbering on
        # all platforms, in case the product is supported on diff OS'es
        dirs.sort()

        for file in sorted(files):

            # Skip files that are not .c source files
            if (file.endswith('.c') is False
               and file.endswith('.cpp') is False
               and file.endswith('.cc') is False):
                continue

            # IF user has asked to generate *.c files in the same src-dir
            # that is being processed, we will come upon loc_filenames.c also.
            # Skip it.
            if file == loc_dotc:
                continue

            # Munge file name to sort dups, and build full-path name
            # root: ~/Code/someProduct/some-Dir/some-subDir
            # Strip out prefix, to just grab: 'some-Dir/some-subDir'
            root_dirname = root.replace(src_root_dir, "", 1)

            file_base_name = file
            file_full_name = src_root_base + root_dirname + "/" + file

            if file in file_names:

                # print(  "Skip duplicate file " + file
                #       + " (Found: " + file_names[file_base_name] + ")")

                # Extend the file's name to include the sub-dir's name.
                # This should more than likely eliminate the duplicate
                file_base_name = os.path.basename(root) + "_" + file

                dup_file_names[file_base_name] = file_full_name

            file_names[file_base_name] = file_full_name

            num_lines = count_lines(root + "/" + file, verbose)
            file_lines[file_base_name] = num_lines
            if num_lines > max_num_lines:
                max_num_lines = num_lines
                file_w_max_num_lines = src_root_base + root_dirname + "/" + file

            num_files += 1

    # ########################################################################
    # Using the hash of filenames, process the list of files to get the max
    # filename length. This will used to auto-format the token in .h file.
    #
    (max_key_name, max_file_name) = find_max_name_lengths(file_names)
    max_file_name = max_file_name + 1   # Add an extra space

    gen_loc_doth_tokens(doth_fh, file_names, max_key_name, num_files, file_lines)

    # Generate the file names in the array of file names
    gen_loc_dotc_filenames(dotc_fh, file_names, max_file_name, file_lines)

    if dump_dup_files:
        pr_dup_file_names(dup_file_names)

    return (num_files, max_num_lines, file_w_max_num_lines)
    # pylint: enable-msg=too-many-locals
    # pylint: enable-msg=too-many-arguments

###############################################################################
def gen_loc_doth_tokens(doth_fh, file_names, max_key_namelen, num_files, file_lines):
    """
    Generate the #define mnemonics for each file's file-name-index

    Arguments:
        doth_fh     - File handle to output to
        file_names  - Hash of file names
        maxKeyName  - Max key-name length (.c file's basename is key)
        num_files   - # of files (expected to find) in hash file_names
        file_lines  - Hash of file's line-count, on file name
    """
    # pylint: disable-msg=too-many-locals

    # Print this as a comment right at the beginning, for ease of readability.
    fprintf(doth_fh, "// LOC_MAX_FILE_NUM=%d   ... "
                     + "Used to update generated file in the source tree.\n\n",
            num_files)

    # In #define, we prepend 'LOC_'. Account for that in field's width.
    # Print format will be, e.g.: "#define %-37s %-5d // %s \n"
    max_name_field_width = max_key_namelen + len("LOC_")

    # pylint: disable-msg=line-too-long
    token_printfmt = "#define %-" + str(max_name_field_width) + "s %-5d // %s: L=%d (line count)\n"
    # pylint: enable-msg=line-too-long

    fctr = 0
    unknown_file = "Unknown_file"

    fprintf(doth_fh, token_printfmt, "LOC_UNKNOWN_FILE", fctr, unknown_file, 0)

    max_line_count = 0
    token_printfmt = "#define %-" + str(max_name_field_width) + "s %-5d // %s: L=%d\n"
    dup_printfmt = "// #define %-" + str(max_name_field_width - 3) + "s %-5d // %s: L=%d\n"

    unique_tokens = set() # To eliminate duplicate generated tokens

    printfmt = token_printfmt
    num_dup_tokens = 0
    for file in sorted(file_names.keys()):
        fctr += 1

        file_full_name = file_names[file]

        # Generate the LOC_<token>, replacing '.' and '-' with "_"
        fname_token = xform_fname_to_token(file)
        if fname_token in unique_tokens:
            printfmt = dup_printfmt
            num_dup_tokens += 1 # Expect that likelihood of finding dups is very low
        else:
            # Save-off generated tokens to eliminate duplicates.
            unique_tokens.add(fname_token)

        fprintf(doth_fh, printfmt, fname_token, fctr, file_full_name, file_lines[file])

        printfmt = token_printfmt

        if file_lines[file] > max_line_count:
            max_line_count = file_lines[file]

    fprintf(doth_fh, "\n")
    fprintf(doth_fh, token_printfmt, "LOC_MAX_FILE_NUM", fctr, "LOC MAX LINE COUNT",
            max_line_count)

    fprintf(doth_fh, token_printfmt, "LOC_NUM_FILES",
            (fctr + 1), "Size of filenames lookup array",
            0)
    # pylint: enable-msg=too-many-locals

###############################################################################
def gen_loc_interface_doth(doth_fh, loc_dotc):
    """
    Generate the external interfaces for this LOC-machinery.
    The limits are a bit hard-coded for now. This will be enhanced to scale
    the number of bits depending on source code base processed.

    Arguments:
        doth_fh     - File handle to output to
        loc_dotc    - Name of generated dot-c file
    """

    fprintf(doth_fh, "#include <inttypes.h>    /* Needed for uint32_t */\n")
    fprintf(doth_fh, "#include \"loc_tokens.h\"\n\n")

    nbits_files = 15
    fprintf(doth_fh,
            "#define LOC_NBITS_FILES %d       // # of bits for file-index component.\n",
            nbits_files)

    nbits_lines = 16
    fprintf(doth_fh,
            "#define LOC_NBITS_LINES %d       // # of bits for line-number component.\n",
            nbits_lines)

    # Masks are meant for internal use; hence LOC__
    files_mask = (1 << nbits_files) -  1
    fprintf(doth_fh,
            "#define LOC__MASK_FILES 0x%x   // %d: Mask to extract file-index component.\n",
            files_mask, files_mask)

    lines_mask = (1 << nbits_lines) -  1
    fprintf(doth_fh,
            "#define LOC__MASK_LINES 0x%x   // %d: Mask to extract line-number component.\n",
            lines_mask, lines_mask)

    fprintf(doth_fh, "\ntypedef uint32_t loc_t;\n")

    fprintf(doth_fh, "\n/* Encode a (f=file-index, l=line-number) into a loc_t value */\n")
    fprintf(doth_fh, "#define LOC_ENCODE(f,l) (loc_t) (((f) << LOC_NBITS_LINES) | (l))\n")

    fprintf(doth_fh, "\n/* Encode a (file-index, __LINE__) into a loc_t value */\n")
    fprintf(doth_fh, "#define __LOC__ LOC_ENCODE(LOC_FILE_INDEX, __LINE__)\n")

    fprintf(doth_fh, "\n/* Extract file-index from an encoded loc_t value */\n")
    fprintf(doth_fh, "#define LOC_FILE_TOKEN(v) ((v) >> LOC_NBITS_LINES)\n")

    fprintf(doth_fh, "\n/* External reference to lookup array defined in %s */\n",
            loc_dotc)
    fprintf(doth_fh, "extern const char *Loc_FileNamesList [];\n")


    # pylint: disable-msg=line-too-long
    fprintf(doth_fh, "\n/* Safe-accessor at index 'i' from string-lookup array, 'lt', of size 'n'. */\n")

    fprintf(doth_fh, "#define LOC__SAFE_LOOKUP(lt, i, n) ")
    fprintf(doth_fh, "    ((((i) >= 0) && ((i) < (n))) ? (lt)[(i)] : (const char *) \"\")\n")

    fprintf(doth_fh, "\n/* Extract file-name from an encoded loc_t value */\n")
    fprintf(doth_fh, "#define LOC_FILE(v) LOC__SAFE_LOOKUP(Loc_FileNamesList, LOC_FILE_TOKEN(v), LOC_NUM_FILES)\n")

    fprintf(doth_fh, "\n/* Extract line-number from an encoded loc_t value */\n")
    fprintf(doth_fh, "#define LOC_LINE(v) ((v) & LOC__MASK_LINES)\n")
    # pylint: enable-msg=line-too-long


###############################################################################
def gen_loc_dotc_filenames(dotc_fh, file_names, max_file_name, file_lines):
    """
    Generate the static array of file names to the generated .c file. This is
    where the meat of the work happens.

    Arguments:
        dotc_fh         - File handle to output to
        file_names      - Hash of file names
        max_file_name   - Max file-name-length
        file_lines      - Hash of file's line-count, on file name
    """

    # Generate start of const char * filenames lookup array
    gen_loc_file_names_array(dotc_fh, True)

    fctr = 0
    unknown_file = "Unknown_file"

    # Now that we know the max file name length, generate the print format
    # First '%s' is the file name, 2nd '%s' is generated spaces for alignment
    dotc_print_fmt = '      "%s" %s// %d, L=%d (line count)\n'

    # Generate the 0th entry for the unknown-file name
    spaces = ' ' * (max_file_name - len(unknown_file))
    fprintf(dotc_fh, dotc_print_fmt, unknown_file, spaces, fctr, 0)

    # Redefine print fmt to have subsequent files separated by ", <filename>"
    dotc_print_fmt = '    , "%s" %s// %d, L=%d\n'

    size_of_string_array = 0
    for file in sorted(file_names.keys()):
        fctr += 1

        file_full_name = file_names[file]

        # Generate spaces to blank-pad generated name for alignment
        spaces = ' ' * (max_file_name - len(file_full_name))

        size_of_string_array += len(file_full_name)

        fprintf(dotc_fh, dotc_print_fmt, file_full_name, spaces, fctr, file_lines[file])

    # Generate closing of filenames lookup array
    gen_loc_file_names_array(dotc_fh, False)

    # Include n-ptrs in the total space consumed by this array.
    size_of_string_array += (fctr * 8)

    fprintf(dotc_fh, "\n/* Overhead of FilenamesList[] array"
                     + ": %d bytes (%.f KB) */\n\n",
                     size_of_string_array, (size_of_string_array / 1024.0))

    filenames_list_len_str = "(sizeof(Loc_FileNamesList)/sizeof(*Loc_FileNamesList))"
    fprintf(dotc_fh, "\nint Loc_FileNamesList_len = "
                     + filenames_list_len_str + ";\n\n")

    # fprintf(dotc_fh, "COMPILE_TIME_ASSERT(("
    #                  + filenames_list_len_str
    #                  + " == LOC_MAX_FILE_NUM + 1), "LengthOfFileNamesListArrayIsIncorrect");\n")
    fprintf(dotc_fh,"// clang-format on\n")


###############################################################################
def gen_loc_decoder(loc_fh, max_file_num, loc_doth, loc_dotc, loc_decode_dotc, loc_decode_bin):
    """
    Generate the stand-alone LOC-decoder program's source code.
    This is just a stand-alone main(), linked with the .c file containing the
    definition of Loc_FileNamesList[] lookup array.

    Arguments:
        loc_fh          - File handle to generate .c file
        max_file_num    - Max file-number found by generation step
        loc_doth        - Name of LOC #include .h file
        loc_dotc        - Name of LOC .c file containing defn of Loc_FileNamesList[]
        loc_decode_dotc - Name of LOC-decode program's source file name
        loc_decode_bin  - Name of LOC-decode binary program
    """
    # pylint: disable-msg=too-many-arguments
    # pylint: disable-msg=too-many-statements
    fprintf(loc_fh, "/*\n")
    fprintf(loc_fh, " * To generate the LOC decoding program for this code-base, do:\n")
    fprintf(loc_fh, " *   cc -o %s %s %s\n", loc_decode_bin, loc_dotc, loc_decode_dotc)
    fprintf(loc_fh, " */\n")

    fprintf(loc_fh, "#include <stdio.h>\n")
    fprintf(loc_fh, "#include <stdint.h>\n")
    fprintf(loc_fh, "#include <stdlib.h>\n")
    fprintf(loc_fh, "#include <string.h>\n")
    fprintf(loc_fh, "#include \"%s\"\n", loc_doth)

    fprintf(loc_fh, "// clang-format off\n")

    fprintf(loc_fh, "\nint\n")
    fprintf(loc_fh, "main(int argc, char *argv[])\n")
    fprintf(loc_fh, "{\n")

    # Generate basic help/usage, custom-fit for code-base being LOC'ified
    fprintf(loc_fh, "    if (argc <= 1) {\n")
    fprintf(loc_fh, "        printf(\"Usage: %%s [--brief] [<loc-ID-values>+]"
                                    + "\\n\", argv[0]);\n")
    fprintf(loc_fh, "        printf(\"Max-file-number: %d\\n\");\n", max_file_num)
    # pylint: disable-msg=line-too-long
    fprintf(loc_fh, "        printf(\"Examples: Specify LOC-encoded value you wish to decode.\\n\");\n")
    # pylint: enable-msg=line-too-long
    fprintf(loc_fh, "        printf(\"  %s [<uint32-value>]+\\n\");\n", loc_decode_bin)

    # Generate some sample encoding values
    nbits_lines = 16
    if max_file_num == 1:
        file_num = 1
        line_num = 4
        loc1 = (file_num << nbits_lines) | line_num

        line_num = 5
        loc2 = (file_num << nbits_lines) | line_num

        line_num = 10
        loc3 = (file_num << nbits_lines) | line_num

        line_num = 17
        loc4 = (file_num << nbits_lines) | line_num
    elif max_file_num == 2:
        file_num = 1
        line_num = 4
        loc1 = (file_num << nbits_lines) | line_num

        line_num = 5
        loc2 = (file_num << nbits_lines) | line_num

        file_num = 2
        line_num = 10
        loc3 = (file_num << nbits_lines) | line_num

        line_num = 17
        loc4 = (file_num << nbits_lines) | line_num
    else:
        file_num = 1
        line_num = 4
        loc1 = (file_num << nbits_lines) | line_num

        file_num = 5
        line_num = 123
        loc2 = (file_num << nbits_lines) | line_num

        file_num = 6
        line_num = 223
        loc3 = (file_num << nbits_lines) | line_num

        file_num = 6
        line_num = 224
        loc4 = (file_num << nbits_lines) | line_num

    fprintf(loc_fh, "        printf(\"  %s %u %u %u %u\\n\");\n",
            loc_decode_bin, loc1, loc2, loc3, loc4)

    # Show an example of generating LOC using encoding macro, using diff
    # file numbers, depending on the source code-base processed.
    file_numbers= []
    if max_file_num == 1:
        file_numbers = [1, 1, 1, 1]
    elif max_file_num == 2:
        file_numbers = [1, 1, 2, 2]
    else:
        file_numbers = [1, 5, 6, 8]

    fprintf(loc_fh, "        printf(\"  %s %%u %%u %%u %%u\\n\", %s, %s, %s, %s);\n",
            loc_decode_bin,
            "LOC_ENCODE(" + str(file_numbers[0]) + ", 10)",
            "LOC_ENCODE(" + str(file_numbers[1]) + ", 30)",
            "LOC_ENCODE(" + str(file_numbers[2]) + ", 31)",
            "LOC_ENCODE(" + str(file_numbers[3]) + ", 44)")

    fprintf(loc_fh, "        return(0);\n")
    fprintf(loc_fh, "    }\n")

    fprintf(loc_fh, "\n")

    # Parse the --brief arg supplied at run-time
    fprintf(loc_fh, "    int brief = (strncmp(argv[1], \"--brief\", 7) == 0);\n")

    # If the decoder's 1st arg is --brief, start iterating from next arg
    # to decode args assuming they are loc-IDs.
    fprintf(loc_fh, "    int i = brief + 1;\n")

    # Generate the actual body of the decoder's source.
    fprintf(loc_fh, "    for (; i < argc; i++) {\n")
    fprintf(loc_fh, "        loc_t loc = atoi(argv[i]);\n")
    fprintf(loc_fh, "        if (brief) {\n")
    fprintf(loc_fh, "            printf(\"%%s:%%d \\n\", LOC_FILE(loc), LOC_LINE(loc));\n")
    fprintf(loc_fh, "        } else { \n")
    fprintf(loc_fh, "            printf(\"%%u: [fnum=%%d] %%s:%%d \\n\",\n")
    fprintf(loc_fh, "                   loc, LOC_FILE_TOKEN(loc), LOC_FILE(loc), LOC_LINE(loc));\n")
    fprintf(loc_fh, "        }\n")
    fprintf(loc_fh, "   }\n")
    fprintf(loc_fh, "}\n")

    fprintf(loc_fh, "\n// clang-format on\n")
    # pylint: enable-msg=too-many-statements
    # pylint: enable-msg=too-many-arguments

# #############################################################################
# pylint: disable-msg=line-too-long
# Ref: https://stackoverflow.com/questions/20388992/python-nice-way-to-iterate-over-shell-command-result
#      https://stackoverflow.com/questions/25079140/subprocess-popen-checking-for-success-and-errors
#      https://stackoverflow.com/questions/21406887/subprocess-changing-directory
#      https://stackoverflow.com/questions/32984058/ld-cant-open-output-file-for-writing-bin-s-errno-2-for-architecture-x86-64
# pylint: enable-msg=line-too-long
# #############################################################################
def gen_cc_loc_decoder(tmpdir, loc_dirname, loc_decode_bin, loc_decode_dotc,
                       full_loct_doth, full_loc_doth, full_loc_dotc,
                       loc_debug) -> int:
    # pylint: disable-msg=too-many-arguments
    """
    Compile the generated loc-decoder source file to generate the LOC-decoder
    binary, specific for the code-base being processed.

    Parameters:
        tmpdir          - /tmp-dir where decoder binary will be produced
        loc_decode_bin  - Decoder-binary name
        loc_decode_dotc - Decoder-binary's .c file name
        full_loct_doth  - Full path-name of generated loc_tokens.h
        full_loc_doth   - Full path-name of generated loc.h
        full_loc_dotc   - Full path-name of generated loc_filenames.c
    Returns: 0 upon success, non-zero otherwise
    """

    # User may have generated filenames.c in some other src-dir. We don't want
    # to pollute the user's src/ tree by generating objects. If user has not
    # used cmdline args to relocate generated files to somewhere other than
    # /tmp-dir, cp over to /tmp-dir the files required to compile the standalone
    # decoder binary.
    if os.path.dirname(full_loct_doth) + '/' != tmpdir:
        shutil.copy2(full_loct_doth, tmpdir)
    if os.path.dirname(full_loc_doth) + '/' != tmpdir:
        shutil.copy2(full_loc_doth, tmpdir)
    if os.path.dirname(full_loc_dotc) + '/' != tmpdir:
        shutil.copy2(full_loc_dotc, tmpdir)

    tmp_loc_dotc = os.path.basename(full_loc_dotc)

    if loc_debug:
        print(  "tmp_loc_dotc    = " + tmp_loc_dotc + "\n"
              + "loc_decode_dotc = " + loc_decode_dotc + "\n"
              + "loc_dirname     = " + loc_dirname + "\n"
              + "loc_decode_bin  = " + loc_decode_bin)

    try:
        result = sp.run(["cc", "-o", loc_dirname + loc_decode_bin,
                          "-I" , tmpdir,
                          tmpdir + tmp_loc_dotc,
                          tmpdir + loc_decode_dotc
                          ],
                          text=True,
                          check=True,
                          capture_output=True, cwd=tmpdir
                          )
    except sp.CalledProcessError as exc:
        print("sp.run() Status: FAIL, rc=", exc.returncode,
              "\nargs=", exc.args,
              "\nstdout=", exc.stdout,
              "\nstderr=", exc.stderr)
        return 1

    return result.returncode
    # pylint: enable-msg=too-many-arguments

###############################################################################
def gen_doth_include_guards(doth_fh, file_name, begin_block):
    """
    Generate ifndef directives to guard against multiple .h file inclusions
    """

    # Build guard_name as '__LOC__'
    guard_name = "__" + os.path.basename(file_name).upper() + "__"
    guard_name = guard_name.replace(".", "_")

    doth_fh.write("\n")
    if begin_block:
        doth_fh.write("// clang-format off\n")
        doth_fh.write('''#ifndef ''' + guard_name)
        doth_fh.write("\n")
        doth_fh.write("\n")
    else:
        doth_fh.write("// clang-format off\n")
        doth_fh.write("#endif  /* " + guard_name + " */")
        doth_fh.write("\n")

###############################################################################
def gen_loc_file_names_array(dotc_fh, array_begin):
    """
    Generate start and end of the Loc_FileNames[] array definition
    """
    if array_begin:
        dotc_fh.write("// clang-format off\n")
        dotc_fh.write("const char *Loc_FileNamesList [] =\n{\n")
    else:
        dotc_fh.write("\n};\n")

###############################################################################
def gen_loc_file_banner_msg(file_hdl, src_dir, file_name):
    """
    Function to generate the banner for a generated file

    Arguments:
        file_hdl    - File handle for generated .h/.c file
        src_dir     - Full path to source code root dir
        file_name   - Generated .h file's name
    """

    file_hdl.write('''/*
 * ****************************************************************************
 * ''' + file_name + '''
 *
 * WARNING: This is a generated file.
 * Any change you make here will be overwritten!
 *
 * This file was generated by processing all source files under
 *     ''' + src_dir + '''
 *
 * Script executed:
 * ''' + __file__ + '''
 * ****************************************************************************
 */
''')

###############################################################################
def gen_loc_cflags(brief):
    """
    Generate a suggested CFLAGS directive which, in most cases, will be
    sufficient to compile any source file which may use one of the LOC-macros.

    For now, this is a simplistic definition.
    Define CFLAGS to generate the -D clause to define LOC_FILE_INDEX
    using the source file name as input:
      - Replace "-" in filename with "_"
      - Replace ".c" with "_c" (Should work for *.cpp and *.cc files.)

    Parameters:
        brief - Emit just the CFLAGS syntax, so the output can be
                appended to "CFLAGS=" clause to automate the build
                w/o having to edit the Makefile.
    """
    cflags_clause = "'-DLOC_FILE_INDEX=LOC_$(subst .,_,$(subst -,_,$(notdir $<)))'"
    if brief:
        print(cflags_clause)
    else:
        print("CFLAGS =",cflags_clause)

###############################################################################
def find_max_name_lengths(file_names):
    """
    Helper function for auto-formatting output for readability.
    Walk an input hash of file names, and find out the max key-name length
    and max filename-length.

    Arguments:
        file_names - Hash of files found, key is files' base name

    Return (max-key-name-length, max-file-name-length)
    """

    max_key_name  = 0
    max_file_name = 0
    for file in file_names.keys():
        max_key_name = max(max_key_name, len(file))
        max_file_name = max(max_file_name, len(file_names[file]))

    return(max_key_name, max_file_name)

###############################################################################
# Helper routines:
###############################################################################
def print_loc_vars(tmp_dir, src_root_dir, inc_dirname, src_dirname):
    """Dump out LOC script variables after parsing."""
    print("tmp_dir       = ", tmp_dir)
    print("src_root_dir  = ", src_root_dir)
    print("inc_dirname   = ", inc_dirname)
    print("src_dirname   = ", src_dirname)

###############################################################################
def loc_validate_args(src_root_dir, inc_dirname, src_dirname):
    """
    Validate sanity of parsed arguments., to see, e.g., if specified directory exists
    """
    if locu.dir_exists(src_root_dir) is False:
        return False

    if locu.dir_exists(inc_dirname) is False:
        return False

    if locu.dir_exists(src_dirname) is False:
        return False

    return True

# ------------------------------------------------------------------------------
def xform_fname_to_token(filename):
    """
    Transform a filename to its token that will become the filename-index.
    E.g. "murmum_hash.c" will become "LOC_murmur_hash_c"
         "preproc-pointer-to-struct.c" becomes "preproc_pointer_to_struct.c"
    """
    fname_token = filename.replace(".", "_")
    fname_token = fname_token.replace("-", "_")
    return "LOC_" + fname_token

# ------------------------------------------------------------------------------
def fprintf(stream, format_spec, *args):
    """ C-like fprintf() interface. """
    stream.write(format_spec % args)

# ------------------------------------------------------------------------------
def count_lines(file_full_path, verbose) -> int:
    """ Open a text file and return # of lines """
    numlines = 0
    with open(file_full_path, encoding="utf8") as src_fh:
        try:
            numlines = len(src_fh.readlines())
        except UnicodeDecodeError:
            if verbose:
                fprintf(sys.stderr, "UnicodeDecode error occurred trying to read %s\n",
                        file_full_path)
        except UnicodeError:
            if verbose:
                fprintf(sys.stderr, "Unicode error occurred trying to read %s\n",
                        file_full_path)

    return numlines


# ------------------------------------------------------------------------------
def pr_dup_file_names(dup_file_names):
    """ Print a list of duplicate file names from a hash """

    if len(dup_file_names) == 0:
        return

    fprintf(sys.stdout, "Duplicate file names found:\n")
    pr_hash(dup_file_names)

# ------------------------------------------------------------------------------
def pr_hash(this_hash):
    """ Print a list of names from a hash """
    for file in this_hash.keys():
        fprintf(sys.stdout, "  %s:%s\n", file, this_hash[file])

###############################################################################
# Helper methods, to facilitate unit-testing
###############################################################################
def loc_get_this_scriptdir():
    """ Return the directory name where this script lives."""
    return LOC_THIS_SCRIPT_DIR

###############################################################################
# Start of the script: Execute only if run as a script
###############################################################################
if __name__ == "__main__":
    main()
