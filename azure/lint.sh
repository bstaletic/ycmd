# Exit immediately if a command returns a non-zero status.
set -e
sudo apt-get update
sudo apt-get install libsqlite3-dev
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
pip install pytest
python run_tests.py --valgrind

set +e
