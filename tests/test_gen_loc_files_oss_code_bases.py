# #############################################################################
# test_gen_loc_files_oss_code_bases.py
#
"""
Exercise LOC py-generator on a collection of OSS code-bases that have
been downloaded on a private Mac / Linux env. These code bases live
alongside the root ~/Code sub-dir where this package lives. These tests
are, currently , not runnable on CI-workflows.
"""

# #############################################################################
import os
from glob import glob
import loc.gen_loc_files as loc_main

# #############################################################################
# Setup some variables pointing to diff dir/sub-dir full-paths.
# Dir-tree:
#  /<....>/LineOfCode/
#           loc/<generator-scripts>
#           test-code/{ < collection of test program source dirs > }
#           tests/<this-file>
# Full dir-path where this tests/  dir lives
LocTestsDir   = os.path.realpath(os.path.dirname(__file__))
LocDirRoot    = os.path.realpath(LocTestsDir + '/..')
LocDirsParent = os.path.realpath(LocDirRoot + '/..')

# #############################################################################
# To see output from test-cases run:
# $ pytest --capture=tee-sys tests/test_gen_loc_files_basic.py -k test_loc_main_scriptdir
# pylint: disable-msg=line-too-long
# Ref: https://stackoverflow.com/questions/800197/how-to-get-all-of-the-immediate-subdirectories-in-python
# pylint: enable-msg=line-too-long
# #############################################################################
def test_all_open_source_code_bases():
    """
    Driver test-case to plough through all OSS source code-bases downloaded
    that reside alongside LocDirRoot. Exercise the generator that it correctly
    executes, produces a test decoder binary program.
    """
    print('\nRunning LOC-generator on multiple OSS source code-bases ...')
    num_oss_code_bases = 0
    sum_num_files = 0
    global_max_num_lines = 0

    subdirs = [s.rstrip("/") for s in glob(LocDirsParent + "/*/")]
    for subdir in subdirs:
        (retval, num_files, max_num_lines) = run_loc_for_one_oss_code(subdir)
        num_oss_code_bases += 1
        print(f'{subdir}, rv={retval}, num_files={num_files}, max_num_lines={max_num_lines}')

        sum_num_files += num_files
        if max_num_lines > global_max_num_lines:
            global_max_num_lines = max_num_lines

    print(f'\nProcessed {num_oss_code_bases} OSS source code-bases'
            + f', {sum_num_files} files, global max_num_lines={global_max_num_lines}.')

# #############################################################################
def test_all_open_source_code_bases_squashed():
    """
    Driver test-case to plough through all OSS source code-bases downloaded
    that reside alongside LocDirRoot. Exercise the generator that it correctly
    executes when processing -ALL- source-code bases squashed as one big code
    base. Test that it produces a test decoder binary program.
    """
    print('\nRunning LOC-generator on multiple OSS source code-bases all squashed into one...')
    subdir = LocDirsParent
    (retval, num_files, max_num_lines) = run_loc_for_one_oss_code(subdir)
    print(f'{subdir}, rv={retval}, num_files={num_files}, max_num_lines={max_num_lines}')

# #############################################################################
def run_loc_for_one_oss_code(code_dir_root) -> bool:
    """Exercise generator on a single code-base"""
    # retval = loc_main.do_main(['--src-root-dir', code_dir_root, '--verbose'])
    (retval, num_files, max_num_lines) = loc_main.do_main(['--src-root-dir',
                                                           code_dir_root])
    assert retval is True
    return (retval, num_files, max_num_lines)
