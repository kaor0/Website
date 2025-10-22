import datetime
import os
import json
from flask import Blueprint, current_app, render_template, request, flash, redirect, send_file, url_for, jsonify
from sqlalchemy import func
from .models import Game, Student, User, Teacher, FlappyScore  # Added FlappyScore here
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from . import db
from flask_login import login_user, logout_user, login_required, current_user
import zipfile

# ================== GAMES CONFIGURATION ==================
GAMES_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'games')

# Create games folder if it doesn't exist
if not os.path.exists(GAMES_FOLDER):
    os.makedirs(GAMES_FOLDER)

auth = Blueprint('auth', __name__)

# ---------------- LOGIN -----------------
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)

# ---------------- LOGOUT -----------------
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', category='success')
    return redirect(url_for('auth.login'))

# ---------------- SIGN UP -----------------
@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()

        if user:
            flash('Email already exists.', category='error')
        elif not email or len(email.strip()) <= 4:
            flash('Email must be greater than 4 characters.', category='error')
        elif not first_name or len(first_name.strip()) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords dont match.', category='error')
        elif not password1 or len(password1) < 8:
            flash('Password must be at least 8 characters.', category='error')
        else:
            new_user = User(
                email=email,
                first_name=first_name,
                password=generate_password_hash(password1, method='pbkdf2:sha256')
            )
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully!', category='success')
            login_user(new_user, remember=True)
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", user=current_user)

# ---------------- STUDENT ROUTES -----------------
@auth.route('/stdu')
@login_required
def students_page():
    students = Student.query.order_by(Student.position.asc()).all()
    return render_template("students.html", students=students, user=current_user)

@auth.route('/add-student', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        contact = request.form.get('contact')
        class_section = request.form.get('class_section')
        email = request.form.get('email')
        profile_pic = request.files.get('profile_pic')

        if not name or not age or not contact or not class_section:
            flash('Please fill all required fields', 'error')
            return render_template("add_student.html", user=current_user)

        profile_pic_name = None
        if profile_pic and profile_pic.filename != '':
            profile_pic_name = secure_filename(profile_pic.filename)
            profile_pic.save(os.path.join(current_app.config['UPLOAD_FOLDER'], profile_pic_name))

        # Get the next position for ordering
        last_student = Student.query.filter_by(user_id=current_user.id).order_by(Student.position.desc()).first()
        next_position = last_student.position + 1 if last_student else 0

        new_student = Student(
            name=name,
            age=age,
            contact=contact,
            class_section=class_section,
            email=email if email else None,
            profile_pic=profile_pic_name,
            user_id=current_user.id,
            position=next_position
        )
        
        db.session.add(new_student)
        db.session.commit()
        flash('Student added successfully!', 'success')
        return redirect(url_for('auth.students_page'))

    return render_template("add_student.html", user=current_user)

@auth.route('/delete-student', methods=['POST'])
@login_required
def delete_student():
    try:
        data = json.loads(request.data)
        student_id = data.get('studentId')
        
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        if student.user_id != current_user.id:
            return jsonify({'error': 'Not authorized to delete this student'}), 403
        
        # Delete profile picture if exists
        if student.profile_pic:
            profile_pic_path = os.path.join(current_app.config['UPLOAD_FOLDER'], student.profile_pic)
            if os.path.exists(profile_pic_path):
                os.remove(profile_pic_path)
        
        # Delete student from database
        db.session.delete(student)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@auth.route('/reorder-students', methods=['POST'])
@login_required
def reorder_students():
    try:
        data = json.loads(request.data)
        student_order = data.get('studentOrder', [])
        
        # Update positions for all students
        for position, student_id in enumerate(student_order):
            student = Student.query.get(student_id)
            if student and student.user_id == current_user.id:
                student.position = position
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Server error'}), 500

# ---------------- TEACHER ROUTES -----------------
@auth.route('/teacher')
@login_required
def teachers_page():
    teachers = Teacher.query.order_by(Teacher.position.asc()).all()
    return render_template("teachers.html", teachers=teachers, user=current_user)

@auth.route('/add-teacher', methods=['GET', 'POST'])
@login_required
def add_teacher():
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        contact = request.form.get('contact')
        subject = request.form.get('subject')
        email = request.form.get('email')
        profile_pic = request.files.get('profile_pic')

        if not name or not age or not contact or not subject:
            flash('Please fill all required fields', 'error')
            return render_template("add_teacher.html", user=current_user)

        profile_pic_name = None
        if profile_pic and profile_pic.filename != '':
            profile_pic_name = secure_filename(profile_pic.filename)
            profile_pic.save(os.path.join(current_app.config['UPLOAD_FOLDER'], profile_pic_name))

        # Get the next position for ordering
        last_teacher = Teacher.query.filter_by(user_id=current_user.id).order_by(Teacher.position.desc()).first()
        next_position = last_teacher.position + 1 if last_teacher else 0

        new_teacher = Teacher(
            name=name,
            age=age,
            contact=contact,
            subject=subject,
            email=email if email else None,
            profile_pic=profile_pic_name,
            user_id=current_user.id,
            position=next_position
        )
        
        db.session.add(new_teacher)
        db.session.commit()
        flash('Teacher added successfully!', 'success')
        return redirect(url_for('auth.teachers_page'))

    return render_template("add_teacher.html", user=current_user)

@auth.route('/delete-teacher', methods=['POST'])
@login_required
def delete_teacher():
    try:
        data = json.loads(request.data)
        teacher_id = data.get('teacherId')
        
        teacher = Teacher.query.get(teacher_id)
        
        if not teacher:
            return jsonify({'error': 'Teacher not found'}), 404
        
        if teacher.user_id != current_user.id:
            return jsonify({'error': 'Not authorized to delete this teacher'}), 403
        
        # Delete profile picture if exists
        if teacher.profile_pic:
            profile_pic_path = os.path.join(current_app.config['UPLOAD_FOLDER'], teacher.profile_pic)
            if os.path.exists(profile_pic_path):
                os.remove(profile_pic_path)
        
        # Delete teacher from database
        db.session.delete(teacher)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': 'Server error'}), 500

@auth.route('/reorder-teachers', methods=['POST'])
@login_required
def reorder_teachers():
    try:
        data = json.loads(request.data)
        teacher_order = data.get('teacherOrder', [])
        
        # Update positions for all teachers
        for position, teacher_id in enumerate(teacher_order):
            teacher = Teacher.query.get(teacher_id)
            if teacher and teacher.user_id == current_user.id:
                teacher.position = position
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Server error'}), 500

# ---------------- OTHER ROUTES -----------------
@auth.route('/notes')
@login_required
def notes_page():
    return render_template("note.html", user=current_user)

@auth.route('/chat')
@login_required
def chat_group():
    return render_template("cg.html", user=current_user)

# ---------------- GAME ROUTES -----------------
@auth.route('/games')
@login_required
def games_hub():
    games = Game.query.all()
    return render_template("games_hub.html", games=games, user=current_user)

@auth.route('/flappy-bird')
@login_required
def flappy_bird():
    return render_template("flappy_bird.html", user=current_user)

@auth.route('/upload-game', methods=['GET', 'POST'])
@login_required
def upload_game():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        game_type = request.form.get('game_type')
        requirements = request.form.get('requirements')
        instructions = request.form.get('instructions')
        game_file = request.files.get('game_file')
        
        # Validate required fields
        if not title or not description or not instructions:
            flash('Please fill all required fields', 'error')
            return render_template("upload_game.html", user=current_user)
        
        if game_file and allowed_game_file(game_file.filename):
            filename = secure_filename(game_file.filename)
            # FIXED: Use GAMES_FOLDER directly
            file_path = os.path.join(GAMES_FOLDER, filename)
            game_file.save(file_path)
            
            new_game = Game(
                title=title,
                description=description,
                filename=filename,
                file_type=game_type,
                requirements=requirements,
                instructions=instructions,
                user_id=current_user.id
            )
            
            db.session.add(new_game)
            db.session.commit()
            flash('Game uploaded successfully! Other students can now play it.', 'success')
            return redirect(url_for('auth.games_hub'))
        else:
            flash('Invalid file type. Please upload .py, .html, .js, or .zip files.', 'error')
    
    return render_template("upload_game.html", user=current_user)

@auth.route('/download-game/<int:game_id>')
@login_required
def download_game(game_id):
    game = Game.query.get_or_404(game_id)
    
    # Increment download count
    game.downloads += 1
    db.session.commit()
    
    # FIXED: Use GAMES_FOLDER directly
    file_path = os.path.join(GAMES_FOLDER, game.filename)
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=game.filename
    )

def allowed_game_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'py', 'html', 'js', 'zip'}

# ---------------- FLAPPY BIRD LEADERBOARD ROUTES -----------------
# REMOVED: FlappyScore model definition (it should be in models.py)
# class FlappyScore(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     player_name = db.Column(db.String(100), nullable=False)
#     score = db.Column(db.Integer, nullable=False)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
#     date_achieved = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

@auth.route('/submit-flappy-score', methods=['POST'])
@login_required
def submit_flappy_score():
    try:
        data = request.get_json()
        score = data.get('score')
        player_name = data.get('playerName', current_user.first_name)
        
        # Only save if it's a decent score (optional)
        if score > 0:
            new_score = FlappyScore(
                player_name=player_name,
                score=score,
                user_id=current_user.id
            )
            db.session.add(new_score)
            db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error submitting score: {e}")
        return jsonify({'error': 'Failed to submit score'}), 500

@auth.route('/flappy-leaderboard')
@login_required
def get_flappy_leaderboard():
    try:
        # Get top 10 scores
        leaderboard = FlappyScore.query.order_by(FlappyScore.score.desc()).limit(10).all()
        
        # Get today's stats
        today = datetime.utcnow().date()
        players_today = db.session.query(FlappyScore.player_name).filter(
            func.date(FlappyScore.date_achieved) == today
        ).distinct().count()
        
        games_played = FlappyScore.query.filter(
            func.date(FlappyScore.date_achieved) == today
        ).count()
        
        leaderboard_data = []
        for score in leaderboard:
            leaderboard_data.append({
                'player_name': score.player_name,
                'score': score.score,
                'date': score.date_achieved.strftime('%Y-%m-%d')
            })
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard_data,
            'stats': {
                'players_today': players_today,
                'games_played': games_played
            }
        })
        
    except Exception as e:
        print(f"Error getting leaderboard: {e}")
        return jsonify({'error': 'Failed to load leaderboard'}), 500