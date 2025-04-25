from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, User, Patient, Doctor, Appointment, Bed, Medicine


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'  # or use any database URL
app.secret_key = 'your_secret_key_here'  # Set this to a real secret key
db.init_app(app)

with app.app_context():
    db.create_all()  # Creates all tables if not exist

    # Create admin user if not exists
    from werkzeug.security import generate_password_hash
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin_user = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Admin user created: username='admin', password='admin123'")
    else:
        print("⚠️ Admin user already exists.")


# Function to check if the user is logged in and if the role matches
def is_admin():
    return 'role' in session and session['role'] == 'admin'

def is_doctor():
    return 'role' in session and session['role'] == 'doctor'

def is_user():
    return 'role' in session and session['role'] == 'user'




# Route for Admin Dashboard (Login required)
@app.route('/')
def index():
    if 'role' not in session:
        return redirect(url_for('login'))
    if is_admin():
        return render_template('index.html')
    else:
        return redirect(url_for('login'))

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if user exists
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # Store session info
            session['username'] = user.username
            session['role'] = user.role  # Store role in session
            
            flash('Login successful!', 'success')

            # Redirect based on user role
            if user.role == 'admin':
                return redirect(url_for('index'))  # Redirect to admin dashboard
            elif user.role == 'doctor':
                return redirect(url_for('view_appointments'))  # Redirect to doctor's appointment view
            elif user.role == 'user':
                return redirect(url_for('book_appointment'))  # Redirect to user appointment booking
            
        else:
            flash('Invalid credentials. Please try again.', 'danger')
            return render_template('login.html')

    return render_template('login.html')


# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']

        # Check if password and confirm password match
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')

        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose another.', 'danger')
            return render_template('register.html')

        # Create a new user
        new_user = User(username=username, role=role)
        new_user.set_password(password)  # Ensure you have a method to hash the password

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return render_template('register.html')

    return render_template('register.html')



# Route to Add Patient (Admin Only)
@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    if not is_admin():
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        
        if not name or not age or not gender:
            flash('All fields are required!', 'danger')
            return render_template('add_patient.html')

        try:
            new_patient = Patient(name=name, age=age, gender=gender)
            db.session.add(new_patient)
            db.session.commit()
            flash('Patient added successfully!', 'success')
            return redirect(url_for('view_patients'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return render_template('add_patient.html')

    return render_template('add_patient.html')

# Route to View Patients (Admin Only)
@app.route('/view_patients')
def view_patients():
    if not is_admin():
        return redirect(url_for('index'))

    patients = Patient.query.all()
    return render_template('view_patients.html', patients=patients)

# Route to Add Doctor (Admin Only)
@app.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    if not is_admin():
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        specialization = request.form['specialization']
        
        if not name or not specialization:
            flash('All fields are required!', 'danger')
            return render_template('add_doctor.html')

        try:
            new_doctor = Doctor(name=name, specialization=specialization)
            db.session.add(new_doctor)
            db.session.commit()
            flash('Doctor added successfully!', 'success')
            return redirect(url_for('view_doctors'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return render_template('add_doctor.html')

    return render_template('add_doctor.html')

# Route to View Doctors (Admin Only)
@app.route('/view_doctors')
def view_doctors():
    if not is_admin():
        return redirect(url_for('index'))

    doctors = Doctor.query.all()
    return render_template('view_doctors.html', doctors=doctors)

# Route to Book Appointment (User Only)
@app.route('/book_appointment', methods=['GET', 'POST'])
def book_appointment():
    # Allow access for both users and admins
    if not (is_user() or is_admin()):
        return redirect(url_for('index'))

    if request.method == 'POST':
        patient_id = request.form['patient_id']
        doctor_id = request.form['doctor_id']
        date = request.form['date']
        
        if not patient_id or not doctor_id or not date:
            flash('All fields are required!', 'danger')
            return render_template('book_appointment.html')

        try:
            new_appointment = Appointment(patient_id=patient_id, doctor_id=doctor_id, date=date)
            db.session.add(new_appointment)
            db.session.commit()
            flash('Appointment booked successfully!', 'success')
            return redirect(url_for('view_appointments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return render_template('book_appointment.html')

    patients = Patient.query.all()
    doctors = Doctor.query.all()
    return render_template('book_appointment.html', patients=patients, doctors=doctors)


@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        name = request.form['name']
        amount = request.form['amount']
        session['payment_info'] = {
            'name': name,
            'amount': amount
        }
        return redirect(url_for('payment_success'))

    return render_template('payment.html')


@app.route('/payment_success')
def payment_success():
    data = session.get('payment_info')
    if not data:
        return redirect(url_for('payment'))
    return render_template('payment_success.html', **data)

@app.route('/receipt')
def receipt():
    data = session.get('payment_info')
    if not data:
        return redirect(url_for('payment'))
    return render_template('receipt.html', name=data['name'], amount=data['amount'])


# Route to View Appointments (Doctor Only)
# Route to View Appointments (Doctor and Admin Only)
@app.route('/view_appointments')
def view_appointments():
    # Allow access for both doctors and admins
    if not (is_doctor() or is_admin()):
        return redirect(url_for('index'))

    appointments = Appointment.query.all()
    return render_template('view_appointments.html', appointments=appointments)


# Route to Add Bed (Admin Only)
@app.route('/add_bed', methods=['GET', 'POST'])
def add_bed():
    if not is_admin():
        return redirect(url_for('index'))

    if request.method == 'POST':
        bed_number = request.form['bed_number']
        ward = request.form['ward']
        
        if not bed_number or not ward:
            flash('All fields are required!', 'danger')
            return render_template('add_bed.html')

        try:
            new_bed = Bed(bed_number=bed_number, ward=ward, is_available=True)
            db.session.add(new_bed)
            db.session.commit()
            flash('Bed added successfully!', 'success')
            return redirect(url_for('view_beds'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return render_template('add_bed.html')

    return render_template('add_bed.html')

# Route to discharge a bed (Admin Only)
@app.route('/discharge_bed')
def discharge_bed(bed_id):
    if not is_admin():
        return redirect(url_for('index'))  # If not admin, redirect to the dashboard

    bed = Bed.query.filter_by(id=bed_id).first()

    if bed and not bed.is_available:
        # Mark the bed as available
        bed.is_available = True
        db.session.commit()
        flash('Bed has been successfully discharged and is now available.', 'success')
    elif bed and bed.is_available:
        flash('This bed is already available.', 'info')
    else:
        flash('Bed not found.', 'danger')

    return redirect(url_for('view_beds')) 




# Route to View Beds (Admin Only)
@app.route('/view_beds')
def view_beds():
    if not is_admin():
        return redirect(url_for('index'))

    beds = Bed.query.all()
    return render_template('view_beds.html', beds=beds)

# Route to Add Medicine (Admin Only)
@app.route('/add_medicine', methods=['GET', 'POST'])
def add_medicine():
    if not is_admin():
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form['quantity']
        
        if not name or not quantity:
            flash('All fields are required!', 'danger')
            return render_template('add_medicine.html')

        try:
            new_medicine = Medicine(name=name, quantity=quantity)
            db.session.add(new_medicine)
            db.session.commit()
            flash('Medicine added successfully!', 'success')
            return redirect(url_for('view_medicines'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return render_template('add_medicine.html')

    return render_template('add_medicine.html')

# Route to View Medicines (Admin Only)
@app.route('/view_medicines')
def view_medicines():
    if not is_admin():
        return redirect(url_for('index'))

    medicines = Medicine.query.all()
    return render_template('view_medicines.html', medicines=medicines)


if __name__ == '__main__':
    app.run(debug=True)


