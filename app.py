from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response
from werkzeug.security import generate_password_hash, check_password_hash
from drowsiness import generate_frames
from threading import Event
import sqlite3

app = Flask(__name__)
app.secret_key = '608a049abdf8d90355ecfadcedf79b97178fafac8f37f17b0389c2a7aafa4c8c'

# SQLite database file path
DB_PATH = 'users.db'

# Event for controlling the video stream
stream_event = Event()

# To hold model status
model_result = {"status": "Awake"}  # Default to "Awake"


def init_db():
    """Initialize the SQLite database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL,
                            email TEXT NOT NULL)''')
        conn.commit()


# Initialize the database if not already done
init_db()


def get_user_by_username(username):
    """Fetch a user from the database by username."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        return user


def add_user(username, password, email):
    """Add a new user to the database."""
    hashed_password = generate_password_hash(password)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                       (username, hashed_password, email))
        conn.commit()


def delete_user(username):
    """Delete a user from the database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username=?", (username,))
        conn.commit()


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_by_username(username)
        if user and check_password_hash(user[2], password):  # user[2] is password
            session['username'] = username
            if username == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        flash('Invalid credentials. Please try again.')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if 'username' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'create_user' in request.form:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            if get_user_by_username(username):
                flash('User already exists.')
            else:
                add_user(username, password, email)
                flash('User created successfully!')
        elif 'delete_user' in request.form:
            username = request.form['delete_user']
            if username != 'admin' and get_user_by_username(username):
                delete_user(username)
                flash('User deleted successfully.')
            else:
                flash('Cannot delete this user.')

    # Fetch all users from the database
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()

    # Pass the 'users' variable to the template
    return render_template('admin_dashboard.html', users=users)

@app.route('/user')
def user_dashboard():
    if 'username' in session:
        return render_template('user_dashboard.html', username=session['username'])
    return redirect(url_for('login'))


EYE_AR_THRESH = 0.3  # Default threshold (global variable)

@app.route('/update_threshold', methods=['POST'])
def update_threshold():
    global EYE_AR_THRESH
    data = request.get_json()
    if 'threshold' in data:
        EYE_AR_THRESH = data['threshold']
        return jsonify({"status": "Threshold updated", "threshold": EYE_AR_THRESH}), 200
    else:
        return jsonify({"error": "Invalid data"}), 400


@app.route('/get_model_status')
def get_model_status():
    global model_result
    return jsonify(model_result)


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(stream_event, model_result), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/start_camera', methods=['POST'])
def start_camera():
    stream_event.set()  # Set the stream event to start video generation
    return jsonify({"status": "Camera started"})


@app.route('/stop_camera', methods=['POST'])
def stop_camera():
    stream_event.clear()
    model_result["status"] = "Awake"  # Reset the status
    return jsonify({"status": "Camera stopped"})


if __name__ == '__main__':
    app.run(debug=True)
