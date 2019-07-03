# Exit immediately if a command returns a non-zero status.
set -e

#
# Compiler setup
#

if [ "${YCM_COMPILER}" == "clang" ]; then
  sudo apt-get install clang-3.5
  sudo update-alternatives --install /usr/bin/cc cc /usr/bin/clang-3.5 100
  sudo update-alternatives --install /usr/bin/c++ c++ /usr/bin/clang++-3.5 100
else
  sudo apt-get install gcc-4.8 g++-4.8
  sudo update-alternatives --install /usr/bin/cc cc /usr/bin/gcc-4.8 100
  sudo update-alternatives --install /usr/bin/c++ c++ /usr/bin/g++-4.8 100
fi

if [ "${YCM_CLANG_TIDY}" ]; then
  wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | sudo apt-key add -
  sudo apt-add-repository "deb http://apt.llvm.org/xenial/ llvm-toolchain-xenial-8 main"
  sudo apt-get update
  sudo apt-get install -y clang-tidy-8
  sudo update-alternatives --install /usr/bin/clang-tidy clang-tidy /usr/bin/clang-tidy-8 100
fi
