from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ezyevent.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))  # 'admin', 'client', 'provider'
    # New fields
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    wilaya = db.Column(db.String(50))
    # Provider specific fields
    service_category = db.Column(db.String(50))
    experience = db.Column(db.String(500))
    certification = db.Column(db.String(500))
    study_degree = db.Column(db.String(100))

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    date = db.Column(db.String(50))
    location = db.Column(db.String(100))
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    provider_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20))  # 'pending', 'confirmed', 'cancelled', 'completed'
    payment_status = db.Column(db.String(20), default='pending')  # 'pending', 'paid'
    payment_amount = db.Column(db.Float, nullable=True)
    event = db.relationship('Event', backref='bookings', lazy=True)
    provider = db.relationship('User', backref='my_bookings', lazy=True)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    provider_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Add relationship to User model
    provider = db.relationship('User', backref=db.backref('services', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'admin':
            admin_user = User.query.filter_by(email='admin@ezyevents.com').first()
            if not admin_user:
                # Create admin user if it doesn't exist
                admin_user = User(
                    email='admin@ezyevents.com',
                    password='admin',
                    role='admin',
                    first_name='Admin',
                    last_name='User'
                )
                db.session.add(admin_user)
                db.session.commit()
            
            login_user(admin_user)
            return redirect(url_for('admin_dashboard'))
            
        flash('Invalid credentials', 'error')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('admin_login'))
    
    # Gather statistics
    stats = {
        'total_users': User.query.count(),
        'total_events': Event.query.count(),
        'total_providers': User.query.filter_by(role='provider').count(),
        'total_bookings': Booking.query.count()
    }
    
    # Gather data for each tab
    users = User.query.all()
    events = Event.query.all()
    providers = User.query.filter_by(role='provider').all()
    bookings = Booking.query.all()
    
    return render_template('admin.html',
                         stats=stats,
                         users=users,
                         events=events,
                         providers=providers,
                         bookings=bookings)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.password == password and user.role != 'admin':
            login_user(user)
            if user.role == 'client':
                return redirect(url_for('client_dashboard'))
            elif user.role == 'provider':
                return redirect(url_for('provider_dashboard'))
                
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register/client', methods=['GET', 'POST'])
def register_client():
    if request.method == 'POST':
        new_user = User(
            email=request.form.get('email'),
            password=request.form.get('password'),
            role='client',
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            wilaya=request.form.get('wilaya')
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register_client.html')

@app.route('/register/provider', methods=['GET', 'POST'])
def register_provider():
    if request.method == 'POST':
        new_user = User(
            email=request.form.get('email'),
            password=request.form.get('password'),
            role='provider',
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            wilaya=request.form.get('wilaya'),
            service_category=request.form.get('service_category'),
            experience=request.form.get('experience'),
            certification=request.form.get('certification'),
            study_degree=request.form.get('study_degree')
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register_provider.html')

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/client')
@login_required
def client_dashboard():
    if current_user.role != 'client':
        return redirect(url_for('index'))
    events = Event.query.filter_by(client_id=current_user.id).all()
    return render_template('client_dashboard.html', user=current_user, events=events)

@app.route('/create_event', methods=['POST'])
@login_required
def create_event():
    if current_user.role != 'client':
        return redirect(url_for('index'))
    
    new_event = Event(
        title=request.form.get('title'),
        date=request.form.get('date'),
        location=request.form.get('location'),
        client_id=current_user.id
    )
    db.session.add(new_event)
    db.session.commit()
    flash('Event created successfully!', 'success')
    return redirect(url_for('client_dashboard'))

@app.route('/provider')
@login_required
def provider_dashboard():
    if current_user.role != 'provider':
        return redirect(url_for('index'))
    
    pending_requests = Booking.query.filter_by(
        provider_id=current_user.id,
        status='pending'
    ).all()
    
    to_pay = Booking.query.filter_by(
        provider_id=current_user.id,
        status='confirmed',
        payment_status='pending'
    ).all()
    
    scheduled = Booking.query.filter_by(
        provider_id=current_user.id,
        status='confirmed',
        payment_status='paid'
    ).all()
    
    completed = Booking.query.filter_by(
        provider_id=current_user.id,
        status='completed'
    ).all()
    
    return render_template('provider_dashboard.html', 
                         user=current_user,
                         pending_requests=pending_requests,
                         to_pay=to_pay,
                         scheduled=scheduled,
                         completed=completed)

@app.route('/add_service', methods=['POST'])
@login_required
def add_service():
    if current_user.role != 'provider':
        return redirect(url_for('index'))
    
    new_service = Service(
        title=request.form.get('title'),
        category=request.form.get('category'),
        description=request.form.get('description'),
        provider_id=current_user.id
    )
    db.session.add(new_service)
    db.session.commit()
    flash('Service added successfully!', 'success')
    return redirect(url_for('provider_dashboard'))

@app.route('/providers')
@login_required
def browse_providers():
    if current_user.role != 'client':
        return redirect(url_for('index'))
    providers = User.query.filter_by(role='provider').all()
    events = Event.query.filter_by(client_id=current_user.id).all()
    return render_template('providers.html', providers=providers, events=events)

@app.route('/request_booking/<int:provider_id>', methods=['POST'])
@login_required
def request_booking(provider_id):
    if current_user.role != 'client':
        return redirect(url_for('index'))
    
    event_id = request.form.get('event_id')
    if not event_id:
        flash('Please select an event first', 'error')
        return redirect(url_for('browse_providers'))
    
    # Check if this provider is already booked for this event
    existing_booking = Booking.query.filter_by(
        event_id=event_id,
        provider_id=provider_id
    ).first()
    
    if existing_booking:
        flash('This provider is already booked for this event', 'warning')
        return redirect(url_for('browse_providers'))
    
    new_booking = Booking(
        event_id=event_id,
        provider_id=provider_id,
        status='pending'
    )
    db.session.add(new_booking)
    db.session.commit()
    flash('Booking request sent to provider', 'success')
    return redirect(url_for('my_bookings'))

@app.route('/booking/<int:booking_id>/accept', methods=['POST'])
@login_required
def accept_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.provider_id != current_user.id:
        return redirect(url_for('index'))
    booking.status = 'confirmed'
    db.session.commit()
    flash('Booking accepted', 'success')
    return redirect(url_for('provider_dashboard'))

@app.route('/booking/<int:booking_id>/decline', methods=['POST'])
@login_required
def decline_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.provider_id != current_user.id:
        return redirect(url_for('index'))
    booking.status = 'cancelled'
    db.session.commit()
    flash('Booking declined', 'info')
    return redirect(url_for('provider_dashboard'))

@app.route('/booking/<int:booking_id>/complete', methods=['POST'])
@login_required
def complete_booking(booking_id):
    if current_user.role != 'provider':
        return redirect(url_for('index'))
        
    booking = Booking.query.get_or_404(booking_id)
    if booking.provider_id != current_user.id:
        return redirect(url_for('index'))
    
    if booking.payment_status != 'paid':
        flash('Cannot complete event before payment is confirmed', 'error')
        return redirect(url_for('provider_dashboard'))
        
    booking.status = 'completed'
    db.session.commit()
    flash('Event marked as completed', 'success')
    return redirect(url_for('provider_dashboard'))

@app.route('/booking/<int:booking_id>/confirm_payment', methods=['POST'])
@login_required
def confirm_payment(booking_id):
    if current_user.role != 'provider':
        return redirect(url_for('index'))
        
    booking = Booking.query.get_or_404(booking_id)
    if booking.provider_id != current_user.id:
        return redirect(url_for('index'))
        
    payment_amount = float(request.form.get('payment_amount', 0))
    if payment_amount <= 0:
        flash('Please enter a valid payment amount', 'error')
        return redirect(url_for('provider_dashboard'))
        
    booking.payment_status = 'paid'
    booking.payment_amount = payment_amount
    db.session.commit()
    flash('Payment confirmed', 'success')
    return redirect(url_for('provider_dashboard'))

@app.route('/my_bookings')
@login_required
def my_bookings():
    if current_user.role != 'client':
        return redirect(url_for('index'))
    # Get all events for the current client
    events = Event.query.filter_by(client_id=current_user.id).all()
    return render_template('client_bookings.html', events=events, user=current_user)

@app.route('/provider/<int:provider_id>/details')
@login_required
def provider_details(provider_id):
    if current_user.role != 'client':
        return redirect(url_for('index'))
    
    # Check if this client has a confirmed booking with this provider
    booking = Booking.query.filter_by(
        provider_id=provider_id,
        status='confirmed'
    ).first()
    
    if not booking:
        flash('You can only view contact details for confirmed providers', 'error')
        return redirect(url_for('my_bookings'))
        
    provider = User.query.get_or_404(provider_id)
    return jsonify({
        'name': f"{provider.first_name} {provider.last_name}",
        'email': provider.email,
        'phone': provider.phone,
        'address': provider.address,
        'wilaya': provider.wilaya,
        'category': provider.service_category,
        'experience': provider.experience,
        'certification': provider.certification
    })

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)