import sqlite3
from flask_bcrypt import Bcrypt
import re

bcrypt = Bcrypt()

def add_user(role='customer'):
    # Accept user data from the registration form
    username = input("Enter username: ")
    email = input("Enter email: ")
    password = input("Enter password: ")
    confirm_password = input("Confirm password: ")

    if password != confirm_password:
        print("Passwords do not match.")
    elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        print("Invalid email format.")
    elif len(password) < 8:
        print("Password must be at least 8 characters long.")
    else:
        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        # Insert user into the database
        with sqlite3.connect("weather.db") as con:
            cur = con.cursor()
            cur.execute("INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                        (username, email, hashed_password, role))
            con.commit()
            print("User registered successfully.")

if __name__ == "__main__":
    add_user()
