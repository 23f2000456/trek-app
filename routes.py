from flask import render_template, redirect, url_for , request, flash
from app import app,db, login_manager
from models import User,Trek,Booking,TrekStaff 
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

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
        return redirect(url_for('login'))
    
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



#trek_management
@app.route('/admin/treks')
@login_required
def admin_treks():
    if current_user.role !='admin':
        return redirect(url_for('login'))
    treks = Trek.query.all()
    return render_template('admin_treks.html', treks=treks)

#add
@app.route('/admin/trek/add', methods=['GET', 'POST'])
@login_required
def admin_add_trek():
    if current_user.role !='admin':
        return redirect(url_for('login'))
    
    staff_list = User.query.filter_by(role='staff', approval=True).all()

    if request.method == 'POST':
        new_trek = Trek(
            name=request.form['name'],
            location=request.form['location'],
            difficulty=request.form['difficulty'],
            duration=request.form['duration'],
            total_slots=int(request.form['total_slots']),
            available_slots=int(request.form.get('available_slots', request.form['total_slots'])),
            assigned_staffid=request.form.get('assigned_staffid') or None,
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date(),
            status=request.form['status'],
            price=float(request.form['price'])
        )
        db.session.add(new_trek)
        db.session.commit()
        flash('Trek added successfully')
        return redirect(url_for('admin_treks'))
    
    return render_template('admin_add_trek.html', staff_list=staff_list)

#edit
@app.route('/admin/trek/edit/<int:trek_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_trek(trek_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    trek = Trek.query.get_or_404(trek_id)
    staff_list=User.query.filter_by(role='staff', approval=True).all()

    if request.method == 'POST':
        trek.name=request.form['name']
        trek.location=request.form['location']
        trek.difficulty=request.form['difficulty']
        trek.duration=request.form['duration']
        trek.total_slots=int(request.form['total_slots'])
        trek.available_slots=int(request.form['available_slots'])
        trek.assigned_staffid=request.form.get('assigned_staffid') or None
        trek.start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        trek.end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        trek.status=request.form['status']
        trek.place=float(request.form['price'])
        db.session.commit()
        flash('Trek updated successfully')
        return redirect(url_for('admin_treks'))
    
    return render_template('admin_edit_trek.html', trek=trek, staff_list=staff_list)

#delete
@app.route('/admin/trek/delete/<int:trek_id>')
@login_required
def admin_delete_trek(trek_id):
    if current_user.role !='admin':
        return redirect(url_for('login'))
    trek = Trek.query.get_or_404(trek_id)
    db.session.delete(trek)
    db.session.commit()
    flash('Trek deleted successfully')
    return redirect(url_for('admin_treks'))



#staff_management
@app.route('/admin/staff')
@login_required
def admin_staff():
    if current_user.role !='admin':
        return redirect(url_for('login'))
    staff_list = User.query.filter_by(role='staff').all()
    return render_template('admin_staff.html', staff_list=staff_list)

#approval
@app.route('/admin/staff/approve/<int:user_id>')
@login_required
def approve_staff(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    staff = User.query.get_or_404(user_id)
    staff.approval = True
    db.session.commit()
    flash(f'{staff.name} approved successfully')
    return redirect(url_for('admin_staff'))

#blacklist
@app.route('/admin/staff/blacklist/<int:user_id>')
@login_required
def blacklist_staff(user_id):
    if current_user.role !='admin':
        return redirect(url_for('login'))
    staff = User.query.get_or_404(user_id)
    staff.blacklist = True
    db.session.commit()
    flash(f'{staff.name} has been blacklisted')
    return redirect(url_for('admin_staff'))

#remove
@app.route('/admin/staff/remove/<int:user_id>')
@login_required
def remove_staff(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    staff = User.query.get_or_404(user_id)
    if staff.staff_profile:
        db.session.delete(staff.staff_profile)
    db.session.delete(staff)
    db.session.commit()
    flash('Staff removed Successfully')
    return redirect(url_for('admin_staff'))


#user_management
@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    users = User.query.filter_by(role='trekker').all()
    return render_template('admin_users.html', users=users)

#blacklist
@app.route('/admin/user/blacklist/<int:user_id>')
@login_required
def blacklist_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    user = User.query.get_or_404(user_id)
    user.blacklist = True
    db.session.commit()
    flash(f'{user.name} had been blacklisted')
    return redirect(url_for('admin_users'))


#bookings
@app.route('/admin/bookings')
@login_required
def admin_bookings():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    bookings = Booking.query.all()
    return render_template('admin_bookings.html', bookings=bookings)


#search
@app.route('/admin/search')
@login_required
def admin_search():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    query=request.args.get('q','')
    search_type= request.args.get('type','trek')
    results=[]

    if query:
        if search_type == 'trek':
            results = Trek.query.filter(
                Trek.name.ilike(f'%{query}%') |
                Trek.id.like(f'%{query}%')
            ).all()
        elif search_type == 'staff':
            results = User.query.filter(
                User.role == 'staff',
                User.name.ilike(f'%{query}%') |
                User.id.like(f'%{query}%')
            ).all()
        elif search_type == 'user':
            results = User.query.filter(
                User.role == 'trekker',
                User.name.ilike(f'%{query}%') |
                User.id.like(f'%{query}%')
            ).all()

    return render_template('admin_search.html',
        results=results,
        query=query,
        search_type=search_type
    )




#staffmanagement

#profile_update
@app.route('/staff/profile', methods=['GET', 'POST'])
@login_required
def staff_profile():
    if current_user.role != 'staff':
        flash('Access Denied')
        return redirect(url_for('login'))
    
    profile = TrekStaff.query.filter_by(id=current_user.id).first()

    if request.method == 'POST':
        current_user.name = request.form.get('name', current_user.name)
        profile.contact = request.form.get('contact', profile.contact)
        db.session.commit()
        flash('Profile updated successfully')
        return redirect(url_for('staff_profile'))
    
    return render_template('staff_profile.html',
                        profile=profile
    )

#staff_dashboard
@app.route('/staff/dashboard')
@login_required
def staff_dashboard():
    if current_user.role != 'staff':
        flash('Acess Denied')
        return redirect(url_for('login'))
    
    assigned_treks = Trek.query.filter_by(assigned_staffid=current_user.id).all()

    #count
    trek_data = []
    for trek in assigned_treks:
        count = Booking.query.filter_by(
            trek_id=trek.id,
            status='Booked'
        ).count()
        trek_data.append({
            'trek': trek,
            'registered_count': count
        })

    return render_template('staff_dashboard.html',
        trek_data=trek_data
    )

#view_participants
@app.route('/staff/trek/<int:trek_id>/participants')
@login_required
def staff_trek_participants(trek_id):
    if current_user.role != 'staff':
        flash('Access Denied')
        return redirect(url_for('login'))
    
    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staffid != current_user.id:
        flash('You are not assigned to this trek')
        return redirect(url_for('staff_dashbooard'))
    
    bookings = Booking.query.filter_by(trek_id=trek_id).all()
    participants = []
    for booking in bookings:
        user = User.query.get(booking.user_id)
        participants.append({
            'user': user,
            'booking': booking
        })

    return render_template('staff_participants.html',
        trek=trek,
        participants=participants
    )

#update_trek
@app.route('/staff/trek/<int:trek_id>/update', methods=['GET', 'POST'])
@login_required
def staff_update_trek(trek_id):
    if current_user.role !='staff':
        flash('Access Denied')
        return redirect(url_for('login'))
    
    trek= Trek.query.get_or_404(trek_id)

    if trek.assigned_staffid != current_user.id:
        flash('You are not assigned to this trek')
        return redirect(url_for('staff_dashboard'))
    
    if request.method == 'POST':
        new_slots = request.form.get('available_slots')
        new_status = request.form.get('status')

        if new_slots:
            trek.available_slots = int(new_slots)
        if new_status:
            trek.status = new_status

        db.session.commit()
        flash('Trek updated successfully')
        return redirect(url_for(staff_dashboard))
    
    return render_template('staff_update_trek.html', trek=trek)