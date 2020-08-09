import os

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
db = SQL("sqlite:///pets.db")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        # Query database for username
        rowsuser = db.execute("SELECT username FROM users WHERE username = :username",
                          username=request.form.get("username"))

         # Query database for email
        rowsemail = db.execute("SELECT email FROM users WHERE email = :email",
                          email=request.form.get("email"))

        if len(rowsuser) != 0:
            return apology("Unvailable username",400)

        elif len(rowsemail) != 0:
            return apology("Unvailable email",400)

        # if does not exist this username, it can be created
        else:

            # putting username and hash into database
            newUser = db.execute("INSERT INTO users (username, hash,email,phonenumber,name) VALUES(:username, :hash, :email, :phonenumber,:name)", username=request.form.get("username"),
                        hash=generate_password_hash(request.form.get("password2")), email=request.form.get("email"), phonenumber=request.form.get("phonenumber"),
                        name=request.form.get("name"))

            # Remember which user has logged in
            session["user_id"] = newUser

            # Redirect user to home page
            flash("Registered!")
            return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

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


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        postId = request.form.get("hidden")

        updateStatus = db.execute('UPDATE posts SET status = 1 WHERE id = :id',id=postId)

        flash("Adopted")
        return redirect("/")

    else:
        rows = db.execute('SELECT animal_type.type, animal_breed.breed, animals.age, sex.genre, cities.name AS city_name, post_status.status, posts.id , posts.description, users.name AS user_name, users.email, users.phonenumber FROM animals JOIN animal_type ON animals.animal = animal_type.id JOIN animal_breed ON animals.breed = animal_breed.id JOIN sex ON animals.sex = sex.id JOIN posts ON animals.id = posts.animal_id JOIN cities ON posts.city = cities.id JOIN post_status ON posts.status = post_status.id JOIN users ON users.id = posts.user_id ORDER BY posts.id DESC')
        return render_template("index.html",rows=rows)


@app.route("/donate", methods=["GET", "POST"])
@login_required
def donate():

    if request.method == "GET":

        rows = db.execute("SELECT * FROM cities")
        breeds = db.execute('SELECT * FROM animal_breed')
        animals = db.execute('SELECT * FROM animal_type')

        return render_template("donate.html", rows=rows, animals=animals, breeds=breeds)

    # REQUEST.METHOD == POST
    else:

        animal = request.form.get('animal')
        breed = request.form.get('breed')
        age = request.form.get('age')
        sex = request.form.get('customRadioInline1')
        city = request.form.get('city')
        description = request.form.get('description')

        animal_id = db.execute('INSERT INTO animals(animal, breed, age, sex) VALUES (:animal, :breed, :age, :sex)',
                        animal=animal, breed=breed, age=age, sex=sex)

        posts = db.execute('INSERT INTO posts(user_id, animal_id, city, description) VALUES (:user_id, :animal_id, :city, :description)',
                            user_id=session['user_id'], animal_id=animal_id, city=city, description=description)

        rows = db.execute('SELECT animal_type.type, animal_breed.breed, animals.age, sex.genre, cities.name, post_status.status FROM animal_type JOIN animals ON animal_type.id = animals.animal JOIN animal_breed ON animal_breed.id = animals.breed JOIN sex ON sex.id = animals.sex JOIN posts ON posts.animal_id = animals.id JOIN cities ON cities.id = posts.city JOIN post_status ON post_status.status = posts.status')

        flash("Donated")
        return redirect("/")

@app.route("/myPosts", methods=["GET", "POST"])
@login_required
def myPosts():
    if request.method == "GET":
        rows = db.execute('SELECT animal_type.type, animal_breed.breed, animals.age, sex.genre, cities.name AS city_name, post_status.status, posts.id , posts.description, users.name AS user_name, users.email, users.phonenumber FROM animals JOIN animal_type ON animals.animal = animal_type.id JOIN animal_breed ON animals.breed = animal_breed.id JOIN sex ON animals.sex = sex.id JOIN posts ON animals.id = posts.animal_id JOIN cities ON posts.city = cities.id JOIN post_status ON posts.status = post_status.id JOIN users ON users.id = posts.user_id  WHERE posts.user_id = :id ORDER BY posts.id DESC',id=session["user_id"])
        return render_template("myPosts.html",rows=rows)
    else:
        postId = request.form.get("hidden")
        updateStatus = db.execute('UPDATE posts SET status = -1 WHERE id = :id',id=postId)
        flash("Deleted")
        return redirect("/")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)