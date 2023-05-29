/*
 * This is a very simple demo program to show how the LOC macros can be used in
 * couple of different ways.
 *
 * 1. Explicitly generate the encoding using __LOC__
 * 2. Hide the generation behind a caller-macro, FUNCTION2().
 * 3. Caller's LOC is decoded inside the callee.
 */
#include <stdio.h>
#include "loc.h"

// Caller-macro to invoke function and synthesize code-location
#define FUNCTION2()     function2(__LOC__)

static void
function1(loc_t loc)
{
    printf("%s:%d:%s(): Hello World! Called from %s:%d\n",
            __FILE__, __LINE__, __func__, LOC_FILE(loc), LOC_LINE(loc));
}

static void
function2(loc_t loc)
{
    printf("%s:%d:%s(): Hello World! Called from %s:%d\n",
            __FILE__, __LINE__, __func__, LOC_FILE(loc), LOC_LINE(loc));
}

int
main(int argc, const char *argv[])
{
    printf("%s:%d:%s(): Hello World!\n", __FILE__, __LINE__, __func__);
    function1(__LOC__);

    FUNCTION2();
}
