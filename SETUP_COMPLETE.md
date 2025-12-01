# Firebase Setup - IMMEDIATE ACTIONS REQUIRED

Your Flask app is now running and connected to Firebase! However, you need to enable the **Realtime Database** to complete the setup.

## ✅ What's Done:
- Firebase credentials (`firebase-key.json`) configured ✓
- Firebase config in frontend (`firebaseConfig.js`) configured ✓
- Flask app running and connected ✓
- Authentication ready ✓

## ⚠️ What You Need to Do:

### Step 1: Enable Realtime Database
1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project: **bccms-3ba95**
3. In the left sidebar, click **Realtime Database** (or Build > Realtime Database)
4. Click **"Create Database"** button
5. Choose:
   - **Location**: United States (or your preferred region)
   - **Security rules**: Select **"Start in test mode"** (for development)
6. Click **"Create"**

### Step 2: Verify in Firebase Console
- You should see your database URL: `https://bccms-3ba95.firebaseio.com`
- This matches the URL in your `firebase_config.py` and `firebaseConfig.js`

### Step 3: Test the App
Once the database is created:
1. The Flask app will automatically create the default admin account
2. Try logging in with:
   - **Email**: `admin01-barangay@gmail.com`
   - **Password**: `admin123`

---

## Database Structure Preview

After the Realtime Database is enabled, your data will be organized like this:

```
bccms-3ba95
├── users/
│   ├── [user-id-1]/
│   │   ├── full_name: "John Doe"
│   │   ├── email: "john@example.com"
│   │   ├── role: "resident"
│   │   └── ...
│   └── [user-id-2]/
│       └── ...
├── complaints/
│   ├── BCMS-2024-abc123/
│   │   ├── title: "Pothole on Main Street"
│   │   ├── status: "New"
│   │   └── ...
│   └── ...
└── notifications/
    └── ...
```

---

## App URLs
- **Home**: http://127.0.0.1:5000/
- **Auth**: http://127.0.0.1:5000/auth/login
- **Resident Dashboard**: http://127.0.0.1:5000/resident/dashboard
- **Official Dashboard**: http://127.0.0.1:5000/official/dashboard
- **Admin Dashboard**: http://127.0.0.1:5000/admin/dashboard

---

## Still Running Into Issues?

If you get a 404 error when trying to access pages, it means:
1. Realtime Database hasn't been created yet
2. Check that the database URL is correctly set

### Check Status:
Run this command to verify Firebase connection:
```bash
python -c "from firebase_config import initialize_firebase; initialize_firebase(); print('✓ Firebase Connected!')"
```

---

## Environment Setup (Optional but Recommended)

For production, store credentials in environment variables instead of firebase-key.json:

Create a `.env` file in your project root:
```
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-key.json
FLASK_SECRET_KEY=your-very-secure-random-key-here
```

Then update `firebase_config.py` to read from `.env`

---

## Features Ready to Use:

✓ User Registration (Email/Password)
✓ Login with role-based access
✓ Resident complaint submission
✓ Official complaint tracking
✓ Admin dashboard
✓ Real-time notifications
✓ Secure authentication

---

## Next: Create Your First Account

Once the Realtime Database is enabled:

1. Go to http://127.0.0.1:5000/
2. Click "Sign Up"
3. Create a resident account
4. Submit a complaint
5. Login as admin (email/password above) to see all complaints

Enjoy! 🎉
