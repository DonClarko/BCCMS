from flask import Blueprint, request, jsonify, session
from firebase_admin import db
from datetime import datetime
from auth_firebase import login_required
import json

feedback_bp = Blueprint('feedback', __name__, url_prefix='/feedback')

@feedback_bp.route('/submit', methods=['POST'])
@login_required
def submit_feedback():
    """Submit feedback from residents"""
    try:
        # Get form data
        feedback_type = request.form.get('feedback-type')
        rating = request.form.get('rating')
        message = request.form.get('feedback-message')
        contact_me = request.form.get('contact-me') == 'on'
        complaint_id = request.form.get('complaint_id', '')
        
        # Validate required fields
        if not feedback_type or not rating or not message:
            return jsonify({
                'success': False,
                'message': 'Please fill in all required fields'
            }), 400
        
        # Get user information from session
        user_id = session.get('user_id')
        user_name = session.get('user_name', 'Anonymous')
        user_email = session.get('user_email', '')
        
        # Create feedback object
        feedback_data = {
            'user_id': user_id,
            'user_name': user_name,
            'user_email': user_email if contact_me else '',
            'feedback_type': feedback_type,
            'rating': int(rating),
            'message': message,
            'contact_me': contact_me,
            'complaint_id': complaint_id,
            'submitted_date': datetime.now().isoformat(),
            'status': 'new'
        }
        
        # Save to Firebase
        feedback_ref = db.reference('feedback')
        new_feedback = feedback_ref.push(feedback_data)
        feedback_id = new_feedback.key
        
        # Update the feedback with its ID
        feedback_ref.child(feedback_id).update({'id': feedback_id})
        
        return jsonify({
            'success': True,
            'message': 'Thank you for your feedback!',
            'feedback_id': feedback_id
        }), 200
        
    except Exception as e:
        print(f"Error submitting feedback: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500


@feedback_bp.route('/recent', methods=['GET'])
@login_required
def get_recent_feedback():
    """Get recent feedback (for officials and admins)"""
    try:
        # Check if user is an official or admin
        user_role = session.get('user_role')
        is_admin = session.get('is_admin', False)
        
        if user_role not in ['official', 'admin'] and not is_admin:
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        
        # Get feedback from Firebase
        feedback_ref = db.reference('feedback')
        feedback_data = feedback_ref.get()
        
        if not feedback_data:
            return jsonify([]), 200
        
        # Convert to list and sort by date
        feedback_list = []
        for feedback_id, feedback in feedback_data.items():
            if isinstance(feedback, dict):
                feedback['id'] = feedback_id
                feedback_list.append(feedback)
        
        # Sort by submitted_date (most recent first)
        feedback_list.sort(key=lambda x: x.get('submitted_date', ''), reverse=True)
        
        return jsonify(feedback_list), 200
        
    except Exception as e:
        print(f"Error getting feedback: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500


@feedback_bp.route('/my-feedback', methods=['GET'])
@login_required
def get_my_feedback():
    """Get feedback submitted by the current user"""
    try:
        user_id = session.get('user_id')
        
        # Get all feedback from Firebase
        feedback_ref = db.reference('feedback')
        feedback_data = feedback_ref.get()
        
        if not feedback_data:
            return jsonify([]), 200
        
        # Filter feedback by user_id
        my_feedback = []
        for feedback_id, feedback in feedback_data.items():
            if isinstance(feedback, dict) and feedback.get('user_id') == user_id:
                feedback['id'] = feedback_id
                my_feedback.append(feedback)
        
        # Sort by submitted_date (most recent first)
        my_feedback.sort(key=lambda x: x.get('submitted_date', ''), reverse=True)
        
        return jsonify(my_feedback), 200
        
    except Exception as e:
        print(f"Error getting my feedback: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500


@feedback_bp.route('/reply', methods=['POST'])
@login_required
def reply_to_feedback():
    """Reply to feedback (for officials)"""
    try:
        # Check if user is an official
        user_role = session.get('user_role')
        if user_role != 'official':
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        
        data = request.get_json()
        feedback_id = data.get('feedback_id')
        reply_message = data.get('reply_message')
        
        if not feedback_id or not reply_message:
            return jsonify({
                'success': False,
                'message': 'Feedback ID and reply message are required'
            }), 400
        
        # Update feedback with reply
        feedback_ref = db.reference(f'feedback/{feedback_id}')
        feedback_ref.update({
            'reply': reply_message,
            'replied_by': session.get('user_name'),
            'replied_date': datetime.now().isoformat(),
            'status': 'replied'
        })
        
        return jsonify({
            'success': True,
            'message': 'Reply sent successfully'
        }), 200
        
    except Exception as e:
        print(f"Error replying to feedback: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500


@feedback_bp.route('/filter', methods=['GET'])
@login_required
def filter_feedback():
    """Filter feedback by rating category (for officials)"""
    try:
        # Check if user is an official
        user_role = session.get('user_role')
        if user_role != 'official':
            return jsonify({
                'success': False,
                'message': 'Access denied'
            }), 403
        
        filter_type = request.args.get('type', 'all')
        
        # Get feedback from Firebase
        feedback_ref = db.reference('feedback')
        feedback_data = feedback_ref.get()
        
        if not feedback_data:
            return jsonify([]), 200
        
        # Convert to list
        feedback_list = []
        for feedback_id, feedback in feedback_data.items():
            if isinstance(feedback, dict):
                feedback['id'] = feedback_id
                feedback_list.append(feedback)
        
        # Filter based on rating
        if filter_type == 'positive':
            feedback_list = [f for f in feedback_list if f.get('rating', 0) >= 4]
        elif filter_type == 'neutral':
            feedback_list = [f for f in feedback_list if f.get('rating', 0) == 3]
        elif filter_type == 'negative':
            feedback_list = [f for f in feedback_list if f.get('rating', 0) <= 2]
        elif filter_type == 'recent':
            # Already sorted by date, just limit to 10
            pass
        
        # Sort by submitted_date (most recent first)
        feedback_list.sort(key=lambda x: x.get('submitted_date', ''), reverse=True)
        
        return jsonify(feedback_list), 200
        
    except Exception as e:
        print(f"Error filtering feedback: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500
