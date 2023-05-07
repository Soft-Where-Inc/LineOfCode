#include <stdio.h>
#include "two_files.h"

static void
function1(void)
{
    printf("%s:%d:%s(): Hello World\n", __FILE__, __LINE__, __func__);
}

static void
function2(void)
{
    printf("%s:%d:%s(): Hello World\n", __FILE__, __LINE__, __func__);
}

int
main(int argc, const char *argv[])
{
    printf("%s(): Hello World\n", __func__);
    function1();
    function2();

    file1_function1();
    file1_function2();
}
