from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from functools import wraps
from datetime import datetime, timedelta

# Load environment variables from .env
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_secret_key')

# MongoDB setup
mongo_uri = os.getenv("MONGO_URI")
try:
    client = MongoClient(mongo_uri)
    db = client['campusApp']
    users = db['users']
    activities = db['activities']
    events = db['events']  # Add this line to define the 'events' collection
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    # Graceful error handling: you can render an error page instead of exiting
    @app.route("/error")
    def error():
        return render_template('error.html', message="Database connection failed. Please try again later.")
    exit(1)

# Set session lifetime
app.permanent_session_lifetime = timedelta(minutes=30)  # Session timeout in minutes

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("You need to log in first.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Log activity function
def log_activity(action, user_name, role):
    activities.insert_one({
        'user_name': user_name,
        'role': role,
        'action': action,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

# Routes
@app.route('/')
def home():
    # If no user is logged in, redirect to the login page
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user' not in session or session['user']['role'] != 'admin':
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        existing_user = users.find_one({'email': email})
        if existing_user:
            flash('User already exists with this email.')
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)
        users.insert_one({
            'name': name,
            'email': email,
            'password': hashed_password,
            'role': role
        })

        # Log the activity
        log_activity('Registered a new user', name, role)
        return redirect(url_for('admin_dashboard'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = users.find_one({'email': email})
        if user and check_password_hash(user['password'], password):
            session.permanent = True  # Make session permanent to apply session timeout
            session['user'] = {
                'email': user['email'],
                'role': user['role'],
                'name': user['name']
            }
            return redirect(url_for(f"{user['role']}_dashboard"))  # Correct redirection to role dashboard

        flash('Invalid email or password.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if session['user']['role'] != 'admin':  # Ensure the user is an admin
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    # Fetch recent activities from the database
    activities_list = activities.find().sort('timestamp', -1).limit(5)

    return render_template('admin_dashboard.html', activities=activities_list)

@app.route('/student_dashboard')
@login_required
def student_dashboard():
    if session['user']['role'] in ['student', 'admin']:
        return render_template('student_dashboard.html')

    flash("Unauthorized access.")
    return redirect(url_for('login'))

@app.route('/faculty_dashboard')
@login_required
def faculty_dashboard():
    if session['user']['role'] in ['faculty', 'admin']:
        return render_template('faculty_dashboard.html')

    flash("Unauthorized access.")
    return redirect(url_for('login'))

@app.route('/staff_dashboard')
@login_required
def staff_dashboard():
    if session['user']['role'] not in ['staff', 'admin']:
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    events_list = list(events.find().sort("timestamp", -1))
    notifications_list = list(activities.find().sort("timestamp", -1))

    return render_template('staff_dashboard.html', events=events_list, notifications=notifications_list)

@app.route('/view_users', methods=['GET'])
@login_required
def view_users():
    if session['user']['role'] != 'admin':
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    search_query = request.args.get('search', '')
    if search_query:
        users_data = users.find({
            '$or': [
                {'name': {'$regex': search_query, '$options': 'i'}},
                {'email': {'$regex': search_query, '$options': 'i'}}
            ]
        })
    else:
        users_data = users.find()

    return render_template('view_users.html', users=users_data)

@app.route('/create_event', methods=['POST'])
@login_required
def create_event():
    if session['user']['role'] != 'staff':  # Only staff can create events
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    title = request.form['title']
    date = request.form['date']
    event_type = request.form['event_type']

    if title and date:
        # Save the event to the database
        events.insert_one({
            'title': title,
            'date': date,
            'event_type': event_type,
            'created_by': session['user']['name'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        log_activity('Created a new event', session['user']['name'], session['user']['role'])

    return redirect(url_for('staff_dashboard'))

@app.route('/send_notification', methods=['POST'])
@login_required
def send_notification():
    if session['user']['role'] != 'staff':  # Only staff can send notifications
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    notification_text = request.form['notification_text']

    if notification_text:
        # Save the notification to the database
        activities.insert_one({
            'user_name': session['user']['name'],
            'role': session['user']['role'],
            'action': f'Sent Notification: {notification_text}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        log_activity('Sent a notification', session['user']['name'], session['user']['role'])

    return redirect(url_for('staff_dashboard'))

@app.route('/get_events', methods=['GET'])
@login_required
def get_events():
    # Retrieve events from the database
    events_data = list(events.find().sort('timestamp', -1))  # Sort by timestamp in descending order
    return events_data

@app.route('/get_notifications', methods=['GET'])
@login_required
def get_notifications():
    # Retrieve the last notification from the database
    last_notification = activities.find().sort('timestamp', -1).limit(1)
    return list(last_notification)

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port=5000, debug=True)
