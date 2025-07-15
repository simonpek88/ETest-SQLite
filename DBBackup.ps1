$BACKUP_DIR = ".\DB\MySQL_Backup"

if (Test-Path $BACKUP_DIR) {
    $TIMESTAMP = Get-Date -Format "yyyyMMddHHmmss"
    $BACKUP_FILE = "$BACKUP_DIR\ETest-MySQL_Backup_$TIMESTAMP.sql"

    cmd /c mysqldump --defaults-file=.mysql.cnf etest-mysql > "$BACKUP_FILE"
    if (Test-Path $BACKUP_FILE) {
        $file = Get-Item $BACKUP_FILE
        if ($file.Length -gt 0) {
            Write-Host "File: $BACKUP_FILE 备份完成，大小: $("{0:F1}" -f ($file.Length / 1KB)) KB"
        } else {
            Write-Host "File: $BACKUP_FILE 备份文件为空，请检查 mysqldump 执行情况。"
            Remove-Item -Path $BACKUP_FILE -Force
            exit 1
        }
    } else {
        Write-Host "File: $BACKUP_FILE 备份失败，请检查路径和权限。"
        exit 1
    }
} else {
    Write-Host "$BACKUP_DIR 路径不存在, 请检查设置."
    exit 1
}