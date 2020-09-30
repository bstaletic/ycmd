cd /D "C:\Program Files (x86)\Microsoft SDKs\Windows\v7.1A\Include\"
dir Windows.h
FOR /F "tokens=* delims=" %%x in (Windows.h) DO echo %%x
