# #############################################################################
# LOC: Line-Of-Code: Makefile: build tests, example programs, run pytests
# Developed based on SplinterDB (https://github.com/vmware/splinterdb) Makefile
# #############################################################################

.DEFAULT_GOAL := all

help::
	@echo 'Usage: make [<target>]'
	@echo 'Supported targets: clean all run-tests run-test-code'

#
# Verbosity
#
ifndef BUILD_VERBOSE
   BUILD_VERBOSE=0
endif

# Boolean, so we run Python generator script only once.
RUN_PYGEN=1

# Setup echo formatting for messages.
ifeq "$(BUILD_VERBOSE)" "1"
   COMMAND=
   PROLIX=@echo
   BRIEF=@ >/dev/null echo
   BRIEF_FORMATTED=@ >/dev/null echo
   BRIEF_PARTIAL=@echo -n >/dev/null
else ifeq "$(BUILD_VERBOSE)" "0"
   COMMAND=@
   PROLIX=@ >/dev/null echo
   BRIEF=@echo
   BRIEF_FORMATTED=@printf
   BRIEF_PARTIAL=@echo -n
else
   $(error Unknown BUILD_VERBOSE mode "$(BUILD_VERBOSE)".  Valid values are "0" or "1". Default is "0")
endif

# ###################################################################
# SOURCE DIRECTORIES AND FILES
#
LOCPACKAGE           = loc
SRCDIR               = src
TESTSDIR             = tests
UNITDIR              = unit
TEST_CODE            = test-code
UNIT_TESTSDIR        = $(TESTSDIR)/$(UNITDIR)
INCDIR               = $(UNIT_TESTSDIR)
LOCGENPY             = $(LOCPACKAGE)/gen_loc_files.py

# ------------------------------------------------------------------------
# Define a recursive wildcard function to 'find' all files under a sub-dir
# See https://stackoverflow.com/questions/2483182/recursive-wildcards-in-gnu-make/18258352#18258352
define rwildcard =
	$(foreach d,$(wildcard $(1:=/*)),$(call rwildcard,$d,$2) $(filter $(subst *,%,$2),$d))
endef

# ###################################################################
# BUILD DIRECTORIES AND FILES
#
ifndef BUILD_ROOT
   BUILD_ROOT := build
endif

#
# Build mode
#
ifndef BUILD_MODE
   BUILD_MODE=release
endif
BUILD_DIR := $(BUILD_MODE)

BUILD_PATH=$(BUILD_ROOT)/$(BUILD_DIR)

OBJDIR = $(BUILD_PATH)/obj
BINDIR = $(BUILD_PATH)/bin

# Target provided in case one wishes to re-gen LOC-files, manually.
genloc:
	$(LOCGENPY) --gen-includes-dir  $(TESTSDIR)/$(UNITDIR) --gen-source-dir $(TESTSDIR)/$(UNITDIR) --src-root-dir $(TESTSDIR)/$(UNITDIR) --verbose

# ##############################################################################
# All the generated files (source and header files)
# Ref: https://stackoverflow.com/questions/37781449/including-generated-files-in-makefile-dependencies
# ##############################################################################
# If you list both .h & .c file, generator gets triggered twice. List just one.
# GENERATED := $(TESTSDIR)/$(UNITDIR)/loc.h $(TESTSDIR)/$(UNITDIR)/loc_filenames.c
GENERATED := $(TESTSDIR)/$(UNITDIR)/loc_filenames.c

# Rule: Use Python generator script to generate this files
$(GENERATED):
	@echo
	@echo "Invoke LOC-generator triggered by: " $@
	$(LOCGENPY) --gen-includes-dir  tests/unit --gen-source-dir tests/unit --src-root-dir tests/unit --verbose
	@echo

ifeq "$(BUILD_VERBOSE)" "1"
	@echo
	$(info $$TEST_CODE_SRC     is [${TEST_CODE_SRC}])
	$(info $$TEST_CODE_OBJS    is [${TEST_CODE_OBJS}])
	$(info $$TEST_CODE_BIN_SRC is [${TEST_CODE_BIN_SRC}])
	$(info $$TEST_CODE_BINS    is [${TEST_CODE_BINS}])
	$(info $$UNIT_TESTSRC      is [${UNIT_TESTSRC}])
	$(info $$GENERATED_OBJS    = [${GENERATED_OBJS}])
	$(info $$UNIT_TESTOBJS     = [${UNIT_TESTOBJS}])
endif

# The rules to generate object files from the generated source files
GENERATED_SRCS := $(filter %.c,$(GENERATED))
GENERATED_OBJS := $(GENERATED_SRCS:%.c=$(OBJDIR)/%.o)

# ###################################################################
# SOURCE DIRECTORIES AND FILES

# Symbol for all unit-test sources, from which we will build standalone
# unit-test binaries.
# UNIT_TESTSRC := $(call rwildcard,$(UNIT_TESTSDIR),*.c)
UNIT_TESTSRC := $(shell find $(TESTSDIR)/$(UNITDIR) -type f -name *.c -print)

# Objects from unit-test sources in tests/unit/ sub-dir, for unit-tests
# Resolves to a list: obj/tests/unit/a.o obj/tests/unit/b.o obj/tests/unit/c.o
UNIT_TESTOBJS := $(UNIT_TESTSRC:%.c=$(OBJDIR)/%.o)

# ---- Symbols to build test-code sample programs
TEST_CODE_SRC := $(shell find $(TEST_CODE) -type f -name *.c -print)
TEST_CODE_OBJS := $(TEST_CODE_SRC:%.c=$(OBJDIR)/%.o)

# Grab the "main.c" for each test-code sample program
TEST_CODE_BIN_SRC=$(filter %-main.c, $(TEST_CODE_SRC))

# ----------------------------------------------------------------------------
# Generate location / name of test-code sample program binary, using built-in
# substitution references. test-code/ has sources like:
#
#   test-code/single-file-program/single-file-main.c
#   test-code/two-files-program/two-files-main.c
#
# Convert this list of *main.c to generate test-code program binary names:
#   build/release/bin/test-code/single-file-program
#   build/release/bin/test-code/two-files-program
#
TEST_CODE_BINS_TMP=$(TEST_CODE_BIN_SRC:$(TEST_CODE)/%-main.c=$(BINDIR)/$(TEST_CODE)/%-program)
TEST_CODE_BINS=$(patsubst %program/, %program, $(dir $(TEST_CODE_BINS_TMP)) )

# ###################################################################
# Report build machine details and compiler version for troubleshooting,
# so we see this output for clean builds, especially in CI-jobs.
# ###################################################################
.PHONY : clean tags
clean:
	uname -a
	$(CC) --version
	rm -rf $(BUILD_ROOT)
	find . \( -name "*loc*.c" -o -name "loc*.h" \)  -exec rm -rf {} \;

####################################################################
# The main targets
#
all: all-tests all-test-code
all-tests: $(BINDIR)/unit_test
all-test-code: $(TEST_CODE_BINS)

# ###################################################################
# CFLAGS, LDFLAGS, ETC
#
CFLAGS=-DLOC_FILE_INDEX=$(patsubst %.c,LOC_%_c,$(notdir $<))

INCLUDE = -I $(INCDIR)

# use += here, so that extra flags can be provided via the environment

CFLAGS += -D_GNU_SOURCE -ggdb3 -Wall -Wfatal-errors -Werror

# ###################################################################
# Automatically create directories, based on
# http://ismail.badawi.io/blog/2017/03/28/automatic-directory-creation-in-make/
.SECONDEXPANSION:

.SECONDARY:

%/.:
	$(COMMAND) mkdir -p $@

# These targets prevent circular dependencies arising from the
# recipe for building binaries
$(BINDIR)/.:
	$(COMMAND) mkdir -p $@

$(BINDIR)/%/.:
	$(COMMAND) mkdir -p $@

# ###################################################################
# Dependencies
#
$(GENERATED_OBJS) :$(GENERATED)
$(UNIT_TESTOBJS): $(GENERATED_OBJS)
$(BINDIR)/unit_test: $(UNIT_TESTOBJS) $(GENERATED_OBJS)

# ###################################################################
# The dependencies for each test-code sample program
# Every example program of the form bin/test-code/<eg-prog> depends on
# obj/test-code/<eg-prog>/*.o -> *.c
# There can be more than one .o's linked to create test-code example
# program.

$(BINDIR)/$(TEST_CODE)/single-file-program: $(OBJDIR)/$(TEST_CODE)/single-file-program/single-file-main.o

$(BINDIR)/$(TEST_CODE)/two-files-program: $(OBJDIR)/$(TEST_CODE)/two-files-program/two-files-main.o \
                                          $(OBJDIR)/$(TEST_CODE)/two-files-program/two-files-file1.o

# ###################################################################
# RECIPES:

# RESOLVE: Need to re-define INCLUDE depending on target.
# For all-test-code, we need to use -I test-code/<subdir>
# Dependencies for the main executables
COMPILE.c = $(CC) $(CFLAGS) $(INCLUDE) -c

# Compile each .c file into its .o
# Also define a dependency on the dir in which .o will be produced (@D).
# The secondary expansion will invoke mkdir to create output dirs first.
$(OBJDIR)/%.o: %.c | $$(@D)/.
	$(BRIEF_FORMATTED) "%-20s %-50s [%s]\n" Compiling $< $@
	$(COMMAND) $(COMPILE.c) $< -o $@
	$(PROLIX) # blank line

# Link .o's to product running binary
# Define dependency on output dir existing, so secondary expansion will
# trigger mkdir to create bin/s output dir.
# If you add "$^" to 'Linking' message, you will see list of .o's being linked
$(BINDIR)/%: | $$(@D)/.
	$(BRIEF_FORMATTED) "%-20s %s\n" Linking $@
	$(COMMAND) $(LD) $(LDFLAGS) $^ -o $@ $(LIBS)
	$(PROLIX) # blank line

unit_test: $(BINDIR)/unit_test

#*************************************************************#
# Testing
#

.PHONY: install

run-tests: run-unit-tests run-test-code
	./test.sh

run-unit-tests: all-tests
	@echo
	@echo "**** Run unit-tests ****"
	$(BINDIR)/unit_test

run-test-code: all-test-code
	@echo
	@echo "**** Run sample test-code programs ****"
	for i in $(TEST_CODE_BINS); do echo " "; echo "-- Executing $$i";$$i || exit;  done
