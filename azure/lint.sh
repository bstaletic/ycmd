# Exit immediately if a command returns a non-zero status.
set -e

python build.py --clang-completer
touch x.cpp
cd third_party/clang/lib
ln -s libclang.so.10 libclang.so
cd -
ls -l third_party/clang/lib
gcc xxx.c -isystem cpp/llvm/include -L third_party/clang/lib -l clang
LD_PRELOAD=third_party/clang/lib/libclang.so.10 valgrind --leak-check=full --show-leak-kinds=definite ./a.out

set +e
