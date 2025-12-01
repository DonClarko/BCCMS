from flask import Blueprint, request, jsonify, session, flash, redirect, url_for, Response, render_template
import time
import json
import os
from datetime import datetime
from functools import wraps
from auth_firebase import login_required, role_required
from firebase_admin import db
from firebase_config import initialize_firebase, get_complaints_db, get_users_db
import uuid

initialize_firebase()

complaint_bp = Blueprint('complaint', __name__)

def calculate_urgency(category):
    """Calculate urgency level based on category"""
    urgency_map = {
        'security': 'High',
        'emergency': 'High',
        'waste': 'Medium',
        'road': 'Medium',
        'water': 'Medium',
        'others': 'Low'
    }
    return urgency_map.get(category.lower(), 'Low')

def estimate_resolution(urgency):
    """Estimate resolution time based on urgency"""
    return {
        'High': '24 hours',
        'Medium': '3 days',
        'Low': '7 days'
    }.get(urgency, '7 days')

def add_official_notification(complaint_id, title, message):
    """Add notification for officials about a complaint"""
    try:
        notifications_ref = db.reference('notifications')
        notification = {
            'complaint_id': complaint_id,
            'title': title,
            'message': message,
            'created_at': datetime.now().isoformat(),
            'read': False
        }
        # Push creates a new child location with an auto-generated key
        notifications_ref.push(notification)
    except Exception as e:
        print(f"Error adding notification: {str(e)}")

@complaint_bp.route('/stream')
def complaint_stream():
    """Real-time complaint updates via Server-Sent Events"""
    def event_stream():
        last_data = None
        while True:
            try:
                complaints_ref = db.reference('complaints')
                complaints = complaints_ref.get()
                
                if complaints != last_data:
                    last_data = complaints
                    yield f"data: {json.dumps(complaints or {})}\n\n"
                
                time.sleep(1)
            except Exception as e:
                print(f"Error in event stream: {str(e)}")
                time.sleep(1)
    
    return Response(event_stream(), mimetype="text/event-stream")

@complaint_bp.route('/complaint/submit', methods=['POST'])
@login_required
def submit_complaint():
    """Submit a new complaint to Firebase"""
    try:
        user_email = session.get('user_email')
        user_uid = session.get('user_uid')
        
        if not user_email or not user_uid:
            return jsonify({'success': False, 'message': 'User not logged in'}), 401
        
        # Generate unique complaint ID
        complaint_id = f"BCMS-{datetime.now().strftime('%Y')}-{str(uuid.uuid4())[:8]}"
        
        # Get form data
        title = request.form.get('title')
        category = request.form.get('category')
        description = request.form.get('description')
        location = request.form.get('location')
        incident_date = request.form.get('incident-date')
        urgency = calculate_urgency(category)
        
        # Create complaint object
        new_complaint = {
            'id': complaint_id,
            'title': title,
            'category': category,
            'description': description,
            'location': location,
            'incident_date': incident_date,
            'submitted_date': datetime.now().isoformat(),
            'user_email': user_email,
            'user_uid': user_uid,
            'user_name': session.get('user_name', 'Anonymous Resident'),
            'status': 'New',
            'urgency': urgency,
            'estimated_resolution': estimate_resolution(urgency),
            'escalated': False,
            'assigned_to': None,
            'notifications_sent': [],
            'updates': []
        }
        
        # Save contact info if provided
        contact_preference = request.form.get('contact-preference')
        if contact_preference == 'yes':
            new_complaint['contact_info'] = {
                'name': request.form.get('full-name'),
                'phone': request.form.get('contact-number'),
                'email': request.form.get('email')
            }
        
        # Handle file attachments
        images = []
        files = request.files.getlist('attachment')
        if files:
            import base64
            for file in files:
                if file and file.filename:
                    # Read file and convert to base64
                    file_data = file.read()
                    file_base64 = base64.b64encode(file_data).decode('utf-8')
                    
                    # Get file extension
                    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                    
                    # Determine MIME type
                    mime_type = file.content_type or 'image/jpeg'
                    
                    images.append({
                        'filename': file.filename,
                        'data': file_base64,
                        'mime_type': mime_type
                    })
            
            if images:
                new_complaint['attachments'] = images
        
        # Save to Firebase
        complaints_ref = db.reference(f'complaints/{complaint_id}')
        complaints_ref.set(new_complaint)
        
        # Add notification for officials
        add_official_notification(
            complaint_id,
            'New complaint submitted',
            f"A new {urgency} urgency complaint has been submitted"
        )
        
        return jsonify({
            'success': True,
            'complaint_id': complaint_id,
            'message': 'Complaint submitted successfully'
        })
        
    except Exception as e:
        print(f"Error submitting complaint: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@complaint_bp.route('/complaint/recent')
@login_required
def get_recent_complaints():
    """Get recent complaints for current user"""
    try:
        user_email = session.get('user_email')
        user_uid = session.get('user_uid')
        user_role = session.get('user_role')
        
        if not user_email:
            return jsonify([])
        
        complaints_ref = db.reference('complaints')
        complaints_data = complaints_ref.get()
        
        if not complaints_data:
            return jsonify([])
        
        # Convert to list
        complaints = list(complaints_data.values()) if isinstance(complaints_data, dict) else complaints_data
        
        # Filter based on role
        if user_role == 'official':
            # Officials see all complaints
            user_complaints = complaints
        else:
            # Residents see only their own
            user_complaints = [c for c in complaints if c.get('user_uid') == user_uid]
        
        # Sort and limit
        recent_complaints = sorted(
            user_complaints,
            key=lambda x: x.get('submitted_date', ''),
            reverse=True
        )[:5]
        
        return jsonify(recent_complaints)
        
    except Exception as e:
        print(f"Error fetching recent complaints: {str(e)}")
        return jsonify([])

@complaint_bp.route('/complaint/all')
@login_required
def get_all_complaints():
    """Get all complaints for current user"""
    try:
        user_email = session.get('user_email')
        user_uid = session.get('user_uid')
        user_role = session.get('user_role')
        
        if not user_email:
            return jsonify([])
        
        complaints_ref = db.reference('complaints')
        complaints_data = complaints_ref.get()
        
        if not complaints_data:
            return jsonify([])
        
        # Convert to list
        complaints = list(complaints_data.values()) if isinstance(complaints_data, dict) else complaints_data
        
        # Filter based on role
        if user_role == 'official':
            user_complaints = complaints
        else:
            user_complaints = [c for c in complaints if c.get('user_uid') == user_uid]
        
        # Sort
        sorted_complaints = sorted(
            user_complaints,
            key=lambda x: x.get('submitted_date', ''),
            reverse=True
        )
        
        return jsonify(sorted_complaints)
        
    except Exception as e:
        print(f"Error fetching all complaints: {str(e)}")
        return jsonify([])

@complaint_bp.route('/complaint/details')
@login_required
def get_complaint_details():
    """Get detailed information about a specific complaint"""
    try:
        complaint_id = request.args.get('id')
        user_email = session.get('user_email')
        user_uid = session.get('user_uid')
        user_role = session.get('user_role')
        
        if not complaint_id:
            return jsonify({'error': 'Invalid request'}), 400
        
        complaints_ref = db.reference(f'complaints/{complaint_id}')
        complaint = complaints_ref.get()
        
        if not complaint:
            return jsonify({'error': 'Complaint not found'}), 404
        
        # Security check
        if user_role == 'official':
            return jsonify(complaint)
        elif complaint.get('user_uid') == user_uid:
            return jsonify(complaint)
        else:
            return jsonify({'error': 'Access denied'}), 403
        
    except Exception as e:
        print(f"Error fetching complaint details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@complaint_bp.route('/officials/complaints/<status>')
@login_required
@role_required('official')
def get_complaints_by_status(status):
    """Get complaints filtered by status for officials"""
    try:
        complaints_ref = db.reference('complaints')
        complaints_data = complaints_ref.get()
        
        if not complaints_data:
            return jsonify([])
        
        # Handle 'all' case
        if status.lower() == 'all':
            complaints_list = list(complaints_data.values())
        else:
            # Map URL parameter to actual status values
            status_map = {
                'new': 'New',
                'pending': 'Pending',
                'pending-review': 'Pending',
                'in-progress': 'In Progress',
                'escalated': 'Escalated',
                'resolved': 'Resolved'
            }
            
            target_status = status_map.get(status.lower(), status)
            complaints_list = [c for c in complaints_data.values() if c.get('status') == target_status]
        
        # Sort by date (newest first)
        complaints_list = sorted(
            complaints_list,
            key=lambda x: x.get('submitted_date', ''),
            reverse=True
        )
        
        return jsonify(complaints_list)
    
    except Exception as e:
        print(f"Error fetching complaints by status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@complaint_bp.route('/complaint/update', methods=['POST'])
@login_required
def update_complaint():
    """Update complaint status or details (officials only)"""
    try:
        user_role = session.get('user_role')
        
        if user_role != 'official':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        complaint_id = request.json.get('complaint_id')
        status = request.json.get('status')
        notes = request.json.get('notes', '')
        
        complaints_ref = db.reference(f'complaints/{complaint_id}')
        complaint = complaints_ref.get()
        
        if not complaint:
            return jsonify({'success': False, 'message': 'Complaint not found'}), 404
        
        # Get old status for comparison
        old_status = complaint.get('status', 'New')
        
        # Update complaint
        complaint['status'] = status
        complaint['updated_at'] = datetime.now().isoformat()
        complaint['updated_by'] = session.get('user_uid')
        if notes:
            complaint['status_notes'] = notes
        
        complaints_ref.set(complaint)
        
        # Send notification to the resident who filed the complaint
        resident_uid = complaint.get('user_uid')
        if resident_uid:
            users_ref = db.reference('users')
            users = users_ref.get() or {}
            
            # Find resident by UID
            resident_data = users.get(resident_uid)
            
            if resident_data:
                # Create notification
                notification = {
                    'id': str(uuid.uuid4())[:8],
                    'timestamp': datetime.now().isoformat(),
                    'title': f'Complaint Status Updated: {complaint_id}',
                    'message': f'Your complaint status has been updated from "{old_status}" to "{status}".{" Note: " + notes if notes else ""}',
                    'complaint_id': complaint_id,
                    'read': False
                }
                
                # Add notification to resident's notifications
                resident_ref = db.reference(f'users/{resident_uid}')
                resident_notifications = resident_data.get('notifications', [])
                resident_notifications.append(notification)
                resident_ref.child('notifications').set(resident_notifications)
                
                print(f'Notification sent to resident {resident_uid} for complaint {complaint_id}')
        
        return jsonify({'success': True, 'message': 'Complaint updated successfully'})
        
    except Exception as e:
        print(f"Error updating complaint: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


# Get list of all officials for messaging
@complaint_bp.route('/officials/list')
@login_required
def get_officials_list():
    try:
        users_ref = db.reference('users')
        users = users_ref.get() or {}
        officials = []
        for uid, user in users.items():
            # Only include users with official role
            if user.get('role') == 'official':
                officials.append({
                    'email': user.get('email', ''),
                    'name': user.get('full_name', user.get('email', '')),
                    'role': 'official'
                })
        print(f'Found {len(officials)} officials for messaging')
        return jsonify(officials)
    except Exception as e:
        print('Error loading officials list:', e)
        return jsonify([]), 500


# Get list of all residents for messaging (officials only)
@complaint_bp.route('/residents/list')
@login_required
@role_required('official')
def get_residents_list():
    try:
        users_ref = db.reference('users')
        users = users_ref.get() or {}
        residents = []
        for uid, user in users.items():
            # Only include users with resident role (not officials, not admins)
            if user.get('role') == 'resident':
                residents.append({
                    'email': user.get('email', ''),
                    'name': user.get('full_name', user.get('email', '')),
                    'role': 'resident'
                })
        print(f'Found {len(residents)} residents for messaging')
        return jsonify(residents)
    except Exception as e:
        print('Error loading residents list:', e)
        return jsonify([]), 500


# Messages & Notifications API
@complaint_bp.route('/messages')
@login_required
def get_messages():
    user_uid = session.get('user_uid')
    if not user_uid:
        return jsonify([]), 401
    user_ref = db.reference(f'users/{user_uid}')
    user = user_ref.get() or {}
    messages = user.get('messages', [])
    # return newest first
    sorted_msgs = sorted(messages, key=lambda m: m.get('timestamp', ''), reverse=True)
    return jsonify(sorted_msgs)


@complaint_bp.route('/message/send', methods=['POST'])
@login_required
def send_message():
    try:
        # Accept JSON or form data
        data = request.get_json() or request.form.to_dict()
        to_email = data.get('to') or data.get('to_email')
        subject = data.get('subject', '')
        content = data.get('content', '')
        complaint_id = data.get('complaint_id')

        if not to_email or not content:
            return jsonify({'success': False, 'error': 'Missing recipient or content'}), 400

        # Find recipient by email
        users_ref = db.reference('users')
        users = users_ref.get() or {}
        
        recipient_uid = None
        recipient_data = None
        sender_uid = session.get('user_uid')
        sender_data = None
        
        for uid, user in users.items():
            if user.get('email') == to_email:
                recipient_uid = uid
                recipient_data = user
            if uid == sender_uid:
                sender_data = user
        
        if not recipient_uid or not recipient_data:
            return jsonify({'success': False, 'error': 'Recipient not found'}), 404

        msg = {
            'id': str(uuid.uuid4())[:8],
            'from_email': session.get('user_email'),
            'from_name': session.get('user_name'),
            'to_email': to_email,
            'to_name': recipient_data.get('full_name', to_email),
            'subject': subject,
            'content': content,
            'complaint_id': complaint_id,
            'timestamp': datetime.now().isoformat(),
            'read': False
        }

        # Save message in recipient's inbox
        recipient_ref = db.reference(f'users/{recipient_uid}')
        recipient_messages = recipient_data.get('messages', [])
        recipient_messages.append(msg)
        recipient_ref.child('messages').set(recipient_messages)
        
        # Also save message in sender's sent folder (create a copy marked as sent)
        sent_msg = msg.copy()
        sent_msg['isSent'] = True
        sender_ref = db.reference(f'users/{sender_uid}')
        sender_messages = sender_data.get('messages', []) if sender_data else []
        sender_messages.append(sent_msg)
        sender_ref.child('messages').set(sender_messages)

        # Optionally add a notification for the recipient
        recipient_notifications = recipient_data.get('notifications', [])
        recipient_notifications.append({
            'id': str(uuid.uuid4())[:8],
            'timestamp': datetime.now().isoformat(),
            'title': f"New message: {subject[:40]}",
            'message': content[:140],
            'read': False
        })
        recipient_ref.child('notifications').set(recipient_notifications)

        return jsonify({'success': True})
    except Exception as e:
        print('Error sending message:', e)
        return jsonify({'success': False, 'error': str(e)}), 500


@complaint_bp.route('/notifications')
@login_required
def get_notifications():
    user_uid = session.get('user_uid')
    if not user_uid:
        return jsonify([]), 401

    # Get user notifications from Firebase
    user_ref = db.reference(f'users/{user_uid}')
    user = user_ref.get() or {}
    user_notes = user.get('notifications', [])

    # Sort by timestamp
    merged_sorted = sorted(user_notes, key=lambda n: n.get('timestamp', ''), reverse=True)
    return jsonify(merged_sorted)


@complaint_bp.route('/notifications/mark_read', methods=['POST'])
@login_required
def mark_notification_read():
    data = request.get_json() or {}
    note_id = data.get('id')
    if not note_id:
        return jsonify({'success': False, 'error': 'Missing id'}), 400

    user_uid = session.get('user_uid')
    user_ref = db.reference(f'users/{user_uid}')
    user = user_ref.get() or {}
    updated = False
    if user and user.get('notifications'):
        notifications = user['notifications']
        for n in notifications:
            if n.get('id') == note_id:
                n['read'] = True
                updated = True
                break
    if updated:
        user_ref.child('notifications').set(user['notifications'])
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Notification not found'}), 404
