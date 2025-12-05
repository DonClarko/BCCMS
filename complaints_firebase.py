from flask import Blueprint, request, jsonify, session, flash, redirect, url_for, Response, render_template
import time
import json
import os
from datetime import datetime
from functools import wraps
from auth_firebase import login_required, role_required
from firebase_admin import firestore
from firebase_config import initialize_firebase, get_db
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
        db = get_db()
        notification = {
            'complaint_id': complaint_id,
            'title': title,
            'message': message,
            'created_at': datetime.now().isoformat(),
            'read': False
        }
        db.collection('notifications').add(notification)
    except Exception as e:
        print(f"Error adding notification: {str(e)}")

@complaint_bp.route('/stream')
def complaint_stream():
    """Real-time complaint updates via Server-Sent Events"""
    def event_stream():
        last_data = None
        while True:
            try:
                db = get_db()
                complaints_ref = db.collection('complaints')
                complaints_docs = complaints_ref.stream()
                
                complaints = {}
                for doc in complaints_docs:
                    complaints[doc.id] = doc.to_dict()
                
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
    """Submit a new complaint to Firebase Firestore"""
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
        
        # Save to Firestore
        db = get_db()
        db.collection('complaints').document(complaint_id).set(new_complaint)
        
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
        
        db = get_db()
        complaints_ref = db.collection('complaints')
        
        # Filter based on role
        if user_role == 'official':
            # Officials see all complaints
            complaints_docs = complaints_ref.stream()
        else:
            # Residents see only their own
            complaints_docs = complaints_ref.where('user_uid', '==', user_uid).stream()
        
        complaints = []
        for doc in complaints_docs:
            complaint = doc.to_dict()
            complaints.append(complaint)
        
        # Sort and limit
        recent_complaints = sorted(
            complaints,
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
        
        db = get_db()
        complaints_ref = db.collection('complaints')
        
        # Filter based on role
        if user_role == 'official':
            complaints_docs = complaints_ref.stream()
        else:
            complaints_docs = complaints_ref.where('user_uid', '==', user_uid).stream()
        
        complaints = []
        for doc in complaints_docs:
            complaint = doc.to_dict()
            complaints.append(complaint)
        
        # Sort
        sorted_complaints = sorted(
            complaints,
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
        
        db = get_db()
        complaint_ref = db.collection('complaints').document(complaint_id)
        complaint_doc = complaint_ref.get()
        
        if not complaint_doc.exists:
            return jsonify({'error': 'Complaint not found'}), 404
        
        complaint = complaint_doc.to_dict()
        
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

@complaint_bp.route('/officials/stats')
@login_required
@role_required('official')
def get_officials_stats():
    """Get dashboard statistics for officials"""
    try:
        db = get_db()
        complaints_ref = db.collection('complaints')
        complaints_docs = complaints_ref.stream()
        
        complaints_list = [doc.to_dict() for doc in complaints_docs]
        
        if not complaints_list:
            return jsonify({
                'total': 0,
                'pending': 0,
                'new': 0,
                'in_progress': 0,
                'escalated': 0,
                'resolved': 0,
                'urgent_pending': 0,
                'avg_resolution_time': 0,
                'change_from_last_month': {
                    'total': 0,
                    'resolved': 0,
                    'resolution_time': 0
                }
            })
        
        # Count by status
        total = len(complaints_list)
        new_count = sum(1 for c in complaints_list if c.get('status') == 'New')
        pending = sum(1 for c in complaints_list if c.get('status') in ['Pending', 'Pending Review'])
        in_progress = sum(1 for c in complaints_list if c.get('status') == 'In Progress')
        escalated = sum(1 for c in complaints_list if c.get('status') == 'Escalated')
        resolved = sum(1 for c in complaints_list if c.get('status') == 'Resolved')
        
        # Count urgent pending (High urgency that are not resolved)
        urgent_pending = sum(1 for c in complaints_list 
                           if c.get('urgency') == 'High' and c.get('status') not in ['Resolved'])
        
        # Calculate average resolution time for resolved complaints
        resolution_times = []
        for complaint in complaints_list:
            if complaint.get('status') == 'Resolved' and complaint.get('submitted_date') and complaint.get('updated_at'):
                try:
                    submitted = datetime.fromisoformat(complaint.get('submitted_date').replace('Z', '+00:00'))
                    resolved_date = datetime.fromisoformat(complaint.get('updated_at').replace('Z', '+00:00'))
                    days = (resolved_date - submitted).days
                    if days >= 0:
                        resolution_times.append(days)
                except:
                    pass
        
        avg_resolution_time = round(sum(resolution_times) / len(resolution_times), 1) if resolution_times else 0
        
        # Calculate changes from last month
        now = datetime.now()
        last_month_start = datetime(now.year, now.month - 1 if now.month > 1 else 12, 1)
        this_month_start = datetime(now.year, now.month, 1)
        
        last_month_total = 0
        last_month_resolved = 0
        this_month_total = 0
        this_month_resolved = 0
        
        for complaint in complaints_list:
            try:
                submitted = datetime.fromisoformat(complaint.get('submitted_date', '').replace('Z', '+00:00'))
                if last_month_start <= submitted < this_month_start:
                    last_month_total += 1
                    if complaint.get('status') == 'Resolved':
                        last_month_resolved += 1
                elif submitted >= this_month_start:
                    this_month_total += 1
                    if complaint.get('status') == 'Resolved':
                        this_month_resolved += 1
            except:
                pass
        
        # Calculate percentage changes
        total_change = round(((this_month_total - last_month_total) / max(last_month_total, 1)) * 100)
        resolved_change = round(((this_month_resolved - last_month_resolved) / max(last_month_resolved, 1)) * 100)
        
        return jsonify({
            'total': total,
            'pending': pending,
            'new': new_count,
            'in_progress': in_progress,
            'escalated': escalated,
            'resolved': resolved,
            'urgent_pending': urgent_pending,
            'avg_resolution_time': avg_resolution_time,
            'change_from_last_month': {
                'total': total_change,
                'resolved': resolved_change,
                'resolution_time': 0.5
            }
        })
        
    except Exception as e:
        print(f"Error fetching officials stats: {str(e)}")
        return jsonify({'error': str(e)}), 500


@complaint_bp.route('/officials/complaints/<status>')
@login_required
@role_required('official')
def get_complaints_by_status(status):
    """Get complaints filtered by status for officials"""
    try:
        db = get_db()
        complaints_ref = db.collection('complaints')
        
        # Handle 'all' case
        if status.lower() == 'all':
            complaints_docs = complaints_ref.stream()
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
            complaints_docs = complaints_ref.where('status', '==', target_status).stream()
        
        complaints_list = [doc.to_dict() for doc in complaints_docs]
        
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
        
        db = get_db()
        complaint_ref = db.collection('complaints').document(complaint_id)
        complaint_doc = complaint_ref.get()
        
        if not complaint_doc.exists:
            return jsonify({'success': False, 'message': 'Complaint not found'}), 404
        
        complaint = complaint_doc.to_dict()
        
        # Get old status for comparison
        old_status = complaint.get('status', 'New')
        
        # Update complaint
        update_data = {
            'status': status,
            'updated_at': datetime.now().isoformat(),
            'updated_by': session.get('user_uid')
        }
        if notes:
            update_data['status_notes'] = notes
        
        complaint_ref.update(update_data)
        
        # Send notification to the resident who filed the complaint
        resident_uid = complaint.get('user_uid')
        if resident_uid:
            user_ref = db.collection('users').document(resident_uid)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                resident_data = user_doc.to_dict()
                
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
                resident_notifications = resident_data.get('notifications', [])
                resident_notifications.append(notification)
                user_ref.update({'notifications': resident_notifications})
                
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
        db = get_db()
        users_ref = db.collection('users')
        users_docs = users_ref.where('role', '==', 'official').stream()
        
        officials = []
        for doc in users_docs:
            user = doc.to_dict()
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


# Get list of all residents for messaging (officials and admins)
@complaint_bp.route('/residents/list')
@login_required
def get_residents_list():
    try:
        user_role = session.get('user_role')
        is_admin = session.get('is_admin', False)
        
        if user_role not in ['official', 'admin'] and not is_admin:
            return jsonify({'error': 'Unauthorized'}), 403
        
        db = get_db()
        users_ref = db.collection('users')
        users_docs = users_ref.where('role', '==', 'resident').stream()
        
        residents = []
        for doc in users_docs:
            user = doc.to_dict()
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
    
    db = get_db()
    user_ref = db.collection('users').document(user_uid)
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        return jsonify([])
    
    user = user_doc.to_dict()
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

        db = get_db()
        users_ref = db.collection('users')
        
        # Find recipient by email
        recipient_docs = users_ref.where('email', '==', to_email).limit(1).stream()
        recipient_uid = None
        recipient_data = None
        
        for doc in recipient_docs:
            recipient_uid = doc.id
            recipient_data = doc.to_dict()
            break
        
        if not recipient_uid or not recipient_data:
            return jsonify({'success': False, 'error': 'Recipient not found'}), 404
        
        sender_uid = session.get('user_uid')
        sender_ref = db.collection('users').document(sender_uid)
        sender_doc = sender_ref.get()
        sender_data = sender_doc.to_dict() if sender_doc.exists else {}

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
        recipient_ref = db.collection('users').document(recipient_uid)
        recipient_messages = recipient_data.get('messages', [])
        recipient_messages.append(msg)
        recipient_ref.update({'messages': recipient_messages})
        
        # Also save message in sender's sent folder (create a copy marked as sent)
        sent_msg = msg.copy()
        sent_msg['isSent'] = True
        sender_messages = sender_data.get('messages', [])
        sender_messages.append(sent_msg)
        sender_ref.update({'messages': sender_messages})

        # Optionally add a notification for the recipient
        recipient_notifications = recipient_data.get('notifications', [])
        recipient_notifications.append({
            'id': str(uuid.uuid4())[:8],
            'timestamp': datetime.now().isoformat(),
            'title': f"New message: {subject[:40]}",
            'message': content[:140],
            'read': False
        })
        recipient_ref.update({'notifications': recipient_notifications})

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

    db = get_db()
    user_ref = db.collection('users').document(user_uid)
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        return jsonify([])
    
    user = user_doc.to_dict()
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
    db = get_db()
    user_ref = db.collection('users').document(user_uid)
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    user = user_doc.to_dict()
    updated = False
    
    if user.get('notifications'):
        notifications = user['notifications']
        for n in notifications:
            if n.get('id') == note_id:
                n['read'] = True
                updated = True
                break
    
    if updated:
        user_ref.update({'notifications': notifications})
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Notification not found'}), 404


@complaint_bp.route('/resident/stats')
@login_required
def get_resident_stats():
    """Get statistics for resident dashboard"""
    user_email = session.get('user_email')
    if not user_email:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        db = get_db()
        complaints_ref = db.collection('complaints')
        complaints_docs = complaints_ref.where('user_email', '==', user_email).stream()
        
        user_complaints = [doc.to_dict() for doc in complaints_docs]
        
        stats = {
            'open_cases': 0,
            'urgent_open': 0,
            'resolved': 0,
            'avg_resolution': 0,
            'resolution_times': []
        }
        
        for complaint in user_complaints:
            status = complaint.get('status', '')
            if status != 'Resolved' and status != 'Closed':
                stats['open_cases'] += 1
                urgency = complaint.get('urgency', 'Low')
                if urgency == 'High':
                    stats['urgent_open'] += 1
            elif status == 'Resolved':
                stats['resolved'] += 1
                # Calculate resolution time if we have both dates
                submitted_date = complaint.get('submitted_date')
                updates = complaint.get('updates', [])
                
                if submitted_date and updates:
                    # Find when it was resolved
                    resolved_date = None
                    for update in reversed(updates):
                        if update.get('to_status') == 'Resolved':
                            resolved_date = update.get('timestamp')
                            break
                    
                    if resolved_date:
                        try:
                            submitted = datetime.fromisoformat(submitted_date.replace('Z', '+00:00'))
                            resolved = datetime.fromisoformat(resolved_date.replace('Z', '+00:00'))
                            days = (resolved - submitted).days
                            if days >= 0:
                                stats['resolution_times'].append(days)
                        except Exception as e:
                            print(f"Error calculating resolution time: {e}")
        
        # Calculate average resolution time
        if stats['resolution_times']:
            stats['avg_resolution'] = round(sum(stats['resolution_times']) / len(stats['resolution_times']), 1)
        else:
            stats['avg_resolution'] = 0
        
        # Remove resolution_times from response (not needed in frontend)
        del stats['resolution_times']
        
        return jsonify(stats)
        
    except Exception as e:
        print(f"Error getting resident stats: {e}")
        return jsonify({
            'open_cases': 0,
            'urgent_open': 0,
            'resolved': 0,
            'avg_resolution': 0
        })
