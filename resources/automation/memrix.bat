@echo off

:: 设置路径
set EXE_PATH="%~dp0memrix.dist\memrix.exe"

:: 检查是否存在
if not exist %EXE_PATH% (
    echo WARN: not found %EXE_PATH%
    pause
    exit /b
)

:: 运行
%EXE_PATH% --help

:: 请按任意键继续
pause