from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from datetime import timedelta
import os
from models import db, User, Post, Category, Organization
import bcrypt
import werkzeug.security

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school_portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

db.init_app(app)
jwt = JWTManager(app)
CORS(app)

def hash_password(password):
    return werkzeug.security.generate_password_hash(password)

def verify_password(stored_password, provided_password):
    return werkzeug.security.check_password_hash(stored_password, provided_password)

@app.before_first_request
def create_tables():
    with app.app_context():
        db.create_all()

with app.app_context():
    db.create_all()
    print("Database and tables created!")

@app.route('/')
def hello():
    return jsonify({"success": True, "message": "Welcome to School Portal API", "version": "1.0"})

@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"success": False, "message": "Username and password are required"}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({"success": False, "message": "User with this username or email already exists"}), 400

    hashed_password = hash_password(data['password'])
    new_user = User(
        username=data['username'],
        password=hashed_password,
        email=data.get('email'),
        role=data.get('role', 'user')
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"success": True, "message": "User registered successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Registration failed: {str(e)}"}), 500

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"success": False, "message": "Username and password are required"}), 400

    user = User.query.filter_by(username=data['username']).first()

    if user and verify_password(user.password, data['password']):
        access_token = create_access_token(identity={"id": user.id, "username": user.username, "role": user.role})
        refresh_token = create_refresh_token(identity={"id": user.id})

        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }

        return jsonify({
            "success": True,
            "message": "Login successful",
            "data": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": 3600,
                "user": user_data
            }
        }), 200
    else:
        return jsonify({"success": False, "message": "Invalid username or password"}), 401

@app.route('/api/v1/auth/refresh', methods=['POST'])
def refresh():
    try:
        data = request.get_json()
        if not data or not data.get('refresh_token'):
            return jsonify({"success": False, "message": "Refresh token is required"}), 400

        try:
            user_id = get_jwt_identity()["id"]
            user = User.query.get(user_id)
            if not user:
                return jsonify({"success": False, "message": "User not found"}), 401

            access_token = create_access_token(identity={"id": user.id, "username": user.username, "role": user.role})
            refresh_token = create_refresh_token(identity={"id": user.id})

            return jsonify({
                "success": True,
                "message": "Token refreshed successfully",
                "data": {
                    "access_token": access_token,
                    "refresh_token": refresh_token
                }
            }), 200
        except Exception as e:
            return jsonify({"success": False, "message": f"Invalid refresh token: {str(e)}"}), 401
    except Exception as e:
        return jsonify({"success": False, "message": f"Token refresh failed: {str(e)}"}), 500

@app.route('/api/v1/auth/user', methods=['GET'])
@jwt_required()
def get_user():
    current_user = get_jwt_identity()
    user_id = current_user["id"]
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role
    }
    
    return jsonify({
        "success": True,
        "message": "User data retrieved successfully",
        "data": user_data
    }), 200

@app.route('/api/v1/posts', methods=['GET'])
def get_posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    posts_data = []
    
    for post in posts:
        posts_data.append({
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "author": post.author.username,
            "created_at": post.created_at.isoformat()
        })
    
    return jsonify({
        "success": True,
        "message": "Posts retrieved successfully",
        "data": posts_data
    }), 200

@app.route('/api/v1/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({"success": False, "message": "Post not found"}), 404
    
    post_data = {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "author": post.author.username,
        "created_at": post.created_at.isoformat()
    }
    
    return jsonify({
        "success": True,
        "message": "Post retrieved successfully",
        "data": post_data
    }), 200

@app.route('/api/v1/posts', methods=['POST'])
@jwt_required()
def create_post():
    current_user = get_jwt_identity()
    user_id = current_user["id"]
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({"success": False, "message": "Title and content are required"}), 400
    
    new_post = Post(
        title=data['title'],
        content=data['content'],
        user_id=user_id
    )
    
    try:
        db.session.add(new_post)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Post created successfully",
            "data": {
                "id": new_post.id
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Failed to create post: {str(e)}"}), 500

@app.route('/api/v1/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    current_user = get_jwt_identity()
    user_id = current_user["id"]
    user_role = current_user["role"]
    
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({"success": False, "message": "Post not found"}), 404
    
    if post.user_id != user_id and user_role != 'admin':
        return jsonify({"success": False, "message": "You don't have permission to update this post"}), 403
    
    data = request.get_json()
    
    if data.get('title'):
        post.title = data['title']
    
    if data.get('content'):
        post.content = data['content']
    
    try:
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Post updated successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Failed to update post: {str(e)}"}), 500

@app.route('/api/v1/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    current_user = get_jwt_identity()
    user_id = current_user["id"]
    user_role = current_user["role"]
    
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({"success": False, "message": "Post not found"}), 404
    
    if post.user_id != user_id and user_role != 'admin':
        return jsonify({"success": False, "message": "You don't have permission to delete this post"}), 403
    
    try:
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Post deleted successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Failed to delete post: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)