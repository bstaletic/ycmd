# Exit immediately if a command returns a non-zero status.
set -e

python build.py --clang-completer
pip install -r test_requirements.txt
pip install bottle waitress requests watchdog regex jedi
PYTHONMALLOC=malloc LD_PRELOAD=third_party/clang/lib/libclang.so.10 valgrind --leak-check=full --show-leak-kinds=definite python -m pytest ycmd/tests/clang/get_completions_test.py
touch x.cpp
cd third_party/clang/lib
ln -s libclang.so.10 libclang.so
cd -
gcc xxx.c -isystem cpp/llvm/include -L third_party/clang/lib -l clang
LD_PRELOAD=third_party/clang/lib/libclang.so.10 valgrind --leak-check=full --show-leak-kinds=definite ./a.out

set +e
