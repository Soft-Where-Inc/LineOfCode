# LOC - Line Of Code, aka Code Location

Frequently for instrumentation, tracing and diagnostics, one needs to track the code-location of where certain things occur. An example is to track the 
place where memory allocation is done, or some other resource such as a lock request is obtained. 

Classical techniques to track file-name / line-number pair usually require a `const char * file` pointer for the `__FILE__` macro, consuming 
8-bytes and a 4-byte line number, given by the `__LINE__` macro. Passing this around on the stack requires at least 12 bytes. 
If you wish to store this pair in some common (diagnostic) structure, you will further need to allocate space for the file-name itself. 
Storing, say, a minimum of 8-characters for a file name plus line-number requires 12 bytes, which can be reduced to, say, 10 bytes by storing the
line number as `uint16_t`. It is not uncommon to save-off 12 to 14 chars of file-name, plus 4 to 2 bytes, respectively, of line-number, requiring a total
of 16 bytes.

LOC is a technique to encode the line-of-code, i.e. the file name and line number pair, as a small 4-byte integer. This encoded integer can then be stored
in your core structures, passed-around the stack, and generally manipulated as an opaque integer. (Line-of-code is also referred to as the code-location
or call-site.)

LOC encoding is an extremely compact way of storing in a 4-byte integer what you would normally use in C/C++, such as `__FILE__` and `__LINE__` macros, 
requiring 12, 16 or more bytes needed with conventional approaches.

This repository contains a Python script which generates core interface `.h` files and basic `.c` files that you can then integrate with your C/C++
code-base.

The generated LOC header files provide encoding macros to generate the 4-byte encoded line-of-code (i.e, code-location) and decoding macros to unpack the
encoded integer value into its consitituent file-name and line-number.

Sample changes to `Makefile` are provided to show how to integrate the generated files into any typical C/C++ code base. Example programs are provided 
to demonstrate how to use this LOC encoding to drive diagnostcs & instrumentation with very little overhead of space consumed at run-time.
