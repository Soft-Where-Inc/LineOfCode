# Unit-Tests - README

This directory contains a small number of CUnit test files to demonstrate
how-to use the LOC interface macros and associated `Makefile` changes.
The tests also verify the correctness of the LOC interface macros.

The unit-test programs are annotated to use the LOC-macros so by themselves,
these programs will not compile cleanly.

[Makefile](../../Makefile) rules are implemented to generate the required
LOC `*.h` and `*.c` files, which are then linked into the `unit_test` binary.
The Makefile syntax shows how to specify the `-DLOC_FILE_INDEX` required to
compile the `.c` files that use the LOC macros, e.g., `__LOC__`, `LOC_FILE()`
and `LOC_LINE()`, and a few others.

