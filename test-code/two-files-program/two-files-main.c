/*
 * This is a simple demo program to show how the LOC macros can be used in
 * programs with multiple source files. Couple of usages are illustrated:
 *
 * 1. The outermost LOC is passed-down and decoded by a lower minion fn
 * 2. The sequence of LOC of caller's is passed-down the stack and decoded by
 *    the lowermost function, with the calls occurring across compilation units.
 */
#include <stdio.h>
#include "two_files.h"
#include "loc.h"

static void
function2(loc_t loc)
{
    printf("%s:%d:%s(): Hello World! Called by: %s:%d\n",
           __FILE__, __LINE__, __func__,
           LOC_FILE(loc), LOC_LINE(loc));
}

static void
function1(loc_t loc)
{
    printf("%s:%d:%s(): Hello World!\n", __FILE__, __LINE__, __func__);
    function2(loc);
}

int
main(int argc, const char *argv[])
{
    printf("%s:%d:%s(): Hello World!\n", __FILE__, __LINE__, __func__);
    function1(__LOC__);

    file1_function1(__LOC__);
}
