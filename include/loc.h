/**
 * ****************************************************************************
 * loc.h : Definitions to generate code-location. Works on Linux & MacOSX.
 * SPDX-License-Identifier: Apache-2.0
 * Copyright (c) 2024 Aditya P. Gurajada
 *
 * History:
 *  3/2024  - Original version provided by Charles Baylis
 *            Modified to fit into LineOfCode's framework of usage.
 * ****************************************************************************
 */
#ifndef __LOC_H__
#define __LOC_H__

#include <stdint.h>

/*
 * NOTE: We use the offset into a named-section in the program's data region
 * as the LOC-ID's offset. This value can be negative, so we cannot define
 * this as uint32_t. (This is, also, convenient for us. If the user #includes
 * this loc.h and the generated loc.h in some sources, the compiler will report
 * a typedef clash. That provides a small alert to the user that something is
 * amiss in their build make-rules.)
 */
typedef int32_t loc_t;

/* Struct describing a source location */
typedef struct location
{
    const char *const func;
    const char *const file;
    const uint32_t    line;
    const uint32_t    spare;    // Compiler pad-bytes
} LOC;

/**
 * A dummy location ID used as reference point within the loc_ids section.
 * All location ids are stored as an offset from this variable.
 */
extern LOC Loc_id_ref;

/**
 * CREATE_LOCID() - Helper macro for generating the code-location ID.
 *
 * This causes the compiler to create an instance of LOC{} describing
 * a function, filename, and line number and returns the offset from the
 * Loc_id_ref pointer.
 */
#if __APPLE__
#define CREATE_LOCID(func, file, line)                                      \
  ({                                                                        \
    static LOC cur_loc                                                      \
        __attribute__((section("__DATA, loc_ids"))) = {func, file, line};   \
   ((intptr_t)&cur_loc - (intptr_t)&Loc_id_ref);                            \
  })
#else   // __APPLE__
#define CREATE_LOCID(func, file, line)                                      \
  ({                                                                        \
    static LOC cur_loc                                                      \
        __attribute__((section("loc_ids"))) = {func, file, line};           \
   ((intptr_t)&cur_loc - (intptr_t)&Loc_id_ref);                            \
  })
#endif  // __APPLE__

/* Generate a 4-byte ID capturing the source location where this macro is used */
#define __LOC__ CREATE_LOCID(__FUNCTION__, __FILE__, __LINE__)

/**
 * Lookup methods to extract code-location details given a LOC-ID.
 */
static inline uint32_t
LOC_LINE(loc_t loc)
{
    LOC *locp = (LOC *)( ((intptr_t) &Loc_id_ref) + (loc));
    return locp->line;
}

static inline const char * const
LOC_FILE(loc_t loc)
{
    LOC *locp = (LOC *)( ((intptr_t) &Loc_id_ref) + (loc));
    return locp->file;
}

static inline const char * const
LOC_FUNC(loc_t loc)
{
    LOC *locp = (LOC *)( ((intptr_t) &Loc_id_ref) + (loc));
    return locp->func;
}

/* Print the location described by a location id created by __LOC__ */
void loc_print(loc_t id);

#endif  // __LOC_H__
