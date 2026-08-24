from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required
from app.models import AdminUser, SiteContent, Event, CarouselImage, Setting, db
from app.security import (
    limiter, LoginForm, SettingsForm, EventForm, save_uploaded_image
)

admin_bp = Blueprint('admin_bp', __name__)


@admin_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute; 20 per hour")
def login():
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user = AdminUser.query.filter_by(
                username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                return redirect(url_for('admin_bp.dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('admin/login.html', form=form)


@admin_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('admin_bp.login'))


@admin_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    # 1. SMART INITIALIZATION (Prevents duplicates by checking specific page names)

    # Check and add 'About' page
    if not SiteContent.query.filter_by(page='about').first():
        db.session.add(SiteContent(
            page='about',
            title='About Us',
            body='Shri Sarwatma Dham Ashram was established by Swami Sarwatma Nand Maharaj in 1984...'
        ))
        db.session.commit()

    # Check and add 'Home' page
    if not SiteContent.query.filter_by(page='home').first():
        db.session.add(SiteContent(
            page='home',
            title='Shri Sarwatma Dham Ashram',
            body='Dhyana Bhakti Yoga Asana Pranayam Satsang'
        ))
        db.session.commit()

    # Check and add 'Events' page
    if not SiteContent.query.filter_by(page='events').first():
        db.session.add(SiteContent(
            page='events',
            title='Upcoming Events',
            body='Join our spiritual gatherings and yoga sessions.'
        ))
        db.session.commit()

    # Check and add Settings
    if not Setting.query.filter_by(key='address').first():
        db.session.add_all([
            Setting(key='address',
                    value='Swarg Ashram, Rishikesh, Uttarakhand 249304'),
            Setting(key='email', value='info@sarwatma.com'),
            Setting(key='footer_text',
                    value='Copyright © 2026 Shri Sarwatma Dham. All rights reserved.'),
            Setting(
                key='map_url', value='https://maps.google.com/maps?q=Sarwatma%20Dham%20Ashram&t=m&z=10&output=embed&iwloc=near')
        ])
        db.session.commit()

    # 2. FETCH ALL DATA
    contents = SiteContent.query.all()
    events = Event.query.all()
    carousel_images = CarouselImage.query.all()
    settings = {s.key: s.value for s in Setting.query.all()}

    # 3. FETCH DONATIONS (Newest First)
    from app.models import Donation
    donations = Donation.query.order_by(Donation.created_at.desc()).all()

    return render_template(
        'admin/dashboard.html',
        contents=contents,
        events=events,
        carousel_images=carousel_images,
        settings_dict=settings,
        donations=donations
    )


@admin_bp.route('/update-settings', methods=['POST'])
@login_required
def update_settings():
    form = SettingsForm()
    if form.validate_on_submit():
        for field_name in ['address', 'email', 'footer_text', 'map_url']:
            val = getattr(form, field_name).data or ''
            setting = Setting.query.filter_by(key=field_name).first()
            if setting:
                setting.value = val.strip()
            else:
                db.session.add(Setting(key=field_name, value=val.strip()))
        db.session.commit()
        flash('Global settings updated successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}", 'danger')
    return redirect(url_for('admin_bp.dashboard'))


@admin_bp.route('/update-content/<int:id>', methods=['POST'])
@login_required
def update_content(id):
    content = SiteContent.query.get_or_404(id)
    title = request.form.get('title', '').strip()
    body = request.form.get('body', '').strip()

    if not title or not body or len(title) > 200 or len(body) > 3000:
        flash('Invalid title or body content length.', 'danger')
        return redirect(url_for('admin_bp.dashboard'))

    content.title = title
    content.body = body

    file = request.files.get('image')
    if file and file.filename:
        try:
            filename = save_uploaded_image(
                file, current_app.config['UPLOAD_FOLDER'])
            if filename:
                content.image_url = f'uploads/{filename}'
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('admin_bp.dashboard'))

    db.session.commit()
    flash(f'{content.page.capitalize()} page updated!', 'success')
    return redirect(url_for('admin_bp.dashboard'))


@admin_bp.route('/upload-slider', methods=['POST'])
@login_required
def upload_slider():
    file = request.files.get('slider_image')
    if not file or not file.filename:
        flash('Please choose an image file to upload.', 'danger')
        return redirect(url_for('admin_bp.dashboard'))

    try:
        filename = save_uploaded_image(
            file, current_app.config['UPLOAD_FOLDER'])
        db.session.add(CarouselImage(image_url=f'uploads/{filename}'))
        db.session.commit()
        flash('Slider image added successfully!', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    return redirect(url_for('admin_bp.dashboard'))


@admin_bp.route('/delete-slider/<int:id>', methods=['POST'])
@login_required
def delete_slider(id):
    slider = CarouselImage.query.get_or_404(id)
    db.session.delete(slider)
    db.session.commit()
    flash('Slider image deleted!', 'success')
    return redirect(url_for('admin_bp.dashboard'))


@admin_bp.route('/add-event', methods=['POST'])
@login_required
def add_event():
    form = EventForm()
    if form.validate_on_submit():
        image_url = ''
        file = request.files.get('image')
        if file and file.filename:
            try:
                filename = save_uploaded_image(
                    file, current_app.config['UPLOAD_FOLDER'])
                if filename:
                    image_url = f'uploads/{filename}'
            except ValueError as e:
                flash(str(e), 'danger')
                return redirect(url_for('admin_bp.dashboard'))

        new_event = Event(
            title=form.title.data.strip(),
            event_date=form.event_date.data.strip(),
            description=form.description.data.strip(),
            image_url=image_url
        )
        db.session.add(new_event)
        db.session.commit()
        flash('New event added successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.capitalize()}: {error}", 'danger')
    return redirect(url_for('admin_bp.dashboard'))


@admin_bp.route('/delete-event/<int:id>', methods=['POST'])
@login_required
def delete_event(id):
    event = Event.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted!', 'success')
    return redirect(url_for('admin_bp.dashboard'))
