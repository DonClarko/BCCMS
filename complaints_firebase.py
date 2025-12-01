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
        
        complaints_ref = db.reference(f'complaints/{complaint_id}')
        complaint = complaints_ref.get()
        
        if not complaint:
            return jsonify({'success': False, 'message': 'Complaint not found'}), 404
        
        # Update complaint
        complaint['status'] = status
        complaint['updated_at'] = datetime.now().isoformat()
        complaint['updated_by'] = session.get('user_uid')
        
        complaints_ref.set(complaint)
        
        return jsonify({'success': True, 'message': 'Complaint updated successfully'})
        
    except Exception as e:
        print(f"Error updating complaint: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
