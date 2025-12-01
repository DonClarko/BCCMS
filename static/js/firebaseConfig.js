/**
 * Firebase Frontend Configuration
 * Replace the config below with your Firebase project config
 * Get this from: Firebase Console > Project Settings > Your Apps > Web
 */

const firebaseConfig = {
    apiKey: "AIzaSyD4RIUrkMKzcF2WRnWuzNNEw73-AUIlde8",
    authDomain: "bccms-3ba95.firebaseapp.com",
    projectId: "bccms-3ba95",
    storageBucket: "bccms-3ba95.firebasestorage.app",
    messagingSenderId: "603854034994",
    appId: "1:603854034994:web:d7ea01b656de2f6b48442b",
    databaseURL: "https://bccms-3ba95-default-rtdb.firebaseio.com"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Get Firebase services
const db = firebase.database();
const auth = firebase.auth();

// Helper function to listen for user authentication state
auth.onAuthStateChanged((user) => {
    if (user) {
        console.log("User logged in:", user.uid);
        // User is logged in
    } else {
        console.log("User logged out");
        // User is logged out
    }
});

// Export functions for use in other scripts
window.firebaseDB = db;
window.firebaseAuth = auth;
