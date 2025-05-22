from flask import Flask, render_template, request, redirect, session
import sqlite3, os
from sqlite3 import Error
from flask_bcrypt import Bcrypt

#this code is used to find the path of the file even if i switch computers.
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DB")

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "abcdef"

#used to save which folder the images save to
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def is_logged_in():
    """
    params: none
    :return: true if the user is logged in. False if the user has not logged in.
    """
    if session.get('first_name') is None:
        return False
    else:
        print("Logged IN")
        return True

def admin_check():
    """
    Checks if the user is a admin by seeing if the ADMIN column has a 1 or 0.
    params: none

    :return:  True if the user is a admin and false if its a normal account

    """
    print("checking admin")
    if session.get('ADMIN') == 1:
        print("Admin logged in")
        return True
    else:
        print("not admin")
        return False


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
    After the user logs in it adds the changes to the home.html to get rid of some of the headings.
    :return: call to the render template function home.html and passes in the logged in status.
    """
    return render_template('home.html', logged_in=is_logged_in(),admin_check=admin_check())


@app.route('/MakeListing', methods=['POST', 'GET'])
def render_Makelisting():
    """
    infomation about the listing that the user wants to make is passed in and get checked if it contains
    valid information and if it is, it gets added to the database. (table=Listings)
    :return: Returns either the same page if there is an error with the html dysplaying it or listings page where the user
    can see the listing they just made.
    """
    if request.method == 'POST':
        listing_name = request.form.get('Listing_name')
        listing_info = request.form.get('Listing_info')
        list_price_res = request.form.get('List_price_res')
        Image = request.form.get('listing_image')
        # checks if any of the values of these variables are empty but if they are not they return template to display error.
        if not all([listing_name, listing_info, list_price_res]):
            print("EMPTYBOXES")
            return render_template('makelisting.html', error="emptyBox", logged_in=is_logged_in(),admin_check=admin_check())



        #checks if the reserve price is lower than 0. stops the code from causing a error later on when bidding
        list_price_res=int(list_price_res)
        if list_price_res <=0:
            print("initial lower than 0")
            return render_template('makelisting.html', error="lower0", logged_in=is_logged_in(),admin_check=admin_check())

        if 'listing_image' in request.files:

            file = request.files['listing_image']
            # checks if the file is a image file
            if file.filename == '' or not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                return render_template('makelisting.html', error="invalidfile", logged_in=is_logged_in(),
                                       admin_check=admin_check())

            filename = file.filename

            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Save the file to the static/images folder
            file.save(filepath)



            con = connect_database(DATABASE)
            query_insert = ("INSERT INTO Listings (Listing_name, Listing_text, Listing_price_res, Image,MadeBy_User_id,Sold)"
                            "VALUES (?, ?, ?, ?, ?,?)")
            cur = con.cursor()
            Made_By_User_id = session['user_id']
            cur.execute(query_insert, (listing_name, listing_info, list_price_res, filename, Made_By_User_id, 0))
            test_store = cur.fetchall()
            print(test_store)
            con.commit()

            return render_template('listings.html', logged_in=is_logged_in(),admin_check=admin_check())

    return render_template('makelisting.html',logged_in=is_logged_in(),admin_check=admin_check())


@app.route('/listings/<int:listing_id>', methods=['POST', 'GET'])
def listing_details(listing_id):

    listing = listing_id

    """
    when the user clicks on a listing in the listings page, it sends the user to a page specifically to the product
     where they can bid. When they bid, they add their information and how much they bid into the database. where it will be displayed in the 
     same page.
    :param listing_id, :
    :return: calls the render template function with the data from the database filtered with the lisiting ID. so it
    displays only the specific product.
    
    """
    con = connect_database(DATABASE)
    cur = con.cursor()

    # Get the maximum bid price for this listing
    cur.execute("SELECT MAX(price) FROM bidhistory WHERE fk_Listing_id = ?", (listing_id,))
    max_result = cur.fetchone()[0]

    # If there are no bids yet max_result will be nonetype. error keeps happening if this is not here when there are no inital bids
    if max_result is None:
        maxbid = 0
    else:
        maxbid = int(max_result)


    query = "SELECT Listing_name, Listing_text, Listing_id, Image, Listing_price_res FROM Listings WHERE listing_id = ?"
    cur = con.cursor()
    cur.execute(query, (listing_id,))
    results = cur.fetchall()

    query2 = "SELECT price, time, COALESCE(First_name, 'User Deleted') FROM Bidhistory LEFT JOIN PEOPLE ON Bidhistory.fk_user_id = PEOPLE.Person_ID WHERE fk_listing_id = ? ORDER BY time DESC"
    print(query2)
    cur = con.cursor()
    cur.execute(query2, (listing_id,))
    results2 = cur.fetchall()

    print(results2)
    print(results)
    if results is None:
        return "listing not found"
    if request.method == 'POST':
        #fname = request.form.get('user_F_name')
        userbid = request.form.get('UserBid')
        if userbid is None or userbid.strip() == '':
            return redirect("/listings?error=No+bids")
        else:
            Bid:int = int(userbid)
        if len(userbid.strip()) > 18:
            return redirect("/listings?error=Number+to+big")

        if Bid <= maxbid:
            error = 'lowerbid'
            #adds the listing id so i can reload the same product page when the user fails to add a bid higher than the current bid
            listing = listing_id
            return render_template('listingpage.html', lisiting = results, listings=results, Info=results2, logged_in=is_logged_in(), error = 'lowerbid',admin_check=admin_check())
        user_id = session['user_id']
        query_insert = ("INSERT INTO Bidhistory (price, time ,fk_Listing_id,fk_user_id) VALUES (?, datetime('now', 'localtime'),?,?)")

        query_test = "SELECT * FROM Bidhistory"

        cur = con.cursor()
        cur.execute(query_insert, (Bid,listing_id,user_id,))
        cur.execute(query_test)

        con.commit()

        #Code to check if bid is reaching the reserve price of the listing and sets it to sold if it is.
        cur.execute("SELECT Listing_price_res FROM Listings WHERE Listing_id = ?", (listing_id,))
        ListRes = cur.fetchone()[0]
        if Bid >= ListRes:
            print("YAYY!")
            #if the listing is sold updates the database to hide the listing in listings page
            cur.execute("UPDATE Listings SET Sold = 1 WHERE Listing_id = ?", (listing_id,))
            con.commit()
            return render_template('Bought.html', logged_in=is_logged_in(),admin_check=admin_check())

        return render_listings()
    return render_template('listingpage.html', listings=results, Info=results2, logged_in=is_logged_in(),admin_check=admin_check())


@app.route('/listings')
def render_listings():
    """
    displays a page with all the products
    :return: calls the render template function with a page with all rows of data with specific information.
    """
    con = connect_database(DATABASE)
    query = "SELECT Listing_name, Listing_text, Listing_id, Image FROM Listings WHERE SOLD = 0"
    cur = con.cursor()
    cur.execute(query)
    results = cur.fetchall()
    print(results)
    con.close()
    return render_template('listings.html', listings=results, logged_in=is_logged_in(),admin_check=admin_check())


@app.route('/profile')
def render_profile():
    user_id = session['user_id']
    """
    displays the user's information and the history of the user's bids and the istings they made and its status.
    :return:renders the profile html while passing in all the information that goes into the tables
    """
    #gets the name of the user to display
    con = connect_database(DATABASE)
    cur = con.cursor()

    query = "SELECT First_name, Last_name FROM people WHERE Person_ID = ?"
    cur.execute(query, (user_id,))
    Userdetail = cur.fetchall()

    # Gets bid history of the bids the user has made
    query2 = "SELECT price, Listing_name, time FROM Bidhistory INNER JOIN Listings ON Bidhistory.fk_Listing_id = Listings.Listing_id WHERE Bidhistory.fk_user_id = ?"
    cur.execute(query2, (user_id,))
    BidData = cur.fetchall()
    print(user_id)
    print(BidData)

    #Gets all the data of listings the user made and its status plus the highest bid ammount on the lising.
    query2 = "SELECT Listings.Listing_name, Listings.Listing_price_res, Listings.Sold, MAX(Bidhistory.price)"\
             " AS Highest_Bid FROM Listings LEFT JOIN Bidhistory ON Listings.Listing_id = Bidhistory.fk_Listing_id WHERE Listings.MadeBy_User_id = ? GROUP BY Listings.Listing_id"

    cur.execute(query2, (user_id,))
    Listingdata = cur.fetchall()
    print(user_id)
    print(Listingdata)




    con.close()
    return render_template("profile.html", logged_in=is_logged_in(),BidData=BidData, ListingData = Listingdata, Userdetail=Userdetail,admin_check=admin_check())


@app.route('/signup', methods=['POST', 'GET'])
def render_signup():
    """
    sign up gets the input from the user and puts it into the database people with the insert query
    :return:
    database with new user info. if there are errors with the values the user inputted it will show the errors instead
    of showing the login page when the sign up is successfull.
    """
    if request.method == 'POST':

        try:
            #puts data into the variables
            fname = request.form.get('user_F_name').title()
            lname = request.form.get('user_L_name').title()
            email = request.form.get('user_email').lower()
            pass1 = request.form.get('user_password')
            pass2 = request.form.get('user_password2')
            print("flag1")
            print(fname)
            #checks if the pass is the same
            if pass1 != pass2:
                return redirect("/signup?error=passwords+do+not+match")
            #checks length
            if len(pass1) < 8:
                return redirect("/signup?error=password+must+be+more+than+8+letters")

            if not all([fname, lname, email]):
                print("EMPTYBOXES")
                return redirect("/signup?error=Empty+boxes+Signup+failed")

            #hashes the password for security
            hashedPass = bcrypt.generate_password_hash(pass1)

            con = connect_database(DATABASE)
            cur = con.cursor()


            #checks if the email is already in use. this is so that a person can't make multiple accounts with one email
            cur.execute("SELECT COUNT(*) FROM People WHERE email = ?", (email,))
            email_exists = cur.fetchone()[0]
            print(email_exists)

            if email_exists >0:
                error='alreadyexist'
                print(email_exists)
                return render_template('signup.html', error='alreadyexist',logged_in=is_logged_in(),admin_check=admin_check())
            query_insert = ("INSERT INTO People (First_name, Last_name, Email, password) "
                            "VALUES (?, ?, ?, ?)")
            query_test = "SELECT * FROM People"

            cur.execute(query_insert, (fname, lname, email, hashedPass))
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
    :return:calls the render template function for the home.html if the details are correct. If not it renders the login with a error.This error
    is displayed on html.
    """
    if is_logged_in():
        return redirect('/')
    if request.method == 'POST':
        email = request.form.get('user_email').lower()
        password = request.form.get('user_password')
        print(email)

        con = connect_database(DATABASE)
        cur = con.cursor()
        query = "SELECT First_name, Last_name, Email, password, Person_ID, ADMIN FROM People WHERE email = ?"
        cur.execute(query, (email,))
        results = cur.fetchone()

        if results is not None:
            if not bcrypt.check_password_hash(results[3],password):
                print("hash prob")
                return render_template('login.html', error='incorrect details',logged_in=is_logged_in(),admin_check=admin_check())
            session['email'] = results[2]
            session['first_name'] = results[0]
            session['last_name'] = results[1]
            session['user_id'] = results[4]
            session['ADMIN'] = results[5]
            print(session)

            return redirect("/")
        else:
            return render_template('login.html', error='incorrect details')
    return render_template('login.html', logged_in=is_logged_in(),admin_check=admin_check())


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    """
    logs out the user. clears the session
    :return:clears the session of the info of the user.
    """
    print(session)
    session.clear()
    print(session)
    return redirect('/')

@app.route('/admin', methods=['POST', 'GET'])
def admin():
    if not admin_check():
        return redirect('/')
    """
    admin page where you can delete users. only accessible when the user passes in the admincheck function adn returns True
    
    :return: passes in data of all the users where the admin can select in the admin page html. 
    """
    con = connect_database(DATABASE)
    cur = con.cursor()
    query = "SELECT First_name, Last_name, Person_ID FROM People"
    cur.execute(query)
    Userlist = cur.fetchall()

    print(Userlist)
    con.commit()

    #Userlist list needed for the users delete
    return render_template('Admin.html', Userlist=Userlist ,logged_in=is_logged_in(), admin_check=admin_check())
@app.route('/delete_user', methods=['POST', 'GET'])
def delete_user():
    if not admin_check():
        return redirect('/')
    """
    the page after the admin selects a user in the admin page. Asks if they really want to delete the user
    for a final confirmation
    :return: the html with the submit button that deletes the user. if the user presses the button it 
    calls the function to acutally excecute the query that has the delete code. 
    """
    if request.method =='POST':
        User = request.form.get('select_user')
        print(User)
    return render_template('DeleteUserConfirm.html', DeleteUser=User ,logged_in=is_logged_in(), admin_check=admin_check())

@app.route('/deleteconfirm', methods=['POST'])
def confirm_delete_user():
    """
    THis is called when the admin selected a user to delete and confirmed that they wanted to delete
    :return: the query is excecuted and the user with the user id is deleted
    """
    if not admin_check():
        return redirect('/')
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        if user_id:
            try:
                con = connect_database(DATABASE)
                cur = con.cursor()

                # First check if this isn't the admin user (user_id 1)
                if session.get('ADMIN') == 1:
                    return redirect('/admin?error=Cannot+delete+admin+user')

                cur.execute("DELETE FROM People WHERE Person_ID = ?", (user_id,))
                con.commit()
                redirect('/')

            except Exception as e:
                print(f"Error deleting user: {str(e)}")
    return redirect('/')


if __name__ == '__main__':
    app.run()

print("WHYYYYY")
