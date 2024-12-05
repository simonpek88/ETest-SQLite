DELETE from MagnetBlacklist where Magnet in (SELECT magnet from tfMD5)
TRUNCATE TABLE tfMD5