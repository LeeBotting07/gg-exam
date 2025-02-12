from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import bcrypt
import requests  # Import requests for API calls

app = Flask(__name__)
app.secret_key = '007'
# Predefined password for admin registration access
ADMIN_REGISTRATION_PASSWORD = 'admin_password'
WEATHER_API_KEY = '2998c6f8198a3fb3caeb1cd7f086653d'  # Your OpenWeatherMap API key

def get_weather_data(location):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(f"Weather API Response: {data}")  # Log the API response for debugging
        if 'main' in data and 'weather' in data:
            return data
    else:
        print(f"Error fetching weather data: {response.status_code} - {response.text}")
    return None

def get_air_quality_data(location):
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={location['lat']}&lon={location['lon']}&appid={WEATHER_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching air quality data: {response.status_code} - {response.text}")
    return None

def get_weekly_forecast(location):
    url = f"http://api.openweathermap.org/data/2.5/forecast/daily?q={location}&cnt=7&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching weekly forecast: {response.status_code} - {response.text}")
        return None

# Routes
@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html', title="Home")

@app.route('/today', methods=['GET', 'POST'])
def today():
    weather_data = None
    air_quality_data = None
    location = None  # Initialize location variable
    
    if request.method == 'POST':
        location = request.form.get('country')  # Get the country from the form
        if location:
            weather_data = get_weather_data(location)
            if weather_data:
                # Get air quality data using the coordinates from weather data
                coords = {'lat': weather_data['coord']['lat'], 'lon': weather_data['coord']['lon']}
                air_quality_data = get_air_quality_data(coords)

    return render_template('today.html', 
                         title="Today's Weather", 
                         weather=weather_data, 
                         air_quality=air_quality_data,
                         location=location)

@app.route('/week', methods=['GET', 'POST'])
def week():
    location = request.form.get('location', 'England')  
    forecast_data = get_weekly_forecast(location)
    return render_template('week.html', title="This Week's Weather", forecast=forecast_data)

@app.route('/about')
def about():
    return render_template('about.html', title="About Us")

@app.route('/contact')
def contact():
    return render_template('contact.html', title="Contact Us")

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html', title="Login")

@app.route('/customer-login', methods=['GET', 'POST'])
def customer_login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if '@admin' in email:
            flash("Admin accounts cannot log in here.", 'error')
            return redirect(url_for('admin_login'))
        
        try:
            with sqlite3.connect("weather.db") as con:
                cur = con.cursor()
                cur.execute("SELECT password, role FROM users WHERE email = ?", (email,))
                data = cur.fetchone()
                if data and bcrypt.checkpw(password.encode('utf-8'), data[0]):
                    session['email'] = email
                    session['role'] = data[1]
                    return redirect(url_for('account'))
                else:
                    flash("Invalid username or password", 'error')
        except sqlite3.Error as e:
            flash(f"Database error: {e}", 'error')
    return render_template('customer-login.html', title="Customer Login", error=error)

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if '@admin' not in email:
            flash("Only admin accounts can log in here.", 'error')
            return redirect(url_for('customer_login'))

        try:
            with sqlite3.connect("weather.db") as con:
                cur = con.cursor()
                cur.execute("SELECT password, role FROM users WHERE email = ?", (email,))
                data = cur.fetchone()

                if data:
                    hashed_password, role = data
                    if bcrypt.checkpw(password.encode('utf-8'), hashed_password) and role.lower() == 'admin':
                        session['email'] = email
                        session['role'] = role
                        con.commit()
                        return redirect(url_for('admin_panel'))
                    else:
                        flash("Invalid email or password", 'error')
                else:
                    flash("Invalid email or password", 'error')
        except sqlite3.Error as e:
            flash(f"Database error: {e}", 'error')

    return render_template('admin-login.html', title="Admin Login", error=error)

@app.route('/admin-register', methods=['GET', 'POST'])
def admin_register():
    error = None
    if request.method == 'GET':
        return render_template('admin-register.html', title='Admin Registration', error="Please provide the access password.")
    
    access_password = request.form.get('access_password')
    username = request.form.get('username')
    firstname = request.form.get('first_name')  
    lastname = request.form.get('last_name')    
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if access_password != ADMIN_REGISTRATION_PASSWORD:
        flash("Incorrect password to access admin registration.", 'error')
    elif password != confirm_password:
        flash("Passwords do not match.", 'error')
    elif '@' not in email or '.' not in email.split('@')[-1]:
        flash("Invalid email format.", 'error')
    elif len(password) < 8:
        flash("Password must be at least 8 characters long.", 'error')
    elif '@admin' not in email:
        flash("Admin accounts must have admin after the '@' symbol.", 'error')
    elif not username:  # Check if username is provided
        flash("Username is required.", 'error')
    elif not firstname:  # Check if first name is provided
        flash("First name is required.", 'error')
    elif not lastname:  # Check if last name is provided
        flash("Last name is required.", 'error')
    else:
        try:
            with sqlite3.connect("weather.db") as con:
                cur = con.cursor()
                cur.execute("SELECT email FROM users WHERE email = ?", (email,))
                if cur.fetchone():
                    flash("Email already registered.", 'error')
                else:
                    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                    cur.execute("INSERT INTO users (username, firstname, lastname, email, password, role) VALUES (?, ?, ?, ?, ?, ?) ",
                                (username, firstname, lastname, email, hashed_password, 'admin'))
                    con.commit()
                    flash("Admin account created successfully. Please log in.", 'success')
                    return redirect(url_for('admin_login'))
        except sqlite3.Error as e:
            flash(f"Database error: {e}", 'error')

    return render_template('admin-register.html', title='Admin Registration', error=error)

@app.route('/customer-register', methods=['GET', 'POST'])
def customer_register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']  
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match.", 'error')
        elif '@' not in email or '.' not in email.split('@')[-1]:
            flash("Invalid email format.", 'error')
        elif len(password) < 8:
            flash("Password must be at least 8 characters long.", 'error')
        else:
            try:
                with sqlite3.connect("weather.db") as con:
                    cur = con.cursor()
                    cur.execute("SELECT email FROM users WHERE email = ?", (email,))
                    if cur.fetchone():
                        flash("Email already registered.", 'error')
                    else:
                        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                        cur.execute("INSERT INTO users (username, firstname, lastname, email, password, role) VALUES (?, ?, ?, ?, ?, ?) ",
                                    (username, first_name, last_name, email, hashed_password, 'customer'))
                        con.commit()
                        flash("Customer account created successfully. Please log in.", 'success')
                        return redirect(url_for('customer_login'))
            except sqlite3.Error as e:
                flash(f"Database error: {e}", 'error')

    return render_template('customer-register.html', title='Customer Registration', error=error)

# Logout route
@app.route('/logout')
def logout():
    session.clear()  # Clear the session
    flash("You have been logged out.", 'success')
    return redirect(url_for('home'))

# Account route
@app.route('/account', methods=['GET', 'POST'])
def account():
    if 'email' not in session:
        flash("You need to log in first.", 'error')
        return redirect(url_for('customer_login'))

    email = session['email']

    try:
        with sqlite3.connect("weather.db") as con:
            cur = con.cursor()
            cur.execute("SELECT username, firstname, lastname, email FROM users WHERE email = ?", (email,))
            user = cur.fetchone()
            if user:
                return render_template('account.html', title="Account", user=user, email=email, user_data={
                    'role': session.get('role', 'customer'),
                    'phoneNumber': 'Not provided',  
                    'address': 'Not provided'
                })
            else:
                flash("User not found.", 'error')
                return redirect(url_for('customer_login'))
    except sqlite3.Error as e:
        flash(f"Database error: {e}", 'error')
        return redirect(url_for('home'))

@app.route('/admin-panel')
def admin_panel():
    if 'email' not in session or session['role'].lower() != 'admin':
        flash("You need to login as admin first.", 'error')
        return redirect(url_for('admin_login'))
    return render_template('admin-panel.html', title="Admin Panel")

if __name__ == '__main__':
    app.run(debug=True)
