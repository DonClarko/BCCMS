# BCCMS - Barangay Complaint and Complaint Management System

A modern web-based platform for residents to submit complaints and receive feedback about barangay (neighborhood) issues. This system streamlines communication between residents and barangay officials, enabling efficient complaint management and resolution tracking.

---

## 📋 Table of Contents

- [Features](#features)
- [Technologies Used](#technologies-used)
- [System Architecture](#system-architecture)
- [Installation & Setup](#installation--setup)
- [Usage Guide](#usage-guide)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [User Roles](#user-roles)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

### Core Features

1. **User Authentication & Authorization**
   - User registration and login with Firebase Authentication
   - Role-based access control (Resident, Barangay Official, Admin)
   - Session management with automatic timeout (30 minutes)
   - Default admin account setup

2. **Complaint Management**
   - Submit complaints with category, location, and incident date
   - Real-time complaint tracking and status updates
   - Automatic urgency calculation based on complaint category
   - Resolution time estimation
   - Complaint history and tracking
   - Server-Sent Events (SSE) for real-time updates

3. **Feedback System**
   - Rate complaints on satisfaction (1-5 stars)
   - Provide feedback on barangay services
   - Optional contact details for follow-up
   - Feedback status tracking

4. **Admin Dashboard**
   - View all complaints and their status
   - Manage complaint resolution and updates
   - View user feedback and ratings
   - User management capabilities
   - System statistics and analytics

5. **Official Dashboard**
   - Receive notifications about new complaints
   - Manage complaints assigned to them
   - Update complaint status and resolution
   - Communicate with residents

6. **Resident Dashboard**
   - Submit new complaints
   - Track complaint status
   - View resolution timeline
   - Provide feedback on services

---

## 🛠 Technologies Used

### Backend
- **Python 3.8+** - Programming language
- **Flask 2.3.3** - Web framework for building routes and server
- **Werkzeug 2.3.7** - WSGI utility library
- **firebase-admin 6.2.0** - Firebase Admin SDK for server-side integration
- **google-cloud-firestore 2.21.0** - Cloud Firestore database
- **Gunicorn 21.2.0** - Production WSGI HTTP Server

### Frontend
- **HTML5** - Markup structure
- **CSS3** - Styling and layouts
- **JavaScript (Vanilla)** - Client-side interactions
- **Firebase Web SDK** - Client-side authentication

### Cloud & Database
- **Firebase Authentication** - User authentication and session management
- **Cloud Firestore** - NoSQL document database

### Deployment
- **Vercel** - Serverless deployment (vercel.json)
- **Render** - Alternative deployment platform (render.yaml)
- **Gunicorn** - Production server

---

## 🏗 System Architecture

```
┌─────────────────┐
│   Frontend      │
│ (HTML/CSS/JS)   │
└────────┬────────┘
         │
    ┌────▼────────────────────────┐
    │    Flask Application         │
    │  (Python Backend)            │
    └────┬───────────────────┬─────┘
         │                   │
    ┌────▼──────┐      ┌────▼────────────┐
    │ Firebase   │      │ Firestore       │
    │ Auth       │      │ Database        │
    └───────────┘      └─────────────────┘
```

### Data Flow
1. User accesses the application through the web interface
2. Authentication requests go through Firebase Authentication
3. Complaint and feedback data are stored in Cloud Firestore
4. Real-time updates are pushed to clients via Server-Sent Events
5. Admin can view all data through the admin dashboard

---

## 📦 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Firebase account (free tier available)
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/DonClarko/BCCMS.git
cd BCCMS
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Firebase Setup

#### Option A: Automated Setup (Recommended)
Follow the detailed guide in [FIREBASE_SETUP.md](FIREBASE_SETUP.md)

#### Option B: Manual Setup
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project named "BCCMS"
3. Enable Authentication, Firestore, and Cloud Messaging services
4. Download service account key as JSON
5. Save as `firebase-key.json` in project root
6. Add Firebase web config to `static/js/firebaseConfig.js`

### Step 5: Environment Variables
Create a `.env` file in the project root:
```
SECRET_KEY=your-secret-key-here
FIREBASE_KEY_PATH=firebase-key.json
PORT=5000
```

### Step 6: Run the Application
```bash
# Development
python app.py

# Production with Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 app:application
```

Access the application at: `http://localhost:5000`

---

## 👤 User Roles

### 1. Resident
- Submit complaints about barangay issues
- Track complaint status
- Provide feedback on services
- View complaint history

### 2. Barangay Official
- Receive complaint notifications
- Manage and resolve complaints
- Update complaint status
- View feedback and ratings

### 3. Admin
- Full system access
- User management
- Complaint and feedback monitoring
- System configuration

**Default Admin Credentials:**
- Email: `admin01-barangay@gmail.com`
- Password: `admin123`

---

## 📖 Usage Guide

### For Residents

1. **Sign Up**
   - Click "Sign Up" on landing page
   - Enter full name, phone, email, and password
   - Select role as "Resident"
   - Click "Create Account"

2. **Submit Complaint**
   - Go to Resident Dashboard
   - Click "Submit Complaint"
   - Fill in:
     - Title (brief description)
     - Category (Security, Emergency, Waste, Road, Water, Other)
     - Description (detailed explanation)
     - Location (where the issue occurred)
     - Incident Date
   - Click "Submit"

3. **Track Complaint**
   - View complaint ID (e.g., BCMS-2024-abc12345)
   - Check status: Pending → In Progress → Resolved
   - View estimated resolution time

4. **Provide Feedback**
   - After complaint is resolved
   - Rate satisfaction (1-5 stars)
   - Select feedback type (Praise, Suggestion, Complaint)
   - Add optional message
   - Provide contact details if you want follow-up

### For Barangay Officials

1. **Login**
   - Enter official email and password
   - Receive automatic role assignment

2. **View Complaints**
   - Go to Official Dashboard
   - View all pending and in-progress complaints
   - See urgency levels and estimated resolution times

3. **Update Complaint**
   - Click complaint details
   - Change status (Pending → In Progress → Resolved)
   - Add update notes
   - Notify residents of changes

4. **Monitor Feedback**
   - View resident feedback ratings
   - Read suggestions and comments
   - Improve services based on feedback

### For Admin

1. **Access Admin Dashboard**
   - Login with admin credentials
   - Go to `/admin/dashboard`

2. **System Management**
   - View all users and their roles
   - Monitor all complaints system-wide
   - Review feedback analytics
   - Generate reports

3. **User Management**
   - Approve or reject user accounts
   - Assign roles to officials
   - Manage admin privileges

---

## 🗂 Project Structure

```
BCCMS/
├── app.py                          # Main Flask application
├── auth_firebase.py                # Authentication logic
├── complaints_firebase.py          # Complaint management
├── feedback_firebase.py            # Feedback system
├── admin_firebase.py               # Admin features
├── firebase_config.py              # Firebase initialization
├── requirements.txt                # Python dependencies
├── firebase-key.json               # Firebase service account (don't commit!)
├── FIREBASE_SETUP.md              # Firebase setup guide
├── SETUP_COMPLETE.md              # Setup verification
│
├── templates/                      # HTML templates
│   ├── landingpage.html           # Homepage
│   ├── auth.html                  # Login/Signup form
│   ├── residentdashboard.html    # Resident interface
│   ├── barangayofficialsdashboard.html  # Official interface
│   ├── admindashboard.html        # Admin interface
│   └── test_api.html              # API testing page
│
├── static/                        # Static files
│   ├── css/                       # Stylesheets
│   │   ├── landingpage.css
│   │   ├── auth.css
│   │   ├── residentdashboard.css
│   │   ├── barangayofficialsdashboard.css
│   │   └── admindashboard.css
│   └── js/                        # JavaScript files
│       ├── firebaseConfig.js      # Firebase client config
│       └── messaging.js           # Push notifications
│
├── Procfile                       # Deployment config (Heroku/Render)
├── render.yaml                    # Render deployment config
└── vercel.json                    # Vercel deployment config
```

---

## 🔌 API Endpoints

### Authentication
- `POST /auth/signup` - Register new user
- `POST /auth/login` - User login
- `GET /auth/logout` - User logout
- `GET /auth` - Show login/signup page

### Complaints
- `POST /complaint/submit` - Submit new complaint
- `GET /complaint/submit` - Get complaint form
- `GET /complaint/stream` - Real-time complaint updates (SSE)
- `GET /complaint/<complaint_id>` - View specific complaint
- `PUT /complaint/<complaint_id>` - Update complaint status
- `GET /complaints` - List user complaints

### Feedback
- `POST /feedback/submit` - Submit feedback
- `GET /feedback` - View feedback history
- `GET /feedback/<feedback_id>` - View specific feedback

### Admin
- `GET /admin/users` - List all users
- `POST /admin/approve-user` - Approve user registration
- `GET /admin/reports` - View system reports
- `GET /admin/statistics` - Get system statistics

### Main Pages
- `GET /` - Landing page
- `GET /resident/dashboard` - Resident dashboard
- `GET /official/dashboard` - Official dashboard
- `GET /admin/dashboard` - Admin dashboard

---

## 🚀 Deployment

### Option 1: Render (Recommended)
1. Push code to GitHub
2. Go to [Render.com](https://render.com)
3. Create new Web Service
4. Connect GitHub repository
5. Set environment variables
6. Deploy from `render.yaml`

### Option 2: Vercel
1. Connect GitHub repository to Vercel
2. Set environment variables
3. Deploy using `vercel.json` configuration
4. Application runs as serverless functions

### Option 3: Heroku (Deprecated but still works)
1. Install Heroku CLI
2. Push to Heroku remote
3. Configure environment variables
4. Use `Procfile` for deployment

### Environment Variables for Deployment
```
SECRET_KEY=<random-secret-key>
FIREBASE_KEY_PATH=firebase-key.json
PORT=5000
```

---

## 🔍 Complaint Categories & Urgency

| Category | Urgency | Est. Resolution |
|----------|---------|-----------------|
| Security | High | 24 hours |
| Emergency | High | 24 hours |
| Waste | Medium | 3 days |
| Road | Medium | 3 days |
| Water | Medium | 3 days |
| Other | Low | 7 days |

---

## ❓ Troubleshooting

### Common Issues

**1. Firebase Connection Error**
- Verify `firebase-key.json` exists in project root
- Check Firebase service account permissions
- Ensure Firestore database is initialized
- Check internet connection

**2. Login Not Working**
- Clear browser cookies and cache
- Verify Firebase Authentication is enabled
- Check user credentials are correct
- Review browser console for errors

**3. Complaints Not Appearing**
- Check Firestore database rules allow read/write
- Verify user is logged in with correct role
- Check network tab in browser DevTools
- Review server logs for errors

**4. Session Timeout Issues**
- Session timeout is set to 30 minutes by default
- Modify `SESSION_PERMANENT_LIFETIME` in `app.py` to change
- Clear browser cache if experiencing session issues

**5. Real-time Updates Not Working**
- Verify Server-Sent Events (SSE) support in browser
- Check browser console for connection errors
- Ensure Firestore security rules allow data access
- Try hard refresh (Ctrl+Shift+R)

### Debug Mode
Enable debug logging:
```python
# In app.py
app.run(host='0.0.0.0', port=5000, debug=True)
```

### Check Logs
```bash
# Terminal output shows application logs
# Browser console (F12) shows frontend errors
# Firestore console shows database operations
```

---

## 📄 Additional Resources

- [Firebase Documentation](https://firebase.google.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Cloud Firestore Guide](https://cloud.google.com/firestore/docs)
- [FIREBASE_SETUP.md](FIREBASE_SETUP.md) - Detailed Firebase setup
- [SETUP_COMPLETE.md](SETUP_COMPLETE.md) - Setup verification checklist

---

## 📝 License

This project is open source and available under the MIT License.

---

## 👨‍💻 Developer

**Created by:** DonClarko  
**Repository:** [GitHub - BCCMS](https://github.com/DonClarko/BCCMS)

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📞 Support

For issues or questions:
- Check existing GitHub issues
- Create a new issue with detailed description
- Include error messages and screenshots
- Describe steps to reproduce the problem

---

**Last Updated:** December 2024
