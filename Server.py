from flask import Flask, render_template,request, redirect, session, flash
from flask_bcrypt import Bcrypt
from mysqlconnection import connectToMySQL
import re

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

app = Flask(__name__)
app.secret_key = "pita"

bcrypt = Bcrypt(app)

@app.route("/")
def log_reg_landing():
    return render_template("login_reg.html")


@app.route("/success")
def tweet_landing():

    if 'user_id' not in session:
        return redirect("/")

    query = "SELECT user.first_name from USER WHERE id_user = %(uid)s"
    data = {'uid': session['user_id']}
    mysql = connectToMySQL("dojo_tweets")
    result = mysql.query_db(query, data)
    if result:

        query = "SELECT tweet.id_tweet, tweet.author, tweet.tweet, user.first_name, user.last_name FROM user JOIN tweet ON user.id_user = tweet.author"
        mysql = connectToMySQL("dojo_tweets")
        tweets = mysql.query_db(query)


        return render_template("tweets.html", user_data = result[0], tweets=tweets)
    else:
        return redirect("/")

@app.route("/on_tweet", methods=["POST"])
def on_tweet():
    is_valid = True
    tweet_content = request.form.get('tweet_content')
    if len(tweet_content) < 1:
        is_valid = False
        flash("Tweets must be at least 1 character long.")

    if is_valid:
        query = "INSERT INTO tweet (tweet, author, created_at, updated_at) VALUES (%(tweet)s, %(user_fk)s, NOW(), NOW());"
        data = {
            'tweet': tweet_content,
            'user_fk': session['user_id']
        }
        mysql = connectToMySQL("dojo_tweets")
        mysql.query_db(query, data)

    return redirect("/success")

@app.route("/on_delete/<tweet_id>")
def on_delete(tweet_id):
    if 'user_id' not in session:
        return redirect("/")

    query = f"DELETE FROM tweet WHERE tweet.id_tweet = %(tweet_id)s"
    data = {'tweet_id': tweet_id}
    mysql = connectToMySQL("dojo_tweets")
    mysql.query_db(query, data)

    return redirect("/success")

@app.route("/edit/<tweet_id>")
def edit_form(tweet_id):
    query = "SELECT tweet.id_tweet, tweet.tweet FROM tweet WHERE tweet.id_tweet = %(tweet_id)s"
    data = {'tweet_id': tweet_id}
    mysql = connectToMySQL("dojo_tweets")
    tweet = mysql.query_db(query, data)
    if tweet:
        return render_template("tweet_edit.html", tweet_data = tweet[0])

    return redirect("/success")

@app.route("/on_edit/<tweet_id>", methods=['POST'])
def on_edit(tweet_id):
    query = "UPDATE tweet SET tweet.tweet = %(tweet)s WHERE tweet.id_tweet = %(tweet_id)s"
    data = {'tweet': request.form.get("tweet_edit"), 'tweet_id': tweet_id}
    mysql = connectToMySQL("dojo_tweets")
    mysql.query_db(query, data)

    return redirect("/success")

@app.route("/like/<tweet_id>")
def like_tweet(tweet_id):
    query = "INSERT INTO liked_tweets (user_id, tweet_id) VALUES (%(u_id)s, %(t_id)s)"
    data = {'u_id': session['user_id'], 't_id': tweet_id}
    mysql = connectToMySQL("dojo_tweets")
    mysql.query_db(query, data)

    return redirect("/success")

@app.route("/unlike/<tweet_id>")
def unlike_tweet(tweet_id):
    query = "DELETE FROM liked_tweets WHERE user_id = %(u_id)s AND tweet_id = %(t_id)s"
    data = {'u_id': session['user_id'], 't_id': tweet_id}
    mysql = connectToMySQL("dojo_tweets")
    mysql.query_db(query, data)

    return redirect("/success")

@app.route("/details/<tweet_id>")
def tweet_details(tweet_id):
    query = "SELECT user.first_name, user.last_name, tweet.created_at, tweet.tweet FROM user JOIN tweet ON user.id_user = tweet.author WHERE tweet.id_tweet = %(tid)s"
    data = {'tid': tweet_id}
    mysql = connectToMySQL("dojo_tweets")
    tweet_data = mysql.query_db(query, data)
    if tweet_data:
        tweet_data = tweet_data[0]
    
    query = "SELECT user.first_name, user.last_name FROM liked_tweets JOIN user ON user.id_user = liked_tweets.user_id WHERE liked_tweets.tweet_id = %(tid)s"
    data = {'tid': tweet_id}
    mysql = connectToMySQL("dojo_tweets")
    like_data = mysql.query_db(query, data)

    query = "SELECT user.first_name, user.last_name, tweet.tweet FROM liked_tweets JOIN user ON user.id_user = liked_tweets.user_id JOIN tweet ON tweet.id_tweet = liked_tweets.tweet_id"
    mysql = connectToMySQL("dojo_tweets")
    all_liked_tweets = mysql.query_db(query)

    return render_template("details.html", tweet_data=tweet_data, like_data=like_data, all_liked_tweets=all_liked_tweets)





@app.route("/on_register", methods=["POST"])
def on_register():
    is_valid = True

    if not EMAIL_REGEX.match(request.form.get('em')):
        is_valid = False
        flash("Email is not valid")
    
    if len(request.form.get('fn')) < 1:
        is_valid = False
        flash("Fist name must be at least 2 characters long.")

    if len(request.form.get('ln')) < 1:
        is_valid = False
        flash("Last name must be at least 2 characters long.")

    if len(request.form.get('pw')) < 8:
        is_valid = False
        flash("Password must be at least 8 characters long.")    

    if request.form.get('pw') != request.form.get('cpw'):
        is_valid = False
        flash("Passwords must match")

    if is_valid:
        query = "INSERT INTO user (first_name, last_name, email, password, created_at, updated_at) VALUES ( %(fn)s, %(ln)s, %(em)s, %(pw)s, NOW(), NOW())"
        data = {
            'fn': request.form.get('fn'),
            'ln': request.form.get('ln'),
            'em': request.form.get('em'),
            'pw': bcrypt.generate_password_hash(request.form.get('pw'))
        }
        mysql = connectToMySQL("dojo_tweets")
        user_id = mysql.query_db(query, data)
        
        if user_id:
            session['user_id'] = user_id
            return redirect("/success")

    return redirect("/")

@app.route("/on_login", methods=["POST"])
def on_login():
    is_valid = True

    if not EMAIL_REGEX.match(request.form.get('em')):
        is_valid = False
        flash("Email is not valid")

    if is_valid: 
        query = "SELECT user.id_user, user.password FROM user WHERE user.email = %(em)s"
        data = {'em': request.form.get('em')}
        mysql = connectToMySQL("dojo_tweets")
        result = mysql.query_db(query, data)

        if result:
            if not bcrypt.check_password_hash(result[0]['password'], request.form.get('pw')):
                flash("incorrect password")
                return redirect("/")
            else:
                session['user_id'] = result[0]['id_user']
                return redirect("/success")
        else:
            flash("email is not in database")

    return redirect("/")

@app.route("/on_logout")
def on_logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)