@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Tat he thong - Cong bao cao su co moi truong
echo Tat web: dong cua so "Cong bao cao su co moi truong - dang chay" ^(hoac bam Ctrl+C trong cua so do^).
echo Dang tat Jaeger ^(container Docker^)...
docker compose down 2>nul
echo Da tat. Du lieu nam tren SQL Server cua may, van giu nguyen.
pause
