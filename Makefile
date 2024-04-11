# #############################################################################
# LOC: Line-Of-Code: Makefile: build tests, example programs, run pytests
# SPDX-License-Identifier: Apache-2.0
#
# Developed based on SplinterDB (https://github.com/vmware/splinterdb) Makefile
#
# This Makefile supports build-and-test for:
#
# a) A small collection of C-unit-tests (.c), under tests/unit/, and
# b) A small collection of sample use-case application programs under test-code/
#     Here, we demonstrate use of this encoding with .c, .cpp and .cc files.
#
# This toolkit supports two forms of code-location encoding, referred to as:
#
# 1) LOC    : Default mode, based on Python generator script. Needs CFLAGS
#             specifier to compile references to LOC-macros in user's sources.
#             Depends on generated loc.h, loc_tokens.h and loc_filenames.c
#
# 2) LOC_ELF: Encoding technique using named ELF-section. Does not require any
#             Makefile / CFLAGS / Python-generator script support.
#             Depends on provided include/loc.h, src/loc.c
#
# The actual steps to integrate either (1) or (2) into any user project are
# simple. This Makefile exists to demonstrate that either encoding scheme can
# be used for any of (a) or (b) sources. Much of the work in this Makefile is
# to tease apart the build-rules for each encoding scheme as applicable to
# each set of unit-test or use-cases test-code.
#
# Most of the magic happens either in the generated loc.h or in the provided
# include/loc.h (& src/loc.c) files. These Makefile-rules are setup so that
# the user does not need to "know" which loc.h is being #include'ed.
# However, one must include only one of the two loc.h includes in the entire
# project.
#
# NOTE:
#   You cannot mix-and-match the loc.h files from different encoding schemes
#   in your project sources.
# #############################################################################

.DEFAULT_GOAL := all

help::
	@echo ' '
	@echo 'Usage: CC=gcc LD=g++ make <target>'
	@echo ' '
	@echo 'Supported targets: clean all all-tests run-tests run-unit-tests all-test-code run-test-code'
	@echo 'Environment variables: '
	@echo ' BUILD_MODE={release,debug}'
	@echo ' BUILD_VERBOSE={0,1}'

#
# Verbosity
#
ifndef BUILD_VERBOSE
   BUILD_VERBOSE=0
endif

# Setup echo formatting for messages.
ifeq "$(BUILD_VERBOSE)" "1"
   COMMAND=
   PROLIX=@echo
   BRIEF=@ >/dev/null echo
   # Always print message describe step executed, even in verbose mode.
   # BRIEF_FORMATTED=@ >/dev/null echo
   BRIEF_FORMATTED=@printf
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

# Compilers to use
CC  ?= gcc
CXX ?= g++
LD  ?= gcc

# ###################################################################
# SOURCE DIRECTORIES AND FILES, Generator Package
#
LOCPACKAGE          := loc
SRCDIR              := src
INCDIR              := include
TESTSDIR            := tests
UNITDIR             := unit
TEST_CODE           := test-code
UNIT_TESTSDIR       := $(TESTSDIR)/$(UNITDIR)
UNIT_INCDIR         := $(UNIT_TESTSDIR)
LOCGENPY            := $(LOCPACKAGE)/gen_loc_files.py
LOC_ELF_SRC         := $(SRCDIR)/loc.c

# LOC-encoding comes in two flavours. Default technique is based on
# Python-generator script. Enhanced technique is based on LOC-ELF
# encoding.
LOC_DEFAULT          := 1
LOC_ELF_ENCODING     := 2

# Re-set env-vars, if not set to script local symbols as == 0
#
ifndef LOC_ENABLED
    LOC_ENABLED := $(LOC_DEFAULT)
endif

LOC_GENERATE := 0
ifeq ($(LOC_ENABLED), $(LOC_DEFAULT))
    LOC_GENERATE := $(LOC_DEFAULT)
else ifeq ($(LOC_ENABLED), $(LOC_ELF_ENCODING))
    LOC_GENERATE := $(LOC_ELF_ENCODING)
endif

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
   BUILD_MODE := release
endif
BUILD_DIR := $(BUILD_MODE)

BUILD_PATH := $(BUILD_ROOT)/$(BUILD_DIR)

OBJDIR := $(BUILD_PATH)/obj
BINDIR := $(BUILD_PATH)/bin

# Target provided in case one wishes to re-gen LOC-files, manually.
genloc:
	$(LOCGENPY) --gen-includes-dir  $(TESTSDIR)/$(UNITDIR) --gen-source-dir $(TESTSDIR)/$(UNITDIR) --src-root-dir $(TESTSDIR)/$(UNITDIR) --verbose

# ##############################################################################
# All the generated files (source and header files)
# Ref: https://stackoverflow.com/questions/37781449/including-generated-files-in-makefile-dependencies
# ##############################################################################
# Maintenance Note: To add a new source file(s) to test-code/ dir, do:
#   - Add block of symbols similar to SINGLE_FILE_CPP_PROGRAM_TESTSRC
#   - If your new source uses LOC-macros, add symbols to include this file
#     as requiring generated-source. Eventually 'GENERATED' will change.
#   - You may have to update TEST_CODE_SRC, TEST_CODE_OBJS, TEST_CODE_BIN_SRC symbols
# ------------------------------------------------------------------------------

# If you list both .h & .c file, generator gets triggered twice. List just one.
# GENERATED := $(TESTSDIR)/$(UNITDIR)/loc.h $(TESTSDIR)/$(UNITDIR)/loc_filenames.c
ifeq ($(LOC_GENERATE), $(LOC_DEFAULT))

    UNIT_GENSRC                    := $(TESTSDIR)/$(UNITDIR)/single_file_src/loc_filenames.c
    SINGLE_FILE_PROGRAM_GENSRC     := $(TEST_CODE)/single-file-program/loc_filenames.c
    TWO_FILES_PROGRAM_GENSRC       := $(TEST_CODE)/two-files-program/loc_filenames.c
    SINGLE_FILE_CPP_PROGRAM_GENSRC := $(TEST_CODE)/single-file-cpp-program/loc_filenames.c
    SINGLE_FILE_CC_PROGRAM_GENSRC  := $(TEST_CODE)/single-file-cc-program/loc_filenames.c

else ifeq ($(LOC_GENERATE), $(LOC_ELF_ENCODING))

    # This is not really a generated source, but we reuse the symbol to keep
    # the downstream Make-logic simple[r].
    SINGLE_FILE_PROGRAM_GENSRC     := $(LOC_ELF_SRC)
    TWO_FILES_PROGRAM_GENSRC       := $(LOC_ELF_SRC)
    SINGLE_FILE_CPP_PROGRAM_GENSRC := $(LOC_ELF_SRC)
    SINGLE_FILE_CC_PROGRAM_GENSRC  := $(LOC_ELF_SRC)

endif

# As this Makefile builds all sources in this repo, we have a larger list
# of dependencies.
GENERATED := $(UNIT_GENSRC)                     \
             $(SINGLE_FILE_PROGRAM_GENSRC)      \
             $(TWO_FILES_PROGRAM_GENSRC)        \
             $(SINGLE_FILE_CPP_PROGRAM_GENSRC)  \
             $(SINGLE_FILE_CC_PROGRAM_GENSRC)

# ------------------------------------------------------------------------------
# Rule: Use Python generator script to generate the LOC-files
# Rule will be triggered for objects defined to be dependent on $(GENERATED) sources.
# Use the triggering target's dir-path to generate .h / .c files
# ------------------------------------------------------------------------------
ifeq ($(LOC_GENERATE), $(LOC_DEFAULT))
$(GENERATED):
	@echo
	@echo "Invoke LOC-generator triggered by: " $@
	$(LOCGENPY) --gen-includes-dir  $(dir $@) --gen-source-dir $(dir $@) --src-root-dir $(dir $@) --verbose
	@echo
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
UNIT_TESTSRC += $(UNIT_GENSRC)

# One of the unit-test programs is written specifically to only use the
# LOC_ELF encoding. So, we must always include the required source.
UNIT_TESTSRC += $(LOC_ELF_SRC)

# Objects from unit-test sources in tests/unit/ sub-dir, for unit-tests
# Resolves to a list: obj/tests/unit/a.o obj/tests/unit/b.o obj/tests/unit/c.o
UNIT_TESTOBJS := $(UNIT_TESTSRC:%.c=$(OBJDIR)/%.o)

# ---- Symbols to build test-code sample programs
# -- Pick-up both C and C++ sources (Support both *.cpp and *.cc for C++).
TEST_CODE_SRC := $(shell find $(TEST_CODE) -type f \( -name *.c -o -name *.cpp -o -name *.cc \) -print)

# -- Sequentially replace src-file extension to generate list of .o's
TEST_CODE_OBJS := $(TEST_CODE_SRC:%.cc=$(OBJDIR)/%.o)
TEST_CODE_OBJS := $(TEST_CODE_OBJS:%.cpp=$(OBJDIR)/%.o)
TEST_CODE_OBJS := $(TEST_CODE_OBJS:%.c=$(OBJDIR)/%.o)

# Grab the "main.c" for each test-code sample program, which will be used
# to construct the list of test-code binaries.
TEST_CODE_BIN_SRC=$(filter %-main.c %-main.cpp %-main.cc, $(TEST_CODE_SRC))

# ----------------------------------------------------------------------------
# Generate location / name of test-code sample program binary, using built-in
# substitution references. test-code/ has sources like:
#
#   test-code/single-file-program/single-file-main.c
#   test-code/two-files-program/two-files-main.c
#
# Convert this list of *main.c to generate test-code program binary names,
# using the src-dir's name as the program name:
#   build/release/bin/test-code/single-file-program
#   build/release/bin/test-code/two-files-program
#
TEST_CODE_BINS_TMP := $(TEST_CODE_BIN_SRC:$(TEST_CODE)/%-main.c=$(BINDIR)/$(TEST_CODE)/%-program)
TEST_CODE_BINS_TMP := $(TEST_CODE_BINS_TMP:$(TEST_CODE)/%-main.cpp=$(BINDIR)/$(TEST_CODE)/%-program)
TEST_CODE_BINS_TMP := $(TEST_CODE_BINS_TMP:$(TEST_CODE)/%-main.cc=$(BINDIR)/$(TEST_CODE)/%-program)
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
	find ./tests ./test-code \( -name "*loc*.c" -o -name "loc*.h" \)  -exec rm -rf {} \;

####################################################################
# The main targets
#
all-tests: $(BINDIR)/unit_test
all-test-code: $(TEST_CODE_BINS)
all: all-tests all-test-code

# ###################################################################
# CFLAGS, LDFLAGS, ETC
#
# -----------------------------------------------------------------------------
# Define CFLAGS to generate the -D clause to define LOC_FILE_INDEX
# using the source file name as input:
#  - Replace "-" in filename with "_"
#  - Replace "." with "_" (*.c -> *_c, *.cpp -> *_cpp, *.cc -> *_cc)
# -----------------------------------------------------------------------------
ifeq ($(LOC_GENERATE), $(LOC_DEFAULT))
    CFLAGS += -DLOC_FILE_INDEX=LOC_$(subst .,_,$(subst -,_,$(notdir $<)))
endif

# -----------------------------------------------------------------------------
# Define the include files' dir-path. All unit-tests need to include ctest.h,
# which lives in top-level unit-tests dir.
# The LOC-generated .h files will appear in each test-code program's src-dir.
# Use this recursively defined variables to build the path to pick-up both
# forms of #include .h files.
# -----------------------------------------------------------------------------
INCLUDE := -I ./$(UNIT_INCDIR)
INCLUDE += -I ./$(dir $<)
INCLUDE += -I ./$(INCDIR)

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
$(BINDIR)/unit_test: $(UNIT_TESTOBJS)

# ###################################################################
# The dependencies for each test-code sample program
# Every example program of the form bin/test-code/<eg-prog> depends on
# obj/test-code/<eg-prog>/*.o -> *.c
# There can be more than one .o's linked to create test-code example
# program.

# -----------------------------------------------------------------------------
SINGLE_FILE_PROGRAM_TESTSRC := $(SINGLE_FILE_PROGRAM_GENSRC)
SINGLE_FILE_PROGRAM_TESTSRC += $(shell find $(TEST_CODE)/single-file-program -type f -name *.c -print)

SINGLE_FILE_PROGRAM_OBJS := $(SINGLE_FILE_PROGRAM_TESTSRC:%.c=$(OBJDIR)/%.o)

$(BINDIR)/$(TEST_CODE)/single-file-program: $(SINGLE_FILE_PROGRAM_OBJS)

# -----------------------------------------------------------------------------
TWO_FILES_PROGRAM_TESTSRC := $(shell find $(TEST_CODE)/two-files-program -type f -name *.c -print)
TWO_FILES_PROGRAM_TESTSRC += $(TWO_FILES_PROGRAM_GENSRC)

TWO_FILES_PROGRAM_OBJS := $(TWO_FILES_PROGRAM_TESTSRC:%.c=$(OBJDIR)/%.o)

$(BINDIR)/$(TEST_CODE)/two-files-program: $(TWO_FILES_PROGRAM_OBJS)
$(BINDIR)/$(TEST_CODE)/single-file-program: $(OBJDIR)/$(TEST_CODE)/single-file-program/single-file-main.o

$(BINDIR)/$(TEST_CODE)/two-files-program: $(OBJDIR)/$(TEST_CODE)/two-files-program/two-files-main.o \
                                          $(OBJDIR)/$(TEST_CODE)/two-files-program/two-files-file1.o

# -----------------------------------------------------------------------------
SINGLE_FILE_CPP_PROGRAM_TESTSRC := $(SINGLE_FILE_CPP_PROGRAM_GENSRC)
SINGLE_FILE_CPP_PROGRAM_TESTSRC += $(shell find $(TEST_CODE)/single-file-cpp-program -type f -name *.cpp -print)

SINGLE_FILE_CPP_PROGRAM_TMP  := $(SINGLE_FILE_CPP_PROGRAM_TESTSRC:%.cpp=$(OBJDIR)/%.o)
SINGLE_FILE_CPP_PROGRAM_OBJS := $(SINGLE_FILE_CPP_PROGRAM_TMP:%.c=$(OBJDIR)/%.o)
$(BINDIR)/$(TEST_CODE)/single-file-cpp-program: $(SINGLE_FILE_CPP_PROGRAM_OBJS)

# -----------------------------------------------------------------------------
SINGLE_FILE_CC_PROGRAM_TESTSRC := $(SINGLE_FILE_CC_PROGRAM_GENSRC)
SINGLE_FILE_CC_PROGRAM_TESTSRC += $(shell find $(TEST_CODE)/single-file-cc-program -type f -name *.cc -print)

SINGLE_FILE_CC_PROGRAM_TMP  := $(SINGLE_FILE_CC_PROGRAM_TESTSRC:%.cc=$(OBJDIR)/%.o)
SINGLE_FILE_CC_PROGRAM_OBJS := $(SINGLE_FILE_CC_PROGRAM_TMP:%.c=$(OBJDIR)/%.o)
$(BINDIR)/$(TEST_CODE)/single-file-cc-program: $(SINGLE_FILE_CC_PROGRAM_OBJS)

# -----------------------------------------------------------------------------
# FIXME: This program needs C++20 support, so currently it's not being built.
SOURCE_LOCATION_CPP_PROGRAM_TESTSRC := $(shell find $(TEST_CODE)/source-location-cpp-program -type f -name *.cpp -print)
SOURCE_LOCATION_CPP_PROGRAM_OBJS := $(SOURCE_LOCATION_CPP_PROGRAM_TESTSRC:%.cpp=$(OBJDIR)/%.o)
$(BINDIR)/$(TEST_CODE)/source-location-cpp-program: $(SOURCE_LOCATION_CPP_PROGRAM_OBJS)

# ###################################################################
# RECIPES:

# For all-test-code, we need to use -I test-code/<subdir>
# Dependencies for the main executables
COMPILE.c   = $(CC) $(CFLAGS) $(INCLUDE) -c
COMPILE.cpp = $(CXX) $(CFLAGS) $(INCLUDE) -c
COMPILE.cc  = $(CXX) $(CFLAGS) $(INCLUDE) -c

# Compile each .c file into its .o
# Also define a dependency on the dir in which .o will be produced (@D).
# The secondary expansion will invoke mkdir to create output dirs first.
$(OBJDIR)/%.o: %.c | $$(@D)/.
	$(BRIEF_FORMATTED) "%-20s %-50s [%s]\n" Compiling $< $@
	$(COMMAND) $(COMPILE.c) $< -o $@
	$(PROLIX) # blank line

$(OBJDIR)/%.o: %.cpp | $$(@D)/.
	$(BRIEF_FORMATTED) "%-20s %-50s [%s]\n" Compiling $< $@
	$(COMMAND) $(COMPILE.cpp) $< -o $@
	$(PROLIX) # blank line

$(OBJDIR)/%.o: %.cc | $$(@D)/.
	$(BRIEF_FORMATTED) "%-20s %-50s [%s]\n" Compiling $< $@
	$(COMMAND) $(COMPILE.cc) $< -o $@
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

ifeq "$(BUILD_VERBOSE)" "1"
	@echo
	$(info $$TEST_CODE_SRC     = [${TEST_CODE_SRC}])
	$(info $$TEST_CODE_OBJS    = [${TEST_CODE_OBJS}])
	$(info $$TEST_CODE_BIN_SRC = [${TEST_CODE_BIN_SRC}])
	$(info $$TEST_CODE_BINS    = [${TEST_CODE_BINS}])
	$(info $$UNIT_TESTSRC      = [${UNIT_TESTSRC}])
	$(info $$GENERATED_OBJS    = [${GENERATED_OBJS}])
	$(info $$UNIT_TESTOBJS     = [${UNIT_TESTOBJS}])
endif

# ###################################################################
# Testing
#

.PHONY: install

# Run the unit-test binary and run individual sample example program binaries.
run-tests: run-unit-tests run-test-code

run-unit-tests: all-tests
	@echo
	@echo "**** Run unit-tests ****"
	$(BINDIR)/unit_test

run-test-code: all-test-code
	@echo
	@echo "**** Run sample test-code programs ****"
	for i in $(TEST_CODE_BINS); do echo " "; echo "-- Executing $$i";$$i || exit;  done
