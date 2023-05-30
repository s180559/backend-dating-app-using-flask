from cs50 import SQL

"""simple script to add new categories to database"""

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///mobby.db")

print("Here you can enter new categories!")
x = input("Type value or 'quit' to break: ")

while x != "quit":
    db.execute("INSERT INTO hobbies (hobby) VALUES (:ho)", ho = x)
    x = input(" type value or quit to break ")

print("You quit")