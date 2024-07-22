from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, session
from db import get_db_connection, hashing
import mysql.connector
import json
from datetime import datetime, timedelta, date
from flask_hashing import Hashing
import scheduler
import logging
import connect


logging.basicConfig(level=logging.DEBUG)

user_bp = Blueprint('user', __name__)
hashing = Hashing()

def calculate_total_prep_time(order_items):
    connection, cursor = get_db_connection()
    total_prep_time = 0
    for item in order_items:
        cursor.execute("SELECT default_prep_time FROM products WHERE productid = %s", (item['product_id'],))
        prep_time = cursor.fetchone()[0]
        total_prep_time += prep_time * item['quantity']
    connection.close()
    return total_prep_time

def schedule_order_updates(order_id, order_type, scheduled_datetime=None):
    now = datetime.now()
    if order_type == 'now':
        # Schedule "preparing" 8 minutes after confirming (2 minutes remaining)
        scheduler.schedule_status_update(order_id, 'preparing', now + timedelta(minutes=2))
        # Schedule "ready" 10 minutes after confirming (0 minutes remaining)
        scheduler.schedule_status_update(order_id, 'ready', now + timedelta(minutes=10))
    elif order_type == 'later' and scheduled_datetime:
        # Schedule "preparing" 8 minutes before the scheduled time
        scheduler.schedule_status_update(order_id, 'preparing', scheduled_datetime - timedelta(minutes=8))
        # Schedule "ready" at the scheduled time
        scheduler.schedule_status_update(order_id, 'ready', scheduled_datetime)

        
@user_bp.route('/role_dashboard')
def role_dashboard():
    if 'username' not in session:
        flash('You need to log in first', 'danger')
        return redirect(url_for('user.login'))

    usertype = session.get('usertype')
    
    if usertype == 'customer':
        return redirect(url_for('user.dashboard'))
    elif usertype == 'staff':
        return redirect(url_for('staff.dashboard'))
    elif usertype == 'manager':
        return redirect(url_for('manager.dashboard'))
    else:
        flash('Invalid user type', 'danger')
        return redirect(url_for('user.login'))

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        hashed_password = hashing.hash_value(password, salt='abc123')

        connection, cursor = get_db_connection()

        if connection is None:
            flash('Database connection failed', 'danger')
            return render_template('register.html')

        try:
            logging.debug(f"Inserting new user {username} into the database")
            cursor.execute("INSERT INTO customers (username, firstname, lastname, email, phonenumber) VALUES (%s, %s, %s, %s, %s)",
                           (username, firstname, lastname, email, phone))
            customer_id = cursor.lastrowid

            cursor.execute("INSERT INTO usercredentials (username, passwordhash, usertype, customerid) VALUES (%s, %s, 'customer', %s)",
                           (username, hashed_password, customer_id))

            connection.commit()  
            flash('Registration successful!', 'success')
            return redirect(url_for('user.login'))
        except mysql.connector.Error as err:
            logging.error(f"Database error during registration: {err}")
            flash(f'Error: {err}', 'danger')
            connection.rollback()
        finally:
            cursor.close()
            connection.close()

    return render_template('register.html')



@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection, cursor = get_db_connection()

        if connection is None:
            flash('Database connection failed', 'danger')
            return render_template('login.html')

        try:
            cursor.execute("SELECT passwordhash, usertype, customerid, staffid, managerid FROM usercredentials WHERE username = %s", (username,))
            user = cursor.fetchone()

            if not user:
                flash('Username does not exist', 'danger')
                return render_template('login.html')

            if user and hashing.check_value(user[0], password, salt='abc123'):
                session['username'] = username
                session['usertype'] = user[1]

                if user[1] == 'customer':
                    session['customer_id'] = user[2]
                    flash('Login successful!', 'success')
                    return redirect(url_for('user.dashboard'))
                elif user[1] == 'staff':
                    session['staff_id'] = user[3]
                    flash('Login successful!', 'success')
                    return redirect(url_for('staff.dashboard'))
                elif user[1] == 'manager':
                    session['manager_id'] = user[4]  # Adjust if necessary
                    flash('Login successful!', 'success')
                    return redirect(url_for('manager.dashboard'))
            else:
                flash('Invalid username or password', 'danger')
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
        finally:
            cursor.close()
            connection.close()

    return render_template('login.html')

@user_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('user.login'))

@user_bp.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('You need to log in first', 'danger')
        return redirect(url_for('user.login'))

    username = session['username']
    customer_id = session.get('customer_id')

    connection, cursor = get_db_connection()
    if connection is None:
        return render_template('users/user_dashboard.html')

    try:
        cursor.execute("SELECT customerid, username, firstname, lastname FROM customers WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('user.login'))

        # Fetching food and drink orders
        cursor.execute("""
            SELECT o.orderid, o.totalprice, o.status, p.name, oi.quantity, oi.specialrequests, o.orderdate, o.estimated_time
            FROM orders o
            JOIN orderitems oi ON o.orderid = oi.orderid
            JOIN products p ON oi.productid = p.productid
            WHERE o.customerid = %s AND p.category IN ('food', 'drink')
            ORDER BY o.orderid DESC
        """, (user[0],))
        orders = cursor.fetchall()

        # Fetching merchandise orders
        cursor.execute("""
            SELECT o.orderid, o.totalprice, o.status, p.name, oi.quantity, o.orderdate
            FROM orders o
            JOIN orderitems oi ON o.orderid = oi.orderid
            JOIN products p ON oi.productid = p.productid
            WHERE o.customerid = %s AND p.category = 'merchandise'
            ORDER BY o.orderid DESC
        """, (user[0],))
        merchandise_orders = cursor.fetchall()

        # Fetching accommodation bookings
        cursor.execute("""
            SELECT b.bookingid, b.checkindate, b.checkoutdate, b.status, b.booking_reference, a.room_type
            FROM bookings b
            JOIN accommodations a ON b.accommodationid = a.accommodationid
            WHERE b.customerid = %s
        """, (user[0],))
        bookings = cursor.fetchall()

        return render_template('users/user_dashboard.html', user=user, orders=orders, merchandise_orders=merchandise_orders, bookings=bookings)
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        connection.close()

    return render_template('users/user_dashboard.html')


@user_bp.route('/profile', methods=['GET'])
def profile():
    customer_id = session.get('customer_id')
    connection, cursor = get_db_connection()

    # Clear specific flash messages related to payment success
    session['_flashes'] = [flash for flash in session.get('_flashes', []) if 'Payment successful' not in flash[1]]

    cursor.execute("SELECT firstname, lastname, email, phonenumber FROM customers WHERE customerid = %s", (customer_id,))
    customer_info = cursor.fetchone()
    cursor.close()
    connection.close()

    return render_template('users/profile.html', customer=customer_info)
@user_bp.route('/update_info', methods=['POST'])
def update_info():
    customer_id = session.get('customer_id')
    
    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    email = request.form.get('email')
    phone = request.form.get('phone')

    connection, cursor = get_db_connection()
    if connection is None:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('user.profile'))

    try:
        cursor.execute("""
            UPDATE customers 
            SET firstname = %s, lastname = %s, email = %s, phonenumber = %s 
            WHERE customerid = %s
        """, (firstname, lastname, email, phone, customer_id))
        connection.commit()
        flash('Information updated successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('user.profile', _anchor='info'))

@user_bp.route('/update_password', methods=['POST'])
def update_password():
    customer_id = session.get('customer_id')
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if new_password != confirm_password:
        flash('Passwords do not match.', 'danger')
        return redirect(url_for('user.profile', _anchor='password'))

    connection, cursor = get_db_connection()
    if connection is None:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('user.profile', _anchor='password'))

    try:
        cursor.execute("SELECT passwordhash FROM usercredentials WHERE customerid = %s AND usertype = 'customer'", (customer_id,))
        user = cursor.fetchone()

        if user and hashing.check_value(user[0], current_password, salt='abc123'):
            hashed_password = hashing.hash_value(new_password, salt='abc123')
            cursor.execute("UPDATE usercredentials SET passwordhash = %s WHERE customerid = %s AND usertype = 'customer'", (hashed_password, customer_id))
            connection.commit()
            flash('Password updated successfully!', 'success')
            return redirect(url_for('user.profile', _anchor='password'))
        else:
            flash('Invalid current password', 'danger')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('user.profile', _anchor='password'))


@user_bp.route('/order', methods=['GET', 'POST'])
def order():
    if request.method == 'POST':
        customer_id = session.get('customer_id')
        if not customer_id:
            flash('You need to log in first', 'danger')
            return redirect(url_for('user.login'))

        order_type = request.form.get('order_type')
        items = json.loads(request.form.get('items', '[]'))
        total_price = request.form.get('total_price')

        connection, cursor = get_db_connection()
        if connection is None:
            flash('Database connection failed.', 'danger')
            return render_template('users/user_order.html')

        try:
            order_details = []
            total_prep_time = calculate_total_prep_time(items)
            if order_type == 'now':
                cursor.execute("INSERT INTO orders (customerid, totalprice, status, ordertype, estimated_time) VALUES (%s, %s, 'pending', 'now', %s)", (customer_id, total_price, total_prep_time))
                order_id = cursor.lastrowid
                for item in items:
                    product_id = item['product_id']
                    quantity = int(item['quantity'])
                    customizations = item.get('customizations', {})
                    customizations['specialRequest'] = item.get('specialRequest', '')
                    customizations_json = json.dumps(customizations)
                    if quantity > 0:
                        cursor.execute("INSERT INTO orderitems (orderid, productid, quantity, specialrequests) VALUES (%s, %s, %s, %s)", (order_id, product_id, quantity, customizations_json))
                        order_details.append({'product_id': product_id, 'quantity': quantity, 'customizations': customizations})

                connection.commit()
                session['order_details'] = order_details
                flash('Order placed successfully for immediate processing!', 'success')
                schedule_order_updates(order_id, 'now')  # Schedule status updates
                return redirect(url_for('user.dashboard'))

            elif order_type == 'later':
                scheduled_time = request.form.get('scheduled_time')
                scheduled_datetime = datetime.fromisoformat(scheduled_time)
                scheduled_date, scheduled_time = scheduled_datetime.date(), scheduled_datetime.time()
                cursor.execute("INSERT INTO orders (customerid, totalprice, status, ordertype, scheduledate, scheduletime, estimated_time) VALUES (%s, %s, 'pending', 'later', %s, %s, %s)", (customer_id, total_price, scheduled_date, scheduled_time, total_prep_time))
                order_id = cursor.lastrowid
                for item in items:
                    product_id = item['product_id']
                    quantity = int(item['quantity'])
                    customizations = item.get('customizations', {})
                    customizations['specialRequest'] = item.get('specialRequest', '')
                    customizations_json = json.dumps(customizations)
                    if quantity > 0:
                        cursor.execute("INSERT INTO orderitems (orderid, productid, quantity, specialrequests) VALUES (%s, %s, %s, %s)", (order_id, product_id, quantity, customizations_json))
                        cursor.execute("INSERT INTO scheduleorders (orderid, productid, quantity, scheduledate, scheduletime, status) VALUES (%s, %s, %s, %s, %s, 'scheduled')", (order_id, product_id, quantity, scheduled_date, scheduled_time))
                        order_details.append({'product_id': product_id, 'quantity': quantity, 'customizations': customizations})

                connection.commit()
                session['order_details'] = order_details
                flash(f'Order scheduled successfully for {scheduled_time}!', 'success')
                schedule_order_updates(order_id, 'later', scheduled_datetime)  # Schedule status updates
                return redirect(url_for('user.dashboard'))

        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
            connection.rollback()
        finally:
            cursor.close()
            connection.close()

    connection, cursor = get_db_connection()
    if connection is None:
        flash('Database connection failed.', 'danger')
        return render_template('users/user_order.html')

    try:
        cursor.execute("""
            SELECT p.productid, p.name, p.description, p.price, p.category, p.image 
            FROM products p
            JOIN inventory i ON p.productid = i.productid
            WHERE i.quantityavailable > 0 AND p.category IN ('food', 'drink')
        """)
        products = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        products = []
    finally:
        cursor.close()
        connection.close()

    return render_template('users/user_order.html', products=products, datetime=datetime)

@user_bp.route('/order-now', methods=['POST'])
def order_now():
    if 'username' not in session:
        return jsonify({'error': 'You need to log in first'}), 401

    data = request.get_json()
    customer_id = session['customer_id']
    total_price = data.get('totalPrice')
    order_items = data.get('orderDetails')

    total_prep_time = calculate_total_prep_time(order_items)

    connection, cursor = get_db_connection()
    if connection is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor.execute("""
            INSERT INTO orders (customerid, totalprice, status, ordertype, estimated_time)
            VALUES (%s, %s, 'pending', 'now', %s)
        """, (customer_id, total_price, total_prep_time))
        order_id = cursor.lastrowid

        for item in order_items:
            product_id = item['product_id']
            quantity = item['quantity']
            customizations = item.get('customizations', '')

            if quantity > 0:
                cursor.execute("""
                    INSERT INTO orderitems (orderid, productid, quantity, specialrequests)
                    VALUES (%s, %s, %s, %s)
                """, (order_id, product_id, quantity, customizations))

                cursor.execute("UPDATE inventory SET quantityavailable = quantityavailable - %s WHERE productid = %s", (quantity, product_id))

        connection.commit()
        schedule_order_updates(order_id, 'now')

        # Store order_id in session
        session['order_id'] = order_id

        return jsonify({'success': True, 'order_id': order_id}), 201
    except mysql.connector.Error as err:
        connection.rollback()
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        connection.close()


@user_bp.route('/order-later', methods=['POST'])
def order_later():
    if 'username' not in session:
        return jsonify({'error': 'You need to log in first'}), 401

    data = request.get_json()
    customer_id = session['customer_id']
    total_price = data.get('totalPrice')
    order_items = data.get('orderDetails')
    scheduled_datetime = datetime.fromisoformat(data.get('scheduledDate'))
    scheduled_date, scheduled_time = scheduled_datetime.date(), scheduled_datetime.time()

    total_prep_time = calculate_total_prep_time(order_items)

    connection, cursor = get_db_connection()
    if connection is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor.execute("""
            INSERT INTO orders (customerid, totalprice, status, ordertype, scheduledate, scheduletime, estimated_time)
            VALUES (%s, %s, 'pending', 'later', %s, %s, %s)
        """, (customer_id, total_price, scheduled_date, scheduled_time, total_prep_time))
        order_id = cursor.lastrowid

        for item in order_items:
            product_id = item['product_id']
            quantity = item['quantity']
            customizations = item.get('customizations', '')

            if quantity > 0:
                cursor.execute("""
                    INSERT INTO orderitems (orderid, productid, quantity, specialrequests)
                    VALUES (%s, %s, %s, %s)
                """, (order_id, product_id, quantity, customizations))

                cursor.execute("UPDATE inventory SET quantityavailable = quantityavailable - %s WHERE productid = %s", (quantity, product_id))

        connection.commit()
        schedule_order_updates(order_id, 'later', scheduled_datetime)

        # Store order_id in session
        session['order_id'] = order_id

        return jsonify({'success': True, 'order_id': order_id}), 201
    except mysql.connector.Error as err:
        connection.rollback()
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@user_bp.route('/update_order_status', methods=['POST'])
def update_order_status():
    data = request.get_json()
    order_id = data['order_id']
    new_status = data['status']

    logging.debug(f"Received request to update order {order_id} to status {new_status}")

    connection, cursor = get_db_connection()
    if connection is None:
        logging.error("Database connection failed")
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor.execute("UPDATE orders SET status = %s WHERE orderid = %s", (new_status, order_id))
        connection.commit()
        logging.debug(f"Order {order_id} successfully updated to status {new_status}")
        return jsonify({'success': True}), 200
    except mysql.connector.Error as err:
        logging.error(f"Error updating order {order_id} to status {new_status}: {err}")
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@user_bp.route('/manage_orders_bookings', methods=['GET', 'POST'])
def manage_orders_bookings():
    if 'username' not in session:
        flash('You need to log in first', 'danger')
        return redirect(url_for('user.login'))

    if request.method == 'POST':
        action = request.form.get('action')
        order_id = request.form.get('order_id')
        booking_id = request.form.get('booking_id')

        connection, cursor = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        if action == 'reorder':
            try:
                cursor.execute("SELECT * FROM orderitems WHERE orderid = %s", (order_id,))
                order_items = cursor.fetchall()

                cursor.execute("""
                    INSERT INTO orders (customerid, totalprice, status, ordertype, orderdate)
                    SELECT customerid, totalprice, 'pending', ordertype, NOW() 
                    FROM orders WHERE orderid = %s
                """, (order_id,))
                new_order_id = cursor.lastrowid

                for item in order_items:
                    cursor.execute("""
                        INSERT INTO orderitems (orderid, productid, quantity, specialrequests)
                        VALUES (%s, %s, %s, %s)
                    """, (new_order_id, item['productid'], item['quantity'], item['specialrequests']))

                connection.commit()
                flash('Order re-ordered successfully!', 'success')
            except mysql.connector.Error as err:
                flash(f"Error: {err}", 'danger')
                connection.rollback()

        elif action == 'modify':
            new_checkin = request.form.get('new_checkin')
            new_checkout = request.form.get('new_checkout')
            new_accommodation_id = request.form.get('new_accommodation_id')
            user_id = session.get('customer_id')
            num_beds = 1  

            try:
                new_checkin_dt = datetime.strptime(new_checkin, '%Y-%m-%d')
                new_checkout_dt = datetime.strptime(new_checkout, '%Y-%m-%d')

                # Fetch accommodation details
                cursor.execute("""
                    SELECT accommodationid, maxcapacity, room_type, price
                    FROM accommodations
                    JOIN products ON accommodations.productid = products.productid
                    WHERE accommodations.productid = %s
                    LIMIT 1;
                """, (new_accommodation_id,))
                accommodation = cursor.fetchone()

                if not accommodation:
                    flash('No accommodation found for this product', 'danger')
                    return redirect(url_for('user.manage_orders_bookings'))

                accommodation_id, max_capacity, room_type, price_per_night = accommodation

                # Check if the dates are blocked
                cursor.execute("""
                    SELECT date
                    FROM blocked_dates
                    WHERE accommodationid = %s
                      AND date BETWEEN %s AND %s;
                """, (accommodation_id, new_checkin_dt, new_checkout_dt))
                blocked_dates = cursor.fetchall()

                if blocked_dates:
                    flash('Selected dates include blocked dates and cannot be booked', 'danger')
                    return redirect(url_for('user.manage_orders_bookings'))

                # Check bed availability
                cursor.execute("""
                    SELECT SUM(num_beds)
                    FROM bookings
                    WHERE accommodationid = %s
                      AND status = 'booked'
                      AND ((checkindate BETWEEN %s AND %s) OR (checkoutdate BETWEEN %s AND %s) OR (checkindate <= %s AND checkoutdate >= %s));
                """, (accommodation_id, new_checkin_dt, new_checkout_dt, new_checkin_dt, new_checkout_dt, new_checkin_dt, new_checkout_dt))
                booked_beds = cursor.fetchone()[0] or 0

                if booked_beds + num_beds > max_capacity:
                    flash('Not enough beds available', 'danger')
                    return redirect(url_for('user.manage_orders_bookings'))

                total_nights = (new_checkout_dt - new_checkin_dt).days
                if room_type == 'dorm':
                    total_cost = total_nights * price_per_night * num_beds
                elif room_type == 'queen':
                    total_cost = total_nights * 100
                elif room_type == 'twin':
                    total_cost = total_nights * 80
                else:
                    total_cost = total_nights * price_per_night

                cursor.execute("""
                    UPDATE bookings 
                    SET accommodationid = %s, checkindate = %s, checkoutdate = %s, num_beds = %s, total_cost = %s
                    WHERE bookingid = %s AND customerid = %s;
                """, (accommodation_id, new_checkin_dt, new_checkout_dt, num_beds, total_cost, booking_id, user_id))

                connection.commit()
                flash('Booking modified successfully!', 'success')
            except mysql.connector.Error as err:
                flash(f"Error: {err}", 'danger')
                connection.rollback()

        elif action == 'cancel':
            try:
                cursor.execute("""
                    UPDATE bookings 
                    SET status = 'cancelled' 
                    WHERE bookingid = %s AND customerid = %s
                """, (booking_id, session['customer_id']))
                connection.commit()
                flash('Booking cancelled successfully!', 'success')
            except mysql.connector.Error as err:
                flash(f"Error: {err}", 'danger')
                connection.rollback()

        cursor.close()
        connection.close()
        return redirect(url_for('user.manage_orders_bookings'))

    customer_id = session.get('customer_id')
    connection, cursor = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM orders 
        WHERE customerid = %s 
        ORDER BY orderdate DESC
    """, (customer_id,))
    orders = cursor.fetchall()

    cursor.execute("""
        SELECT b.bookingid, b.checkindate, b.checkoutdate, p.name as product_name, b.status, b.accommodationid
        FROM bookings b
        JOIN accommodations a ON b.accommodationid = a.accommodationid
        JOIN products p ON a.productid = p.productid
        WHERE b.customerid = %s
        ORDER BY b.checkindate DESC
    """, (customer_id,))
    bookings = cursor.fetchall()

    cursor.execute("""
        SELECT a.accommodationid, p.name 
        FROM accommodations a
        JOIN products p ON a.productid = p.productid
    """)
    accommodations = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('users/manage_orders_bookings.html', orders=orders, bookings=bookings, accommodations=accommodations)

@user_bp.route('/reorder', methods=['POST'])
def reorder():
    order_id = request.form.get('order_id')

    try:
        connection, cursor = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT productid, quantity, specialrequests 
            FROM orderitems 
            WHERE orderid = %s
        """, (order_id,))
        order_items = cursor.fetchall()

        cursor.execute("""
            INSERT INTO orders (customerid, totalprice, status, ordertype, orderdate)
            SELECT customerid, totalprice, 'pending', 'now', NOW()
            FROM orders 
            WHERE orderid = %s
        """, (order_id,))
        connection.commit()
        
        cursor.execute("SELECT LAST_INSERT_ID()")
        new_order_id = cursor.fetchone()['LAST_INSERT_ID()']

        for item in order_items:
            cursor.execute("""
                INSERT INTO orderitems (orderid, productid, quantity, specialrequests) 
                VALUES (%s, %s, %s, %s)
            """, (new_order_id, item['productid'], item['quantity'], item['specialrequests']))

        connection.commit()
        flash(f'New order placed successfully! Order ID: {new_order_id}', 'success')

    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('user.manage_orders_bookings'))

@user_bp.route('/modify_booking', methods=['POST'])
def modify_booking():
    data = request.form
    booking_id = data.get('booking_id')
    new_accommodation_id = data.get('new_accommodation_id')
    new_checkin = data.get('new_checkin')
    new_checkout = data.get('new_checkout')
    user_id = session.get('customer_id') or session.get('staff_id') or session.get('manager_id')
    num_beds = 1 

    logging.debug(f"Received data: booking_id={booking_id}, new_accommodation_id={new_accommodation_id}, new_checkin={new_checkin}, new_checkout={new_checkout}")

    if not (new_checkin and new_checkout):
        flash('Missing required fields', 'danger')
        return redirect(url_for('user.manage_orders_bookings'))

    try:
        new_checkin = datetime.strptime(new_checkin, '%Y-%m-%d')
        new_checkout = datetime.strptime(new_checkout, '%Y-%m-%d')
    except ValueError:
        flash('Invalid date format', 'danger')
        return redirect(url_for('user.manage_orders_bookings'))

    connection, cursor = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    logging.debug(f"Querying accommodation details for accommodation ID: {new_accommodation_id}")

    cursor.execute("""
        SELECT a.accommodationid, a.maxcapacity, a.room_type, p.price
        FROM accommodations a
        JOIN products p ON a.productid = p.productid
        WHERE a.accommodationid = %s
        LIMIT 1;
    """, (new_accommodation_id,))
    accommodation = cursor.fetchone()

    logging.debug(f"Accommodation query result: {accommodation}")

    if not accommodation:
        connection.close()
        flash('No accommodation found for this accommodation ID', 'danger')
        return redirect(url_for('user.manage_orders_bookings'))

    accommodation_id = accommodation['accommodationid']
    max_capacity = accommodation['maxcapacity']
    room_type = accommodation['room_type']
    price_per_night = accommodation['price']

    cursor.execute("""
        SELECT date
        FROM blocked_dates
        WHERE accommodationid = %s
          AND date BETWEEN %s AND %s;
    """, (accommodation_id, new_checkin, new_checkout))
    blocked_dates = cursor.fetchall()

    logging.debug(f"Blocked dates query result: {blocked_dates}")

    if blocked_dates:
        connection.close()
        flash('Selected dates include blocked dates and cannot be booked', 'danger')
        return redirect(url_for('user.manage_orders_bookings'))

    cursor.execute("""
        SELECT SUM(num_beds) as total_beds
        FROM bookings
        WHERE accommodationid = %s
          AND status = 'booked'
          AND ((checkindate BETWEEN %s AND %s) OR (checkoutdate BETWEEN %s AND %s) OR (checkindate <= %s AND checkoutdate >= %s));
    """, (accommodation_id, new_checkin, new_checkout, new_checkin, new_checkout, new_checkin, new_checkout))
    booked_beds = cursor.fetchone()
    total_beds_booked = booked_beds['total_beds'] or 0

    logging.debug(f"Booked beds query result: {total_beds_booked}")

    if total_beds_booked + num_beds > max_capacity:
        connection.close()
        flash('Not enough beds available', 'danger')
        return redirect(url_for('user.manage_orders_bookings'))

    total_nights = (new_checkout - new_checkin).days
    if room_type == 'dorm':
        total_cost = total_nights * price_per_night * num_beds
    elif room_type == 'queen':
        total_cost = total_nights * 100
    elif room_type == 'twin':
        total_cost = total_nights * 80
    else:
        total_cost = total_nights * price_per_night

    cursor.execute("""
        UPDATE bookings 
        SET accommodationid = %s, checkindate = %s, checkoutdate = %s, num_beds = %s, total_cost = %s
        WHERE bookingid = %s AND customerid = %s;
    """, (accommodation_id, new_checkin, new_checkout, num_beds, total_cost, booking_id, user_id))

    connection.commit()
    logging.debug(f"Booking {booking_id} modified successfully")
    connection.close()

    flash('Booking modified successfully!', 'success')
    return redirect(url_for('user.manage_orders_bookings'))



@user_bp.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    booking_id = request.form.get('booking_id')

    connection, cursor = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            UPDATE bookings
            SET status = 'cancelled'
            WHERE bookingid = %s AND customerid = %s
        """, (booking_id, session['customer_id']))
        connection.commit()
        flash('Booking cancelled successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f"Error: {err}", 'danger')
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('user.manage_orders_bookings'))

@user_bp.route('/payment')
def payment():
    return render_template('users/user_payment.html')


@user_bp.route('/process_payment', methods=['POST'])
def process_payment():
    # Handle booking payment
    booking_details = session.get('booking_details')
    if booking_details:
        customer_id = booking_details['customer_id']
        accommodation_id = booking_details['accommodation_id']
        check_in = datetime.strptime(booking_details['check_in'], '%Y-%m-%d')
        check_out = datetime.strptime(booking_details['check_out'], '%Y-%m-%d')
        num_beds = booking_details['num_beds']
        booking_reference = booking_details['booking_reference']
        total_cost = booking_details['total_cost']

        connection, cursor = get_db_connection()
        cursor.execute("""
            INSERT INTO bookings (customerid, accommodationid, checkindate, checkoutdate, status, num_beds, booking_reference, total_cost)
            VALUES (%s, %s, %s, %s, 'booked', %s, %s, %s);
        """, (customer_id, accommodation_id, check_in, check_out, num_beds, booking_reference, total_cost))

        connection.commit()
        connection.close()

        flash('Payment successful!', 'success')
        session.pop('booking_details', None)  # Clear booking details from session

        return redirect(url_for('user.booking_summary', **booking_details))

    # Handle food order payment
    order_id = session.get('order_id')
    if order_id:
        connection, cursor = get_db_connection()
        if connection is None:
            flash('Database connection failed.', 'danger')
            return redirect(url_for('user.order'))

        try:
            cursor.execute("UPDATE orders SET status = 'pending' WHERE orderid = %s", (order_id,))
            connection.commit()
        except mysql.connector.Error as err:
            flash(f'Error updating order status: {err}', 'danger')
            connection.rollback()
        finally:
            cursor.close()
            connection.close()

        flash('Payment successful!', 'success')
        return redirect(url_for('user.order_confirmation'))

    flash('No booking or order found to process payment.', 'danger')
    return redirect(url_for('user.payment'))

@user_bp.route('/booking_summary')
def booking_summary():
    booking_details = {
        'check_in': request.args.get('check_in'),
        'check_out': request.args.get('check_out'),
        'room': request.args.get('room'),
        'booking_reference': request.args.get('booking_reference'),
        'total_cost': request.args.get('total_cost')
    }
    return render_template('accommodation/booking_summary.html', booking_details=booking_details)


@user_bp.route('/apply_promo', methods=['POST'])
def apply_promo():
    data = request.get_json()
    promo_code = data.get('code')
    sub_total = float(data.get('sub_total', 0.0))

    logging.debug(f"Received promo code: {promo_code} with sub total: {sub_total}")

    connection, cursor = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT discountpercent, validfrom, validto
            FROM promotions
            WHERE code = %s AND %s BETWEEN validfrom AND validto
        """, (promo_code, datetime.now()))
        promo = cursor.fetchone()

        logging.debug(f"Promo fetched from DB: {promo}")

        if promo:
            discount_percent = float(promo['discountpercent']) 
            new_sub_total = sub_total * (1 - discount_percent / 100)
            return jsonify({'success': True, 'new_sub_total': new_sub_total})
        else:
            return jsonify({'success': False}), 400

    except Exception as e:
        logging.error(f"Error applying promo code: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

    finally:
        cursor.close()
        connection.close()

@user_bp.route('/messages', methods=['GET', 'POST'])
def messages():
    if 'username' not in session:
        flash('Please log in to view and send messages.', 'danger')
        return redirect(url_for('user.login'))

    user_id = session.get('customer_id')
    user_type = 'customer'  # Assuming customers are using this route

    connection, cursor = get_db_connection()
    if connection is None:
        flash('Database connection could not be established.', 'danger')
        return render_template('error_page.html')

    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        data = request.get_json()
        content = data.get('content')
        receivertype = data.get('receivertype')

        logging.debug(f"Received message data: {data}")

        if not content:
            return jsonify({'success': False, 'error': 'Message content cannot be empty.'}), 400

        try:
            if receivertype == 'staff':
                cursor.execute("SELECT staffid as id FROM staff")
            elif receivertype == 'manager':
                cursor.execute("SELECT managerid as id FROM managers")
            else:
                return jsonify({'success': False, 'error': 'Invalid recipient type.'}), 400

            recipients = cursor.fetchall()

            for recipient in recipients:
                cursor.execute("""
                    INSERT INTO messages (senderid, receiverid, sendertype, receivertype, content)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, recipient['id'], user_type, receivertype, content))

            connection.commit()
            logging.debug("Messages inserted successfully")
            return jsonify({'success': True}), 201
        except Exception as e:
            connection.rollback()
            logging.error(f"Error inserting messages: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            cursor.close()

    try:
        # Fetch staff and manager recipients for the dropdowns
        cursor.execute("SELECT staffid as id, username FROM staff")
        staff_recipients = cursor.fetchall()

        cursor.execute("SELECT managerid as id, username FROM managers")
        manager_recipients = cursor.fetchall()

        cursor.execute("""
            SELECT 
                m.messageid, m.content, m.timestamp,
                (CASE WHEN m.sendertype = 'customer' THEN (SELECT username FROM customers WHERE customerid = m.senderid)
                      WHEN m.sendertype = 'staff' THEN (SELECT username FROM staff WHERE staffid = m.senderid)
                      WHEN m.sendertype = 'manager' THEN (SELECT username FROM managers WHERE managerid = m.senderid) END) AS sender_name,
                (CASE WHEN m.receivertype = 'customer' THEN (SELECT username FROM customers WHERE customerid = m.receiverid)
                      WHEN m.receivertype = 'staff' THEN (SELECT username FROM staff WHERE staffid = m.receiverid)
                      WHEN m.receivertype = 'manager' THEN (SELECT username FROM managers WHERE managerid = m.receiverid) END) AS receiver_name
            FROM 
                messages m
            WHERE 
                (m.senderid = %s AND m.sendertype = 'customer') OR 
                (m.receiverid = %s AND m.receivertype = 'customer')
            ORDER BY 
                m.timestamp DESC
        """, (user_id, user_id))
        messages = cursor.fetchall()
        logging.debug(f"Fetched messages: {messages}")
    except Exception as e:
        flash(f"Failed to load messages: {e}", 'danger')
        logging.error(f"Error fetching messages: {e}")
        messages = []
    finally:
        cursor.close()
        connection.close()

    return render_template('users/messages.html', messages=messages, staff_recipients=staff_recipients, manager_recipients=manager_recipients)

@user_bp.route('/reply_message', methods=['POST'])
def reply_message():
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Please log in to reply to messages.'}), 403

    data = request.get_json()
    sender_id = session.get('customer_id')
    sender_type = 'customer'  # Assuming customers are using this route
    receiver_id = data.get('receiver_id')
    receiver_type = data.get('receiver_type')
    content = data.get('content')

    if not content:
        return jsonify({'success': False, 'error': 'Reply content cannot be empty.'}), 400

    if not receiver_id or not receiver_type:
        return jsonify({'success': False, 'error': 'Invalid receiver data.'}), 400

    connection, cursor = get_db_connection()
    if connection is None:
        return jsonify({'success': False, 'error': 'Database connection could not be established.'}), 500

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO messages (senderid, receiverid, sendertype, receivertype, content)
            VALUES (%s, %s, %s, %s, %s)
        """, (sender_id, receiver_id, sender_type, receiver_type, content))

        connection.commit()
        return jsonify({'success': True}), 201
    except Exception as e:
        connection.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()







@user_bp.route('/news')
def news():
    connection, cursor = get_db_connection()
    if connection is None:
        flash('Database connection failed.', 'danger')
        return render_template('users/news.html', news=[])

    try:
        # Fetch all news items
        cursor.execute("SELECT newsid, title, content, publishedat FROM news ORDER BY publishedat DESC")
        news_items = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f'Error fetching news: {err}', 'danger')
        news_items = []
    finally:
        cursor.close()
        connection.close()

    return render_template('users/news.html', news=news_items)



@user_bp.route('/merchandise_order', methods=['GET', 'POST'])
def merchandise_order():
    if request.method == 'POST':
        if 'username' not in session:
            flash('You need to log in first', 'danger')
            return redirect(url_for('user.login'))

        username = session['username']
        customer_id = session.get('customer_id')
        connection = None
        cursor = None

        if request.content_type != 'application/json':
            return jsonify(success=False, message='Unsupported Media Type: Content-Type must be application/json'), 415

        try:
            data = request.get_json()  # Correct way to get JSON data
            order_details = data.get('orderDetails')
            total_price = data.get('totalPrice')
            promo_code = data.get('promoCode')

            connection, cursor = get_db_connection()
            if connection is None:
                flash('Could not connect to the database', 'danger')
                return redirect(url_for('user.dashboard'))

            cursor.execute("SELECT customerid FROM customers WHERE username = %s", (username,))
            customer = cursor.fetchone()
            if not customer:
                flash('User not found', 'danger')
                return redirect(url_for('user.login'))

            # Insert into orders table with status set to 'pending'
            cursor.execute("""
                INSERT INTO orders (customerid, totalprice, status, ordertype, orderdate) 
                VALUES (%s, %s, %s, %s, %s)
            """, (customer_id, total_price, 'pending', 'now', datetime.now()))
            order_id = cursor.lastrowid

            # Insert into orderitems table
            for item in order_details:
                cursor.execute("""
                    INSERT INTO orderitems (orderid, productid, quantity)
                    VALUES (%s, %s, %s)
                """, (order_id, item['product_id'], item['quantity']))

            connection.commit()

            # Store the order_id in session
            session['order_id'] = order_id

            return jsonify(success=True, redirect_url=url_for('user.merchandise_payment')), 200
        except Exception as err:
            logging.error(f"Error: {err}")
            if connection:
                connection.rollback()
            return jsonify(success=False, message=f'Error: {err}'), 500
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    connection = None
    cursor = None
    connection, cursor = get_db_connection()
    if connection is None:
        flash('Database connection failed.', 'danger')
        return render_template('users/user_merchandise_order.html')

    try:
        cursor.execute("""
            SELECT productid, name, description, price, category, image
            FROM products
            WHERE category = 'merchandise'
        """)
        products = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        products = []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template('users/user_merchandise_order.html', products=products)

@user_bp.route('/merchandise_payment', methods=['GET'])
def merchandise_payment():
    if 'order_id' not in session:
        flash('Order details are missing.', 'danger')
        return redirect(url_for('user.merchandise_order'))

    return render_template('users/merchandise_payment.html')

@user_bp.route('/process_merchandise_payment', methods=['POST'])
def process_merchandise_payment():
    if 'customer_id' not in session:
        flash('You need to log in first', 'danger')
        return redirect(url_for('user.login'))

    card_number = request.form.get('cardNumber')
    name_on_card = request.form.get('nameOnCard')
    expiry_date = request.form.get('expiryDate')
    cvv = request.form.get('cvv')

    customer_id = session['customer_id']
    order_id = session.get('order_id')
    if not order_id:
        flash('Order details are missing.', 'danger')
        return redirect(url_for('user.merchandise_order'))

    connection, cursor = get_db_connection()
    if connection is None:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('user.merchandise_order'))

    try:
        # Do not update the order status here
        flash('Payment successful!', 'success')
    except mysql.connector.Error as err:
        connection.rollback()
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('user.dashboard'))



@user_bp.route('/order_confirmation')
def order_confirmation():
    order_id = session.get('order_id')
    if not order_id:
        flash('No order found to display confirmation.', 'danger')
        return redirect(url_for('user.order'))

    connection, cursor = get_db_connection()
    if connection is None:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('user.order'))

    try:
        cursor.execute("""
            SELECT o.orderid, o.totalprice, o.status, o.orderdate, oi.productid, p.name, oi.quantity, oi.specialrequests
            FROM orders o
            JOIN orderitems oi ON o.orderid = oi.orderid
            JOIN products p ON oi.productid = p.productid
            WHERE o.orderid = %s
        """, (order_id,))
        order_details = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f'Error fetching order details: {err}', 'danger')
        return redirect(url_for('user.order'))
    finally:
        cursor.close()
        connection.close()

    return render_template('users/order_confirmation.html', order_details=order_details)
