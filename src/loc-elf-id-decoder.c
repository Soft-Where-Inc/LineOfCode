/**
 * Sample program to read the ELF-sections info and dump it out.
 *
 * Setup:
 *  $ sudo apt search libelf-dev
 *  $ sudo apt-get install -y libelf-dev/jammy
 *
 * Usage: $ gcc -o locations_dump locations_dump.c -lelf
 *   Run: $ ./locations_dump ./locations_dump
 *        $ ./locations_dump ./locations_example
 *
 * Note: The final output that is displayed after some parsing by
 * dump_loc_ids() is also obtained by:
 *
 *  $ readelf -x .rodata ./locations_example
 *  $ readelf -p .rodata ./locations_example
 *
 * References:
 *
 *  [1] Tutorial: libelf by Example, Joseph Koshy, March, 2012
 *      https://phoenixnap.dl.sourceforge.net/project/elftoolchain/Documentation/libelf-by-example/20200330/libelf-by-example.pdf
 *
 *  [2] Soft-copy of same on my Mac:
 *      ~/Work/Docs/Elf-Tutorial-Ref-libelf-by-example-2012.pdf
 *
 * History:
 *  3/2024  - Restarted; to get something working on Linux-VM
 */
#include <stdio.h>
#include <stdint.h>     // uint32_t etc.
#include <stdlib.h>     // exit(), EXIT_FAILURE etc.
#include <fcntl.h>      // For file open() etc.
#include <unistd.h>     // For file read(), close() etc.
#include <string.h>     // For strncmp() etc.
#include <stdbool.h>    // For _Bool
#include <getopt.h>     // For getopt_long()
#include <libelf.h>     // For ELF apis: elf_begin(), elf_kind() etc.
#include <gelf.h>       // For ELF apis: GElf_Shdr{}, gelf_getshdr() etc.

// Define the struct location
struct location
{
    const char *const   fn;
    const char *const   file;
    const uint32_t      line;
    const uint32_t      spare;      // Compiler pad-bytes
    const uint64_t      spare2;     // Compiler pad-bytes
};

/* Is 'str2' equal to null-terminated string 'str1'? */
#define STR_EQ(str1, str2)  (strncmp(str1, str2, strlen(str1)) == 0)

#define REQD_SECTION_NAME       "loc_ids"
#define RODATA_SECTION_NAME     ".rodata"
#define DATA_SECTION_NAME       ".data"

// Section-name matching macros
#define IS_REQD_SECTION(name)       STR_EQ(REQD_SECTION_NAME, (name))
#define IS_RODATA_SECTION(name)     STR_EQ(RODATA_SECTION_NAME, (name))

// Tracing macros

#define STRINGIFY(x)       #x
#define STRINGIFY_VALUE(s) STRINGIFY(s)

// Fabricate a string to track code-location of call-site.
#define __LOC__     "[" __FILE__ ":" STRINGIFY_VALUE(__LINE__) "]"

/**
 * Simple argument parsing structure.
 */
struct option Long_options[] = {
    // { "brief"   , required_argument , NULL, 'f'},
      { "program-binary", required_argument   , NULL, 'p'}
    , { "brief"         , no_argument         , NULL, 'b'}
    , { "dump-rodata"   , no_argument         , NULL, 'r'}
    , { "dump-loc-ids"  , no_argument         , NULL, 'l'}
    , { "debug"         , no_argument         , NULL, 'd'}
    , { "help"          , no_argument         , NULL, 'h'}
    , { NULL, 0, NULL, 0} // End of options
};

const char * Options_str = "p:bldh";

typedef struct args {
    const char *    binary;
    _Bool           brief;
    _Bool           dump_rodata;
    _Bool           dump_loc_ids;
    _Bool           debug;
} ArgStruct;

ArgStruct Args = {0};

// Function prototypes
int parse_arguments(const int argc, char *argv[], ArgStruct *args);

void print_usage(const char *program, struct option options[]);

_Bool print_this_section(const char *name);

void dump_loc_ids(_Bool dump_loc_ids, struct location *loc_id_ref,
                  uint32_t count, const char *rodata_buf,
                  const size_t rodata_addr, uint64_t sh_addr);

void prGElf_Shdr(const GElf_Shdr *shdr, Elf_Scn *scn, const char *name);

void prSection_details(const char *name, Elf_Scn *scn, GElf_Shdr *shdr);

void readSection_data(char *buffer, Elf_Scn *scn, GElf_Shdr *shdr);

void hexdump(const void* data, size_t size, size_t sh_addr);

/**
 * *****************************************************************************
 * main() begins here.
 * *****************************************************************************
 */
int
main(const int argc, char *argv[])
{
    ArgStruct *args = &Args;
    int rv = parse_arguments(argc, argv, args);
    if (rv) {
        return EXIT_FAILURE;
    }

    if (Args.binary == NULL) {
        fprintf(stderr, "Option --program-binary is required.\n");
        print_usage((const char *) argv[0], Long_options);
        return EXIT_FAILURE;
    }

    // Initialize libelf
    if (elf_version(EV_CURRENT) == EV_NONE) {
        fprintf(stderr, "Failed to initialize libelf\n");
        return EXIT_FAILURE;
    }

    // Open the binary file
    int fd;
    if ((fd = open(args->binary, O_RDONLY, 0)) < 0) {
        perror("open");
        return EXIT_FAILURE;
    }

    // Open the ELF file
    Elf *elf = NULL;
    if ((elf = elf_begin(fd, ELF_C_READ, NULL)) == NULL) {
        fprintf(stderr, "Failed to open ELF file: %s\n", elf_errmsg(-1));
        close(fd);
        return EXIT_FAILURE;
    }

    if (elf_kind(elf) != ELF_K_ELF) {
        fprintf(stderr, "'%s' is not an ELF object.\n", args->binary);
        return EXIT_FAILURE;
    }

    // Retrieve the section-index of the ELF section containing the string
    // table of section names.
    size_t shstrndx = 0;
    if (elf_getshdrstrndx (elf, &shstrndx ) != 0) {
        fprintf(stderr, "elf_getshdrstrndx() failed: %s.", elf_errmsg(-1));
        return EXIT_FAILURE;
    }
    if (args->debug) {
        printf("%s: shstrndx=%lu\n", __LOC__, shstrndx);
    }

    // Scan all ELF-sections and print brief info about each.
    GElf_Shdr shdr;
    Elf_Scn *scn = NULL;
    char *rodata_buf = NULL;
    struct location *loc_ids = NULL;
    size_t rodata_addr = 0;
    char *name = NULL;
    while ((scn = elf_nextscn(elf, scn)) != NULL) {

        // Get ELF section's header.
        if (gelf_getshdr(scn, &shdr) != &shdr) {
            fprintf(stderr, "getshdr() failed: %s.\n", elf_errmsg(-1));
            return EXIT_FAILURE;
        }
        if ((name = elf_strptr(elf, shstrndx, shdr.sh_name)) == NULL ) {

            fprintf(stderr, "elf_strptr() failed: %s.\n", elf_errmsg(-1));
            return EXIT_FAILURE;
        }

        // Save-off .rodata section's contents, so we can parse through it
        // to extract file/function-names.
        if (IS_RODATA_SECTION(name)) {
            rodata_buf = (char *)malloc(shdr.sh_size);
            readSection_data(rodata_buf, scn, &shdr);
            rodata_addr = shdr.sh_addr;

            if (args->dump_rodata) {
                prGElf_Shdr(&shdr, scn, name);
                hexdump(rodata_buf, shdr.sh_size, rodata_addr);
            }
        } else if (IS_REQD_SECTION(name)) {

            uint32_t nloc_id_entries = 0;
            // Account for alignment bytes left in GElf_Shdr
            nloc_id_entries = ((shdr.sh_size - shdr.sh_addralign)
                                    / sizeof(struct location));

            loc_ids = (struct location *) malloc((nloc_id_entries + 1)
                                                    * sizeof(*loc_ids));
            readSection_data((char *) loc_ids, scn, &shdr);

            if (args->dump_loc_ids) {
                prGElf_Shdr(&shdr, scn, name);
                printf("Section %s expected to have %d entries.\n",
                       name, nloc_id_entries);

                hexdump(&loc_ids, shdr.sh_size, 0);

            }
            if (args->dump_loc_ids || args->brief) {
                dump_loc_ids(args->dump_loc_ids,
                             &loc_ids[0], nloc_id_entries,
                             rodata_buf, rodata_addr, shdr.sh_addr);
            }
        }
    }

    // Cleanup.
    if (loc_ids) {
        free(loc_ids);
    }
    if (rodata_buf) {
        free(rodata_buf);
    }
    elf_end(elf);
    close(fd);
    return 0;
}

/**
 * Helper methods
 */

/**
 * Simple argument parsing support.
 */
int
parse_arguments(const int argc, char *argv[], ArgStruct *args)
{
    int option_index = 0;
    int opt;

    while ((opt = getopt_long(argc, argv, Options_str,  Long_options, &option_index))
                != -1) {
        switch (opt) {
            case 'h':
                print_usage((const char *) argv[0], Long_options);
                exit(EXIT_SUCCESS);

            case ':':
                printf("%s: Option '%c' requires an argument\n",
                       argv[0], optopt);
                return EXIT_FAILURE;

            case 'p':
                args->binary = optarg;
                break;

            case 'b':
                args->brief = true;
                break;

            case 'r':
                args->dump_rodata = true;
                break;

            case 'l':
                args->dump_loc_ids = true;
                break;

            case 'd':
                args->debug = true;
                break;

            case '?': // Invalid option or missing argument
                printf("%s: Invalid option '%c' or missing argument\n",
                       argv[0], opt);
                return EXIT_FAILURE;

            default:
                // Handle error
                return EXIT_FAILURE;
        }
    }
    return 0;
}

void
print_usage(const char *program_name, struct option options[])
{
    printf("Usage: %s [options] "
           "{-p | --program-binary} <program-binary> [ <loc-IDs>+ ]\n",
           program_name);
    printf("Options:\n");

    for (int i = 0; options[i].name != NULL; i++) {
        if (options[i].val != 0) {
            printf("  -%c, --%s", options[i].val, options[i].name);
        } else {
            printf("      --%s", options[i].name);
        }

        if (options[i].has_arg == required_argument) {
            printf(" <%s>", options[i].name);
        } else if (options[i].has_arg == optional_argument) {
            printf(" [<%s>]", options[i].name);
        }

        printf("\n");
    }
}

_Bool
print_this_section(const char *name)
{
    bool rv = (IS_REQD_SECTION(name) || IS_RODATA_SECTION(name));
    return rv;
}

void
prGElf_Shdr(const GElf_Shdr *shdr, Elf_Scn *scn, const char *name)
{
    printf("\nSection %-4.4ld, sh_addr=0x%lx sh_size=%lu, sh_addralign=%lu"
            ", sh_entsize=%lu: %s\n",
            (uintmax_t) elf_ndxscn(scn),
            shdr->sh_addr, shdr->sh_size, shdr->sh_addralign,
            shdr->sh_entsize,
            name);
}

/**
 * prSection_details() - Unpack entries from required named section.
 */
void
prSection_details(const char *name, Elf_Scn *scn, GElf_Shdr *shdr)
{
    if (!scn || !shdr || (shdr->sh_size == 0)) {
        fprintf(stderr, "%s: Illegal inputs: scn=%p, shdr=%p, sh_size=%lu",
                __LOC__, scn, shdr,
                (shdr ? shdr->sh_size : -1));
        return;
    }
    printf("\n%s: Unpacking %lu bytes of contents from '%s' section: \n",
            __LOC__, shdr->sh_size, name);

    int nloc_id_entries = 0;
    _Bool found_reqd_section = false;
    if (strncmp(name, REQD_SECTION_NAME, strlen(REQD_SECTION_NAME)) == 0) {

        // Account for alignment bytes left in GElf_Shdr
        nloc_id_entries = ((shdr->sh_size - shdr->sh_addralign) / sizeof(struct location));
        printf("Section %s expected to have %d entries.\n", name, nloc_id_entries);
        found_reqd_section = true;
    }

    char buffer[shdr->sh_size];
    readSection_data(buffer, scn, shdr);

    hexdump(buffer, sizeof(buffer), shdr->sh_addr);
    if (found_reqd_section) {
        struct location loc_ids[nloc_id_entries + 1];
        memmove(&loc_ids, buffer, shdr->sh_size);
        dump_loc_ids(true, &loc_ids[0], nloc_id_entries, (char *) NULL, 0, 0);
    }
    printf("\n");
}


/**
 * readSection_data(): Read section's data into output 'buffer'
 */
void
readSection_data(char *buffer, Elf_Scn *scn, GElf_Shdr *shdr)
{
    if (!buffer || !scn || !shdr || (shdr->sh_size == 0)) {
        fprintf(stderr, "%s: Illegal inputs: "
                "buffer=%p, scn=%p, shdr=%p, sh_size=%lu",
                __LOC__, buffer, scn, shdr,
                (shdr ? shdr->sh_size : -1));
        return;
    }
    char *outp = buffer;
    Elf_Data *data = NULL;
    size_t n = 0;
    while ((n < shdr->sh_size) && (data = elf_getdata(scn, data)) != NULL) {
        memmove(outp, data->d_buf, data->d_size);
        outp += data->d_size;
    }
}

/* Specifiers related to hexdump() print utility */
#define HEXD_NBYTES_PER_LINE    16      // Keep this an even number
#define HEXD_NHALF_BYTES        (HEXD_NBYTES_PER_LINE / 2)

/**
 * hexdump(): Cp'ed from DumpHex() Ref: https://gist.github.com/ccbrown/9722406
 *
 * Enhanced from original version for improved diagnostics.
 *
 * In many cases, caller is likely dumping contents of some memory region
 * after copying it over to some allocated buffer 'data'. To help the user
 * navigate the byte-stream, allow 'sh_addr' to be supplied, which will be
 * the start address of the source buffer. If that's supplied, print the
 * byte-offsets for each chunk of bytes on each line.
 */
void hexdump(const void* data, size_t size, size_t sh_addr) {
    char ascii[HEXD_NBYTES_PER_LINE + 1] = { '\0' };
    size_t i;
    size_t j;
    for (i = 0; i < size; ++i) {
        if ((i % HEXD_NBYTES_PER_LINE) == 0) {
            if (sh_addr) {
                printf("%p 0x%4lx [%4ld]: ", (data + i), (sh_addr + i), i);
            } else {
                printf("%p [%4ld]: ", (data + i), i);
            }
        }
        unsigned char u_curr = ((unsigned char *)data)[i];
        printf("%02x ", u_curr);
        if ((u_curr >= ' ') && (u_curr <= '~')) {
            ascii[i % HEXD_NBYTES_PER_LINE] = u_curr;
        } else {
            ascii[i % HEXD_NBYTES_PER_LINE] = '.';
        }

        size_t inext = i + 1;
        if ((inext % HEXD_NHALF_BYTES) == 0 || (inext == size)) {
            printf(" ");
            if ((inext % HEXD_NBYTES_PER_LINE) == 0) {
                printf("|  %s \n", ascii);
            } else if (inext == size) {
                ascii[inext % HEXD_NBYTES_PER_LINE] = '\0';
                if ((inext % HEXD_NBYTES_PER_LINE) <= HEXD_NHALF_BYTES) {
                    printf(" ");
                }
                for (j = (inext % HEXD_NBYTES_PER_LINE);
                     j < HEXD_NBYTES_PER_LINE; ++j) {
                    printf("   ");
                }
                printf("|  %s \n", ascii);
            }
        }
    }
}

/**
 * *****************************************************************************
 * dump_loc_ids(): Dump the contents of the loc_ids section
 *
 * Parameters:
 *  dump_loc_ids- Boolean; True => print verbose dump. False => --brief output
 *  loc_id_ref  - Array of struct location{} entries
 *  count       - Number of entries in above array.
 *  rodata_buf  - Buffer holding '.rodata' section's data
 *  rodata_addr - Start address (i.e. GElf_Shdr->sh_addr) of .rodata section
 *  sh_addr     - GElf_Shdr.sh_addr value for this `loc_ids` section.
 *                This address gives start of this section.
 *
 * NOTE: {rodata_buf, rodata_addr} are optional, and can be {NULL,0}
 * When provided, this routine unpacks the loc_id_ref->fn and loc_id_ref->file
 * values as offsets into .rodata buffers to extract the function / file name.
 *
 * The way this works is as follows:
 *
 *             rodata_addr   func_offset (start of function-name)
 *               │           │
 *               ▼           ▼
 *  rodata_buf ->┌──────────────────────────────────────┐
 *               │                                      │
 *               └───────────────────────▲──────────────┘
 *                                       │
 *                                       file_offset (start of file-name)
 *
 * Empirically, it appears that &Loc_id_ref will be higher than the struct location{}
 * of each such location stashed in this section.
 * *****************************************************************************
 */
void
dump_loc_ids(_Bool dump_loc_ids, struct location *loc_id_ref, uint32_t count,
             const char *rodata_buf, const size_t rodata_addr,
             uint64_t sh_addr)
{
    _Bool extract_data = ((rodata_buf != NULL) && (rodata_addr > 0));
    if (dump_loc_ids) {
        printf("\n%s: Dump %u location-IDs to stdout\n", __LOC__, count);
        printf("Index\t\tFunction\tFile\t\tLine\n");
    }

    for (size_t i = 0; i < count; ++i) {
        size_t func_offset = (intptr_t) loc_id_ref[i].fn;
        size_t file_offset = (intptr_t) loc_id_ref[i].file;

        if (dump_loc_ids) {
            printf("%zu (0x%lx) \tfn=0x%lx, \tfile=0x%lx, \tline=%u",
                    i, sh_addr,     // &loc_id_ref[i],
                    func_offset, file_offset, loc_id_ref[i].line);
        }
        if (extract_data) {
            if (dump_loc_ids) {
                printf(" fn='%s', file='%s'",
                       (rodata_buf + (func_offset - rodata_addr)),
                       (rodata_buf + (file_offset - rodata_addr)));
            } else {
                printf("%s:%d::%s()",
                       (rodata_buf + (file_offset - rodata_addr)),
                       loc_id_ref[i].line,
                       (rodata_buf + (func_offset - rodata_addr)));
            }
        }
        printf("\n");
        sh_addr += sizeof(*loc_id_ref);
    }
}
