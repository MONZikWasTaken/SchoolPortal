from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# API URL
API_URL = os.environ.get('API_URL', 'http://localhost:5000/api/v1')

# Context processors
@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

# Utility functions for API requests
def api_request(method, endpoint, data=None, token=None):
    """Make a request to the API with proper headers and error handling"""
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    url = f"{API_URL}/{endpoint}"
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            return {'success': False, 'message': 'Invalid method'}
        
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'success': False, 'message': f'API request failed: {str(e)}'}

# Authentication middleware
def is_logged_in():
    """Check if user is logged in"""
    return 'token' in session and 'user' in session

# Routes
@app.route('/')
def home():
    # Get latest posts from API
    response = api_request('GET', 'posts')
    posts = response.get('data', []) if response.get('success') else []
    
    return render_template('home.html', posts=posts, is_logged_in=is_logged_in(), user=session.get('user'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('home'))
    
    error = None
    if request.method == 'POST':
        data = {
            'username': request.form.get('username'),
            'password': request.form.get('password')
        }
        
        response = api_request('POST', 'auth/login', data)
        
        if response.get('success'):
            # Store tokens and user data in session
            session['token'] = response['data']['access_token']
            session['refresh_token'] = response['data']['refresh_token']
            session['user'] = response['data']['user']
            
            return redirect(url_for('profile'))
        else:
            error = response.get('message', 'Login failed')
    
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if is_logged_in():
        return redirect(url_for('home'))
    
    error = None
    success = None
    
    if request.method == 'POST':
        data = {
            'username': request.form.get('username'),
            'password': request.form.get('password'),
            'email': request.form.get('email'),
            'role': request.form.get('role', 'user')
        }
        
        response = api_request('POST', 'auth/register', data)
        
        if response.get('success'):
            success = 'Registration successful! You can now log in.'
        else:
            error = response.get('message', 'Registration failed')
    
    return render_template('register.html', error=error, success=success)

@app.route('/logout')
def logout():
    # Clear session data
    session.pop('token', None)
    session.pop('refresh_token', None)
    session.pop('user', None)
    
    return redirect(url_for('home'))

@app.route('/profile')
def profile():
    if not is_logged_in():
        return redirect(url_for('login'))
    
    # Get user's posts if they have any
    user_id = session['user']['id']
    user_posts = []
    
    # TODO: Implement endpoint to get user's posts
    
    return render_template('profile.html', user=session.get('user'), posts=user_posts)

@app.route('/news')
def news():
    # Get all posts from API
    response = api_request('GET', 'posts')
    posts = response.get('data', []) if response.get('success') else []
    
    return render_template('news.html', posts=posts, is_logged_in=is_logged_in(), user=session.get('user'))

@app.route('/news/<int:post_id>')
def post_details(post_id):
    # Get specific post from API
    response = api_request('GET', f'posts/{post_id}')
    
    if not response.get('success'):
        flash('Post not found', 'error')
        return redirect(url_for('news'))
    
    post = response.get('data')
    
    return render_template('post_details.html', post=post, is_logged_in=is_logged_in(), user=session.get('user'))

@app.route('/about')
def about():
    return render_template('about.html', is_logged_in=is_logged_in(), user=session.get('user'))

@app.route('/contact')
def contact():
    return render_template('contact.html', is_logged_in=is_logged_in(), user=session.get('user'))

@app.route('/create-post', methods=['GET', 'POST'])
def create_post():
    if not is_logged_in():
        return redirect(url_for('login'))
    
    # Check if user has permission to create posts
    user_role = session['user']['role']
    if user_role not in ['admin', 'organization']:
        flash('You do not have permission to create posts', 'error')
        return redirect(url_for('home'))
    
    error = None
    
    if request.method == 'POST':
        data = {
            'title': request.form.get('title'),
            'content': request.form.get('content')
        }
        
        response = api_request('POST', 'posts', data, session['token'])
        
        if response.get('success'):
            flash('Post created successfully', 'success')
            return redirect(url_for('news'))
        else:
            error = response.get('message', 'Failed to create post')
    
    return render_template('create_post.html', error=error, is_logged_in=is_logged_in(), user=session.get('user'))

# Run the application
if __name__ == '__main__':
    app.run(debug=True, port=5001) 