# #############################################################################
# gen_loc_files_basic_test.py
#
"""
Collection of basic test cases to exercise the LOC generation machinery
end-to-end.
"""

# #############################################################################
import os
import subprocess as sp
import pytest
import loc.gen_loc_files as loc_main

# #############################################################################
# Setup some variables pointing to diff dir/sub-dir full-paths.
# Dir-tree:
#  /<....>/LineOfCode/
#           loc/<generator-scripts>
#           test-code/{ < collection of test program source dirs > }
#           tests/<this-file>
# Full dir-path where this tests/  dir lives
LocTestsDir    = os.path.realpath(os.path.dirname(__file__))
LocDirRoot     = os.path.realpath(LocTestsDir + '/..')
LocTestCodeDir = LocDirRoot + '/' + 'test-code'
LocDirsParent  = os.path.realpath(LocDirRoot + '/..')
LOC_PACKAGE    = 'LineOfCode'
LOC_ABBREV     = 'loc'

# #############################################################################
# To see output from test-cases run:
# $ pytest --capture=tee-sys tests/gen_loc_files_basic_test.py -k test_loc_main_scriptdir
# #############################################################################
def test_loc_main_script_dir():
    """
    Cross-check expected source dir location of main LOC <generator>.py script.
    """
    loc_main_script_dir = loc_main.loc_get_this_scriptdir()
    print("LOC-MainScriptDir='" + loc_main_script_dir + "'")
    assert loc_main_script_dir.endswith('/' +  LOC_PACKAGE + '/' + LOC_ABBREV) is True

# #############################################################################
def test_loc_tests_dir():
    """
    Cross-check expected source dir location of LOC tests dir.
    """
    loc_main_script_dir = loc_main.loc_get_this_scriptdir()
    print("LocTestsDir='" + LocTestsDir + "'")
    assert LocTestsDir == os.path.realpath(loc_main_script_dir + '/../tests')

# #############################################################################
def test_loc_dir():
    """
    Cross-check expected top-level dir location of LOC package.
    """
    loc_main_script_dir = loc_main.loc_get_this_scriptdir()
    print("LocDirRoot='" + LocDirRoot + "'")
    assert LocDirRoot == os.path.realpath(loc_main_script_dir + '/..')
    assert LocDirRoot.endswith(LOC_PACKAGE)

# #############################################################################
# pylint: disable-msg=line-too-long
# Ref: https://stackoverflow.com/questions/30256332/verify-the-error-code-or-message-from-systemexit-in-pytest
# pylint: enable-msg=line-too-long
# #############################################################################
def test_help():
    """
    --help prints a message and exists with SystemExit:0. Wrap this in
    this raises() exception block to let the test case pass.
    If you want to see the --help output, do:

      $ pytest --capture=tee-sys tests/gen_loc_files_basic_test.py -k test_help
    """
    with pytest.raises(SystemExit):
        loc_main.loc_parse_args(['--help'])

# #############################################################################
def test_invalid_cmdline_args():
    """
    Exercise usages where dirs-specified by cmd-line args are wrong.
    """
    with pytest.raises(SystemExit):
        loc_main.do_main([])

    with pytest.raises(SystemExit):
        loc_main.do_main(['--src-root-dir', '/tmp/non-existing-dir'] )

    # pylint: disable-msg=expression-not-assigned
    with pytest.raises(SystemExit):
        loc_main.do_main(['--src-root-dir',
                          LocTestCodeDir + '/single-file-program/',
                          '--gen-includes-dir', '/tmp/non-existing-dir'
                         ]),

    with pytest.raises(SystemExit):
        loc_main.do_main(['--src-root-dir',
                          LocTestCodeDir + '/single-file-program/',
                          '--gen-source-dir', '/tmp/non-existing-dir'
                         ]),
    # pylint: enable-msg=expression-not-assigned

# #############################################################################
def test_single_file_program():
    """Exercise generator on a single-file program from test-code base"""
    (retval, num_files, max_num_lines, file_w_max_num_lines) = \
      loc_main.do_main(['--src-root-dir',
                        LocTestCodeDir + '/single-file-program/',
                        '--verbose'])

    assert retval is True
    assert num_files == 1
    assert max_num_lines > 0
    assert file_w_max_num_lines.endswith('single-file-main.c')

# #############################################################################
def test_single_file_program_with_gen_dir_args():
    """
    Exercise generator on a single-file program from test-code base
    with --gen-includes-dir and --gen-source-dir arguments.
    """
    codedir = LocTestCodeDir + '/single-file-program/'

    (retval, num_files, max_num_lines, file_w_max_num_lines) = \
      loc_main.do_main(['--src-root-dir', codedir,
                        '--gen-includes-dir', codedir,
                        '--gen-source-dir', codedir,
                        '--verbose'])

    assert retval is True
    assert num_files == 1
    assert max_num_lines > 0
    assert file_w_max_num_lines.endswith('single-file-main.c')

# #############################################################################
def test_two_files_program():
    """Exercise generator on a program with two source files from test-code base"""
    (retval, num_files, max_num_lines, file_w_max_num_lines) = \
      loc_main.do_main(['--src-root-dir',
                        LocTestCodeDir + '/two-files-program',
                        '--verbose'])
    assert retval is True
    assert num_files == 2
    assert max_num_lines > 0
    assert file_w_max_num_lines.endswith('two-files-main.c')

# #############################################################################
def test_two_files_program_with_gen_dir_args():
    """
    Exercise generator on a program with two source files from test-code base
    with --gen-includes-dir and --gen-source-dir arguments.
    """
    codedir = LocTestCodeDir + '/two-files-program/'
    (retval, num_files, max_num_lines, file_w_max_num_lines) = \
      loc_main.do_main(['--src-root-dir', codedir,
                        '--gen-includes-dir', codedir,
                        '--gen-source-dir', codedir,
                        '--verbose'])
    assert retval is True
    assert num_files == 2
    assert max_num_lines > 0
    assert file_w_max_num_lines.endswith('two-files-main.c')
    verify_file_exists(codedir, 'loc.h')
    verify_file_exists(codedir, 'loc_tokens.h')
    verify_file_exists(codedir, 'loc_filenames.c')

# #############################################################################
def test_two_files_program_with_loc_decoder_dir_arg():
    """
    Exercise generator on a program with two source files from test-code base
    with --loc-decoder-dir . Verify that binary is produced as expected.
    Execute the binary w/default and with one arg, to ensure that it basically
    works.
    """
    binname = 'two-files-program'
    codedir = LocTestCodeDir + '/' + binname + '/'
    (retval, num_files, max_num_lines, file_w_max_num_lines) = \
      loc_main.do_main(['--src-root-dir', codedir,
                        '--loc-decoder-dir', codedir,
                        '--verbose'])
    assert retval is True
    assert num_files == 2
    assert max_num_lines > 0
    assert file_w_max_num_lines.endswith('two-files-main.c')

    binname_loc = binname + '_loc'
    verify_file_exists(codedir, binname_loc)

    print(f"Execute LOC-decoder binary {binname_loc}:\n")
    exec_binary([codedir + '/' + binname + '_loc'])

    # Execute --brief arg, w/known hard-coded input LOC-IDs.
    print(f"Execute LOC-decoder binary {binname_loc} --brief:\n")
    exec_binary([codedir + '/' + binname + '_loc', '--brief',
                 '65540', '65541', '131082', '131089'])

    # Execute LOC-decoder w/known hard-coded input LOC-IDs.
    print(f"Execute LOC-decoder binary {binname_loc}:\n")
    exec_binary([codedir + '/' + binname + '_loc',
                 '65540', '65541', '131082', '131089'])

# #############################################################################
# Helper test methods
# #############################################################################

def test_verify_file_exists():
    """Exerciser for verify_file_exists() method."""
    verify_file_exists(LocTestsDir, os.path.basename(__file__))
    # verify_file_exists(LocTestsDir, __file__ + 'xxx')

# #############################################################################
def verify_file_exists(dirname:str, filename:str) -> bool:
    """
    Check that the expected [generated] file exists.
    """
    assert os.path.exists(dirname + '/' + filename) is True

# #############################################################################
def exec_binary(cmdargs:list):
    """Execute a binary, with args, and print output to stdout."""
    try:
        result = sp.run(cmdargs, text=True, check=True, capture_output=True)
    except sp.CalledProcessError as exc:
        print("sp.run() Status: FAIL, rc=", exc.returncode,
              "\nargs=", exc.args,
              "\nstdout=", exc.stdout,
              "\nstderr=", exc.stderr)
    else:
        for line in str(result).split('\\n'):
            print(line)
