/*
 * single-file-main.cc:
 *
 * This is a very simple demo program to show how the LOC macros can be used
 * in couple of different ways, implemented in C++ code, name *.cc.
 *
 * This example program shows that LOC-macros are equally applicable
 * in C++ code base, when the source file is named *.cc. This sample program
 * is identical to single-file-cpp-program/single-file-main.cpp, except it
 * adds the following testing variations:
 *
 * - The file name is *.cc, to show the Makefile changes needed to
 *   compile such file.
 * - More importantly, Makefile does not specify the CFLAGS rules
 *   for this file (unlike how it's done for other files.)
 * - The Py-generator script is updated to report the form of CFLAGS
 *   that will work for all files using LOC-macros.
 * - The build system is invoked using this generated CFLAGS symbol
 *   to show how one could automate the build process for such
 *   LOC-enabled files w/o making explicit Makefile changes.
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
