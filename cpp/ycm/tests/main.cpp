#include "gtest/gtest.h"
#include "gmock/gmock.h"
#include <pybind11/embed.h>

int main( int argc, char **argv ) {
  pybind11::scoped_interpreter guard{};

  testing::InitGoogleMock( &argc, argv );
  return RUN_ALL_TESTS();
}

