from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

#Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root12'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MYSQL
mysql = MySQL(app)

# Index
@app.route('/')
def index():
    return render_template('home.html')

# About
@app.route('/about')
def about():
    return render_template('about.html')

# Articles
@app.route('/articles')
def articles():
    # create cursor
    cur = mysql.connection.cursor()

    # execute query
    result = cur.execute('SELECT * FROM articles')

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = "No article Found"
        return render_template('articles.html', msg=msg)
    # close conection
    cur.close()

# Single article
@app.route('/article/<string:id>/')
def article(id):
    # create cursor
    cur = mysql.connection.cursor()

    # execute query
    result = cur.execute('SELECT * FROM articles WHERE id=%s', [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)

# Regiser form class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Confirm Password')

# User regiser
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # create cursor
        cur = mysql.connection.cursor()

        # execute query
        cur.execute('INSERT INTO users(name, username, email, password) VALUES(%s, %s, %s, %s)',
                    [name, username, email, password])

        # commit to db
        mysql.connection.commit()

        # close conection
        cur.close()

        flash("you are now logged in", "success")

        return redirect(url_for("index"))

    return render_template('register.html', form=form)

# User login
@app.route('/login', methods=["GET", "POST"])
def login():
    form = RegisterForm(request.form)
    if request.method == "POST" :
        # get form fields
        username = request.form["username"]
        password_candidate = request.form["password"]

        # create cursor
        cur = mysql.connection.cursor()

        # execute query
        result = cur.execute('SELECT password, username FROM users WHERE username=%s',[username])

        if result > 0:
            # get stored hash
            data = cur.fetchone()
            # get password
            password = data["password"]
            # compare password
            if sha256_crypt.verify(password_candidate, password):
                session["logged_in"] = True
                session["username"] = username
                flash("you are now logged in", "success")
                return redirect(url_for("dashboard"))
            else:
                error = "Invalid login"
                return render_template("login.html", error=error)
            # close conection
            cur.close()
        else:
            error = "Username not found"
            # close conection
            cur.close()
            return render_template("login.html", error=error)

    return render_template('login.html', form=form)

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("you are now logged out", "success")
    return redirect(url_for("login"))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # create cursor
    cur = mysql.connection.cursor()

    # execute query
    result = cur.execute('SELECT * FROM articles')

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = "No article Found"
        return render_template('dashboard.html', msg=msg)
    # close conection
    cur.close()

# Article form class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add article
@app.route('/add_article', methods=["GET", "POST"])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        body = form.body.data

        # create cursor
        cur = mysql.connection.cursor()

        # execute query
        cur.execute('INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)',
                    [title, body, session["username"]])

        # commit to db
        mysql.connection.commit()

        # close conection
        cur.close()

        flash("Article created", "success")

        return redirect(url_for("dashboard"))

    return render_template('add_article.html', form=form)


# Add article
@app.route('/edit_article/<string:id>/', methods=["GET", "POST"])
@is_logged_in
def edit_article(id):
    # create cursor
    cur = mysql.connection.cursor()

    # execute query
    result = cur.execute('SELECT * FROM articles WHERE id=%s', [id])

    article = cur.fetchone()

    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article["title"]
    form.body.data = article["body"]

    if request.method == "POST" and form.validate():
        title = request.form["title"]
        body = request.form["body"]

        # create cursor
        cur = mysql.connection.cursor()

        # execute query
        cur.execute('UPDATE articles SET title=%s, body=%s WHERE id=%s',[title, body, id])

        # commit to db
        mysql.connection.commit()

        # close conection
        cur.close()

        flash("Article updated", "success")

        return redirect(url_for("dashboard"))

    return render_template('edit_article.html', form=form)

# Add article
@app.route('/delete_article/<string:id>/', methods=["POST"])
@is_logged_in
def delete_article(id):
    # create cursor
    cur = mysql.connection.cursor()

    # execute query
    cur.execute('DELETE FROM articles WHERE id=%s', [id])

    # commit to db
    mysql.connection.commit()

    # close conection
    cur.close()

    flash("Article deleted", "success")

    return redirect(url_for("dashboard"))


if __name__ == '__main__':
    app.secret_key = "secret123"
    app.run(debug=True)

