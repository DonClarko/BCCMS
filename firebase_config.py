"""
Firebase Configuration and Initialization (Firestore)
Replace the credentials below with your Firebase project details
"""
import firebase_admin
from firebase_admin import credentials, firestore, auth as firebase_auth
import json
import os

# Path to your Firebase service account key
FIREBASE_CREDENTIALS_PATH = 'firebase-key.json'

# Global Firestore client
_firestore_client = None

def initialize_firebase():
    """Initialize Firebase Admin SDK with Firestore"""
    global _firestore_client
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
        
        # Initialize Firebase Admin SDK (no databaseURL needed for Firestore)
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully with Firestore!")
    
    # Initialize Firestore client
    if _firestore_client is None:
        _firestore_client = firestore.client()
    
    return _firestore_client

def get_db():
    """Get Firestore client"""
    global _firestore_client
    if _firestore_client is None:
        initialize_firebase()
    return _firestore_client

def get_users_collection():
    """Get users collection reference"""
    return get_db().collection('users')

def get_complaints_collection():
    """Get complaints collection reference"""
    return get_db().collection('complaints')

def get_feedback_collection():
    """Get feedback collection reference"""
    return get_db().collection('feedback')

def get_notifications_collection():
    """Get notifications collection reference"""
    return get_db().collection('notifications')

# Initialize Firebase on module import
initialize_firebase()
