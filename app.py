import os
import datetime

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///mobby.db")


@app.route("/")
@login_required
def index():
    """Show searches and matches"""
    user = session["user_id"]

    # select stocks
    data = db.execute("SELECT hobby, male, female, min_age, max_age, level FROM search WHERE user_id = :us" , us = user)

    return render_template("index.html", data = data, leng = len(data))


@app.route("/match")
@login_required
def match():
    """Show matches"""
    user = session["user_id"]

    # select my searches
    my_searches = db.execute("SELECT hobby, male, female, min_age, max_age, level FROM search WHERE user_id = :us" , us = user)
    my_hobbies = []
    final_matches = []
    for row in my_searches:
        my_hobbies.append(row["hobby"])

    if not my_hobbies:
        flash("You are searching for nothing until now!")
        return render_template("search.html")

    # select my data
    my_data = db.execute("SELECT age, sex FROM users WHERE id = :us", us = user)
    my_age = int(my_data[0]["age"])
    my_sex = my_data[0]["sex"]

    for h in range(len(my_hobbies)):
        # get people matching with me
        if my_sex == "Male":
            matched_by = db.execute("SELECT user_id FROM search WHERE (user_id != :us AND hobby = :ho AND male = :ma AND min_age <= :mi AND max_age >= :m)",
                                    us = user, ho = my_hobbies[h], ma = "yes", mi = my_age, m = my_age)   # FÜR JEDES HOBBY NACHBESSERN!
        else:
            matched_by = db.execute("SELECT user_id FROM search WHERE (user_id != :us AND hobby = :ho AND female = :fe AND min_age <= :mi AND max_age >= :m)",
                                    us = user, ho = my_hobbies[h], fe = "yes", mi = my_age, m = my_age)

        if len(matched_by) == 0:
            no_match1 = [{}]
            final_matches.append(no_match1)
            continue


        # compare to my own matches
        matches=[]
        for i in matched_by:
            # check for my own search criteria
            if my_searches[h]["male"] == "yes":
                match1 = db.execute("SELECT id FROM users WHERE (id = :us AND sex = :se AND age >= :mi AND age <= :m)",
                                    us = i["user_id"], se = "Male", mi = my_searches[h]["min_age"], m = my_searches[h]["max_age"] )
                for j in match1:
                    matches.append(j["id"])
            if my_searches[h]["female"] == "yes":
                match2 = db.execute("SELECT id FROM users WHERE (id = :us AND sex = :se AND age >= :mi AND age <= :m)",
                                    us = i["user_id"], se = "Female", mi = my_searches[h]["min_age"], m = my_searches[h]["max_age"] )
                for k in match2:
                    matches.append(k["id"])

        # show matches
        if len(matches) == 0:
            no_match2 = [{}]
            final_matches.append(no_match2)
            continue

        elif len(matches) == 1:
            final = db.execute("SELECT name, email, sex, age FROM users WHERE id = :ma", ma = matches[0])
        else:
            final = db.execute("SELECT name, email, sex, age FROM users WHERE id In {}".format(tuple(matches)))

        # get data from match
        for l in range(len(matches)):
           final2 = db.execute("SELECT hobby, text, level  FROM search WHERE (user_id = :us AND hobby = :ho)" , us = matches[l], ho = my_hobbies[h])
           final[l].update(final2[0])

        final_matches.append(final[:5])   # limit to length of 5 for displaying 

    return render_template("match.html", matches = final_matches, hobbies = my_hobbies, leng = len(my_hobbies))

@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Send request"""
    hobbies = db.execute("SELECT hobby FROM hobbies")

    if request.method == "POST":

        user = session["user_id"]
        hobby = request.form.get("hobby")
        mi_age = request.form.get("mi_age")
        ma_age = request.form.get("ma_age")
        male = request.form.get("male")
        female = request.form.get("female")
        level = request.form.get("gridRadios")
        text = request.form.get("text")

        if (male==None and female==None) or not mi_age or not ma_age or not text:
            flash("Please complete all entries!")
            return render_template("search.html", hobbies = hobbies)

        # check if search already exists
        data = db.execute("SELECT * FROM search WHERE (user_id = :us AND hobby = :ho)" , us = user, ho = hobby)
        if len(data) != 0:
            db.execute("DELETE FROM search WHERE (user_id = :us AND hobby = :ho)" , us = user, ho = hobby)
            flash("Your search has been edited!")

        if male == None:
            male = "no"
        else:
            male = "yes"
        if female == None:
            female = "no"
        else:
            female="yes"

        db.execute("INSERT INTO search (user_id, hobby, text, male, female, min_age, max_age, level) VALUES (:us, :ho, :te, :ma, :fe, :mi, :m, :le)",
                   us= user, ho = hobby, te=text, ma = male, fe = female, mi = mi_age, m = ma_age, le = level)
        return redirect("/")

    else:
        return render_template("search.html", hobbies = hobbies)


@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    user = session["user_id"]
    data = db.execute("SELECT hobby, male, female, min_age, max_age, level, text FROM search WHERE user_id = :us" , us = user)

    if request.method == "POST":

        user = session["user_id"]
        hobby = request.form.get("delete")

        db.execute("DELETE FROM search WHERE (user_id = :us AND hobby = :ho)" , us = user, ho = hobby)

        flash(hobby + " has been deleted from your searches!")
        return redirect("/")

    else:
        return render_template("edit.html", data = data, leng = len(data))


@app.route("/suggest", methods=["GET", "POST"])
@login_required
def suggest():
    user = session["user_id"]
    data = db.execute("SELECT title, COUNT(title) AS n FROM suggest GROUP BY title ORDER BY n DESC LIMIT 5")
    sug = db.execute("SELECT title FROM suggest WHERE user_id = :us", us = user)

    if request.method == "POST":

        suggestion = request.form.get("suggest")

        if len(sug) == 3:
            flash("You have reached the limit of 3 suggestions.")
            return redirect("/suggest")

        if suggestion.isalpha():
            suggestion.title()

        for i in sug:
            if suggestion == i["title"]:
                flash("You can not submit a suggestion twice!")
                return redirect("/suggest")


        db.execute("INSERT INTO suggest (user_id, title) VALUES (:us, :ti)", us = user, ti = suggestion )

        flash(suggestion + " has been added to suggestions!")
        return redirect("/suggest")

    else:
        return render_template("suggest.html", data = data, sug = sug)



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("email"):
            return apology("must provide E-Mail", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE email = :em",
                          em=request.form.get("email"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("Invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")




@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # get username and password from form
        f_name = request.form.get("f_name")
        l_name = request.form.get("l_name")
        email = request.form.get("email")
        pword = request.form.get("password")
        age = request.form.get("age")
        sex = request.form.get("SEX")

        # Ensure username was submitted
        if not f_name or not l_name or not f_name.isalpha() or not l_name.isalpha():
            flash("You must provide a correct name!", "danger")
            return render_template("register.html")

        elif not email or not "@" in email:
            flash("You must provide a valid E-Mail!")
            return render_template("register.html")

        # Ensure password was submitted
        elif not pword:
            flash("You must provide a password!")
            return render_template("register.html")

        elif not age:
            flash("You must provide your Age")
            return render_template("register.html")

        elif len(pword) < 6 or pword.isalpha():
            flash("Please choose at least 6 digits including one non-alphabetic character!")
            return render_template("register.html")

        elif int(age) < 16 or int(age) > 111:
            flash("Sorry the app is only suitable for age 16+")
            return render_template("register.html")

        # Ensure mail does not exist already
        rows = db.execute("SELECT * FROM users WHERE email = :em",
                          em=email)
        if len(rows) != 0:
            return apology("Your account exists already.", 403)

        if email != request.form.get("c_email"):
            flash("E_Mail Adresses did not match")
            return render_template("register.html")

        # Ensure password confirm matches
        if pword != request.form.get("c_password"):
            flash("passwords did not match")
            return render_template("register.html")

        # hash password
        hash_pword = generate_password_hash(pword, method='pbkdf2:sha256', salt_length=8)

        # insert data to database
        db.execute("INSERT INTO users (name, email, hash, age, sex) VALUES (:na, :em, :ha, :ag, :se)",
                   na= (f_name+" "+l_name), em = email, ha=hash_pword, ag = age, se = sex)

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)