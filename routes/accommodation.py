from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, flash
from datetime import datetime, timedelta
import uuid
from db import get_db_connection

accommodation_bp = Blueprint('accommodation', __name__)

@accommodation_bp.route('/booking')
def booking():
    if 'customer_id' not in session and 'staff_id' not in session and 'manager_id' not in session:
        flash('Please log in to access booking.', 'warning')
        return redirect(url_for('user.login'))

    connection, cursor = get_db_connection()
    cursor.execute("""
        SELECT products.productid,
               products.name,
               products.description,
               products.price AS price_per_night,
               products.image
        FROM products
        WHERE products.category = 'accommodation'
          AND products.isavailable = 1;
    """)
    accommodation_products = cursor.fetchall()
    connection.close()
    return render_template('accommodation/accommodation_booking.html', accommodation_products=accommodation_products, userid=session.get('customer_id') or session.get('staff_id') or session.get('manager_id'))

@accommodation_bp.route('/availability/<int:productid>', methods=['GET'])
def check_availability(productid):
    connection, cursor = get_db_connection()
    
    # Get availability data
    cursor.execute("""
        SELECT accommodationavailability.date,
               accommodationavailability.availablerooms
        FROM accommodations
        JOIN accommodationavailability ON accommodations.accommodationid = accommodationavailability.accommodationid
        WHERE accommodations.productid = %s;
    """, (productid,))
    availability = cursor.fetchall()

    # Get booked dates
    cursor.execute("""
        SELECT checkindate, checkoutdate, SUM(num_beds) as total_beds
        FROM bookings
        JOIN accommodations ON bookings.accommodationid = accommodations.accommodationid
        WHERE accommodations.productid = %s
          AND bookings.status = 'booked'
        GROUP BY checkindate, checkoutdate;
    """, (productid,))
    bookings = cursor.fetchall()
    
    # Get blocked dates
    cursor.execute("""
        SELECT date
        FROM blocked_dates
        JOIN accommodations ON blocked_dates.accommodationid = accommodations.accommodationid
        WHERE accommodations.productid = %s;
    """, (productid,))
    blocked_dates = cursor.fetchall()

    connection.close()

    # Process the data
    availability_data = [{
        'date': row[0].strftime('%Y-%m-%d'),
        'availablerooms': row[1]
    } for row in availability]
    
    booked_dates = {}
    for booking in bookings:
        checkin_date = booking[0]
        checkout_date = booking[1] - timedelta(days=1)  # Fix for not including the next day
        total_beds = booking[2]
        current_date = checkin_date
        while current_date <= checkout_date:
            date_str = current_date.strftime('%Y-%m-%d')
            if date_str not in booked_dates:
                booked_dates[date_str] = 0
            booked_dates[date_str] += total_beds
            current_date += timedelta(days=1)

    blocked_dates_list = [row[0].strftime('%Y-%m-%d') for row in blocked_dates]

    return jsonify({
        'availability': availability_data,
        'booked_dates': booked_dates,
        'blocked_dates': blocked_dates_list
    })

@accommodation_bp.route('/check_availability', methods=['POST'])
def check_availability_post():
    data = request.json
    productid = data.get('productid')
    check_in = data.get('check_in')
    check_out = data.get('check_out')
    num_guests = data.get('num_guests')

    # Validate input
    if not (check_in and check_out and num_guests):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        check_in = datetime.strptime(check_in, '%Y-%m-%d')
        check_out = datetime.strptime(check_out, '%Y-%m-%d')
        num_guests = int(num_guests)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid date format or number of guests'}), 400

    connection, cursor = get_db_connection()

    # Fetch accommodation details
    cursor.execute("""
        SELECT accommodationid, maxcapacity, room_type, price
        FROM accommodations
        JOIN products ON accommodations.productid = products.productid
        WHERE accommodations.productid = %s
        LIMIT 1;
    """, (productid,))
    accommodation = cursor.fetchone()

    if not accommodation:
        connection.close()
        return jsonify({'error': 'No accommodation found for this product'}), 404

    accommodation_id, max_capacity, room_type, price_per_night = accommodation

    # Check if the dates are blocked
    cursor.execute("""
        SELECT date
        FROM blocked_dates
        WHERE accommodationid = %s
          AND date BETWEEN %s AND %s;
    """, (accommodation_id, check_in, check_out))
    blocked_dates = cursor.fetchall()

    if blocked_dates:
        connection.close()
        return jsonify({'error': 'Selected dates include blocked dates and cannot be booked'}), 400

    # Check bed availability
    cursor.execute("""
        SELECT SUM(num_beds)
        FROM bookings
        WHERE accommodationid = %s
          AND status = 'booked'
          AND ((checkindate BETWEEN %s AND %s) OR (checkoutdate BETWEEN %s AND %s) OR (checkindate <= %s AND checkoutdate >= %s));
    """, (accommodation_id, check_in, check_out, check_in, check_out, check_in, check_out))
    booked_beds = cursor.fetchone()[0] or 0

    if booked_beds + num_guests > max_capacity:
        connection.close()
        return jsonify({'error': 'Not enough beds available'}), 400

    # Calculate total cost
    total_nights = (check_out - check_in).days
    if room_type == 'dorm':
        total_cost = total_nights * price_per_night * num_guests  # Cost per guest per night
    elif room_type == 'queen':
        total_cost = total_nights * 100  # Fixed cost per night for queen room
    elif room_type == 'twin':
        total_cost = total_nights * 80  # Fixed cost per night for twin room
    else:
        total_cost = total_nights * price_per_night

    connection.close()

    return jsonify({
        'total_cost': total_cost,
        'available_rooms': max_capacity - booked_beds
    })

@accommodation_bp.route('/book', methods=['POST'])
def book_room():
    data = request.json
    productid = data.get('productid')
    check_in = data.get('check_in')
    check_out = data.get('check_out')
    customer_id = data.get('customer_id')
    num_beds = data.get('num_beds')

    # Validate input
    if not (check_in and check_out and customer_id and num_beds):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        check_in = datetime.strptime(check_in, '%Y-%m-%d')
        check_out = datetime.strptime(check_out, '%Y-%m-%d')
        num_beds = int(num_beds)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid date format or number of beds'}), 400

    connection, cursor = get_db_connection()

    # Fetch accommodation details
    cursor.execute("""
        SELECT accommodationid, maxcapacity, room_type, price
        FROM accommodations
        JOIN products ON accommodations.productid = products.productid
        WHERE accommodations.productid = %s
        LIMIT 1;
    """, (productid,))
    accommodation = cursor.fetchone()

    if not accommodation:
        connection.close()
        return jsonify({'error': 'No accommodation found for this product'}), 404

    accommodation_id, max_capacity, room_type, price_per_night = accommodation

    # Check if the dates are blocked
    cursor.execute("""
        SELECT date
        FROM blocked_dates
        WHERE accommodationid = %s
          AND date BETWEEN %s AND %s;
    """, (accommodation_id, check_in, check_out))
    blocked_dates = cursor.fetchall()

    if blocked_dates:
        connection.close()
        return jsonify({'error': 'Selected dates include blocked dates and cannot be booked'}), 400

    # Check bed availability
    cursor.execute("""
        SELECT SUM(num_beds)
        FROM bookings
        WHERE accommodationid = %s
          AND status = 'booked'
          AND ((checkindate BETWEEN %s AND %s) OR (checkoutdate BETWEEN %s AND %s) OR (checkindate <= %s AND checkoutdate >= %s));
    """, (accommodation_id, check_in, check_out, check_in, check_out, check_in, check_out))
    booked_beds = cursor.fetchone()[0] or 0

    if booked_beds + num_beds > max_capacity:
        connection.close()
        return jsonify({'error': 'Not enough beds available'}), 400

    # Calculate total cost based on room type
    total_nights = (check_out - check_in).days
    if room_type == 'dorm':
        total_cost = total_nights * price_per_night * num_beds  # Cost per guest per night
    elif room_type == 'queen':
        total_cost = total_nights * 100  # Fixed cost per night for queen room
    elif room_type == 'twin':
        total_cost = total_nights * 80  # Fixed cost per night for twin room
    else:
        total_cost = total_nights * price_per_night

    booking_reference = str(uuid.uuid4())

    session['booking_details'] = {
        'customer_id': customer_id,
        'accommodation_id': accommodation_id,
        'check_in': check_in.strftime('%Y-%m-%d'),
        'check_out': check_out.strftime('%Y-%m-%d'),
        'num_beds': num_beds,
        'total_cost': total_cost,
        'booking_reference': booking_reference
    }

    connection.close()

    return jsonify({
        'customer_id': customer_id,
        'accommodation_id': accommodation_id,
        'check_in': check_in.strftime('%Y-%m-%d'),
        'check_out': check_out.strftime('%Y-%m-%d'),
        'total_cost': total_cost,
        'booking_reference': booking_reference
    })


@accommodation_bp.route('/availability_page/<int:productid>')
def availability_page(productid):
    connection, cursor = get_db_connection()
    cursor.execute("""
        SELECT productid, name, description, image
        FROM products
        WHERE productid = %s
    """, (productid,))
    product = cursor.fetchone()
    connection.close()

    if not product:
        flash('Product not found', 'danger')
        return redirect(url_for('accommodation.booking'))

    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('accommodation/booking_availability.html', product=product, current_date=current_date)
