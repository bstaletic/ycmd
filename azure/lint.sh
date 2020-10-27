# Exit immediately if a command returns a non-zero status.
set -e
sudo apt-get update
sudo apt-get install -y valgrind

test -d "$HOME/.pyenv/bin" && export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"

mkdir ${HOME}/.cache

sudo apt-get install -y build-essential \
                        libssl-dev \
                        zlib1g-dev \
                        libbz2-dev \
                        libreadline-dev \
                        libsqlite3-dev \
                        wget \
                        curl \
                        llvm \
                        libncurses5-dev \
                        libncursesw5-dev \
                        xz-utils \
                        tk-dev \
                        libffi-dev \
                        liblzma-dev \
                        python-openssl \
                        git
curl https://pyenv.run | bash
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install ${YCM_PYTHON_VERSION}
pyenv global ${YCM_PYTHON_VERSION}
gcc test.c $(python-config --cflags) $(python-config --ldflags) -lpython3.9 -o python-error
LD_LOAD_LIBRARIES=$(python-config --prefix)/lib PYTHONMALLOC=malloc valgrind ./python-error

set +e
