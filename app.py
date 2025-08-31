from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Ambulance, Booking
from forms import RegistrationForm, LoginForm, BookAmbulanceForm, UpdateLocationForm
from datetime import datetime
from chat import HealthMateChatbot
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a random secret key in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize the chatbot
chatbot = HealthMateChatbot()

CORS(app, resources={r"/api/*": {"origins": "*"}})


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.user_type == 'patient':
            return redirect(url_for('ambulance_page'))
        else:
            return redirect(url_for('requests_page'))
    return redirect(url_for('login'))


@app.route('/services')
def services():
    return render_template('services_quickcare.html')


@app.route('/about')
def about():
    return render_template('about_quickcare.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password,
            user_type=form.user_type.data
        )
        db.session.add(user)
        db.session.commit()

        # If driver, create an ambulance record
        if user.user_type == 'driver':
            ambulance = Ambulance(driver_id=user.id, status='active')
            db.session.add(ambulance)
            db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register_quickcare.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            if user.user_type == 'patient':
                return redirect(url_for('ambulance_page'))
            else:
                return redirect(url_for('requests_page'))
        else:
            flash('Login failed. Check your email and password.', 'danger')
    return render_template('login_quickcare.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/ambulance_page')
@login_required
def ambulance_page():
    if current_user.user_type != 'patient':
        return redirect(url_for('requests_page'))

    # Check if patient has an active booking (pending or confirmed)
    active_booking = Booking.query.filter_by(patient_id=current_user.id).filter(
        Booking.status.in_(['pending', 'confirmed'])
    ).first()

    if active_booking:
        if active_booking.status == 'confirmed':
            return redirect(url_for('map', booking_id=active_booking.id))
        else:
            flash('You have a pending booking. Wait for confirmation.', 'info')
            return render_template('ambulance_page.html', ambulances=[], has_active_booking=True)

    ambulances = Ambulance.query.filter_by(status='active').all()
    return render_template('ambulance_page.html', ambulances=ambulances, has_active_booking=False)


@app.route('/book_ambulance/<int:ambulance_id>', methods=['GET', 'POST'])
@login_required
def book_ambulance(ambulance_id):
    if current_user.user_type != 'patient':
        return redirect(url_for('index'))
    ambulance = Ambulance.query.get_or_404(ambulance_id)
    form = BookAmbulanceForm()
    if form.validate_on_submit():
        booking = Booking(
            patient_id=current_user.id,
            ambulance_id=ambulance.id,
            status='pending',
            patient_lat=form.patient_lat.data,
            patient_lng=form.patient_lng.data,
            timestamp=datetime.utcnow()
        )
        db.session.add(booking)
        db.session.commit()
        flash('Booking request sent to the driver.', 'success')
        return redirect(url_for('ambulance_page'))
    return render_template('book_ambulance.html', form=form, ambulance=ambulance)


@app.route('/requests_page', methods=['GET', 'POST'])
@login_required
def requests_page():
    if current_user.user_type != 'driver':
        return redirect(url_for('ambulance_page'))

    ambulance = Ambulance.query.filter_by(driver_id=current_user.id).first()
    if not ambulance:
        flash('No ambulance assigned.', 'danger')
        return redirect(url_for('index'))

    requests_list = Booking.query.filter_by(ambulance_id=ambulance.id, status='pending').all()

    update_form = UpdateLocationForm()
    # Make UpdateLocationForm robust to different field names (lat/lng vs latitude/longitude etc.)
    if update_form.validate_on_submit():
        # try several common field names; raise friendly message if none exist
        possible_lat_fields = ('lat', 'latitude', 'driver_lat', 'current_lat')
        possible_lng_fields = ('lng', 'longitude', 'driver_lng', 'current_lng')

        lat_field = None
        lng_field = None
        for name in possible_lat_fields:
            lat_field = getattr(update_form, name, None)
            if lat_field is not None:
                break
        for name in possible_lng_fields:
            lng_field = getattr(update_form, name, None)
            if lng_field is not None:
                break

        if lat_field is None or lng_field is None:
            flash('Location form is missing expected latitude/longitude fields. Please check the form field names.', 'danger')
            return redirect(url_for('requests_page'))

        # Extract values safely
        try:
            lat_val = lat_field.data
            lng_val = lng_field.data
        except Exception:
            flash('Failed to read latitude/longitude from form fields.', 'danger')
            return redirect(url_for('requests_page'))

        # Save to current_user (driver) if these attributes exist on the User model
        if hasattr(current_user, 'lat') and hasattr(current_user, 'lng'):
            current_user.lat = lat_val
            current_user.lng = lng_val
            db.session.commit()
            flash('Location updated.', 'success')
        else:
            # If your driver location fields live on Ambulance model instead of User, update ambulance
            if hasattr(ambulance, 'lat') and hasattr(ambulance, 'lng'):
                ambulance.lat = lat_val
                ambulance.lng = lng_val
                db.session.commit()
                flash('Ambulance location updated.', 'success')
            else:
                flash('No place to save location on your models. Update your models to include lat/lng for driver or ambulance.', 'danger')

    return render_template('requests_page.html', requests=requests_list, update_form=update_form)


@app.route('/confirm_booking/<int:booking_id>', methods=['POST'])
@login_required
def confirm_booking(booking_id):
    if current_user.user_type != 'driver':
        return redirect(url_for('index'))
    booking = Booking.query.get_or_404(booking_id)
    # Ensure the ambulance and its driver exist
    if not booking.ambulance or booking.ambulance.driver_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('requests_page'))
    booking.status = 'confirmed'
    db.session.commit()
    flash('Booking confirmed.', 'success')
    return redirect(url_for('map', booking_id=booking_id))


@app.route('/reject_booking/<int:booking_id>', methods=['POST'])
@login_required
def reject_booking(booking_id):
    if current_user.user_type != 'driver':
        return redirect(url_for('index'))
    booking = Booking.query.get_or_404(booking_id)
    if not booking.ambulance or booking.ambulance.driver_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('requests_page'))
    booking.status = 'rejected'
    db.session.commit()
    flash('Booking rejected.', 'info')
    return redirect(url_for('requests_page'))


@app.route('/map/<int:booking_id>')
@login_required
def map(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    # authorization: patient or driver only if they belong to booking
    if (current_user.user_type == 'patient' and booking.patient_id != current_user.id) or \
       (current_user.user_type == 'driver' and (not booking.ambulance or booking.ambulance.driver_id != current_user.id)):
        flash('Unauthorized.', 'danger')
        return redirect(url_for('index'))
    if booking.status != 'confirmed':
        flash('Booking not confirmed.', 'info')
        return redirect(url_for('index'))

    patient = booking.patient
    driver = booking.ambulance.driver if booking.ambulance else None

    # defensive defaults for lat/lng if missing
    driver_lat = getattr(driver, 'lat', 0) if driver else 0
    driver_lng = getattr(driver, 'lng', 0) if driver else 0

    return render_template(
        'map.html',
        booking=booking,
        patient_lat=booking.patient_lat,
        patient_lng=booking.patient_lng,
        driver_lat=driver_lat,
        driver_lng=driver_lng
    )


# --- Chatbot API endpoint ---
@app.route('/api/chat', methods=['POST'])
def api_chat():
    payload = request.get_json(silent=True) or {}
    message = payload.get("message", "").strip()

    if not message:
        return jsonify({"status": "error", "response": "Please provide a message."}), 400

    response_text = chatbot.get_response(message)
    return jsonify({"status": "ok", "response": response_text}), 200

if __name__ == '__main__':
    with app.app_context():
        # create tables if missing
        db.create_all()
    app.run(debug=True)