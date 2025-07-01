param(
    [string]$target = ""
)

switch ($target.ToLower()) {
    "simon" {
        $BACKUP_DIR = "D:\My Documents\OneDrive\私人文档\Python Project\ETest-SQLite\DB\MySQL_Backup"
    }
    "cnaf" {
        $BACKUP_DIR = "D:\Another\Path\MySQL_Backup"
    }
    "st" {
        $BACKUP_DIR = "D:\Third\Path\MySQL_Backup"
    }
    default {
        Write-Host "Invalid parameter. Please specify simon, cnaf, or st (must be lowercase)."
        exit 1
    }
}

if (Test-Path $BACKUP_DIR) {
    $TIMESTAMP = Get-Date -Format "yyyyMMddHHmmss"
    $BACKUP_FILE = "$BACKUP_DIR\ETest-MySQL_Backup_$TIMESTAMP.sql"

    cmd /c mysqldump --defaults-file=.mysql.cnf etest-mysql > "$BACKUP_FILE"

    Write-Host "File: $BACKUP_FILE Backup completed successfully."
} else {
    Write-Host "$BACKUP_DIR is not exist. Exiting..."
    exit 1
}