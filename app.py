from flask import Flask, render_template, session, redirect, url_for, flash
from auth_firebase import auth_bp, create_default_admin, login_required, role_required
from complaints_firebase import complaint_bp
from feedback_firebase import feedback_bp
from admin_firebase import admin_bp
from firebase_config import initialize_firebase

# Initialize Firebase
initialize_firebase()

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a random secure key in production
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # Session timeout in seconds (30 minutes)

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(complaint_bp)
app.register_blueprint(feedback_bp)
app.register_blueprint(admin_bp)

# Create default admin account
create_default_admin()

@app.route('/')
def home():
    return render_template('landingpage.html')

@app.route('/resident/dashboard')
@login_required
@role_required('resident')
def resident_dashboard():
    return render_template('residentdashboard.html', 
                          user_name=session.get('user_name', 'Resident'))

@app.route('/official/dashboard')
@login_required
@role_required('official')
def official_dashboard():
    return render_template('barangayofficialsdashboard.html',
                          user_name=session.get('user_name', 'Official'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Check if user is admin
    if session.get('user_role') != 'official' or not session.get('is_admin', False):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('home'))
    
    return render_template('admindashboard.html',
                          user_name=session.get('user_name', 'Admin'),
                          user_email=session.get('user_email', ''))

@app.route('/test-api')
def test_api():
    return render_template('test_api.html')

# Redirect routes for /login and /signup to auth blueprint
@app.route('/login')
def login_redirect():
    return redirect(url_for('auth.show_auth', form_type='login'))

@app.route('/signup')
def signup_redirect():
    return redirect(url_for('auth.show_auth', form_type='signup'))

if __name__ == '__main__':
    app.run(debug=True)