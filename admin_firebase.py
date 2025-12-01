from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
from functools import wraps
from auth_firebase import login_required
from firebase_admin import db, auth as firebase_auth
from firebase_config import initialize_firebase
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
        users_ref = db.reference('users')
        users_data = users_ref.get() or {}
        
        complaints_ref = db.reference('complaints')
        complaints_data = complaints_ref.get() or {}
        
        # Count users by role
        residents_count = sum(1 for u in users_data.values() if u.get('role') == 'resident')
        officials_count = sum(1 for u in users_data.values() if u.get('role') == 'official')
        
        # Count complaints by status
        complaints_list = list(complaints_data.values()) if complaints_data else []
        pending_count = sum(1 for c in complaints_list if c.get('status') in ['New', 'Pending', 'Pending Review', 'In Progress'])
        
        # For demo purposes - upcoming events (you can integrate real events later)
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
        
        # Get recent users (last 10)
        users_ref = db.reference('users')
        users_data = users_ref.get() or {}
        users_list = []
        for uid, user in users_data.items():
            user['uid'] = uid
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
        complaints_ref = db.reference('complaints')
        complaints_data = complaints_ref.get() or {}
        complaints_list = []
        for complaint in complaints_data.values():
            complaints_list.append(complaint)
        
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
        complaints_ref = db.reference('complaints')
        complaints_data = complaints_ref.get() or {}
        
        if not complaints_data:
            return jsonify([])
        
        complaints_list = []
        users_ref = db.reference('users')
        users_data = users_ref.get() or {}
        
        for complaint_id, complaint in complaints_data.items():
            # Get resident name
            user_uid = complaint.get('user_uid')
            resident_name = 'Unknown'
            if user_uid and user_uid in users_data:
                resident_name = users_data[user_uid].get('full_name', 'Unknown')
            
            complaints_list.append({
                'id': complaint.get('id', complaint_id),
                'title': complaint.get('title', 'Untitled'),
                'resident': resident_name,
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
    """Get all users for admin dashboard"""
    try:
        users_ref = db.reference('users')
        users_data = users_ref.get() or {}
        
        if not users_data:
            return jsonify([])
        
        users_list = []
        for uid, user in users_data.items():
            users_list.append({
                'uid': uid,
                'name': user.get('full_name', 'Unknown'),
                'email': user.get('email', ''),
                'role': user.get('role', 'resident'),
                'is_admin': user.get('is_admin', False)
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
        complaints_ref = db.reference('complaints')
        complaints_data = complaints_ref.get() or {}
        
        if not complaints_data:
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
        
        complaints_list = list(complaints_data.values())
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
        
        # Delete from Realtime Database
        user_ref = db.reference(f'users/{user_uid}')
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
        
        # Find and delete from Realtime Database
        complaints_ref = db.reference('complaints')
        complaints_data = complaints_ref.get() or {}
        
        # Find the complaint key
        complaint_key = None
        for key, complaint in complaints_data.items():
            if complaint.get('id') == complaint_id:
                complaint_key = key
                break
        
        if complaint_key:
            complaint_ref = db.reference(f'complaints/{complaint_key}')
            complaint_ref.delete()
            return jsonify({'success': True, 'message': 'Complaint deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Complaint not found'}), 404
        
    except Exception as e:
        print(f"Error deleting complaint: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
