# Exit immediately if a command returns a non-zero status.
set -e

bash <(curl -s https://codecov.io/bash)

set +e
