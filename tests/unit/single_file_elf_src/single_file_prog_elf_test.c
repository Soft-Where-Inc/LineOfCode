/*
 * -----------------------------------------------------------------------------
 * single_file_prog_elf_test.c
 *
 * LOC test for a single file program, using LOC-variation based on ELF.
 * No Python generation is needed for this program. It relies only on loc.h
 *
 * The Makefile INCDIR rules for this file are written so that even if we
 * run the builds with LOC_ENABLED=1 (i.e., LOC-files are generated), for this
 * file, we #include the default include/loc.h . E.g., build output:
 *
 * ... gcc -DLOC_FILE_INDEX=LOC_single_file_prog_elf_test_c             \
 *      -I ./tests/unit -I ./ -I ./include                              \
 *      -c tests/unit/single_file_elf_src/single_file_prog_elf_test.c
 *
 * So, there is no dependency on the generation step.
 * -----------------------------------------------------------------------------
 */
#include <string.h>
#include "ctest.h" // This is required for all test-case files.
#include "loc.h"

extern _Bool str_endswith(const char *str, const char *suffix);
extern _Bool str_cmp_eq(const char *str1, const char *str2);

/*
 * Global data declaration macro:
 */
CTEST_DATA(single_file_prog_loc_elf){};

CTEST_SETUP(single_file_prog_loc_elf) {}

// Optional teardown function for suite, called after every test in suite
CTEST_TEARDOWN(single_file_prog_loc_elf) {}

/*
 * Basic test case to show use-and-verification of LOC-encoding macro.
 */
CTEST2(single_file_prog_loc_elf, test_basic_LOC)
{
    // Encode current line-of-code into loc
    loc_t loc = __LOC__; int exp_line = __LINE__;

    // Invoke LOC's default print method.
    loc_print(loc);

    const char *file = LOC_FILE(loc);
    const char *func = LOC_FUNC(loc);
    int line = LOC_LINE(loc);

    // Print for visual examination.
    printf("\n__LINE__=%d, LOC line=%d\n", exp_line, line);
    printf("__FILE__='%s', LOC file='%s'\n", __FILE__, file);
    printf("__FUNC__='%s', LOC func='%s'\n", __FUNCTION__, func);

    ASSERT_EQUAL(exp_line, line,
                 "Expected line=%d, actual line=%d\n", exp_line, line);

    // Compare LOC-filename with actual file name.
    ASSERT_TRUE(str_cmp_eq(__FILE__, file),
                "Expected: '%s', Actual: '%s'\n", __FILE__, file);

    // Compare LOC-function name with actual function name.
    ASSERT_TRUE(str_cmp_eq(__FUNCTION__, func),
                "Expected: '%s', Actual: '%s'\n", __FUNCTION__, func);
}
