# db.py
from flask import Flask
from flask_hashing import Hashing
import mysql.connector
import connect

app = Flask(__name__)
app.secret_key = 'thisiskey'
hashing = Hashing(app)

def get_db_connection():
    print("Attempting to connect to the database...")
    connection = mysql.connector.connect(user=connect.dbuser,
                                         password=connect.dbpass,
                                         host=connect.dbhost,
                                         auth_plugin='mysql_native_password',
                                         database=connect.dbname)
    cursor = connection.cursor()
    print("Database connection established.")
    return connection, cursor
