# #############################################################################
# LOC: Line-Of-Code: Makefile: build tests, example programs, run pytests
# Developed based on SplinterDB (https://github.com/vmware/splinterdb) Makefile
# #############################################################################

.DEFAULT_GOAL := all

help::
	@echo 'Usage: make [<target>]'
	@echo 'Supported targets: clean all run-tests'

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
SRCDIR               = src
TESTSDIR             = tests
UNITDIR              = unit
UNIT_TESTSDIR        = $(TESTSDIR)/$(UNITDIR)
INCDIR               = $(UNIT_TESTSDIR)

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

# ###################################################################
# SOURCE DIRECTORIES AND FILES

# Symbol for all unit-test sources, from which we will build standalone
# unit-test binaries.
# UNIT_TESTSRC := $(call rwildcard,$(UNIT_TESTSDIR),*.c)
UNIT_TESTSRC := $(shell find $(TESTSDIR)/$(UNITDIR) -type f -name *.c -print)
$(info $$UNIT_TESTSRC is [${UNIT_TESTSRC}])

# Objects from unit-test sources in tests/unit/ sub-dir, for unit-tests
# Resolves to a list: obj/tests/unit/a.o obj/tests/unit/b.o obj/tests/unit/c.o
UNIT_TESTOBJS := $(UNIT_TESTSRC:%.c=$(OBJDIR)/%.o)
$(info $$UNIT_TESTOBJS is [${UNIT_TESTOBJS}])

####################################################################
# The main targets
#
all: all-tests
all-tests: $(BINDIR)/unit_test

# ###################################################################
# CFLAGS, LDFLAGS, ETC
#
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

$(BINDIR)/unit_test: $(UNIT_TESTOBJS)

# ###################################################################
# RECIPES:

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
$(BINDIR)/%: | $$(@D)/.
	$(BRIEF_FORMATTED) "%-20s %s\n" Linking $@
	$(COMMAND) $(LD) $(LDFLAGS) $^ -o $@ $(LIBS)
	$(PROLIX) # blank line

unit_test: $(BINDIR)/unit_test

# ###################################################################
# Report build machine details and compiler version for troubleshooting, so
# we see this output for clean builds, especially in CI-jobs.
.PHONY : clean tags
clean:
	rm -rf $(BUILD_ROOT)
	uname -a
	$(CC) --version

#*************************************************************#
# Testing
#

.PHONY: install

run-tests:
	./test.sh
