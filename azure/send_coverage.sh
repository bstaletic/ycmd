# Exit immediately if a command returns a non-zero status.
set -e

if [[ "$YCM_USE_PYENV" -eq 1 ]]; then
  eval "$(pyenv init -)"
  pyenv global ${YCM_PYTHON_VERSION}
fi

python -m codecov --name "${CODECOV_JOB_NAME}"

set +e
