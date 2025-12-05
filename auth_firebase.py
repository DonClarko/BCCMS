from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import json
import os
from datetime import datetime
from functools import wraps
from firebase_admin import auth as firebase_auth, db, exceptions
from firebase_config import initialize_firebase, get_users_db

initialize_firebase()

auth_bp = Blueprint('auth', __name__)

def create_default_admin():
    """Create default admin account in Firebase"""
    try:
        admin_email = 'admin01-barangay@gmail.com'
        admin_password = 'admin123'
        
        # Try to get existing admin user
        try:
            user = firebase_auth.get_user_by_email(admin_email)
            print(f"Admin user already exists: {user.uid}")
        except firebase_auth.UserNotFoundError:
            # Create new admin user
            user = firebase_auth.create_user(
                email=admin_email,
                password=admin_password,
                display_name='Barangay Admin'
            )
            print(f"Admin user created: {user.uid}")
        
        # Store/update admin user data in Realtime Database
        admin_ref = db.reference(f'users/{user.uid}')
        admin_data = {
            'full_name': 'Barangay Admin',
            'email': admin_email,
            'phone': '09123456789',
            'role': 'official',
            'created_at': datetime.now().isoformat(),
            'is_admin': True
        }
        
        admin_ref.set(admin_data)
        print("✓ Default admin account ready!")
        
    except Exception as e:
        print(f"Admin setup note: {str(e)}")

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('auth.show_auth', form_type='login'))
        return f(*args, **kwargs)
    return decorated_function

# Role required decorator
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_email' not in session:
                flash('Please login to access this page', 'error')
                return redirect(url_for('auth.show_auth', form_type='login'))
            
            user_uid = session.get('user_uid')
            
            if user_uid:
                user_ref = db.reference(f'users/{user_uid}')
                user = user_ref.get()
                
                if not user or user.get('role') != role:
                    flash(f'Access denied. This page is only for {role}s', 'error')
                    return redirect(url_for('home'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/<form_type>')
def show_auth(form_type):
    """Show authentication form"""
    if form_type not in ['login', 'signup']:
        form_type = 'login'
    return render_template('auth.html', form_type=form_type)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle user login with Firebase"""
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'resident')
        
        # Authenticate with Firebase
        user = firebase_auth.get_user_by_email(email)
        
        # Get user data from Realtime Database using direct reference
        users_ref = db.reference(f'users/{user.uid}')
        user_info = users_ref.get()
        
        if not user_info:
            flash('User profile not found', 'error')
            return redirect(url_for('auth.show_auth', form_type='login'))
        
        # Check if official account is pending approval
        if user_info.get('role') == 'official' and user_info.get('status') == 'pending_approval':
            flash('Your account is pending admin approval. Please wait for confirmation.', 'warning')
            return redirect(url_for('auth.show_auth', form_type='login'))
        
        # Check if account was rejected
        if user_info.get('status') == 'rejected':
            flash('Your registration was not approved. Please contact the admin for more information.', 'error')
            return redirect(url_for('auth.show_auth', form_type='login'))
        
        # Check role
        if user_info.get('role') != role and not user_info.get('is_admin', False):
            flash(f'Please login as {user_info["role"]}', 'error')
            return redirect(url_for('auth.show_auth', form_type='login'))
        
        # Store user info in session
        session['user_email'] = email
        session['user_uid'] = user.uid
        session['user_role'] = user_info.get('role')
        session['user_name'] = user_info.get('full_name')
        session['is_admin'] = user_info.get('is_admin', False)
        
        flash('Login successful!', 'success')
        
        # Redirect based on role
        if user_info.get('is_admin', False):
            return redirect(url_for('admin_dashboard'))
        elif role == 'resident':
            return redirect(url_for('resident_dashboard'))
        else:
            return redirect(url_for('official_dashboard'))
        
    except firebase_auth.UserNotFoundError:
        flash('Invalid email or password', 'error')
        return redirect(url_for('auth.show_auth', form_type='login'))
    except Exception as e:
        flash(f'Login failed: {str(e)}', 'error')
        return redirect(url_for('auth.show_auth', form_type='login'))

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Handle user registration with Firebase"""
    try:
        full_name = request.form.get('fullName')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')
        role = request.form.get('role', 'resident')
        
        # Validate inputs
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('auth.show_auth', form_type='signup'))
        
        if len(password) < 8:
            flash('Password must be at least 8 characters', 'error')
            return redirect(url_for('auth.show_auth', form_type='signup'))
        
        # Create user in Firebase Authentication
        user = firebase_auth.create_user(
            email=email,
            password=password,
            display_name=full_name
        )
        
        # Store additional user data in Realtime Database
        user_ref = db.reference(f'users/{user.uid}')
        user_data = {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'role': role,
            'created_at': datetime.now().isoformat()
        }
        
        # If signing up as official, set status to pending approval
        if role == 'official':
            user_data['status'] = 'pending_approval'
            user_ref.set(user_data)
            flash('Registration submitted! Please wait for admin approval before you can login.', 'info')
        else:
            user_data['status'] = 'approved'
            user_ref.set(user_data)
            flash('Account created successfully! Please login.', 'success')
        
        return redirect(url_for('auth.show_auth', form_type='login'))
        
    except firebase_auth.EmailAlreadyExistsError:
        flash('Email already exists', 'error')
        return redirect(url_for('auth.show_auth', form_type='signup'))
    except Exception as e:
        flash(f'Signup failed: {str(e)}', 'error')
        return redirect(url_for('auth.show_auth', form_type='signup'))

@auth_bp.route('/logout')
def logout():
    """Handle user logout"""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))
