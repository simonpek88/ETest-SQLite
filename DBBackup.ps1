param(
    [string]$target = ""
)

switch ($target.ToLower()) {
    "simon" {
        $BACKUP_DIR = "D:\My Documents\OneDrive\私人文档\Python Project\ETest-SQLite\DB\MySQL_Backup"
    }
    "cnaf" {
        $BACKUP_DIR = "D:\Simon\Codes\ETest-SQLite-VSC\ETest-SQLite\DB\MySQL_Backup"
    }
    "st" {
        $BACKUP_DIR = "D:\Third\Path\MySQL_Backup"
    }
    default {
        Write-Host "无效参数. 请使用如下参数: simon, cnaf, or st (必须小写)."
        exit 1
    }
}

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