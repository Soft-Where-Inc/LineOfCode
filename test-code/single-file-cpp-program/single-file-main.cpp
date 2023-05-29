/*
 * This is a very simple demo program to show how the LOC macros can be used
 * in couple of different ways, implemented in C++ code.
 *
 * 1. Explicitly generate the encoding using __LOC__
 * 2. Hide the generation behind a caller-macro, FUNCTION2().
 * 3. Caller's LOC is decoded inside the callee.
 *
 * This example program shows that LOC-macros are equally applicable
 * in C++ code base.
 */
#include <iostream>
#include "loc.h"

using namespace std;

// Caller-macro to invoke function and synthesize code-location
#define FUNCTION2()     function2(__LOC__)

static void
function1(loc_t loc)
{
    cout << __FILE__ << ":" << __func__ << ":" <<  __LINE__
         << ": Hello World! Called from "
         << LOC_FILE(loc) << ":" << LOC_LINE(loc)
         << endl;
}

static void
function2(loc_t loc)
{
    cout << __FILE__ << ":" << __func__ << ":" <<  __LINE__
         << ": Hello World! Called from "
         << LOC_FILE(loc) << ":" << LOC_LINE(loc)
         << ", __PRETTY_FUNCTION__=" << __PRETTY_FUNCTION__
         << endl;
}

int
main(int argc, const char *argv[])
{
    cout << __FILE__ << ":" << __func__ << ":" <<  __LINE__
         << endl;
    function1(__LOC__);

    FUNCTION2();
}
