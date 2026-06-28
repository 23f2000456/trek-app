from flask import render_template, redirect, url_for , request, flash
from app import app,db, login_manager
from models import User,Trek,Booking,TrekStaff 
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return redirect(url_for('login'))

#login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password')
            return redirect(url_for('login'))
        
        if user.blacklist:
            flash('Your account is Blacklisted')
            return redirect(url_for('login'))
        
        if user.role == 'staff' and not user.approval:
            flash('YOUR ACCOUNT IS PENDING APPROVAL')
            return redirect(url_for('login'))
        
        login_user(user)

        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user.role == 'staff':
            return redirect(url_for('staff_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
        
    return render_template('login.html')

#register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        if User.query.filter_by(email=email).first():
            flash ('Email already registered')
            return redirect(url_for('register'))
        
        if role == 'admin':
            flash('You cannot register as admin')
            return redirect(url_for('register'))
        
        approved = True if role == 'trekker' else False

        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role=role,
            approval=True,
            blacklist=False
        )
        db.session.add(new_user)
        db.session.commit()

        if role == 'staff':
            contact = request.form.get('contact','')
            staff_profile = TrekStaff(
                id=new_user.id,
                contact=contact
            )
            db.session.add(staff_profile)
            db.session.commit()
        flash('Registration successful, please login')
        return redirect(url_for('login'))

    return render_template('register.html')

#logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

#admin_dashboard
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access Denied')
        return redirect(url_for(login))
    
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='trekker').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()

    return render_template('admin_dashboard.html',
        total_treks=total_treks,
        total_users=total_users,
        total_staff=total_staff,
        total_bookings=total_bookings
    )

#staff_dashboard
@app.route('/staff/dashboard')
@login_required
def staff_dashboard():
    if current_user.role !='staff':
        flash('Access Denied')
        return redirect(url_for('login'))
    
    assigned_treks=Trek.query.filter_by(assigned_staffid=current_user.id).all()
    return render_template('staff_dashboard.html',
        assigned_treks=assigned_treks
    )

#user_dashboard
@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.role != 'trekker':
        flash('Access Denied')
        return redirect(url_for('login'))
    
    my_bookings=Booking.query.filter_by(user_id=current_user.id).all()

    return render_template('user_dashboard.html',
        my_bookings=my_bookings
    )

