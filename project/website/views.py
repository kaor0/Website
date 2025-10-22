import os 
from flask import Blueprint, redirect, render_template, request, flash , jsonify, current_app, url_for
from flask_login import login_required, current_user
from .models import Note, FlappyScore
from . import UPLOAD_FOLDER, db
import json
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note_data = request.form.get('note')
        file = request.files.get('file')
        subject = request.form.get('subject', 'General')

        file_name = None
        if file and file.filename != '':
            file_name = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, file_name))

        new_note = Note(
            data=note_data, 
            user_id=current_user.id, 
            file_name=file_name, 
            public=False,
            subject=subject
        )
        db.session.add(new_note)
        db.session.commit()
        flash('Note added successfully!', 'success')
        return redirect(url_for('views.home'))

    return render_template("home.html", user=current_user)

@views.route('/delete-note', methods=['POST'])
@login_required
def delete_note():
    try:
        data = json.loads(request.data)
        noteId = data.get('noteId')
        print(f"🎯 DELETE REQUEST - Note ID: {noteId}, Current User ID: {current_user.id}")
        
        note = Note.query.get(noteId)
        
        if not note:
            print("❌ Note not found")
            return jsonify({'error': 'Note not found'}), 404
        
        print(f"📝 Note found - Note User ID: {note.user_id}, Current User ID: {current_user.id}")
        
        if note.user_id != current_user.id:
            print("🚫 Authorization failed: User doesn't own this note")
            return jsonify({'error': 'Not authorized'}), 403
        
        # Delete the file if it exists
        if note.file_name:
            file_path = os.path.join(UPLOAD_FOLDER, note.file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🗑️ Deleted file: {note.file_name}")
        
        db.session.delete(note)
        db.session.commit()
        print("✅ Note deleted successfully")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"💥 Error in delete_note: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'txt','pdf','png','jpg','jpeg','docx'}

@views.route('/upload', methods=['POST'])
@login_required
def upload_file():
    file = request.files.get('file')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # FIXED: Use current_app instead of app
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        
        # Create a note entry in the database
        new_note = Note(data=f"Uploaded file: {filename}", file_name=filename, user_id=current_user.id)
        db.session.add(new_note)
        db.session.commit()
        
        flash('File uploaded successfully!', 'success')
    else:
        flash('Invalid file type!', 'error')
    
    return redirect(url_for('views.home'))

@views.route('/notes')
@login_required
def notes():
    shared_notes = Note.query.filter_by(public=True).all()
    return render_template("note.html", notes=shared_notes, user=current_user)

@views.route('/toggle-share', methods=['POST'])
@login_required
def toggle_share():
    try:
        data = json.loads(request.data)
        note_id = data.get('noteId')
        make_public = data.get('public')
        
        print(f"🎯 TOGGLE SHARE - Note ID: {note_id}, Make Public: {make_public}, User: {current_user.id}")
        
        note = Note.query.get(note_id)
        
        if not note:
            print("❌ Note not found")
            return jsonify({'error': 'Note not found'}), 404
        
        if note.user_id != current_user.id:
            print("🚫 Authorization failed")
            return jsonify({'error': 'Not authorized'}), 403
        
        note.public = make_public
        db.session.commit()
        
        print("✅ Share status updated successfully")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"💥 Error in toggle_share: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

# ==================== FLAPPY BIRD LEADERBOARD ROUTES ====================
@views.route('/submit-flappy-score', methods=['POST'])
@login_required
def submit_flappy_score():
    try:
        data = request.get_json()
        score = data.get('score', 0)
        
        print(f"🎯 SUBMIT SCORE - User: {current_user.first_name}, Score: {score}")
        
        # Always save the score (for statistics)
        new_score = FlappyScore(
            score=score,
            player_name=current_user.first_name,
            user_id=current_user.id
        )
        db.session.add(new_score)
        db.session.commit()
        
        print(f"✅ Score saved: {score}")
        return jsonify({'success': True, 'message': 'Score saved!'})
        
    except Exception as e:
        db.session.rollback()
        print(f"💥 Error submitting score: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@views.route('/flappy-leaderboard')
def get_flappy_leaderboard():
    try:
        # Get the highest score for each player (only show best)
        subquery = db.session.query(
            FlappyScore.player_name,
            db.func.max(FlappyScore.score).label('max_score')
        ).group_by(FlappyScore.player_name).subquery()
        
        leaderboard = db.session.query(FlappyScore).join(
            subquery,
            db.and_(
                FlappyScore.player_name == subquery.c.player_name,
                FlappyScore.score == subquery.c.max_score
            )
        ).order_by(FlappyScore.score.desc()).limit(10).all()
        
        # Rest of the stats calculation remains the same...
        today = datetime.utcnow().date()
        start_of_day = datetime(today.year, today.month, today.day)
        
        players_today = db.session.query(FlappyScore.player_name).filter(
            FlappyScore.date_achieved >= start_of_day
        ).distinct().count()
        
        total_games = FlappyScore.query.count()
        total_players = db.session.query(FlappyScore.player_name).distinct().count()
        
        leaderboard_data = []
        for score in leaderboard:
            leaderboard_data.append({
                'player_name': score.player_name,
                'score': score.score,
                'date_achieved': score.date_achieved.isoformat()
            })
        
        print(f"📊 Leaderboard loaded - {len(leaderboard_data)} best scores from {total_players} players")
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard_data,
            'stats': {
                'players_today': players_today,
                'games_played': total_games,
                'total_players': total_players
            }
        })
        
    except Exception as e:
        print(f"💥 Error loading leaderboard: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500@views.route('/flappy-bird')
@login_required
def flappy_bird():
    return render_template("flappy_bird.html", user=current_user)