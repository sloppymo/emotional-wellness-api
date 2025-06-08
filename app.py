# --- DM Review System API Endpoints ---

@app.route('/api/session/<session_id>/pending-responses', methods=['GET'])
def get_pending_responses(session_id):
    """Get pending responses for a session (DMs only) with pagination and filtering"""
    user_id = request.args.get('user_id')
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)  # Cap at 100
    priority_filter = request.args.get('priority', type=int)
    response_type_filter = request.args.get('response_type')
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    try:
        # Verify the user is the GM for this session
        session = Session.query.filter_by(id=session_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        if session.gm_user_id != user_id:
            return jsonify({'error': 'Only GMs can view pending responses'}), 403
        
        # Build query with filters
        query = PendingResponse.query.filter_by(session_id=session_id, status='pending')
        
        if priority_filter:
            query = query.filter(PendingResponse.priority == priority_filter)
        if response_type_filter:
            query = query.filter(PendingResponse.response_type == response_type_filter)
        
        # Order by priority (desc) then created_at (asc)
        query = query.order_by(PendingResponse.priority.desc(), PendingResponse.created_at.asc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        pending = pagination.items
        
        return jsonify({
            'items': [{
                'id': p.id,
                'user_id': p.user_id,
                'context': p.context,
                'ai_response': p.ai_response,
                'response_type': p.response_type,
                'priority': p.priority,
                'created_at': p.created_at.isoformat() if p.created_at else None
            } for p in pending],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
    
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/session/<session_id>/pending-responses/bulk', methods=['POST'])
def bulk_review_responses(session_id):
    """Bulk approve/reject/edit multiple pending responses"""
    data = request.json
    dm_user_id = data.get('user_id')
    action = data.get('action')  # 'approve', 'reject', 'edit'
    response_ids = data.get('response_ids', [])
    dm_notes = data.get('dm_notes', '')
    
    if not dm_user_id or not action or not response_ids:
        return jsonify({'error': 'user_id, action, and response_ids are required'}), 400
    
    if action not in ['approve', 'reject']:
        return jsonify({'error': 'Bulk operations only support approve/reject actions'}), 400
    
    try:
        # Verify the user is the GM for this session
        session = Session.query.filter_by(id=session_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        if session.gm_user_id != dm_user_id:
            return jsonify({'error': 'Only GMs can review responses'}), 403
        
        # Process each response
        results = []
        for response_id in response_ids:
            pending = PendingResponse.query.filter_by(id=response_id, session_id=session_id).first()
            if not pending:
                results.append({'id': response_id, 'status': 'error', 'message': 'Response not found'})
                continue
            
            if pending.status != 'pending':
                results.append({'id': response_id, 'status': 'error', 'message': 'Response already reviewed'})
                continue
            
            # Create review history entry
            original_response = pending.ai_response
            
            # Update pending response
            if action == 'approve':
                pending.status = 'approved'
                pending.final_response = pending.ai_response
            elif action == 'reject':
                pending.status = 'rejected'
                pending.final_response = None
            
            pending.dm_notes = dm_notes
            pending.reviewed_at = db.func.now()
            
            # Create review history
            history = ReviewHistory(
                pending_response_id=response_id,
                dm_user_id=dm_user_id,
                action=action,
                original_response=original_response,
                final_response=pending.final_response,
                notes=dm_notes
            )
            
            db.session.add(history)
            results.append({'id': response_id, 'status': 'success', 'action': action})
        
        db.session.commit()
        return jsonify({'results': results})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/session/<session_id>/pending-response/<response_id>/review', methods=['POST'])
def review_response(session_id, response_id):
    """DM reviews and approves/rejects/edits a pending response"""
    data = request.json
    dm_user_id = data.get('user_id')
    action = data.get('action')  # 'approve', 'reject', 'edit'
    final_response = data.get('final_response', '')
    dm_notes = data.get('dm_notes', '')
    
    if not dm_user_id or not action:
        return jsonify({'error': 'user_id and action are required'}), 400
    
    if action not in ['approve', 'reject', 'edit']:
        return jsonify({'error': 'Invalid action. Must be approve, reject, or edit'}), 400
    
    if action == 'edit' and not final_response:
        return jsonify({'error': 'final_response is required for edit action'}), 400
    
    try:
        # Verify the user is the GM for this session
        session = Session.query.filter_by(id=session_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        if session.gm_user_id != dm_user_id:
            return jsonify({'error': 'Only GMs can review responses'}), 403
        
        pending = PendingResponse.query.filter_by(id=response_id, session_id=session_id).first()
        if not pending:
            return jsonify({'error': 'Pending response not found'}), 404
        
        if pending.status != 'pending':
            return jsonify({'error': 'Response has already been reviewed'}), 400
        
        # Create review history entry
        original_response = pending.ai_response
        
        # Update pending response based on action
        if action == 'approve':
            pending.status = 'approved'
            pending.final_response = pending.ai_response
        elif action == 'reject':
            pending.status = 'rejected'
            pending.final_response = None
        elif action == 'edit':
            pending.status = 'edited'
            pending.final_response = final_response
        
        pending.dm_notes = dm_notes
        pending.reviewed_at = db.func.now()
        
        # Create review history
        history = ReviewHistory(
            pending_response_id=response_id,
            dm_user_id=dm_user_id,
            action=action,
            original_response=original_response,
            final_response=pending.final_response,
            notes=dm_notes
        )
        
        db.session.add(history)
        db.session.commit()
        
        return jsonify({
            'status': 'success', 
            'action': action,
            'response': {
                'id': pending.id,
                'final_response': pending.final_response,
                'dm_notes': pending.dm_notes,
                'reviewed_at': pending.reviewed_at.isoformat() if pending.reviewed_at else None
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/session/<session_id>/dm/analytics', methods=['GET'])
def get_dm_analytics(session_id):
    """Get DM analytics for review performance and queue status"""
    dm_user_id = request.args.get('user_id')
    
    if not dm_user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    try:
        # Verify the user is the GM for this session
        session = Session.query.filter_by(id=session_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        if session.gm_user_id != dm_user_id:
            return jsonify({'error': 'Only GMs can view analytics'}), 403
        
        # Queue statistics
        pending_count = PendingResponse.query.filter_by(session_id=session_id, status='pending').count()
        high_priority_count = PendingResponse.query.filter_by(
            session_id=session_id, status='pending', priority=3
        ).count()
        
        # Review history statistics
        total_reviewed = PendingResponse.query.filter(
            PendingResponse.session_id == session_id,
            PendingResponse.status.in_(['approved', 'rejected', 'edited'])
        ).count()
        
        approved_count = PendingResponse.query.filter_by(
            session_id=session_id, status='approved'
        ).count()
        
        rejected_count = PendingResponse.query.filter_by(
            session_id=session_id, status='rejected'
        ).count()
        
        edited_count = PendingResponse.query.filter_by(
            session_id=session_id, status='edited'
        ).count()
        
        # Average review time (for completed reviews)
        from sqlalchemy import func
        avg_review_time_query = db.session.query(
            func.avg(func.extract('epoch', PendingResponse.reviewed_at - PendingResponse.created_at))
        ).filter(
            PendingResponse.session_id == session_id,
            PendingResponse.reviewed_at.isnot(None)
        ).scalar()
        
        avg_review_time_minutes = round(avg_review_time_query / 60, 2) if avg_review_time_query else 0
        
        # Unread notifications count
        unread_notifications = DmNotification.query.filter_by(
            session_id=session_id,
            dm_user_id=dm_user_id,
            is_read=False
        ).count()
        
        return jsonify({
            'queue_status': {
                'pending_count': pending_count,
                'high_priority_count': high_priority_count
            },
            'review_stats': {
                'total_reviewed': total_reviewed,
                'approved_count': approved_count,
                'rejected_count': rejected_count,
                'edited_count': edited_count,
                'approval_rate': round(approved_count / total_reviewed * 100, 1) if total_reviewed > 0 else 0,
                'avg_review_time_minutes': avg_review_time_minutes
            },
            'notifications': {
                'unread_count': unread_notifications
            }
        })
    
    except Exception as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500 