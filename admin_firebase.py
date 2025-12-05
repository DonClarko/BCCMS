from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
from functools import wraps
from auth_firebase import login_required
from firebase_admin import firestore, auth as firebase_auth
from firebase_config import initialize_firebase, get_db
import uuid

initialize_firebase()

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to ensure user is admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_role') != 'official' or not session.get('is_admin', False):
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin/stats')
@login_required
@admin_required
def get_admin_stats():
    """Get dashboard statistics for admin"""
    try:
        db = get_db()
        
        # Get users
        users_ref = db.collection('users')
        users_docs = users_ref.stream()
        users_list = [doc.to_dict() for doc in users_docs]
        
        # Get complaints
        complaints_ref = db.collection('complaints')
        complaints_docs = complaints_ref.stream()
        complaints_list = [doc.to_dict() for doc in complaints_docs]
        
        # Count users by role
        residents_count = sum(1 for u in users_list if u.get('role') == 'resident')
        officials_count = sum(1 for u in users_list if u.get('role') == 'official')
        
        # Count complaints by status
        pending_count = sum(1 for c in complaints_list if c.get('status') in ['New', 'Pending', 'Pending Review', 'In Progress'])
        
        # For demo purposes - upcoming events
        events_count = 8
        
        return jsonify({
            'total_residents': residents_count,
            'total_officials': officials_count,
            'pending_requests': pending_count,
            'upcoming_events': events_count
        })
    except Exception as e:
        print(f"Error getting admin stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/recent-activity')
@login_required
@admin_required
def get_recent_activity():
    """Get recent activity for admin dashboard"""
    try:
        activities = []
        db = get_db()
        
        # Get recent users (last 10)
        users_ref = db.collection('users')
        users_docs = users_ref.stream()
        users_list = []
        for doc in users_docs:
            user = doc.to_dict()
            user['uid'] = doc.id
            users_list.append(user)
        
        # Sort by created_at
        users_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Add recent registrations to activities
        for user in users_list[:3]:
            created_at = user.get('created_at', '')
            if created_at:
                try:
                    created_time = datetime.fromisoformat(created_at)
                    time_diff = datetime.now() - created_time
                    
                    if time_diff.days > 0:
                        timestamp = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
                    elif time_diff.seconds // 3600 > 0:
                        hours = time_diff.seconds // 3600
                        timestamp = f"{hours} hour{'s' if hours > 1 else ''} ago"
                    else:
                        minutes = time_diff.seconds // 60
                        timestamp = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
                    
                    activities.append({
                        'type': 'new_user',
                        'icon': 'user-plus',
                        'message': f'New {user.get("role", "user")} registered: {user.get("full_name", "Unknown")}',
                        'timestamp': timestamp
                    })
                except:
                    pass
        
        # Get recent complaints
        complaints_ref = db.collection('complaints')
        complaints_docs = complaints_ref.stream()
        complaints_list = [doc.to_dict() for doc in complaints_docs]
        
        complaints_list.sort(key=lambda x: x.get('submitted_date', ''), reverse=True)
        
        # Add recent complaint updates
        for complaint in complaints_list[:2]:
            submitted_date = complaint.get('submitted_date', '')
            if submitted_date:
                try:
                    submitted_time = datetime.fromisoformat(submitted_date)
                    time_diff = datetime.now() - submitted_time
                    
                    if time_diff.days > 0:
                        timestamp = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
                    elif time_diff.seconds // 3600 > 0:
                        hours = time_diff.seconds // 3600
                        timestamp = f"{hours} hour{'s' if hours > 1 else ''} ago"
                    else:
                        minutes = time_diff.seconds // 60
                        timestamp = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
                    
                    if complaint.get('status') == 'Resolved':
                        activities.append({
                            'type': 'document',
                            'icon': 'check-circle',
                            'message': f'Complaint resolved: {complaint.get("title", "Untitled")}',
                            'timestamp': timestamp
                        })
                    else:
                        activities.append({
                            'type': 'document',
                            'icon': 'file-alt',
                            'message': f'New complaint: {complaint.get("title", "Untitled")}',
                            'timestamp': timestamp
                        })
                except:
                    pass
        
        # Sort all activities by timestamp relevance
        return jsonify(activities[:5])
        
    except Exception as e:
        print(f"Error getting recent activity: {str(e)}")
        return jsonify([])

@admin_bp.route('/admin/complaints')
@login_required
@admin_required
def get_admin_complaints():
    """Get all complaints for admin dashboard"""
    try:
        db = get_db()
        complaints_ref = db.collection('complaints')
        complaints_docs = complaints_ref.stream()
        
        complaints_data = {}
        for doc in complaints_docs:
            complaints_data[doc.id] = doc.to_dict()
        
        if not complaints_data:
            return jsonify([])
        
        # Get users for name lookup
        users_ref = db.collection('users')
        users_docs = users_ref.stream()
        users_data = {doc.id: doc.to_dict() for doc in users_docs}
        
        complaints_list = []
        for complaint_id, complaint in complaints_data.items():
            # Get resident name and email
            user_uid = complaint.get('user_uid')
            resident_name = 'Unknown'
            resident_email = ''
            if user_uid and user_uid in users_data:
                resident_name = users_data[user_uid].get('full_name', 'Unknown')
                resident_email = users_data[user_uid].get('email', '')
            
            complaints_list.append({
                'id': complaint.get('id', complaint_id),
                'title': complaint.get('title', 'Untitled'),
                'resident': resident_name,
                'resident_email': resident_email,
                'date': complaint.get('submitted_date', ''),
                'status': complaint.get('status', 'New')
            })
        
        # Sort by date (newest first)
        complaints_list.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return jsonify(complaints_list[:10])  # Return top 10
        
    except Exception as e:
        print(f"Error getting admin complaints: {str(e)}")
        return jsonify([])

@admin_bp.route('/admin/users')
@login_required
@admin_required
def get_admin_users():
    """Get all users for admin dashboard (excludes admin users and pending/rejected)"""
    try:
        db = get_db()
        users_ref = db.collection('users')
        users_docs = users_ref.stream()
        
        users_list = []
        for doc in users_docs:
            user = doc.to_dict()
            uid = doc.id
            
            # Skip admin users - they should not appear in user management
            if user.get('is_admin', False):
                continue
            
            # Skip pending or rejected users - they should be in pending registrations section
            if user.get('status') in ['pending_approval', 'rejected']:
                continue
                
            users_list.append({
                'uid': uid,
                'name': user.get('full_name', 'Unknown'),
                'email': user.get('email', ''),
                'role': user.get('role', 'resident'),
                'is_admin': user.get('is_admin', False),
                'status': user.get('status', 'approved')
            })
        
        # Sort by name
        users_list.sort(key=lambda x: x.get('name', ''))
        
        return jsonify(users_list[:10])  # Return top 10
        
    except Exception as e:
        print(f"Error getting admin users: {str(e)}")
        return jsonify([])

@admin_bp.route('/admin/analytics')
@login_required
@admin_required
def get_complaint_analytics():
    """Get complaint analytics for admin"""
    try:
        db = get_db()
        complaints_ref = db.collection('complaints')
        complaints_docs = complaints_ref.stream()
        complaints_list = [doc.to_dict() for doc in complaints_docs]
        
        if not complaints_list:
            return jsonify({
                'total': 0,
                'resolved': 0,
                'in_progress': 0,
                'escalated': 0,
                'resolved_percentage': 0,
                'in_progress_percentage': 0,
                'escalated_percentage': 0,
                'avg_resolution_time': 0,
                'fastest_resolution': 0,
                'pending': 0,
                'sla_compliance': 0
            })
        
        total = len(complaints_list)
        
        # Count by status
        resolved = sum(1 for c in complaints_list if c.get('status') == 'Resolved')
        in_progress = sum(1 for c in complaints_list if c.get('status') == 'In Progress')
        escalated = sum(1 for c in complaints_list if c.get('status') == 'Escalated')
        pending = sum(1 for c in complaints_list if c.get('status') in ['New', 'Pending', 'Pending Review'])
        
        # Calculate percentages
        resolved_pct = round((resolved / total * 100)) if total > 0 else 0
        in_progress_pct = round((in_progress / total * 100)) if total > 0 else 0
        escalated_pct = round((escalated / total * 100)) if total > 0 else 0
        
        # Calculate resolution times (for resolved complaints)
        resolution_times = []
        for complaint in complaints_list:
            if complaint.get('status') == 'Resolved':
                submitted = complaint.get('submitted_date')
                updated = complaint.get('updated_at')
                if submitted and updated:
                    try:
                        submit_time = datetime.fromisoformat(submitted)
                        resolve_time = datetime.fromisoformat(updated)
                        diff = (resolve_time - submit_time).total_seconds() / 3600  # hours
                        resolution_times.append(diff)
                    except:
                        pass
        
        avg_resolution = round(sum(resolution_times) / len(resolution_times) / 24, 1) if resolution_times else 0
        fastest = round(min(resolution_times), 1) if resolution_times else 0
        
        # SLA compliance (assuming 7 days is the SLA)
        sla_compliant = sum(1 for t in resolution_times if t <= 168)  # 7 days = 168 hours
        sla_compliance = round((sla_compliant / len(resolution_times) * 100)) if resolution_times else 0
        
        return jsonify({
            'total': total,
            'resolved': resolved,
            'in_progress': in_progress,
            'escalated': escalated,
            'resolved_percentage': resolved_pct,
            'in_progress_percentage': in_progress_pct,
            'escalated_percentage': escalated_pct,
            'avg_resolution_time': avg_resolution,
            'fastest_resolution': fastest,
            'pending': pending,
            'sla_compliance': sla_compliance
        })
        
    except Exception as e:
        print(f"Error getting complaint analytics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/user/<uid>')
@login_required
@admin_required
def get_user_details(uid):
    """Get user details for viewing"""
    try:
        db = get_db()
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        user_data = user_doc.to_dict()
        
        # Return user details (excluding sensitive data like password)
        return jsonify({
            'success': True,
            'user': {
                'uid': uid,
                'full_name': user_data.get('full_name', 'Unknown'),
                'email': user_data.get('email', ''),
                'phone': user_data.get('phone', 'N/A'),
                'role': user_data.get('role', 'resident'),
                'status': user_data.get('status', 'approved'),
                'created_at': user_data.get('created_at', ''),
                'approved_at': user_data.get('approved_at', ''),
                'is_admin': user_data.get('is_admin', False)
            }
        })
        
    except Exception as e:
        print(f"Error getting user details: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/admin/user/delete', methods=['POST'])
@login_required
@admin_required
def delete_user():
    """Delete a user (admin only)"""
    try:
        data = request.get_json()
        user_uid = data.get('uid')
        
        if not user_uid:
            return jsonify({'success': False, 'message': 'User UID required'}), 400
        
        # Don't allow deleting yourself
        if user_uid == session.get('user_uid'):
            return jsonify({'success': False, 'message': 'Cannot delete your own account'}), 400
        
        # Delete from Firebase Auth
        firebase_auth.delete_user(user_uid)
        
        # Delete from Firestore
        db = get_db()
        user_ref = db.collection('users').document(user_uid)
        user_ref.delete()
        
        return jsonify({'success': True, 'message': 'User deleted successfully'})
        
    except Exception as e:
        print(f"Error deleting user: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/admin/complaint/delete', methods=['POST'])
@login_required
@admin_required
def delete_complaint():
    """Delete a complaint (admin only)"""
    try:
        data = request.get_json()
        complaint_id = data.get('id')
        
        if not complaint_id:
            return jsonify({'success': False, 'message': 'Complaint ID required'}), 400
        
        db = get_db()
        
        # Try to delete by document ID (which is the complaint_id)
        complaint_ref = db.collection('complaints').document(complaint_id)
        complaint_doc = complaint_ref.get()
        
        if complaint_doc.exists:
            complaint_ref.delete()
            return jsonify({'success': True, 'message': 'Complaint deleted successfully'})
        
        # If not found by ID, search by 'id' field
        complaints_query = db.collection('complaints').where('id', '==', complaint_id).limit(1).stream()
        
        for doc in complaints_query:
            db.collection('complaints').document(doc.id).delete()
            return jsonify({'success': True, 'message': 'Complaint deleted successfully'})
        
        return jsonify({'success': False, 'message': 'Complaint not found'}), 404
        
    except Exception as e:
        print(f"Error deleting complaint: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/residents/list')
@login_required
@admin_required
def get_residents_list():
    """Get list of all residents for messaging"""
    try:
        db = get_db()
        users_ref = db.collection('users')
        users_docs = users_ref.where('role', '==', 'resident').stream()
        
        residents_list = []
        for doc in users_docs:
            user = doc.to_dict()
            residents_list.append({
                'uid': doc.id,
                'name': user.get('full_name', 'Unknown'),
                'email': user.get('email', '')
            })
        
        # Sort by name
        residents_list.sort(key=lambda x: x.get('name', ''))
        
        return jsonify(residents_list)
        
    except Exception as e:
        print(f"Error getting residents list: {str(e)}")
        return jsonify([])

@admin_bp.route('/notifications/list')
@login_required
@admin_required
def get_notifications_list():
    """Get notifications for admin"""
    try:
        db = get_db()
        notifications_ref = db.collection('notifications')
        notifications_docs = notifications_ref.stream()
        
        notifications_list = []
        for doc in notifications_docs:
            notification = doc.to_dict()
            notification['id'] = doc.id
            notifications_list.append(notification)
        
        # Sort by timestamp (newest first)
        notifications_list.sort(key=lambda x: x.get('created_at', x.get('timestamp', '')), reverse=True)
        
        return jsonify(notifications_list[:50])  # Return latest 50
        
    except Exception as e:
        print(f"Error getting notifications: {str(e)}")
        return jsonify([])

@admin_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
@admin_required
def mark_notification_read():
    """Mark a notification as read"""
    try:
        data = request.get_json()
        notification_id = data.get('notification_id')
        
        if not notification_id:
            return jsonify({'success': False, 'message': 'Notification ID required'}), 400
        
        db = get_db()
        notification_ref = db.collection('notifications').document(notification_id)
        notification_ref.update({'read': True})
        
        return jsonify({'success': True, 'message': 'Notification marked as read'})
        
    except Exception as e:
        print(f"Error marking notification as read: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
@admin_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    try:
        db = get_db()
        notifications_ref = db.collection('notifications')
        notifications_docs = notifications_ref.stream()
        
        # Update all notifications
        for doc in notifications_docs:
            db.collection('notifications').document(doc.id).update({'read': True})
        
        return jsonify({'success': True, 'message': 'All notifications marked as read'})
        
    except Exception as e:
        print(f"Error marking all notifications as read: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ============ PENDING REGISTRATIONS MANAGEMENT ============

@admin_bp.route('/admin/pending-registrations')
@login_required
@admin_required
def get_pending_registrations():
    """Get all pending official registrations for admin approval"""
    try:
        db = get_db()
        users_ref = db.collection('users')
        # Query for officials with pending_approval status
        users_docs = users_ref.where('role', '==', 'official').where('status', '==', 'pending_approval').stream()
        
        pending_list = []
        for doc in users_docs:
            user = doc.to_dict()
            pending_list.append({
                'uid': doc.id,
                'name': user.get('full_name', 'Unknown'),
                'email': user.get('email', ''),
                'phone': user.get('phone', ''),
                'created_at': user.get('created_at', '')
            })
        
        # Sort by created_at (newest first)
        pending_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify(pending_list)
        
    except Exception as e:
        print(f"Error getting pending registrations: {str(e)}")
        return jsonify([])

@admin_bp.route('/admin/approve-registration/<uid>', methods=['POST'])
@login_required
@admin_required
def approve_registration(uid):
    """Approve a pending official registration"""
    try:
        db = get_db()
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        user_data = user_doc.to_dict()
        
        if user_data.get('status') != 'pending_approval':
            return jsonify({'success': False, 'message': 'User is not pending approval'}), 400
        
        # Update user status to approved
        user_ref.update({
            'status': 'approved',
            'approved_at': datetime.now().isoformat(),
            'approved_by': session.get('user_uid')
        })
        
        return jsonify({
            'success': True, 
            'message': f'Registration approved for {user_data.get("full_name", "user")}'
        })
        
    except Exception as e:
        print(f"Error approving registration: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/admin/reject-registration/<uid>', methods=['POST'])
@login_required
@admin_required
def reject_registration(uid):
    """Reject a pending official registration"""
    try:
        db = get_db()
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        user_data = user_doc.to_dict()
        
        if user_data.get('status') != 'pending_approval':
            return jsonify({'success': False, 'message': 'User is not pending approval'}), 400
        
        # Update user status to rejected
        user_ref.update({
            'status': 'rejected',
            'rejected_at': datetime.now().isoformat(),
            'rejected_by': session.get('user_uid')
        })
        
        return jsonify({
            'success': True, 
            'message': f'Registration rejected for {user_data.get("full_name", "user")}'
        })
        
    except Exception as e:
        print(f"Error rejecting registration: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/admin/pending-count')
@login_required
@admin_required
def get_pending_count():
    """Get count of pending registrations"""
    try:
        db = get_db()
        users_ref = db.collection('users')
        users_docs = users_ref.where('role', '==', 'official').where('status', '==', 'pending_approval').stream()
        
        pending_count = sum(1 for _ in users_docs)
        
        return jsonify({'count': pending_count})
        
    except Exception as e:
        print(f"Error getting pending count: {str(e)}")
        return jsonify({'count': 0})

@admin_bp.route('/admin/user/toggle-block', methods=['POST'])
@login_required
@admin_required
def toggle_block_user():
    """Block or unblock a user"""
    try:
        data = request.get_json()
        uid = data.get('uid')
        action = data.get('action')  # 'block' or 'unblock'
        
        if not uid or action not in ['block', 'unblock']:
            return jsonify({'success': False, 'message': 'Invalid request'}), 400
        
        db = get_db()
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        user_data = user_doc.to_dict()
        
        # Don't allow blocking admins
        if user_data.get('is_admin', False):
            return jsonify({'success': False, 'message': 'Cannot block admin users'}), 400
        
        # Don't allow blocking yourself
        if uid == session.get('user_uid'):
            return jsonify({'success': False, 'message': 'Cannot block yourself'}), 400
        
        if action == 'block':
            user_ref.update({
                'status': 'blocked',
                'blocked_at': datetime.now().isoformat(),
                'blocked_by': session.get('user_uid')
            })
            message = f'User {user_data.get("full_name", "Unknown")} has been blocked'
        else:
            user_ref.update({
                'status': 'approved',
                'unblocked_at': datetime.now().isoformat(),
                'unblocked_by': session.get('user_uid')
            })
            message = f'User {user_data.get("full_name", "Unknown")} has been unblocked'
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        print(f"Error toggling block status: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
