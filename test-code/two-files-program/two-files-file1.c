#include <stdio.h>
#include "two_files.h"
#include "loc.h"

static void file1_function2(loc_t outer);
static void file1_function3(loc_t outer, loc_t inner);

void
file1_function1(loc_t loc)
{
    printf("%s:%d:%s(): Hello World!\n", __FILE__, __LINE__, __func__);
    file1_function2(loc);
}

static void
file1_function2(loc_t outerloc)
{
    printf("%s:%d:%s(): Hello World!\n", __FILE__, __LINE__, __func__);
    file1_function3(outerloc, __LOC__);
}

static void
file1_function3(loc_t outerloc, loc_t innerloc)
{
    printf("%s:%d:%s(): Hello World! Call sequence: %s:%d -> %s:%d\n",
           __FILE__, __LINE__, __func__,
           LOC_FILE(outerloc), LOC_LINE(outerloc),
           LOC_FILE(innerloc), LOC_LINE(innerloc));
}
