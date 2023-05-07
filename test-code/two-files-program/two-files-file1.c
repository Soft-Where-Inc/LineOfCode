#include <stdio.h>
#include "two_files.h"

void
file1_function1(void)
{
    printf("%s:%d:%s(): Hello World\n", __FILE__, __LINE__, __func__);
}

void
file1_function2(void)
{
    printf("%s:%d:%s(): Hello World\n", __FILE__, __LINE__, __func__);
}
