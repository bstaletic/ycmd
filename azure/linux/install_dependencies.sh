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
  sudo apt-get install python python-wheel python-setuptools
else
  sudo apt-get install python3 python3-wheel python3-setuptools
  sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 100
fi

pip install -r test_requirements.txt

# Enable coverage for Python subprocesses. See:
# http://coverage.readthedocs.io/en/latest/subprocess.html
echo 'import coverage;coverage.process_startup()' | sudo tee -a `python2 -c 'import site;print(site.getsitepackages()[0])'`/sitecustomize.py 1>/dev/null

set +e
