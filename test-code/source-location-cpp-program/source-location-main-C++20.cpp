/*
 * C++ 20 has intrinsic support for this file/line# combo through
 * source_location object.
 *
 * This sample program is copied from:
 * https://en.cppreference.com/w/cpp/utility/source_location
 *
 * NOTE: On the dev macOS machine, g++ is still at v13.xx
 *       Leave this file named w/o "-main", so that it does not
 *       get picked up by Makefile rules.
 */
#include <iostream>
#include <source_location>
#include <string_view>

void log(const std::string_view message,
         const std::source_location location =
               std::source_location::current())
{
    std::clog << "file: "
              << location.file_name() << '('
              << location.line() << ':'
              << location.column() << ") `"
              << location.function_name() << "`: "
              << message << '\n';
}

template<typename T>
void fun(T x)
{
    log(x);
}

int main(int, char*[])
{
    log("Hello world!");
    fun("Hello C++20!");
}
