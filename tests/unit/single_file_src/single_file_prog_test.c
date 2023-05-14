/*
 * -----------------------------------------------------------------------------
 * single_file_prog_test.c --
 *
 * LOC test for a single file program.
 * -----------------------------------------------------------------------------
 */
#include "ctest.h" // This is required for all test-case files.

/*
 * Global data declaration macro:
 */
CTEST_DATA(single_file_prog){};

CTEST_SETUP(single_file_prog) {}

// Optional teardown function for suite, called after every test in suite
CTEST_TEARDOWN(single_file_prog) {}

/*
 * Basic test case.
 */
CTEST2(single_file_prog, test_basic_LOC) {}
