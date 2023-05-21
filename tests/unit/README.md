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

----
## Workflow

The typical workflow to incorporate the LOC-machinery in your project would 
be something as follows:

- Choose which source files where the LOC-macros would be used.  Typically,
  you would start using the `__LOC__` macro to encode code-location.
  Then, you would use the `LOC_FILE()` and `LOC_LINE()` macros to decode
  the encoded code-location. The unit-test sources are an example of how
  you would start using these annotations.

  - `#include "loc.h"` in the source files where the LOC macros are used.

- Run the [gen_loc_files.py](../../loc/gen_loc_files.py) tool with the
  `--verbose` option to see where the files are generated.
  Update your Makefile system to copy over the generated
  `loc.h` and `loc_tokens.h` to your `include/` dir. Copy over the
  generated `loc_filenames.c` to an appropriate source sub-directory.

- Apply the suggested Makefile `patsubst()` clause that the Python script
  generates to your project's `Makefile` `CFLAGS` clause in order to
  successfully compile the source files that were changed to use the
  LOC macros.

  - Update your project's Makefile to compile and link the
  `loc_filenames.c` with your binary. As the Make-rules may vary based
  on your build system, the Python script does not provide any
  suggested syntax to compile and link this file.

These steps should get you going to compile and build your project.

----
## Automation

You can automate to some extent this workflow as follows:

- Use the `--gen-includes-dir` argument to specify the `include/`
  files directory for your project. (It's preferable to specify the
  full directory path.) The `.h` files will be generated at this
  location and will, then, be accessible when `#include`-ed in the
  source files which use the LOC macros.

- Use the `--gen-sources-dir` argument to specify the `src/`
  files directory for your project. (It's preferable to specify the
  full directory path.) The `.c` file(s) will be generated at this
  location.

  - The generated `loc_filenames.c` file should be included in the
    list of files that are compiled and linked into your project's
    binary.

  - The project-specific generated `<project>_loc.c` file is linked
    with `loc_filenames.c` to build a standalone decoder binary.
    The Python script does this, by default. You can use the
    decoder binary to unpack encoded LOC-int values to their
    constituent file name and line number.

    This `*_loc.c` file should **not** be included in the list
    of files linked with your project as it is a standalone
    program with its own `main()`.

- For most cases, the `CFLAGS` clause suggested by the Python script
  can be used directly to invoke your project's `make`, as:

  ```shell
  $ CFLAGS=patsubst(...) make
  ```

  This will usually work as the expected convention is that most
  `Makefile`s define their `CFLAGS` as `CFLAGS += ...`

- You can further automate this using the `--gen-cflags` argument
  which will print the suggested `CFLAGS` clause.
  ```shell
  $ ./gen_loc_files.py --src-root-dir ~/Project --gen-cflags
  ```

- Assume that the LOC packages lives at `~/LOC`. And that the `Makefile`
  for your source code project lives at `~/Project/Makefile`.

  A typical full invocation of the Python script to process your source
  code repository and to suggest the `Makefile` clause required to compile
  all sources (that may eventually use LOC-macros) would be something
  on the lines of:
  ```shell
  $ cd ~/Project

  $ export CFLAGS=$(~/LOC/loc/gen_loc_files.py              \
                    --gen-includes-dir ~/Project/include    \
                    --gen-sources-dir ~/Project/src         \
                    --src-root-dir ~/Project                \
                    --gen-cflags)
  $ make
  ```
- In some cases, described below, you may have to do a one-time
  hand-edit of your project's `Makefile` to add the suggested
  `CFLAGS` clause:

   - If you have a complex set of Make rules
   - If there are some duplicate conflicts in your project's
     sources, which get disambiguated by the Python script to
     avoid conflicts in the generated LOC-token names.

     In this case, the suggested `CFLAGS` may be complex,
     and may list source files that will never use the LOC-macros.
     In such cases, you may have to custom-edit the suggested
     `CFLAGS` accounting for actual, and potential future, usages
     of the LOC-macros in source files with duplicate file names.
