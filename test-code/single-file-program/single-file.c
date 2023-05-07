#include <stdio.h>

static void
function1(void)
{
    printf("%s(): Hello World\n", __func__);
}

static void
function2(void)
{
    printf("%s(): Hello World\n", __func__);
}

int
main(int argc, const char *argv[])
{
    printf("%s(): Hello World\n", __func__);
    function1();

    function2();
}
