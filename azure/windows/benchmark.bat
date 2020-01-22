:: Add Python to PATH
:: set "PATH=C:\Python;C:\Python\Scripts;%PATH%"

:: python benchmark.py

"C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\VC\Tools\MSVC\14.24.28314\bin\Hostx64\x64\cl.exe" /c /I cpp\ctre /I cpp\robin_hood /std:c++17 /DYCM_EXPORT="__declspec( dllexport )" cpp\ycm\IdentifierUtils.cpp
