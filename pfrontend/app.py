from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import requests
import json
from functools import wraps
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')

API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:5000/api/v1')

def make_api_request(method, endpoint, data=None, headers=None, files=None):
    url = f"{API_BASE_URL}/{endpoint}"
    default_headers = {}
    if 'access_token' in session:
        default_headers['Authorization'] = f"Bearer {session['access_token']}"
    
    if headers:
        default_headers.update(headers)
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=default_headers)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=default_headers, files=files)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=default_headers)
        elif method == 'DELETE':
            response = requests.delete(url, headers=default_headers)
        else:
            return {'success': False, 'message': 'Invalid request method'}, 400
        
        if response.status_code == 401 and 'access_token' in session:
            session.pop('access_token', None)
            session.pop('user_data', None)
            return {'success': False, 'message': 'Your session has expired. Please log in again.'}, 401
        
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return {'success': False, 'message': f"API request failed: {str(e)}"}, 500
    except json.decoder.JSONDecodeError:
        return {'success': False, 'message': "Invalid response from API"}, 500

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_data' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    response, status_code = make_api_request('GET', 'posts')
    posts = []
    if status_code == 200 and response.get('success'):
        posts = response.get('data', [])
    return render_template('home.html', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('login.html')
        
        data = {
            'username': username,
            'password': password
        }
        
        response, status_code = make_api_request('POST', 'auth/login', data)
        
        if status_code == 200 and response.get('success'):
            session['access_token'] = response['data']['access_token']
            session['refresh_token'] = response['data']['refresh_token']
            session['user_data'] = response['data']['user']
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash(response.get('message', 'Login failed. Please try again.'), 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password:
            flash('Username, email, and password are required.', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        
        data = {
            'username': username,
            'email': email,
            'password': password
        }
        
        response, status_code = make_api_request('POST', 'auth/register', data)
        
        if status_code == 201 and response.get('success'):
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash(response.get('message', 'Registration failed. Please try again.'), 'danger')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('access_token', None)
    session.pop('refresh_token', None)
    session.pop('user_data', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/news')
def news():
    response, status_code = make_api_request('GET', 'posts')
    posts = []
    if status_code == 200 and response.get('success'):
        posts = response.get('data', [])
    return render_template('news.html', posts=posts)

@app.route('/post/<int:post_id>')
def post_detail(post_id):
    response, status_code = make_api_request('GET', f'posts/{post_id}')
    post = {}
    if status_code == 200 and response.get('success'):
        post = response.get('data', {})
    return render_template('post_detail.html', post=post)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/create-post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title or not content:
            flash('Title and content are required.', 'danger')
            return render_template('create_post.html')
        
        data = {
            'title': title,
            'content': content
        }
        
        response, status_code = make_api_request('POST', 'posts', data)
        
        if status_code == 201 and response.get('success'):
            flash('Post created successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash(response.get('message', 'Failed to create post. Please try again.'), 'danger')
    
    return render_template('create_post.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001) 