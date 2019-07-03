# Exit immediately if a command returns a non-zero status.
set -e

clang++ -c cpp/ycm/CandidateRepository.cpp -DYCM_EXPORT= -isystemcpp/abseil
