@echo off
chcp 65001 >nul
set PY=C:\Users\时雨时衣\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe
set TOOL=F:\GoHModManager\tools

if "%~1"=="" (
    echo 用法:
    echo   gohmod units ^<阵营^> ^<时期^>      导出单位表
    echo   gohmod check ^<目录^>               检查脚本
    echo   gohmod pack ^<目录^> ^<输出.pak^>    打包
    echo   gohmod unpack ^<pak^> ^<目录^>       解包
    echo   gohmod inject ^<地图目录^> ^<include^> ^<输出^>
    echo   gohmod icon ^<图标名^> ^<输出.png^>  提取单位图标
    echo   gohmod lint ^<mod目录^>             深度检查
    exit /b 0
)

if /i "%~1"=="lint" (
    "%PY%" "%TOOL%\gohlint.py" %2
) else if /i "%~1"=="icon" (
    "%PY%" "%TOOL%\gohmod.py" tga2png "%~2" "%~3"
) else (
    "%PY%" "%TOOL%\gohmod.py" %1 %2 %3 %4
)
