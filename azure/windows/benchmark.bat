:: Add Python to PATH
:: set "PATH=C:\Python;C:\Python\Scripts;%PATH%"

:: python benchmark.py

cl.exe /c /I cpp\ctre /I cpp\robin_hood /std:c++17 /DYCM_EXPORT="__declspec( dllexport )" cpp\ycm\IdentifierUtils.cpp
