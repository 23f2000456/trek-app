from flask import render_template, redirect, url_for , request, flash
from app import app,db, login_manager
from models import User,Trek,Booking,TrekStaff 
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, UTC

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


#adminmanagement admin admin admin admin admin admin admin admin admin admin admin admin admin admin admin admin admin admin admin admin admin

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

#trek_management
@app.route('/admin/treks')
@login_required
def admin_treks():
    if current_user.role !='admin':
        return redirect(url_for('login'))
    treks = Trek.query.all()
    return render_template('admin_treks.html', treks=treks)

#addtrek
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

#edittrek
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

#deletetrek
@app.route('/admin/trek/delete/<int:trek_id>')
@login_required
def admin_delete_trek(trek_id):
    if current_user.role !='admin':
        return redirect(url_for('login'))
    trek = Trek.query.get_or_404(trek_id)
    Booking.query.filter_by(trek_id=trek_id).delete()

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

@app.route('/admin/staff/unblacklist/<int:user_id>')
@login_required
def unblacklist_staff(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    staff = User.query.get_or_404(user_id)
    staff.blacklist = False
    db.session.commit()
    flash(f'{staff.name} has been unblacklisted')
    return redirect(url_for('admin_staff'))

@app.route('/admin/staff/remove/<int:user_id>')
@login_required
def remove_staff(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))

    staff = User.query.get_or_404(user_id)

    # Delete bookings for treks assigned to this staff
    assigned_treks = Trek.query.filter_by(assigned_staffid=user_id).all()
    for trek in assigned_treks:
        Booking.query.filter_by(trek_id=trek.id).delete()
        db.session.delete(trek)

    # Delete staff profile
    if staff.staff_profile:
        db.session.delete(staff.staff_profile)

    # Delete the user
    db.session.delete(staff)
    db.session.commit()

    flash('Staff removed successfully')
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

@app.route('/admin/user/unblacklist/<int:user_id>')
@login_required
def unblacklist_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    user = User.query.get_or_404(user_id)
    user.blacklist = False
    db.session.commit()
    flash(f'{user.name} has been unblacklisted')
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




#staffmanagement staff staff staff staff  staff staff staff staff  staff staff staff staff  staff staff staff staff  staff staff staff staff 

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
        return redirect(url_for('staff_dashboard'))
    
    return render_template('staff_update_trek.html', trek=trek)



#usermanagemnt user user user user user user user user user user user user user user user user user user user user user user user user


#user_dashboard
@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.role != 'trekker':
        flash('Access Denied')
        return redirect(url_for('login'))

    my_bookings = Booking.query.filter_by(user_id=current_user.id).all()
    
    booking_data = []
    for booking in my_bookings:
        trek = Trek.query.get(booking.trek_id)
        booking_data.append({
            'booking': booking,
            'trek': trek
        })

    available_treks = Trek.query.filter_by(status='Open').all()

    return render_template('user_dashboard.html',
        booking_data=booking_data,
        available_treks=available_treks
    )

#user_profile
@app.route('/user/profile',methods=['GET', 'POST'])
@login_required
def user_profile():
    if current_user.role != 'trekker':
        flash('Access Denied')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        current_user.name = request.form.get('name', current_user.name)
        db.session.commit()
        flash ('Profile updated successfully')
        return redirect(url_for('user_profile'))
    
    return render_template('user_profile.html')

#view_treks
@app.route('/user/treks')
@login_required
def user_treks():
    if current_user.role != 'trekker':
        flash('Access Denied')
        return redirect(url_for('login'))
    
    difficulty = request.args.get('difficulty','')
    location = request.args.get('location', '')
    search = request.args.get('search', '')

    query = Trek.query.filter_by(status='Open')

    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if location:
        query = query.filter(Trek.location.ilike(f'%{location}%'))
    if search:
        query = query.filter(Trek.name.ilike(f'%{search}%'))

    treks = query.all()

    return render_template('user_treks.html',
        treks=treks,
        difficulty=difficulty,
        location=location,
        search=search
    )

#booktrek
@app.route('/user/trek/<int:trek_id>/book', methods=['GET', 'POST'])
@login_required
def book_trek(trek_id):
    if current_user.role != 'trekker':
        flash('Access Denied')
        return redirect(url_for('login'))

    trek = Trek.query.get_or_404(trek_id)

    if trek.status != 'Open':
        flash('This trek is not open for booking')
        return redirect(url_for('user_treks'))
    
    if trek.available_slots <= 0:
        flash('No slots available for this trek')
        return redirect(url_for('user_treks'))

    existing = Booking.query.filter_by(
        user_id=current_user.id,
        trek_id=trek_id
    ).first()
    if existing:
        flash('You have already booked this trek')
        return redirect(url_for('user_treks'))

    if request.method == 'POST':
        new_booking = Booking(
            user_id=current_user.id,
            trek_id=trek_id,
            booking_date=datetime.now(UTC).date(),
            status='Booked'
        )
        db.session.add(new_booking)

        trek.available_slots -= 1
        db.session.commit()

        flash('Trek booked successfully')
        return redirect(url_for('user_dashboard'))
    
    return render_template('user_book_trek.html', trek=trek)


#cancelbooking
@app.route('/user/booking/<int:booking_id>/cancel')
@login_required
def cancel_booking(booking_id):
    if current_user.role != 'trekker':
        flash('Access Denied')
        return redirect(url_for('login'))

    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current_user.id:
        flash('Unauthorized action')
        return redirect(url_for('user_dashboard'))
    
    if booking.status != 'Booked':
        flash('This booking cannot be cancelled')
        return redirect(url_for('user_dashboard'))
    
    booking.status = 'Cancelled'

    trek = Trek.query.get(booking.trek_id)
    trek.available_slots += 1
    db.session.commit()

    flash('Booking cancelled successfully')
    return redirect(url_for('user_dashboard'))

#trekhistory
@app.route('/user/history')
@login_required
def user_history():
    if current_user.role != 'trekker':
        flash('Access Denied')
        return redirect(url_for('login'))

    history = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.status.in_(['Completed', 'Cancelled'])
    ).all()

    history_data = []
    for booking in history:
        trek = Trek.query.get(booking.trek_id)
        history_data.append({
            'booking': booking,
            'trek': trek
        })

    return render_template('user_history.html',
        history_data=history_data
    ) 


#booking_management


#booking_completed
@app.route('/admin/booking/<int:booking_id>/complete')
@login_required
def admin_complete_booking(booking_id):
    if current_user.role != 'admin':
        flash('Access Denied')
        return redirect(url_for('login'))

    booking = Booking.query.get_or_404(booking_id)
    booking.status = 'Completed'
    db.session.commit()
    flash('Booking marked as completed')
    return redirect(url_for('admin_bookings'))

#booking_cancelled
@app.route('/admin/booking/<int:booking_id>/cancel')
@login_required
def admin_cancel_booking(booking_id):
    if current_user.role != 'admin':
        flash('Access Denied')
        return redirect(url_for('login'))

    booking = Booking.query.get_or_404(booking_id)

    if booking.status == 'Booked':
        trek = Trek.query.get(booking.trek_id)
        trek.available_slots += 1

    booking.status = 'Cancelled'
    db.session.commit()
    flash('Booking cancelled')
    return redirect(url_for('admin_bookings'))



@app.route('/staff/trek/<int:trek_id>/complete')
@login_required
def staff_complete_trek(trek_id):
    if current_user.role != 'staff':
        flash('Access Denied')
        return redirect(url_for('login'))

    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staffid != current_user.id:
        flash('You are not assigned to this trek')
        return redirect(url_for('staff_dashboard'))
    
    trek.status = 'Completed'

    bookings = Booking.query.filter_by(
        trek_id=trek_id,
        status='Booked'
    ).all()
    for booking in bookings:
        booking.status = 'Completed'

    db.session.commit()
    flash(f'{trek.name} marked as completed')
    return redirect(url_for('staff_dashboard'))

#staff_view_history
@app.route('/staff/trek/<int:trek_id>/history')
@login_required
def staff_trek_history(trek_id):
    if current_user.role != 'staff':
        flash('Access Denied')
        return redirect(url_for('login'))

    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staffid != current_user.id:
        flash('You are not assigned to this trek')
        return redirect(url_for('staff_dashboard'))

    all_bookings = Booking.query.filter_by(trek_id=trek_id).all()

    booking_data = []
    for booking in all_bookings:
        user = User.query.get(booking.user_id)
        booking_data.append({
            'booking': booking,
            'user': user
        })

    return render_template('staff_trek_history.html',
        trek=trek,
        booking_data=booking_data
    )