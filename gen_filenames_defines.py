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
# as part of the src/ Makefile system of most C/C++ code bases.
"""

import sys
import os
import tempfile

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

    # Open the to-be-generated .h and .c files in /tmp first.
    tmp_dir = tempfile.gettempdir() + '/'
    loc_doth = "loc.h"
    loc_dotc = "loc_filenames.c"
    print(tmp_dir)

    src_dir = args[0]

    # The filename-index mnemonics will come out in the .h file, but the list
    # of file names array will come out in the .c file. Only after we source
    # the list of src files can we generate the .h tokens. Hence, both file
    # handles have to be working in tandem.
    with open(tmp_dir + os.path.basename(loc_doth), 'w', encoding="utf8") as doth_fh:
        gen_loc_file_banner_msg(doth_fh, src_dir, loc_doth)
        gen_doth_include_guards(doth_fh, loc_doth, True)

        with open(tmp_dir + os.path.basename(loc_dotc), 'w', encoding="utf8") as dotc_fh:
            gen_loc_file_banner_msg(dotc_fh, src_dir, loc_dotc)

            gen_loc_generated_files(doth_fh, dotc_fh, src_dir)

        gen_doth_include_guards(doth_fh, loc_doth, False)
    retval = True
    return retval

###############################################################################
def gen_loc_generated_files(doth_fh, dotc_fh, src_root_dir):
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
    """

    src_base_name = os.path.basename(src_root_dir)

    # Hash on file's base name as key, mapping it to full-name w/dir-path
    file_names = {}

    # Hash to collect any duplicate filenames, that are renamed below
    dup_file_names = {}

    num_files = 0

    # ########################################################################
    # Run 'find' on the source-tree rooted at src_root_dir, finding all .c files
    for root, dirs, files in os.walk(src_root_dir):
        # Ensure list of files is sorted, so we get a consistent numbering on
        # all platforms, in case the product is supported on diff OS'es
        dirs.sort()

        for file in sorted(files):

            # Skip files that are not .c source files
            if file.endswith('.c') is False:
                continue

            root_dirname_sh = root.replace(src_root_dir, "", 1)

            # Munge file name to sort dups, and build full-path name
            file_base_name = file
            file = src_base_name + root_dirname_sh + "/" + file_base_name

            if file_base_name in file_names:

                # print(  "Skip duplicate file " + file
                #       + " (Found: " + file_names[file_base_name] + ")")

                # Extend the file's name to include the sub-dir's name.
                # This should more than likely eliminate the duplicate
                file_base_name = os.path.basename(root) + "_" + file_base_name

                dup_file_names[file_base_name] = file
                # continue

            file_names[file_base_name] = file
            num_files += 1

    # ########################################################################
    # Using the hash of filenames, process the list of files to get the max
    # filename length. This will used to auto-format the token in .h file.
    #
    (max_key_name, max_file_name) = find_max_name_lengths(file_names)
    max_file_name = max_file_name + 1   # Add an extra space

    gen_loc_doth_tokens(doth_fh, file_names, max_key_name, num_files)

    # Generate the file names in the array of file names
    gen_loc_dotc_filenames(dotc_fh, file_names, max_file_name)

###############################################################################
def gen_loc_doth_tokens(doth_fh, file_names, max_key_namelen, num_files):
    """
    Generate the #define mnemonics for each file's file-name-index

    Arguments:
        doth_fh     - File handle to output to
        file_names  - Hash of file names
        maxKeyName  - Max key-name length (.c file's basename is key)
        num_files   - # of files (expected to find) in hash file_names
    """

    # Print this as a comment right at the beginning, for ease of readability.
    fprintf(doth_fh, "// LOC_MAX_FILE_NUM=%d   ... "
                     + "Used to update generated file in the source tree.\n\n",
            num_files)

    # In #define, we prepend 'LOC_'. Account for that in field's width.
    # Print format will be, e.g.: "#define %-37s %-5d // %s \n"
    token_printfmt = "#define %-" + str(max_key_namelen + len("LOC_")) + "s %-5d // %s\n"

    fctr = 0
    unknown_file = "Unknown_file"

    fprintf(doth_fh, token_printfmt, "LOC_UNKNOWN_FILE", fctr, unknown_file)

    for file in sorted(file_names.keys()):
        fctr += 1

        file_full_name = file_names[file]

        # Generate the LOC_<token>, replacing '.' and '-' with "_"
        fname_token = xform_fname_to_token(file)
        fprintf(doth_fh, token_printfmt, fname_token, fctr, file_full_name)

    fprintf(doth_fh, "\n")
    fprintf(doth_fh, token_printfmt, "LOC_MAX_FILE_NUM", fctr, "For diagnostics")

###############################################################################
def gen_loc_dotc_filenames(dotc_fh, file_names, max_file_name):
    """
    Generate the static array of file names to the generated .c file. This is
    where the meat of the work happens.

    Arguments:
        dotc_fh              - File handle to output to
        file_names       - Hash of file names
    """

    # Generate start of const char * filenames lookup array
    gen_loc_file_names_array(dotc_fh, True)

    fctr = 0
    unknown_file = "Unknown_file"

    # Now that we know the max file name length, generate the print format
    # First '%s' is the file name, 2nd '%s' is generated spaces for alignment
    dotc_print_fmt = '      "%s" %s// %d\n'

    # Generate the 0th entry for the unknown-file name
    spaces = ' ' * (max_file_name - len(unknown_file))
    fprintf(dotc_fh, dotc_print_fmt, unknown_file, spaces, fctr)

    # Redefine print fmt to have subsequent files separated by ", <filename>"
    dotc_print_fmt = '    , "%s" %s// %d\n'

    size_of_string_array = 0
    for file in sorted(file_names.keys()):
        fctr += 1

        file_full_name = file_names[file]

        # Generate spaces to blank-pad generated name for alignment
        spaces = ' ' * (max_file_name - len(file_full_name))

        size_of_string_array += len(file_full_name)

        fprintf(dotc_fh, dotc_print_fmt, file_full_name, spaces, fctr)

    # Generate closing of filenames lookup array
    gen_loc_file_names_array(dotc_fh, False)

    # Include n-ptrs in the total space consumed by this array.
    size_of_string_array += (fctr * 8)

    fprintf(dotc_fh, "\n/* Overhead of FilenamesList[] array"
                     + ": %d bytes (%.f KB) */\n\n",
                     size_of_string_array, (size_of_string_array / 1024.0))

    filenames_list_len_str = "(sizeof(FileNamesList)/sizeof(*FileNamesList))"
    fprintf(dotc_fh, "\nint FileNamesList_len = "
                     + filenames_list_len_str + ";\n\n")

    fprintf(dotc_fh, "COMPILE_TIME_ASSERT(("
                     + filenames_list_len_str
                     + " == LOC_MAX_FILE_NUM + 1), LengthOfFileNamesListArrayIsIncorrect);\n")
    fprintf(dotc_fh,"\n// clang-format on\n")

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
        doth_fh.write("\n")
        doth_fh.write("// clang-format on\n")
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
*** ****************************************************************************
*** ''' + file_name + '''
***
*** WARNING: this is a generated file. Any change you make here will be overwritten!
***
*** This file was generated by processing all source files under
***     ''' + src_dir + '''
***
*** Script executed: ''' + __file__ + '''
*** ****************************************************************************
*/
''')

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
def xform_fname_to_token(filename):
    """
    Transform a filename to its token that will become the filename-index.
    E.g. "murmum_hash.c" will become "LOC_murmur_hash_c"
    """
    fname_token = filename.replace(".", "_")
    fname_token = fname_token.replace("-", "_")
    return "LOC_" + fname_token

def fprintf(stream, format_spec, *args):
    """ C-like fprintf() interface. """
    stream.write(format_spec % args)

###############################################################################
# Start of the script: Execute only if run as a script
###############################################################################
if __name__ == "__main__":
    main()
