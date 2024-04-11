# #############################################################################
# makefile_test.py
#
"""
Collection of basic test cases to exercise different combinations of `make`
commands. Cross-check that the generation step _does_ happen only when needed
and Makefile-build rules are not indiscriminately triggering the Python
generator when LOC_ENABLED=2 (non-default build mode) is run.

Each test-case hammers out `make` target invocation(s) with different
environment variable settings for LOC_ENABLED, so that we exercise all
possible useful combinations that users could invoke.
"""

# #############################################################################
import os
import subprocess as sp

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

LOC_EXPLICITLY_UNSET = "0"
LOC_DEFAULT          = "1"
LOC_ELF_ENCODING     = "2"

# #############################################################################
# To see output from test-cases run:
# $ pytest --capture=tee-sys tests/makefile_test.py -k test_make_help
# #############################################################################
def test_make_help():
    """Test `make help`"""

    exec_make(['make', 'help'])

# #############################################################################
def test_make_all():
    """Test `make all`"""

    make_rv = exec_make(['make', 'clean'])
    make_rv = exec_make(['make', 'all'],
                        { "BUILD_VERBOSE": "1", "CC": "gcc", "LD": "g++" })
    assert make_rv is True

# #############################################################################
def test_make_all_loc_eq_0():
    """Test `LOC_ENABLED=0 make all`"""

    make_rv = exec_make(['make', 'clean'])
    make_rv = exec_make(['make', 'all'],
                        { "BUILD_VERBOSE": "1", "CC": "gcc", "LD": "g++",
                          "LOC_ENABLED": LOC_EXPLICITLY_UNSET})
    assert make_rv is True

# #############################################################################
def test_make_all_tests():
    """Test `make all-tests`"""

    make_rv = exec_make(['make', 'clean'])
    make_rv = exec_make(['make', 'all-tests'],
                        { "BUILD_VERBOSE": "1", "CC": "gcc", "LD": "g++" })
    assert make_rv is True

# #############################################################################
def test_make_all_tests_loc_eq_0():
    """Test `LOC_ENABLED=0 make all-tests`"""

    make_rv = exec_make(['make', 'clean'])
    make_rv = exec_make(['make', 'all-tests'],
                        { "BUILD_VERBOSE": "1", "CC": "gcc", "LD": "g++",
                          "LOC_ENABLED": LOC_EXPLICITLY_UNSET})
    assert make_rv is True

# #############################################################################
def test_make_all_run_tests():
    """Test `make all` followed by `make run-tests`"""

    make_rv = exec_make(['make', 'clean'])
    make_rv = exec_make(['make', 'all'],
                        { "BUILD_VERBOSE": "1", "CC": "gcc", "LD": "g++" })
    make_rv = exec_make(['make', 'run-tests'])
    assert make_rv is True

# #############################################################################
def test_make_all_run_tests_loc_eq_0():
    """Test `make all` followed by `LOC_ENABLED=0 make run-tests`"""

    make_rv = exec_make(['make', 'clean'])
    make_rv = exec_make(['make', 'all'],
                        { "BUILD_VERBOSE": "1", "CC": "gcc", "LD": "g++",
                          "LOC_ENABLED": LOC_EXPLICITLY_UNSET})
    make_rv = exec_make(['make', 'run-tests'])
    assert make_rv is True

# #############################################################################
def test_make_all_run_tests_loc_eq_1():
    """Test `make all` followed by `LOC_ENABLED=1 make run-tests`"""

    make_rv = exec_make(['make', 'clean'])
    make_rv = exec_make(['make', 'all'],
                        { "BUILD_VERBOSE": "1", "CC": "gcc", "LD": "g++",
                          "LOC_ENABLED": LOC_DEFAULT})
    make_rv = exec_make(['make', 'run-tests'])
    assert make_rv is True
    verify_unit_test_gen_files()

# #############################################################################
def test_make_all_run_tests_loc_elf():
    """Test `make all` followed by `LOC_ENABLED=2 make run-tests`"""

    make_rv = exec_make(['make', 'clean'])
    make_rv = exec_make(['make', 'all'],
                        { "BUILD_VERBOSE": "1", "CC": "gcc", "LD": "g++",
                          "LOC_ENABLED": LOC_ELF_ENCODING})
    make_rv = exec_make(['make', 'run-tests'])
    assert make_rv is True
    verify_unit_test_gen_files(loc_generate = False)

# #############################################################################
def test_make_run_unit_tests():
    """Test `make run-unit-tests`"""

    make_rv = exec_make(['make', 'clean'])
    make_rv = exec_make(['make', 'run-unit-tests'],
                        { "BUILD_VERBOSE": "1", "CC": "gcc", "LD": "g++" })
    assert make_rv is True
    verify_unit_test_gen_files()

# #############################################################################
def test_make_run_unit_tests_loc_eq_0():
    """Test `LOC_ENABLED=1 make run-unit-tests`"""

    make_rv = exec_make(['make', 'clean'])
    make_rv = exec_make(['make', 'run-unit-tests'],
                        { "BUILD_VERBOSE": "1", "CC": "gcc", "LD": "g++",
                          "LOC_ENABLED": LOC_EXPLICITLY_UNSET})
    assert make_rv is True
    verify_unit_test_gen_files(loc_generate = False)

# #############################################################################
def test_make_run_unit_tests_loc_eq_1():
    """Test `LOC_ENABLED=1 make run-unit-tests`"""

    make_rv = exec_make(['make', 'clean'])
    make_rv = exec_make(['make', 'run-unit-tests'],
                        { "BUILD_VERBOSE": "1", "CC": "gcc", "LD": "g++",
                          "LOC_ENABLED": LOC_DEFAULT})
    assert make_rv is True
    verify_unit_test_gen_files()

# #############################################################################
def test_make_run_unit_tests_loc_elf():
    """Test `LOC_ENABLED=2 make run-unit-tests`"""

    make_rv = exec_make(['make', 'clean'])
    make_rv = exec_make(['make', 'run-unit-tests'],
                        { "BUILD_VERBOSE": "1", "CC": "gcc", "LD": "g++",
                          "LOC_ENABLED": LOC_ELF_ENCODING})
    assert make_rv is True
    verify_unit_test_gen_files(loc_generate = False)

# #############################################################################
def test_make_all_test_code():
    """Test `make all-test-code`"""

    make_rv = exec_make(['make', 'clean'])
    make_rv = exec_make(['make', 'all-test-code'],
                        { "BUILD_VERBOSE": "1", "CC": "gcc", "LD": "g++" })
    assert make_rv is True

# #############################################################################
def test_make_all_test_code_loc_eq_0():
    """Test `LOC_ENABLED=0 make all-test-code`"""

    make_rv = exec_make(['make', 'clean'])
    make_rv = exec_make(['make', 'all-test-code'],
                        { "BUILD_VERBOSE": "1", "CC": "gcc", "LD": "g++",
                          "LOC_ENABLED": LOC_EXPLICITLY_UNSET})
    assert make_rv is True

# #############################################################################
def test_make_run_test_code():
    """Test `make run-test-code`"""

    make_rv = exec_make(['make', 'clean'])
    make_rv = exec_make(['make', 'run-test-code'],
                        { "BUILD_VERBOSE": "1", "CC": "gcc", "LD": "g++" })
    assert make_rv is True
    verify_test_code_gen_files()

# #############################################################################
def test_make_run_test_code_loc_eq_0():
    """Test `LOC_ENABLED=1 make run-test-code`"""

    make_rv = exec_make(['make', 'clean'])
    make_rv = exec_make(['make', 'run-test-code'],
                        { "BUILD_VERBOSE": "1", "CC": "gcc", "LD": "g++",
                          "LOC_ENABLED": LOC_EXPLICITLY_UNSET})
    assert make_rv is True
    verify_test_code_gen_files(loc_generate = False)

# #############################################################################
def test_make_run_test_code_loc_eq_1():
    """Test `LOC_ENABLED=1 make run-test-code`"""

    make_rv = exec_make(['make', 'clean'])
    make_rv = exec_make(['make', 'run-test-code'],
                        { "BUILD_VERBOSE": "1", "CC": "gcc", "LD": "g++",
                          "LOC_ENABLED": LOC_DEFAULT})
    assert make_rv is True
    verify_test_code_gen_files()

# #############################################################################
def test_make_run_test_code_loc_elf():
    """Test `LOC_ENABLED=2 make run-test-code`"""

    make_rv = exec_make(['make', 'clean'])
    make_rv = exec_make(['make', 'run-test-code'],
                        { "BUILD_VERBOSE": "1", "CC": "gcc", "LD": "g++",
                          "LOC_ENABLED": LOC_ELF_ENCODING})
    assert make_rv is True
    verify_test_code_gen_files(loc_generate = False)

# #############################################################################
# Helper test methods
# #############################################################################

def verify_unit_test_gen_files(loc_generate:bool = True) -> bool:
    """
    Verify the state of generated files for unit-test sources.
    For unit-tests we will generate LOC-files in the unit-tests' dir.
    For ELF-based unit-test, we should never generate any files.
    """
    dirname = LocTestsDir + '/unit/'
    for genfile in [ 'loc.h', 'loc_tokens.h', 'loc_filenames.c' ]:
        make_rv =  verify_file_exists(dirname + 'single_file_src/', genfile)
        if loc_generate is True:
            assert make_rv is True
        else:
            assert make_rv is False

        make_rv =  verify_file_exists(dirname + 'single_file_elf_src/', genfile)
        assert make_rv is False


# #############################################################################
def verify_test_code_gen_files(loc_generate:bool = True) -> bool:
    """
    Verify the state of generated files for sample test-code sources.
    For sample tests we will generate LOC-files in the sample-tests' dir.
    While building sample-tests using ELF-based encoding, we should never
    generate any files.
    """
    dirname = LocDirRoot + '/test-code/'
    for test_code_dir in [   'single-file-cpp-program'
                         ]:
        for genfile in [ 'loc.h', 'loc_tokens.h', 'loc_filenames.c' ]:
            make_rv =  verify_file_exists(dirname + test_code_dir, genfile)
            if loc_generate is True:
                print(f'{dirname=}, {test_code_dir=}, {genfile=}')
                assert make_rv is True
            else:
                assert make_rv is False

# #############################################################################
def verify_file_exists(dirname:str, filename:str) -> bool:
    """
    Check that the expected [generated] file exists.
    """
    return os.path.exists(dirname + '/' + filename)

# #############################################################################
def exec_make(cmdargs:list, extra_env:dict = None) -> bool:
    """Execute `make` command with specified arguments."""
    if extra_env is None:
        extra_env = {}
    try:
        # Need to run `make` from the dir where Makefile lives.
        # Add-in user-specified env-vars to existing env of process.
        result = sp.run(cmdargs, text=True, check=True, capture_output=True,
                        cwd = LocDirRoot,
                        env={**os.environ, **extra_env}
                        )
    except sp.CalledProcessError as exc:
        print("sp.run() Status: FAIL, rc =", exc.returncode,
              "\nargs =", exc.args,
              "\nstdout =", exc.stdout,
              "\nstderr =", exc.stderr)
        return False
    for line in str(result).split('\\n'):
        print(line)
    return True
