UPDATE mysql.user SET Password=PASSWORD('miaowu') WHERE User='root';
FLUSH PRIVILEGES;