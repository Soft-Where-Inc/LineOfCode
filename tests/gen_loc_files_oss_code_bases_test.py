# #############################################################################
# gen_loc_files_oss_code_bases_test.py
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
# pylint: disable-msg=line-too-long
# Ref: https://stackoverflow.com/questions/800197/how-to-get-all-of-the-immediate-subdirectories-in-python
#      https://docs.python.org/3/tutorial/inputoutput.html
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

    # Find max-name-length of subdirs, for auto-formatting output below
    max_subdir_namelen = 0
    for subdir in sorted(subdirs):
        subdir_namelen = len(os.path.basename(subdir))
        max_subdir_namelen = max(subdir_namelen, max_subdir_namelen)

    for subdir in sorted(subdirs):
        (retval, num_files, max_num_lines, file_w_max_num_lines) = run_loc_for_one_oss_code(subdir)
        num_oss_code_bases += 1
        assert retval is True

        print(  f'{os.path.basename(subdir):{max_subdir_namelen}}'
              + f', num_files={num_files:8d}'
              + f', max_num_lines={max_num_lines:8d} {file_w_max_num_lines}')

        sum_num_files += num_files
        global_max_num_lines = max(max_num_lines, global_max_num_lines)

    print(f'\nProcessed {num_oss_code_bases} OSS source code-bases'
            + f', {sum_num_files} files, global max_num_lines={global_max_num_lines}.')

# #############################################################################
def test_one_big_open_source_code_bases_repo():
    """
    Driver test-case to plough through all OSS source code-bases downloaded
    that reside alongside LocDirRoot. Exercise the generator that it correctly
    executes when processing -ALL- source-code bases squashed as one big code
    base. Test that it produces a test decoder binary program.
    """
    nsubdirs = len([s.rstrip("/") for s in glob(LocDirsParent + "/*/")])
    print( f'\nRunning LOC-generator on multiple ({nsubdirs}) '
          + 'OSS source code-bases all treated as one big repo ...')

    subdir = LocDirsParent
    (retval, num_files, max_num_lines, file_w_max_num_lines) = run_loc_for_one_oss_code(subdir)
    assert retval is True

    print(  f'{subdir}, num_files={num_files}'
          + f', max_num_lines={max_num_lines}, {file_w_max_num_lines}')

# #############################################################################
def run_loc_for_one_oss_code(code_dir_root) -> bool:
    """Exercise generator on a single code-base"""
    (retval, num_files, max_num_lines, file_w_max_num_lines) = loc_main.do_main(['--src-root-dir',
                                                           code_dir_root])
    assert retval is True
    return (retval, num_files, max_num_lines, file_w_max_num_lines)
