import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import csv
from io import StringIO

from models import db, User, Candidate, Vote, ElectionSettings

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key_here_for_production'
# Use absolute path for sqlite db to avoid location issues
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'voting.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Decorator for admin only routes
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access is required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ------------- ROUTING ------------- #

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        voter_id = request.form.get('voter_id')
        name = request.form.get('name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))
        
        existing_user = db.session.scalar(db.select(User).filter_by(voter_id=voter_id))
        if existing_user:
            flash('Voter ID already registered.', 'warning')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(voter_id=voter_id, name=name, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        voter_id = request.form.get('voter_id')
        password = request.form.get('password')
        
        user = db.session.scalar(db.select(User).filter_by(voter_id=voter_id))
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Login Unsuccessful. Please check voter ID and password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def user_dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
        
    candidates = db.session.scalars(db.select(Candidate)).all()
    settings = db.session.scalar(db.select(ElectionSettings))
    
    # Check if election is active or deadline has passed
    election_active = True
    if settings:
        if not settings.is_active:
            election_active = False
        elif settings.deadline and datetime.utcnow() > settings.deadline:
            election_active = False
            
    return render_template('user_dashboard.html', candidates=candidates, 
                           has_voted=current_user.has_voted, election_active=election_active)

@app.route('/vote/<int:candidate_id>', methods=['POST'])
@login_required
def vote(candidate_id):
    if current_user.role == 'admin':
        return jsonify({"success": False, "message": "Admins cannot vote."}), 403

    if current_user.has_voted:
        return jsonify({"success": False, "message": "You have already voted."}), 400
        
    settings = db.session.scalar(db.select(ElectionSettings))
    if settings and (not settings.is_active or (settings.deadline and datetime.utcnow() > settings.deadline)):
        return jsonify({"success": False, "message": "Election is closed."}), 400

    candidate = db.get_or_404(Candidate, candidate_id)
    
    new_vote = Vote(voter_id=current_user.id, candidate_id=candidate.id)
    db.session.add(new_vote)
    
    current_user.has_voted = True
    db.session.commit()
    
    return jsonify({"success": True, "message": f"Successfully voted for {candidate.name}!"})

# ------------- ADMIN ROUTING ------------- #

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    candidates = db.session.scalars(db.select(Candidate)).all()
    settings = db.session.scalar(db.select(ElectionSettings))
    return render_template('admin_dashboard.html', candidates=candidates, settings=settings)

@app.route('/admin/candidate/add', methods=['POST'])
@login_required
@admin_required
def add_candidate():
    name = request.form.get('name')
    party = request.form.get('party')
    agenda = request.form.get('agenda')
    
    if name and party:
        candidate = Candidate(name=name, party=party, agenda=agenda)
        db.session.add(candidate)
        db.session.commit()
        flash('Candidate added successfully.', 'success')
    else:
        flash('Name and Party are required.', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/candidate/delete/<int:candidate_id>', methods=['POST'])
@login_required
@admin_required
def delete_candidate(candidate_id):
    candidate = db.get_or_404(Candidate, candidate_id)
    # Also delete votes for this candidate to maintain referential integrity
    db.session.execute(db.delete(Vote).filter_by(candidate_id=candidate_id))
    db.session.delete(candidate)
    db.session.commit()
    flash(f'Candidate "{candidate.name}" removed.', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/election/settings', methods=['POST'])
@login_required
@admin_required
def update_settings():
    settings = db.session.scalar(db.select(ElectionSettings))
    if not settings:
        settings = ElectionSettings()
        db.session.add(settings)
    
    # Toggle active status
    action = request.form.get('action')
    if action == 'close_election':
        settings.is_active = False
        flash('Election has been manually closed.', 'warning')
    elif action == 'open_election':
        settings.is_active = True
        flash('Election has been opened.', 'success')
        
    deadline_str = request.form.get('deadline')
    if deadline_str:
        try:
            # HTML datetime-local format is YYYY-MM-DDTHH:MM
            settings.deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
            flash('Election deadline updated.', 'info')
        except ValueError:
            flash('Invalid date format.', 'danger')
            
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/election/reset', methods=['POST'])
@login_required
@admin_required
def reset_election():
    # Remove all votes
    db.session.execute(db.delete(Vote))
    # Reset user vote statuses (except admins)
    users = db.session.scalars(db.select(User).filter_by(role='user')).all()
    for u in users:
        u.has_voted = False
    db.session.commit()
    flash('Election has been reset. All votes are cleared.', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/results')
def results():
    # Only authenticated users or admins can view results
    if not current_user.is_authenticated:
        flash('Please login to view results.', 'warning')
        return redirect(url_for('login'))
        
    return render_template('results.html')

@app.route('/api/results')
@login_required
def api_results():
    candidates = db.session.scalars(db.select(Candidate)).all()
    results_data = {
        "labels": [],
        "votes": [],
        "colors": [] # Optional random colors
    }
    
    # Simple color generator
    colors = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#858796']
    
    for i, candidate in enumerate(candidates):
        results_data["labels"].append(f"{candidate.name} ({candidate.party})")
        # Count votes for this candidate
        vote_count = db.session.scalar(db.select(db.func.count(Vote.id)).filter_by(candidate_id=candidate.id))
        results_data["votes"].append(vote_count)
        results_data["colors"].append(colors[i % len(colors)])
        
    return jsonify(results_data)

@app.route('/admin/export/csv')
@login_required
@admin_required
def export_csv():
    candidates = db.session.scalars(db.select(Candidate)).all()
    
    def generate():
        data = StringIO()
        writer = csv.writer(data)
        writer.writerow(('Candidate ID', 'Name', 'Party', 'Total Votes'))
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)
        
        for candidate in candidates:
            vote_count = db.session.scalar(db.select(db.func.count(Vote.id)).filter_by(candidate_id=candidate.id))
            writer.writerow((candidate.id, candidate.name, candidate.party, vote_count))
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    response = Response(generate(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename="election_results.csv")
    return response

if __name__ == '__main__':
    app.run(debug=True)
