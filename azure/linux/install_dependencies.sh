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

#
# Go setup
#

# Create manually the cache folder before pip does to avoid the error
#
#   failed to initialize build cache at /home/vsts/.cache/go-build: mkdir /home/vsts/.cache/go-build: permission denied
#
# while installing the Go completer.
mkdir ${HOME}/.cache

#
# Python setup
#

if [ "${YCM_PYTHON_VERSION}" == "2.7.1" ]; then
  sudo apt-get install python python-wheel
else
  sudo apt-get install python3 python3-wheel
  sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 100
fi

pip install -r test_requirements.txt

# Enable coverage for Python subprocesses. See:
# http://coverage.readthedocs.io/en/latest/subprocess.html
echo -e "import coverage\ncoverage.process_startup()" > \
${HOME}/.pyenv/versions/${YCM_PYTHON_VERSION}/lib/python${YCM_PYTHON_VERSION%.*}/site-packages/sitecustomize.py

#
# Rust setup
#

# rustup is required to enable the Rust completer on Python versions older than
# 2.7.9.
if [ "${YCM_PYTHON_VERSION}" == "2.7.1" ]; then
  curl https://sh.rustup.rs -sSf | sh -s -- -y --default-toolchain none
fi

set +e
