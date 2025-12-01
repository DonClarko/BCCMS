"""
Firebase Configuration and Initialization
Replace the credentials below with your Firebase project details
"""
import firebase_admin
from firebase_admin import credentials, db, auth as firebase_auth
import json
import os

# Path to your Firebase service account key
FIREBASE_CREDENTIALS_PATH = 'firebase-key.json'

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Check if Firebase is already initialized
        firebase_admin.get_app()
    except ValueError:
        # Firebase not initialized yet
        if not os.path.exists(FIREBASE_CREDENTIALS_PATH):
            raise FileNotFoundError(
                f"Firebase credentials file not found at {FIREBASE_CREDENTIALS_PATH}. "
                "Please download your service account key from Firebase Console and save it as firebase-key.json"
            )
        
        # Initialize Firebase Admin SDK
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://bccms-3ba95-default-rtdb.firebaseio.com'
        })
        print("Firebase initialized successfully!")

def get_db():
    """Get Firebase Realtime Database reference"""
    return db.reference()

def get_users_db():
    """Get users database reference"""
    return db.reference('users')

def get_complaints_db():
    """Get complaints database reference"""
    return db.reference('complaints')

# Initialize Firebase on module import
initialize_firebase()
