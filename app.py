from flask import Flask, render_template, request, redirect, session
import sqlite3, os
from sqlite3 import Error

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DB")

app = Flask(__name__)
app.secret_key = "abcdef"


def is_logged_in():
    if session.get('first_name') is None:
        return False
    if session['first_name'] is None:
        print("Not Logged IN")
        return False
    else:
        print("Logged IN")
        return True


def connect_database(db_file):
    """
    Creates a connection with the database
    :param db_file:
    :return: conn
    """
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
        print(f'an error when connecting the db')
    return


@app.route('/')
def render_homepage():
    return render_template('home.html', logged_in=is_logged_in())


@app.route('/listings')
def render_listings():
    con = connect_database(DATABASE)
    query = "SELECT Listing_name, Listing_text, Listing_id, Image, Listing_price FROM Listings"
    cur = con.cursor()
    cur.execute(query)
    results = cur.fetchall()
    print(results)
    con.close()
    return render_template('listings.html', listings=results)

@app.route('/signup', methods=['POST', 'GET'])
def render_signup():
    """
    sign up gets the input from the user and puts it into the database people with the append
    :return:
    database with new user info
    """
    if request.method == 'POST':

        try:
            fname = request.form.get('user_F_name')
            lname = request.form.get('user_L_name')
            email = request.form.get('user_email')
            pass1 = request.form.get('user_password')
            pass2 = request.form.get('user_password2')
            print("flag1")
            print(fname)
            if pass1 != pass2:
                return redirect("/signup?error=passwords+do+not+match")
            if len(pass1) < 8:
                return redirect("/signup?error=password+must+be+more+than+8+letters")

            con = connect_database(DATABASE)
            query_insert = ("INSERT INTO People (First_name, Last_name, Email, password) "
                            "VALUES (?, ?, ?, ?)")
            query_test = "SELECT * FROM People"
            cur = con.cursor()
            cur.execute(query_insert, (fname, lname, email, pass1))
            cur.execute(query_test)
            test_store = cur.fetchall()
            print(test_store)
            con.commit()

            return redirect("/login?message=signup+successful")

        except Exception as e:
            print(f"Signup error: {str(e)}")
            return redirect("/signup?error=registration+failed")

    # If it's a GET request, render the signup form
    return render_template("signup.html", logged_in=is_logged_in())


@app.route('/login', methods=['POST', 'GET'])
def render_login():
    if is_logged_in():
        return redirect('/')
    if request.method == 'POST':
        email = request.form.get('user_email')
        password = request.form.get('user_password')

        con = connect_database(DATABASE)
        cur = con.cursor()
        query = "SELECT First_name, Last_name, Email, password FROM People WHERE email = ?"
        cur.execute(query, (email,))
        results = cur.fetchone()
        if results is not None:
            if password != results[3]:
                return render_template('login.html', error='incorrect details')
            session['email'] = results[2]
            session['first_name'] = results[0]
            session['last_name'] = results[1]
            print(session)
            return redirect("/")
        else:
            return render_template('login.html', error='incorrect details')
    return render_template('login.html', logged_in=is_logged_in())

#@app.route('/listings/<int:listing_id>')
#def listing_details(listing_id):





@app.route('/logout', methods=['POST', 'GET'])
def logout():
    print(session)
    session.clear()
    print(session)
    return redirect('/')


if __name__ == '__main__':
    app.run()

print("WHYYYYY")
