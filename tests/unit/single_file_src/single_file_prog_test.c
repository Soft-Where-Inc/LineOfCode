/*
 * -----------------------------------------------------------------------------
 * single_file_prog_test.c --
 *
 * LOC test for a single file program.
 * -----------------------------------------------------------------------------
 */
#include <string.h>
#include "ctest.h" // This is required for all test-case files.
#include "loc.h"

_Bool str_endswith(const char *str, const char *suffix);

/*
 * Global data declaration macro:
 */
CTEST_DATA(single_file_prog){};

CTEST_SETUP(single_file_prog) {}

// Optional teardown function for suite, called after every test in suite
CTEST_TEARDOWN(single_file_prog) {}

/*
 * Basic test case to show use-and-verification of LOC-encoding macro.
 */
CTEST2(single_file_prog, test_basic_LOC)
{
    // Encode current line-of-code into loc
    loc_t loc = __LOC__; int exp_line = __LINE__;

    const char *file = LOC_FILE(loc);
    int line = LOC_LINE(loc);

    // Print for visual examination.
    printf("\n__LINE__=%d, LOC line=%d\n", exp_line, line);
    printf("__FILE__='%s', LOC file='%s'\n", __FILE__, file);

    ASSERT_EQUAL(exp_line, line,
                 "Expected line=%d, actual line=%d\n", exp_line, line);

    // Compare LOC-filename with actual file name.
    ASSERT_TRUE(str_endswith(__FILE__, file),
                "Expected: '%s', Actual: '%s'\n", __FILE__, file);
}

/* Helper functions */

/*
 * C-version of Python endswith() function.
 * Ref: https://stackoverflow.com/questions/744766/how-to-compare-ends-of-strings-in-c
 *
 * Returns TRUE, if suffix is a trailing sub-string of str. FALSE, otherwise.
 */
_Bool
str_endswith(const char *str, const char *suffix)
{
  size_t str_len = strlen(str);
  size_t suffix_len = strlen(suffix);

  return (   (str_len >= suffix_len)
          && (!memcmp(str + str_len - suffix_len, suffix, suffix_len)));
}
