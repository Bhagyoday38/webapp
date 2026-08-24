import razorpay
from flask import Blueprint, request, jsonify, current_app
from app.models import Donation, db
from app.security import limiter

payment_bp = Blueprint('payment_bp', __name__)


@payment_bp.route('/create-order', methods=['POST'])
@limiter.limit("10 per minute; 50 per hour")
def create_order():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid request format.'}), 400

    donor_name = str(data.get('name', '')).strip()
    donor_email = str(data.get('email', '')).strip()
    donor_phone = str(data.get('phone', '')).strip()
    amount_input = data.get('amount')

    # Strict Server-Side Validation
    try:
        amount_in_rupees = int(amount_input)
        if not (1 <= amount_in_rupees <= 1_000_000):
            return jsonify({'error': 'Donation amount must be between ₹1 and ₹10,00,000.'}), 400
        if not donor_name or len(donor_name) > 120:
            return jsonify({'error': 'Please provide a valid donor name (max 120 characters).'}), 400
        if not donor_email or '@' not in donor_email or len(donor_email) > 200:
            return jsonify({'error': 'Please provide a valid email address.'}), 400
        if not donor_phone or not donor_phone.isdigit() or not (10 <= len(donor_phone) <= 15):
            return jsonify({'error': 'Please provide a valid phone number (10-15 digits).'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid donation amount.'}), 400

    amount_in_paise = amount_in_rupees * 100

    client = razorpay.Client(auth=(
        current_app.config['RAZORPAY_KEY_ID'],
        current_app.config['RAZORPAY_KEY_SECRET']
    ))

    order_data = {
        'amount': amount_in_paise,
        'currency': 'INR',
        'payment_capture': 1
    }

    try:
        order = client.order.create(data=order_data)
        donation = Donation(
            donor_name=donor_name,
            donor_email=donor_email,
            donor_phone=donor_phone,
            amount=amount_in_rupees,
            payment_id=order['id'],
            status='Pending'
        )
        db.session.add(donation)
        db.session.commit()

        return jsonify({
            'order_id': order['id'],
            'amount': order['amount'],
            'key': current_app.config['RAZORPAY_KEY_ID']
        })
    except Exception as e:
        return jsonify({'error': 'Unable to initiate payment transaction.'}), 500


@payment_bp.route('/verify', methods=['POST'])
@limiter.limit("20 per minute")
def verify_payment():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'status': 'Payment Failed', 'error': 'Missing payload'}), 400

    client = razorpay.Client(auth=(
        current_app.config['RAZORPAY_KEY_ID'],
        current_app.config['RAZORPAY_KEY_SECRET']
    ))

    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': data.get('razorpay_order_id'),
            'razorpay_payment_id': data.get('razorpay_payment_id'),
            'razorpay_signature': data.get('razorpay_signature')
        })

        donation = Donation.query.filter_by(
            payment_id=data.get('razorpay_order_id')).first()
        if donation:
            donation.status = 'Success'
            db.session.commit()

        return jsonify({'status': 'Payment Verified'})
    except razorpay.errors.SignatureVerificationError:
        return jsonify({'status': 'Payment Failed', 'error': 'Signature verification failed'}), 400
    except Exception as e:
        return jsonify({'status': 'Payment Failed', 'error': str(e)}), 400
