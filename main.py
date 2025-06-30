from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from dotenv import load_dotenv
load_dotenv() 
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from pathlib import Path
import json
import uuid
from functools import wraps
from app.logic import check_symptoms

app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)


# Load users
USERS_FILE = Path(__file__).parent / 'users.json'

def load_users():
    try:
        with open(USERS_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return redirect(url_for('login'))
from authlib.integrations.flask_client import OAuth

# Initialize OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'email profile'},
)

@app.route('/google-login')
def google_login():
    redirect_uri = url_for('google_authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/google-authorize')
def google_authorize():
    token = google.authorize_access_token()
    user_info = google.get('userinfo').json()
    
    # Process user registration/login
    email = user_info['email']
    users = load_users()
    
    if email not in users:
        users[email] = {
            'password': None,  # Or generate a random password
            'name': user_info.get('name', 'Google User'),
            'created_at': datetime.now().isoformat()
        }
        save_users(users)
    
    session['email'] = email
    session['username'] = users[email]['name']
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        
        users = load_users()
        user = users.get(email)
        
        if user and check_password_hash(user['password'], password):
            session['email'] = email
            session['username'] = user['name']
            session.permanent = True
            return redirect(url_for('index'))
        
        return render_template('login.html', error='Invalid email or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        name = request.form.get('name', '').strip()
        
        if not all([email, password, name]):
            return render_template('register.html', error='All fields are required')
        
        users = load_users()
        if email in users:
            return render_template('register.html', error='Email already registered')
        
        users[email] = {
            'password': generate_password_hash(password),
            'name': name,
            'created_at': datetime.now().isoformat()
        }
        save_users(users)
        
        # Redirect to login page after registration
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/index')
@login_required
def index():
    return render_template('index.html', user=session.get('username'))

@app.route('/check', methods=['POST'])
@login_required
def check():
    try:
        data = request.get_json()
        symptoms = data.get("symptoms", "")
        result = check_symptoms(symptoms, session.get('username'))
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/history')
@login_required
def history():
    try:
        # Get the absolute path to userhistory.json
        base_path = Path(__file__).parent
        history_path = base_path / 'app' / 'userhistory.json'
        
        print(f"DEBUG: Looking for history file at: {history_path}")  # Debug
        
        # Initialize empty history if file doesn't exist
        if not history_path.exists():
            print("DEBUG: History file not found, creating empty history")  # Debug
            return render_template('history.html', data=[], user=session.get('username'))
            
        # Load history data
        with open(history_path, 'r') as f:
            try:
                history_data = json.load(f)
            except json.JSONDecodeError:
                print("DEBUG: Error reading history file, using empty data")  # Debug
                history_data = {}
        
        # Get current user's email from session
        user_email = session.get('email')
        print(f"DEBUG: User email from session: {user_email}")  # Debug
        
        # Get user's name from users.json to match history records
        users = load_users()
        user_name = users.get(user_email, {}).get('name', '')
        print(f"DEBUG: User name from users.json: {user_name}")  # Debug
        
        # Get user's history - check both name and email
        user_history = history_data.get(user_name, [])
        print(f"DEBUG: Found {len(user_history)} history entries")  # Debug
        
        # Sort history by timestamp (newest first)
        try:
            user_history.sort(key=lambda x: datetime.fromisoformat(x['timestamp']), reverse=True)
        except Exception as e:
            print(f"DEBUG: Error sorting history: {str(e)}")  # Debug
        
        # Format timestamps for display
        for entry in user_history:
            try:
                dt = datetime.fromisoformat(entry['timestamp'])
                entry['formatted_time'] = dt.strftime("%b %d, %Y at %I:%M %p")
            except:
                entry['formatted_time'] = "Previous"
                print(f"DEBUG: Error formatting timestamp for entry")  # Debug
        
        return render_template('history.html', 
                            data=user_history,
                            user=session.get('username'))
                            
    except Exception as e:
        print(f"ERROR: Failed to load history: {str(e)}")  # Debug
        return render_template('history.html', data=[], user=session.get('username'))
@app.before_request
def check_session():
    if request.endpoint not in ['login', 'register', 'static', 'google_login', 'google_authorize']:
        if 'email' not in session:
            return redirect(url_for('login'))

if __name__ == '__main__':
    # Create users.json if not exists
    if not USERS_FILE.exists():
        save_users({})
    app.run(debug=True)