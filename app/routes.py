from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models import SiteContent, Event, CarouselImage
from app.security import ContactForm, limiter

public_bp = Blueprint('public_bp', __name__)


@public_bp.route('/')
def index():
    content = SiteContent.query.filter_by(page='home').first()
    carousel_images = CarouselImage.query.all()
    return render_template('index.html', content=content, carousel_images=carousel_images)


@public_bp.route('/about')
def about():
    content = SiteContent.query.filter_by(page='about').first()
    return render_template('about.html', content=content)


@public_bp.route('/events')
def events():
    events_list = Event.query.all()
    return render_template('events.html', events=events_list)


@public_bp.route('/contact', methods=['GET', 'POST'])
@limiter.limit("5 per minute; 20 per hour", methods=['POST'])
def contact():
    form = ContactForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            # If the honeypot field is filled, silently discard or flash success without processing
            if form.website.data:
                flash('Your message has been sent!', 'success')
                return redirect(url_for('public_bp.contact'))

            # Process / log / email the validated contact inquiry here
            flash('Thank you for reaching out! We will get back to you soon.', 'success')
            return redirect(url_for('public_bp.contact'))
        else:
            for field, errors in form.errors.items():
                if field != 'website':
                    for error in errors:
                        flash(f"{field.capitalize()}: {error}", 'danger')
    return render_template('contact.html', form=form)


@public_bp.route('/donate')
def donate():
    return render_template('donate.html')
