# import os

# class Config:
#     SECRET_KEY = "supetSecretkeyPortfolioWebApp"

#     MYSQL_HOST = "localhost"
#     MYSQL_USER = "root"
#     MYSQL_PASSWORD = "SQLPassCode"
#     MYSQL_DB = "portfolio_db"
    
#     MYSQL_CHARSET = "utf8mb4"

#     # mail: admin@email.com
#     # Pass: admin123

import os
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "superSecret")

    ENV = os.environ.get("ENV", "development")

    if ENV == "production":
        MYSQL_HOST = os.environ.get("MYSQL_HOST")
        MYSQL_USER = os.environ.get("MYSQL_USER")
        MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
        MYSQL_DB = os.environ.get("MYSQL_DB")
        MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
        MYSQL_SSL_CA = os.environ.get("MYSQL_SSL_CA")

        # Password of admin of Aiven
        # mail: admin@siddiq.com
        # Password: admin123

    else:
        MYSQL_HOST = "localhost"
        MYSQL_USER = "root"
        MYSQL_PASSWORD = "SQLPassCode"
        MYSQL_DB = "portfolio_db"
        MYSQL_PORT = 3306
        MYSQL_SSL_CA = None  

    MYSQL_CHARSET = "utf8mb4"