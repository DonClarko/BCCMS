# Firebase Integration Setup Guide

## Quick Start

Your BCCMS application has been configured to use Firebase. Follow these steps to complete the setup:

### Step 1: Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a new project" or "Add project"
3. Enter project name (e.g., "BCCMS") and continue
4. Enable Google Analytics (optional) and create the project

### Step 2: Get Your Firebase Credentials

#### Backend Setup (Python)
1. In Firebase Console, go to **Project Settings** (gear icon)
2. Click on **Service Accounts** tab
3. Click **Generate New Private Key** button
4. Save the JSON file as **`firebase-key.json`** in your project root directory
   ```
   BCCMS/
   ├── firebase-key.json  ← Save it here
   ├── app.py
   ├── auth_firebase.py
   └── ...
   ```

#### Frontend Setup (JavaScript)
1. In Firebase Console, go to **Project Settings** (gear icon)
2. Click on **Your Apps** section
3. Click **Add App** and select **Web** (</> icon)
4. Register your web app
5. Copy the Firebase config object
6. Replace the config in `static/js/firebaseConfig.js`:
   ```javascript
   const firebaseConfig = {
       apiKey: "YOUR_API_KEY_HERE",
       authDomain: "your-project.firebaseapp.com",
       projectId: "your-project-id",
       storageBucket: "your-project.appspot.com",
       messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
       appId: "YOUR_APP_ID",
       databaseURL: "https://your-project.firebaseio.com"
   };
   ```

### Step 3: Enable Firebase Services

In Firebase Console:

1. **Enable Realtime Database**
   - Go to **Realtime Database** → Click "Create Database"
   - Choose **Start in test mode** (for development)
   - Select region and create
   - Note the database URL (format: `https://your-project.firebaseio.com`)
   - Update `firebase_config.py` with this URL

2. **Enable Authentication**
   - Go to **Authentication** → Click "Get started"
   - Enable **Email/Password** provider
   - (Optional) Enable other providers: Google, Facebook, etc.

### Step 4: Update Configuration Files

**`firebase_config.py`** - Update the database URL:
```python
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://YOUR-PROJECT.firebaseio.com'  # ← Add your URL here
})
```

**`static/js/firebaseConfig.js`** - Update with your Firebase config from Step 2

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

The requirements.txt includes:
- `firebase-admin` - Backend Admin SDK
- `google-cloud-firestore` - For future Firestore integration
- `Flask` and `Werkzeug` - Web framework

### Step 6: Update Your App.py Import (if needed)

Your `app.py` has been updated to use Firebase. Make sure it imports from `auth_firebase` and `complaints_firebase`:

```python
from auth_firebase import auth_bp, create_default_admin
from complaints_firebase import complaint_bp
```

### Step 7: Run the Application

```bash
python app.py
```

The application will:
- Initialize Firebase connection
- Create the default admin account in Firebase
- Start the Flask server

---

## New Files Created

| File | Purpose |
|------|---------|
| `firebase_config.py` | Firebase Admin SDK initialization |
| `auth_firebase.py` | Firebase Authentication (replaces auth.py) |
| `complaints_firebase.py` | Firebase Database operations (replaces complaints.py) |
| `static/js/firebaseConfig.js` | Frontend Firebase configuration |
| `requirements.txt` | Python dependencies |

## Old JSON Files

You can keep your old files as backup:
- `users.json` - Now stored in Firebase Realtime Database
- `complaints.json` - Now stored in Firebase Realtime Database
- `auth.py` - Replaced by `auth_firebase.py`
- `complaints.py` - Replaced by `complaints_firebase.py`

To switch back, just update `app.py` imports.

---

## Database Structure

### Realtime Database Structure:
```
users/
  ├── user-uid-1/
  │   ├── full_name: "John Doe"
  │   ├── email: "john@example.com"
  │   ├── phone: "09123456789"
  │   ├── role: "resident"
  │   └── created_at: "2024-12-01T10:30:00"
  │
  └── user-uid-2/
      ├── full_name: "Jane Smith"
      ├── email: "jane@example.com"
      ├── phone: "09187654321"
      ├── role: "official"
      ├── is_admin: true
      └── created_at: "2024-12-01T09:15:00"

complaints/
  ├── BCMS-2024-abc12345/
  │   ├── id: "BCMS-2024-abc12345"
  │   ├── title: "Pothole on Main Street"
  │   ├── category: "road"
  │   ├── description: "Large pothole near corner store"
  │   ├── location: "Main Street, Barangay"
  │   ├── status: "New"
  │   ├── urgency: "Medium"
  │   ├── user_uid: "user-uid-1"
  │   ├── submitted_date: "2024-12-01T11:00:00"
  │   └── updates: []
  │
  └── BCMS-2024-def67890/
      └── ...

notifications/
  ├── notif-1/
  │   ├── complaint_id: "BCMS-2024-abc12345"
  │   ├── title: "New complaint submitted"
  │   ├── message: "A new Medium urgency complaint..."
  │   ├── read: false
  │   └── created_at: "2024-12-01T11:00:00"
  │
  └── notif-2/
      └── ...
```

---

## Important Notes

### Security Rules (Firebase Console)
For development, test mode allows read/write access. For production, update Security Rules in Firebase Console > Realtime Database > Rules:

```json
{
  "rules": {
    "users": {
      "$uid": {
        ".read": "$uid === auth.uid",
        ".write": "$uid === auth.uid || root.child('users').child(auth.uid).child('is_admin').val() === true"
      }
    },
    "complaints": {
      "$complaint_id": {
        ".read": "root.child('users').child(auth.uid).child('role').val() === 'official' || data.child('user_uid').val() === auth.uid",
        ".write": "root.child('users').child(auth.uid).child('is_admin').val() === true"
      }
    },
    "notifications": {
      ".read": "auth != null",
      ".write": "auth != null"
    }
  }
}
```

### Default Admin Account
- **Email**: `admin01-barangay@gmail.com`
- **Password**: `admin123`
- **Role**: Official with admin privileges

Change this after first login!

### Troubleshooting

**Error: "Firebase credentials file not found"**
- Make sure `firebase-key.json` is in the project root directory

**Error: "databaseURL is not specified"**
- Update `firebase_config.py` with your Firebase Realtime Database URL

**Error: "PERMISSION_DENIED"**
- Check Firebase Security Rules in Console
- Make sure you're in Test Mode for development

---

## Next Steps

1. Replace hardcoded credentials with environment variables
2. Migrate existing data from JSON files to Firebase (if needed)
3. Set up Firebase Security Rules for production
4. Enable additional auth providers (Google, Facebook, etc.)
5. Implement real-time listeners for live updates
6. Set up Firebase Cloud Functions for automated tasks

For more help, visit:
- [Firebase Documentation](https://firebase.google.com/docs)
- [Firebase Admin SDK (Python)](https://firebase.google.com/docs/database/admin/start)
- [Firebase Authentication](https://firebase.google.com/docs/auth)
