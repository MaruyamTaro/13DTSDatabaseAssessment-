from flask import Flask, render_template, request, redirect, session
import sqlite3, os
from sqlite3 import Error


#this code is used to find the path of the file even if i switch computers.
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DB")

app = Flask(__name__)
app.secret_key = "abcdef"


def is_logged_in():
    """
    params: none
    :return: true if the user is logged in. False if the user has not logged in
    """
    if session.get('first_name') is None:
        return False
    else:
        print("Logged IN")
        return True


def connect_database(db_file):
    """
    Creates a connection with the database
    :param db_file the database needed to be connected to be used:
    :return: conn
    """
    try:  #error detection
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)
        print(f'an error when connecting the db')
    return


@app.route('/')
def render_homepage():

    #con = connect_database(DATABASE)
    #query = ("INSERT INTO Bidhistory (time) VALUES (datetime('now', 'localtime'))")
    #cur = con.cursor()
    #cur.execute(query)

    """
    TEST for the time before the bid funtion EXIST. DELETE
    :return:
    """
    """
    After the user logs in it adds the changes to the home.html to get rid of some of the headings.
    :return: call to the render template function home.html and passes in the logged in status.
    """
    return render_template('home.html', logged_in=is_logged_in())


@app.route('/listings/<int:listing_id>', methods=['POST', 'GET'])
def listing_details(listing_id):
    """
    when the user clicks on a listing in the listings page, it sends the user to a page specifically to the product
     where they can bid
    :param listing_id:
    :return: calls the render template function with the data from the database filtered with the lisiting ID. so it
    displays only the specific product.
    """
    con = connect_database(DATABASE)
    query = "SELECT Listing_name, Listing_text, Listing_id, Image, Listing_price_res FROM Listings WHERE listing_id = ?"
    cur = con.cursor()
    cur.execute(query, (listing_id,))
    results = cur.fetchall()
    query2 = "SELECT price, time, fk_user_id FROM Bidhistory WHERE fk_listing_id = ? ORDER BY time DESC"
    cur = con.cursor()
    cur.execute(query2, (listing_id,))
    results2 = cur.fetchall()
    print(results2)
    print(results)
    if results is None:
        return "listing not found"
    if request.method == 'POST':
        #fname = request.form.get('user_F_name')
        Bid:int = int(request.form.get('UserBid'))
        if Bid <= 3:
            #adds the listing id so i can reload the same product page when the user fails to add a bid higher than the current bid
            listing = listing_id

            return render_template('listingpage.html', lisiting = listing, listings=results, History=results2, logged_in=is_logged_in())
        user_id = session['user_id']
        query_insert = ("INSERT INTO Bidhistory (price, time ,fk_Listing_id,fk_user_id) VALUES (?, datetime('now', 'localtime'),?,?)")

        query_test = "SELECT * FROM Bidhistory"

        cur = con.cursor()
        cur.execute(query_insert, (Bid,listing_id,user_id,))
        cur.execute(query_test)
        test_store = cur.fetchall()
        print(test_store)
        con.commit()



        return redirect('/listings/<int:listing_id>')
    return render_template('Listingpage.html', listings=results, Info=results2, logged_in=is_logged_in())


@app.route('/listings')
def render_listings():
    """
    displays a page with all the products
    :return: calls the render template function with a page with all rows of data with specific information.
    """
    con = connect_database(DATABASE)
    query = "SELECT Listing_name, Listing_text, Listing_id, Image FROM Listings"
    cur = con.cursor()
    cur.execute(query)
    results = cur.fetchall()
    print(results)
    con.close()
    return render_template('listings.html', listings=results, logged_in=is_logged_in())

# @app.route('/profile')
# def render_profile():
#     """
#     displays the user's information and the history of the user's bids and the history of their listings.
#     :return:
#     """
#     con = connect_database(DATABASE)
#     query1 = "SELECT Listing_name, Listing_text, Listing_id, Image, Listing_price FROM Listings"
#     query2 = "SELECT "
#     query3 = ""
#     cur = con.cursor()
#     cur.execute(query1)
#     Userdetail = cur.fetchall()
#
#     cur.execute(query2)
#     bidhistorydetail = cur.fetchall()
#
#     cur.execute(query3)
#     ListingHistorydetail = cur.fetchall()
#
#
#     con.close()
#     return render_template("profile.html", logged_in=is_logged_in())
#

@app.route('/signup', methods=['POST', 'GET'])
def render_signup():
    """
    sign up gets the input from the user and puts it into the database people with the insert
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
    """
    Displays the html with the login area. The user inserts the data and checks if the data they inserted
    is the same as the ones in the database. if not it displays a error.
    :return:calls the render template function for the home.html if the details are correct. If not it renders the login with a error.
    """
    if is_logged_in():
        return redirect('/')
    if request.method == 'POST':
        email = request.form.get('user_email')
        password = request.form.get('user_password')

        con = connect_database(DATABASE)
        cur = con.cursor()
        query = "SELECT First_name, Last_name, Email, password, Person_ID FROM People WHERE email = ?"
        cur.execute(query, (email,))
        results = cur.fetchone()
        if results is not None:
            if password != results[3]:
                return render_template('login.html', error='incorrect details')
            session['email'] = results[2]
            session['first_name'] = results[0]
            session['last_name'] = results[1]
            session['user_id'] = results[4]

            print(session)
            return redirect("/")
        else:
            return render_template('login.html', error='incorrect details')
    return render_template('login.html', logged_in=is_logged_in())


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    """

    :return:
    """
    print(session)
    session.clear()
    print(session)
    return redirect('/')


if __name__ == '__main__':
    app.run()

print("WHYYYYY")
