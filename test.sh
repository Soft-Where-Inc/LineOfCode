#!/bin/bash
# ##############################################################################
# test.sh - Driver script to invoke LOC test suites.
# ##############################################################################

Me=$(basename "$0")
set -euo pipefail

pushd "$(dirname "$0")" > /dev/null 2>&1
# shellcheck disable=SC2046
CurrDir="$(pwd)"
popd > /dev/null 2>&1

# Location of binaries, which live under $BUILD_ROOT, if set.
Build_dir="${BUILD_ROOT:-build}"
Build_mode="${BUILD_MODE:-release}"
Bindir="${BINDIR:-${Build_dir}/${Build_mode}/bin}"
Unit_test="${Bindir}/unit_test"

# ##################################################################
# Print help / usage
# ##################################################################
function usage() {

   echo "Usage: $Me [--help | --list] | [ < test-name > ]"
   echo "To run quick smoke tests         : ./${Me}"
}

# ##################################################################
function run_pytests() {
    set -x
    pushd "${CurrDir}"/tests > /dev/null 2>&1

    pytest -v

    popd > /dev/null 2>&1
    set +x
}

# ##################################################################
function run_unit_tests() {
    set -x
    ${Unit_test}
    set +x
}

# List of functions each driving one kind of test.
Tests=( "run_pytests"
        "run_unit_tests"
      )

# ##################################################################
# List the set of tests that can be run.
function list_tests() {
    echo "${Me}: List of tests that can be run:"
    list_items_in_array "${Tests[@]}"
}

# --------------------------------------------------------------------------
# Minion to print the contents of a step-array passed-in.
# Ref: https://askubuntu.com/questions/674333/how-to-pass-an-array-as-function-argument
function list_items_in_array() {
    local tests_array=("$@")
    for str in "${tests_array[@]}"; do
        echo "  ${str}"
    done
}

# ##################################################################
# main() begins here
# ##################################################################

if [ $# -eq 1 ]; then
    if [ "$1" == "--help" ]; then
        usage
        exit 0
    fi

    if [ "$1" == "--list" ]; then
        list_tests
        exit 0
    fi

    # Run the only arg provided, expecting it to be a valid test-fn-name
    $1
    exit 0
fi


echo "$Me: $(TZ="America/Los_Angeles" date) Start LOC Test Suite Execution."
run_pytests
echo "$Me: $(TZ="America/Los_Angeles" date) LOC Test Suite Execution completed."
