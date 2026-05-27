from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'epicfunk-change-this-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///epicfunkhq.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    instrument = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rsvps = db.relationship('RSVP', backref='member', lazy=True)

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(200))
    key = db.Column(db.String(20))
    tempo = db.Column(db.Integer)
    feel = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Gig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    venue = db.Column(db.String(200))
    date = db.Column(db.DateTime, nullable=False)
    call_time = db.Column(db.String(20))
    load_in = db.Column(db.String(20))
    pay = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rsvps = db.relationship('RSVP', backref='gig', lazy=True)

class RSVP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gig_id = db.Column(db.Integer, db.ForeignKey('gig.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.relationship('User', backref='announcements')

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated

def current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user()
    upcoming_gigs = Gig.query.filter(Gig.date >= datetime.utcnow()).order_by(Gig.date).limit(3).all()
    announcements = Announcement.query.order_by(Announcement.pinned.desc(), Announcement.created_at.desc()).limit(5).all()
    song_count = Song.query.count()
    member_count = User.query.count()
    return render_template('dashboard.html', user=user, upcoming_gigs=upcoming_gigs,
                           announcements=announcements, song_count=song_count, member_count=member_count)

@app.route('/songs')
@login_required
def songs():
    user = current_user()
    all_songs = Song.query.order_by(Song.title).all()
    return render_template('songs.html', user=user, songs=all_songs)

@app.route('/gigs')
@login_required
def gigs():
    user = current_user()
    all_gigs = Gig.query.order_by(Gig.date).all()
    gig_data = []
    for gig in all_gigs:
        rsvp = RSVP.query.filter_by(gig_id=gig.id, user_id=user.id).first()
        yes_count = RSVP.query.filter_by(gig_id=gig.id, status='yes').count()
        no_count = RSVP.query.filter_by(gig_id=gig.id, status='no').count()
        maybe_count = RSVP.query.filter_by(gig_id=gig.id, status='maybe').count()
        gig_data.append({'gig': gig, 'my_rsvp': rsvp.status if rsvp else 'pending',
                         'yes': yes_count, 'no': no_count, 'maybe': maybe_count})
    return render_template('gigs.html', user=user, gig_data=gig_data)

@app.route('/announcements')
@login_required
def announcements():
    user = current_user()
    all_announcements = Announcement.query.order_by(Announcement.pinned.desc(), Announcement.created_at.desc()).all()
    return render_template('announcements.html', user=user, announcements=all_announcements)

@app.route('/members')
@login_required
def members():
    user = current_user()
    all_members = User.query.order_by(User.name).all()
    return render_template('members.html', user=user, members=all_members)

@app.route('/api/me')
def api_me():
    user = current_user()
    if not user:
        return jsonify({'error': 'Not logged in'}), 401
    return jsonify({'id': user.id, 'name': user.name, 'email': user.email,
                    'instrument': user.instrument, 'is_admin': user.is_admin})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    user = User.query.filter_by(email=data.get('email', '').lower().strip()).first()
    if user and bcrypt.check_password_hash(user.password, data.get('password', '')):
        session['user_id'] = user.id
        return jsonify({'success': True, 'is_admin': user.is_admin})
    return jsonify({'error': 'Invalid email or password'}), 401

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    if User.query.filter_by(email=data.get('email', '').lower().strip()).first():
        return jsonify({'error': 'Email already registered'}), 400
    hashed = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = User(name=data['name'], email=data['email'].lower().strip(), password=hashed,
                instrument=data.get('instrument', ''), is_admin=User.query.count() == 0)
    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id
    return jsonify({'success': True, 'is_admin': user.is_admin})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/songs', methods=['POST'])
@admin_required
def add_song():
    data = request.json
    song = Song(title=data['title'], artist=data.get('artist',''), key=data.get('key',''),
                tempo=data.get('tempo'), feel=data.get('feel',''), notes=data.get('notes',''))
    db.session.add(song)
    db.session.commit()
    return jsonify({'success': True, 'id': song.id})

@app.route('/api/songs/<int:song_id>', methods=['PUT'])
@admin_required
def update_song(song_id):
    song = Song.query.get_or_404(song_id)
    data = request.json
    song.title = data.get('title', song.title)
    song.artist = data.get('artist', song.artist)
    song.key = data.get('key', song.key)
    song.tempo = data.get('tempo', song.tempo)
    song.feel = data.get('feel', song.feel)
    song.notes = data.get('notes', song.notes)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/songs/<int:song_id>', methods=['DELETE'])
@admin_required
def delete_song(song_id):
    song = Song.query.get_or_404(song_id)
    db.session.delete(song)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/gigs', methods=['POST'])
@admin_required
def add_gig():
    data = request.json
    gig = Gig(title=data['title'], venue=data.get('venue',''),
              date=datetime.fromisoformat(data['date']), call_time=data.get('call_time',''),
              load_in=data.get('load_in',''), pay=data.get('pay',''), notes=data.get('notes',''))
    db.session.add(gig)
    db.session.commit()
    return jsonify({'success': True, 'id': gig.id})

@app.route('/api/gigs/<int:gig_id>', methods=['DELETE'])
@admin_required
def delete_gig(gig_id):
    gig = Gig.query.get_or_404(gig_id)
    RSVP.query.filter_by(gig_id=gig_id).delete()
    db.session.delete(gig)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/gigs/<int:gig_id>/rsvp', methods=['POST'])
@login_required
def rsvp_gig(gig_id):
    data = request.json
    user = current_user()
    rsvp = RSVP.query.filter_by(gig_id=gig_id, user_id=user.id).first()
    if rsvp:
        rsvp.status = data['status']
        rsvp.updated_at = datetime.utcnow()
    else:
        rsvp = RSVP(gig_id=gig_id, user_id=user.id, status=data['status'])
        db.session.add(rsvp)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/gigs/<int:gig_id>/rsvps')
@admin_required
def get_rsvps(gig_id):
    rsvps = RSVP.query.filter_by(gig_id=gig_id).all()
    return jsonify([{'name': r.member.name, 'instrument': r.member.instrument, 'status': r.status} for r in rsvps])

@app.route('/api/gigs/<int:gig_id>/rsvps/all')
@login_required
def get_rsvps_all(gig_id):
    rsvps = RSVP.query.filter_by(gig_id=gig_id).all()
    return jsonify([{'name': r.member.name, 'instrument': r.member.instrument, 'status': r.status} for r in rsvps])

@app.route('/api/announcements', methods=['POST'])
@admin_required
def add_announcement():
    data = request.json
    user = current_user()
    ann = Announcement(title=data['title'], body=data['body'], author_id=user.id, pinned=data.get('pinned', False))
    db.session.add(ann)
    db.session.commit()
    return jsonify({'success': True, 'id': ann.id})

@app.route('/api/announcements/<int:ann_id>', methods=['DELETE'])
@admin_required
def delete_announcement(ann_id):
    ann = Announcement.query.get_or_404(ann_id)
    db.session.delete(ann)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/announcements/<int:ann_id>/pin', methods=['POST'])
@admin_required
def toggle_pin(ann_id):
    ann = Announcement.query.get_or_404(ann_id)
    ann.pinned = not ann.pinned
    db.session.commit()
    return jsonify({'success': True, 'pinned': ann.pinned})

@app.route('/api/members/<int:user_id>/admin', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    return jsonify({'success': True, 'is_admin': user.is_admin})

@app.route('/api/members/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_member(user_id):
    me = current_user()
    if me.id == user_id:
        return jsonify({'error': 'Cannot delete yourself'}), 400
    RSVP.query.filter_by(user_id=user_id).delete()
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True})

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
