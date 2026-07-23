from flask_mysqldb import MySQL

mysql = MySQL()


def get_cursor():
    return mysql.connection.cursor()


def commit():
    mysql.connection.commit()


def rollback():
    mysql.connection.rollback()
