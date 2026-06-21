from flask import Flask, render_template, request, redirect, session

import mysql.connector

from dotenv import load_dotenv
import os

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = conn.cursor()

app = Flask(__name__)
app.secret_key = 'skyfly_secret_key'

@app.route('/')
def home():

    welcome = session.pop('welcome', False)

    cursor.execute("SELECT COUNT(*) FROM passengers")
    total_bookings = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users where username != 'admin'")
    total_users = cursor.fetchone()[0]

    return render_template(
        'index.html',
        welcome=welcome,
        total_bookings=total_bookings,
        total_users=total_users
    )

@app.route('/book', methods=['GET', 'POST'])
def book():

    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':

        name = request.form['name']
        source = request.form['source']
        destination = request.form['destination']
        journey_date = request.form['journey_date']

        sql = """
        INSERT INTO passengers
        (name, source, destination, journey_date)
        VALUES (%s, %s, %s, %s)
        """

        values = (
            name,
            source,
            destination,
            journey_date
        )

        cursor.execute(sql, values)
        conn.commit()

        print("Booking Saved Successfully")
        
        session['booking_success'] = True

        return redirect('/bookings')
    
    return render_template('book_ticket.html')

@app.route('/bookings')
def bookings():

    if 'user_id' not in session:
     return redirect('/login')

    cursor.execute("SELECT * FROM passengers")
    data = cursor.fetchall()

    success = session.pop('booking_success', False)

    return render_template(
     'bookings.html',
      passengers=data,
     success=success
    )

@app.route('/ticket/<int:id>')
def ticket(id):

    if 'user_id' not in session:
        return redirect('/login')

    cursor.execute(
        "SELECT * FROM passengers WHERE passenger_id=%s",
        (id,)
    )

    passenger = cursor.fetchone()

    return render_template(
        'ticket.html',
        passenger=passenger
    )

@app.route('/delete/<int:id>')
def delete_booking(id):

    if not session.get('is_admin'):
        return render_template('access_denied.html')
    
    if id == session['user_id']:
     return "You cannot delete your own account."

    cursor.execute(
        "DELETE FROM passengers WHERE passenger_id = %s",
        (id,)
    )

    conn.commit()

    return redirect('/bookings')

@app.route('/signup', methods=['GET','POST'])
def signup():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        sql = """
        INSERT INTO users
        (username,password)
        VALUES(%s,%s)
        """

        cursor.execute(
            sql,
            (username,password)
        )

        conn.commit()

        return redirect('/login')

    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        cursor.execute(
            """
            SELECT * FROM users
            WHERE username=%s
            AND password=%s
            """,
            (username,password)
        )

        user = cursor.fetchone()

        if user:

            session['user_id'] = user[0]
            session['username'] = user[1]

            if user[1] == "admin":
                session['is_admin'] = True
            else:
                session['is_admin'] = False

            session['welcome'] = True
            return redirect('/')

        else:

            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')


@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')

@app.route('/users')
def users():

    if 'user_id' not in session:
        return redirect('/login')

    if not session.get('is_admin'):
        return render_template('access_denied.html')

    cursor.execute("SELECT * FROM users")
    data = cursor.fetchall()

    return render_template(
        'users.html',
        users=data
    )

@app.route('/delete-user/<int:id>')
def delete_user(id):

    if not session.get('is_admin'):
        return render_template('access_denied.html')

    cursor.execute(
        "DELETE FROM users WHERE user_id=%s",
        (id,)
    )

    conn.commit()

    return redirect('/users')

@app.route('/forgot-password')
def forgot_password():
    return "Feature Coming Soon"


if __name__ == '__main__':
    app.run(debug=True)

