#!/usr/bin/env python3

import os
import sys
import requests
import argparse
import getpass
import json
from dotenv import load_dotenv

load_dotenv()

API_URL = os.environ.get('API_URL', 'http://localhost:5000/api/v1')

def create_admin_user(username, email, password, api_url=API_URL):
    """
    Create an admin user using the API
    """
    print("\n==== Creating Admin User ====")
    print(f"Username: {username}")
    print(f"Email: {email}")
    print(f"API URL: {api_url}")
    
    data = {
        'username': username,
        'email': email,
        'password': password,
        'role': 'admin'  
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        register_url = f"{api_url}/auth/register"
        print(f"\nSending request to: {register_url}")
        
        response = requests.post(
            register_url, 
            data=json.dumps(data),
            headers=headers
        )
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            if result.get('success'):
                print("\n✅ Admin user created successfully!")
                print(f"Username: {username}")
                print(f"Role: admin")
                return True
            else:
                print(f"\n❌ Failed to create admin user: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"\n❌ API request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error connecting to API: {str(e)}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return False

def validate_input(username, email, password):
    """Validate user input fields"""
    errors = []
    
    if not username or len(username) < 3:
        errors.append("Username must be at least 3 characters long")
    
    if not email or '@' not in email:
        errors.append("Please provide a valid email address")
    
    if not password or len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    return errors

def main():
    """Main function to create an admin user"""
    parser = argparse.ArgumentParser(description='Create an admin user for the School Portal')
    parser.add_argument('--username', help='Admin username')
    parser.add_argument('--email', help='Admin email')
    parser.add_argument('--password', help='Admin password')
    parser.add_argument('--api-url', help=f'API URL (default: {API_URL})')
    
    args = parser.parse_args()
    
    username = args.username
    if not username:
        username = input("Enter admin username: ")
    
    email = args.email
    if not email:
        email = input("Enter admin email: ")
    
    password = args.password
    if not password:
        password = getpass.getpass("Enter admin password: ")
        password_confirm = getpass.getpass("Confirm admin password: ")
        
        if password != password_confirm:
            print("❌ Passwords do not match!")
            return 1
    
    api_url = args.api_url or API_URL
    
    errors = validate_input(username, email, password)
    if errors:
        print("\n❌ Validation errors:")
        for error in errors:
            print(f"  - {error}")
        return 1
    
    success = create_admin_user(username, email, password, api_url)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 