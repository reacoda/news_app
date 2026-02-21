import pymysql

pymysql.install_as_MySQLdb()

# Bypass Django's version check
pymysql.version_info = (2, 2, 1, "final", 0)
