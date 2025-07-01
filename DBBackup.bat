@echo off
set DB_USER=root
set DB_PASSWORD=7745
set DB_PORT=3001

if "%1"=="simon" (
    set BACKUP_DIR=D:\My Documents\OneDrive\私人文档\Python Project\ETest-SQLite\DB\MySQL_Backup
) else if "%1"=="cnaf" (
        set BACKUP_DIR=D:\Another\Path\MySQL_Backup
    ) else if "%1"=="st" (
            set BACKUP_DIR=D:\Third\Path\MySQL_Backup
        ) else (
            echo Invalid parameter. Please specify simon, cnaf, or st [must be lowercase].
            exit /b 1
        )

if exist "%BACKUP_DIR%" (
    for /f "tokens=1-4 delims=:. " %%a in ("%Date% %Time%") do (
        set DATE=%%a
        set HOUR=%%b
        set MINUTE=%%c
        set SECOND=%%d
    )
    set TIMESTAMP=%DATE:~0,4%%DATE:~5,2%%DATE:~8,2%%HOUR%%MINUTE%%SECOND%
    set BACKUP_FILE=%BACKUP_DIR%\ETest-MySQL_Backup_%TIMESTAMP%.sql

    mysqldump -u %DB_USER% -P%DB_PORT% -p%DB_PASSWORD% etest-mysql > "%BACKUP_FILE%"

    echo File: %BACKUP_FILE% Backup completed successfully.
) else (
    echo %BACKUP_DIR% is not exist. Exiting...
    exit /b 1
)
