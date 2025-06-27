@echo off
set DB_USER=root
set DB_PASSWORD=7745
set DB_PORT=3001
set BACKUP_DIR=D:\MySQL_Backup
set hour=%time:~0,2%
if "%time:~0,1%"==" " set hour=0%time:~1,1%
set DATE=%Date:~0,4%%Date:~5,2%%Date:~8,2%%hour%%Time:~3,2%%Time:~6,2%
set BACKUP_FILE=%BACKUP_DIR%\ETest-MySQL_Backup_%DATE%.sql

mysqldump -u %DB_USER% -P%DB_PORT% -p%DB_PASSWORD% etest-mysql > "%BACKUP_FILE%"

echo Backup completed: %BACKUP_FILE%