from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for, flash, send_file
import pandas as pd
import mysql.connector
from db import get_db_connection
from flask_hashing import Hashing
import io
from fpdf import FPDF
import datetime
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/images/products'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


staff_bp = Blueprint("staff", __name__, template_folder="templates")
hashing = Hashing()


def check_staff_role():
    if 'usertype' not in session or session['usertype'] != 'staff':
        return False
    return True

def calculate_total_prep_time(order_items):
    connection, cursor = get_db_connection()
    total_prep_time = 0
    for item in order_items:
        cursor.execute("SELECT default_prep_time FROM products WHERE productid = %s", (item['productid'],))
        prep_time = cursor.fetchone()[0]
        total_prep_time += prep_time * item['quantity']
    connection.close()
    return total_prep_time

@staff_bp.route('/dashboard')
def dashboard():
    if not check_staff_role():
        return redirect(url_for('home_bp.home'))

    connection, cursor = get_db_connection()

    # Fetch low stock alerts
    low_stock_alerts_query = """
        SELECT p.productid, p.name, i.quantityavailable, i.lowstockthreshold
        FROM products p
        JOIN inventory i ON p.productid = i.productid
        WHERE i.quantityavailable <= i.lowstockthreshold
    """
    cursor.execute(low_stock_alerts_query)
    low_stock_alerts = cursor.fetchall()

    # Fetch current orders (Order Now) excluding merchandise orders
    current_orders_now_query = """
        SELECT o.orderid, c.username, o.totalprice, o.status, o.orderdate, o.estimated_time, p.name
        FROM orders o
        JOIN customers c ON o.customerid = c.customerid
        JOIN orderitems oi ON o.orderid = oi.orderid
        JOIN products p ON oi.productid = p.productid
        WHERE o.ordertype = 'now' 
          AND o.status IN ('pending', 'confirmed', 'preparing', 'ready')
          AND p.category != 'merchandise'
        ORDER BY o.orderid DESC
    """
    cursor.execute(current_orders_now_query)
    current_orders_now = cursor.fetchall()

    # Fetch current orders (Order Later) excluding merchandise orders
    current_orders_later_query = """
        SELECT o.orderid, c.username, o.totalprice, o.status, o.orderdate, o.estimated_time, o.scheduledate, o.scheduletime, p.name
        FROM orders o
        JOIN customers c ON o.customerid = c.customerid
        JOIN orderitems oi ON o.orderid = oi.orderid
        JOIN products p ON oi.productid = p.productid
        WHERE o.ordertype = 'later' 
          AND o.status IN ('pending', 'confirmed', 'preparing', 'ready')
          AND p.category != 'merchandise'
        ORDER BY o.orderid DESC
    """
    cursor.execute(current_orders_later_query)
    current_orders_later = cursor.fetchall()

    # Fetch merchandise orders
    merchandise_orders_query = """
        SELECT o.orderid, c.username, o.totalprice, o.status, o.orderdate, p.name
        FROM orders o
        JOIN customers c ON o.customerid = c.customerid
        JOIN orderitems oi ON o.orderid = oi.orderid
        JOIN products p ON oi.productid = p.productid
        WHERE p.category = 'merchandise' 
          AND o.status IN ('pending', 'confirmed')
        ORDER BY o.orderid DESC
    """
    cursor.execute(merchandise_orders_query)
    merchandise_orders = cursor.fetchall()

    # Fetch past orders
    past_orders_query = """
        SELECT o.orderid, c.username, o.totalprice, o.status, o.orderdate, o.estimated_time, o.scheduledate, o.scheduletime, p.name
        FROM orders o
        JOIN customers c ON o.customerid = c.customerid
        JOIN orderitems oi ON o.orderid = oi.orderid
        JOIN products p ON oi.productid = p.productid
        WHERE o.status IN ('completed', 'cancelled')
        ORDER BY o.orderid DESC
    """
    cursor.execute(past_orders_query)
    past_orders = cursor.fetchall()

    # Fetch current bookings
    current_bookings_query = """
        SELECT b.bookingid, c.username, b.accommodationid, b.checkindate, b.checkoutdate, b.status, b.booking_reference, a.room_type
        FROM bookings b
        JOIN customers c ON b.customerid = c.customerid
        JOIN accommodations a ON b.accommodationid = a.accommodationid
        WHERE b.status = 'booked'
    """
    cursor.execute(current_bookings_query)
    current_bookings = cursor.fetchall()

    connection.close()

    return render_template('staff/staff_dashboard.html',
                           low_stock_alerts=low_stock_alerts,
                           current_orders_now=current_orders_now,
                           current_orders_later=current_orders_later,
                           merchandise_orders=merchandise_orders,
                           past_orders=past_orders,
                           current_bookings=current_bookings)


@staff_bp.route('/latest_order_statuses', methods=['GET'])
def latest_order_statuses():
    connection, cursor = get_db_connection()
    try:
        cursor.execute("""
            SELECT orderid, status
            FROM orders
            WHERE status IN ('pending', 'confirmed', 'preparing', 'ready')
        """)
        orders = cursor.fetchall()
        return jsonify(orders)
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        connection.close()

@staff_bp.route('/order_now', methods=['POST'])
def order_now():
    data = request.get_json()
    customer_id = data['customer_id']
    order_items = data['order_items']  # List of items with productid and quantity

    total_prep_time = calculate_total_prep_time(order_items)

    try:
        connection, cursor = get_db_connection()
        cursor.execute("""
            INSERT INTO orders (customerid, orderdate, totalprice, status, ordertype, estimated_time)
            VALUES (%s, NOW(), %s, 'pending', 'now', %s)
        """, (customer_id, data['total_price'], total_prep_time))
        order_id = cursor.lastrowid

        for item in order_items:
            cursor.execute("""
                INSERT INTO orderitems (orderid, productid, quantity)
                VALUES (%s, %s, %s)
            """, (order_id, item['productid'], item['quantity']))

        connection.commit()
        cursor.close()
        connection.close()
        return jsonify({'success': True, 'order_id': order_id})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@staff_bp.route('/order_later', methods=['POST'])
def order_later():
    data = request.get_json()
    customer_id = data['customer_id']
    order_items = data['order_items']  # List of items with productid and quantity
    scheduled_date = data['scheduled_date']
    scheduled_time = data['scheduled_time']

    total_prep_time = calculate_total_prep_time(order_items)

    try:
        connection, cursor = get_db_connection()
        cursor.execute("""
            INSERT INTO orders (customerid, orderdate, totalprice, status, ordertype, scheduledate, scheduletime, estimated_time)
            VALUES (%s, NOW(), %s, 'pending', 'later', %s, %s, %s)
        """, (customer_id, data['total_price'], scheduled_date, scheduled_time, total_prep_time))
        order_id = cursor.lastrowid

        for item in order_items:
            cursor.execute("""
                INSERT INTO orderitems (orderid, productid, quantity)
                VALUES (%s, %s, %s)
            """, (order_id, item['productid'], item['quantity']))

        connection.commit()
        cursor.close()
        connection.close()
        return jsonify({'success': True, 'order_id': order_id})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@staff_bp.route('/confirm_order', methods=['POST'])
def confirm_order():
    if not check_staff_role():
        return jsonify({'error': 'Unauthorized access'}), 403

    data = request.get_json()
    order_id = data.get('order_id')

    if not order_id:
        return jsonify({'error': 'Invalid data'}), 400

    try:
        connection, cursor = get_db_connection()
        update_query = "UPDATE orders SET status = 'confirmed' WHERE orderid = %s"
        cursor.execute(update_query, (order_id,))
        connection.commit()
        cursor.close()
        connection.close()
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@staff_bp.route('/update_order_status', methods=['POST'])
def update_order_status():
    if not check_staff_role():
        return jsonify({'error': 'Unauthorized access'}), 403

    data = request.get_json()
    order_id = data.get('order_id')
    new_status = data.get('status')

    if not order_id or not new_status:
        return jsonify({'error': 'Invalid data'}), 400

    try:
        connection, cursor = get_db_connection()
        update_query = "UPDATE orders SET status = %s WHERE orderid = %s"
        cursor.execute(update_query, (new_status, order_id))
        connection.commit()
        cursor.close()
        connection.close()
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@staff_bp.route('/update_booking_status', methods=['POST'])
def update_booking_status():
    if not check_staff_role():
        return jsonify({'error': 'Unauthorized access'}), 403

    data = request.get_json()
    booking_id = data.get('booking_id')
    new_status = data.get('status')

    if not booking_id or not new_status:
        return jsonify({'error': 'Invalid data'}), 400

    try:
        connection, cursor = get_db_connection()
        update_query = "UPDATE bookings SET status = %s WHERE bookingid = %s"
        cursor.execute(update_query, (new_status, booking_id))
        connection.commit()
        cursor.close()
        connection.close()
        return jsonify({'success': True})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@staff_bp.route('/profile', methods=['GET'])
def profile():
    staff_id = session.get('staff_id')
    if not staff_id:
        flash('Invalid session or not logged in.', 'danger')
        return redirect(url_for('home_bp.home'))

    connection, cursor = get_db_connection()

    cursor.execute("SELECT email FROM staff WHERE staffid = %s", (staff_id,))
    staff_info = cursor.fetchone()
    cursor.close()
    connection.close()

    return render_template('staff/profile.html', staff=staff_info)


@staff_bp.route('/update_info', methods=['GET', 'POST'])
def update_info():
    staff_id = session.get('staff_id')

    if request.method == 'POST':
        email = request.form.get('email')

        connection, cursor = get_db_connection()
        if connection is None:
            flash('Database connection failed.', 'danger')
            return redirect(url_for('staff.profile', tab='info'))

        try:
            cursor.execute("""
                UPDATE staff 
                SET email = %s 
                WHERE staffid = %s
            """, (email, staff_id))
            connection.commit()

            flash('Information updated successfully!', 'success')
            return redirect(url_for('staff.profile', tab='info'))
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
            connection.rollback()
        finally:
            cursor.close()
            connection.close()

    connection, cursor = get_db_connection()
    if connection is None:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('staff.profile', tab='info'))

    cursor.execute("SELECT email FROM staff WHERE staffid = %s", (staff_id,))
    staff_info = cursor.fetchone()
    cursor.close()
    connection.close()

    return render_template('staff/profile.html', staff=staff_info, active_tab='info')


@staff_bp.route('/update_password', methods=['GET', 'POST'])
def update_password():
    staff_id = session.get('staff_id')

    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        connection, cursor = get_db_connection()

        if new_password != confirm_password:
            flash('Passwords do not match.', 'password_error')
            return redirect(url_for('staff.profile', tab='password'))

        if connection is None:
            flash('Database connection failed.', 'danger')
            return redirect(url_for('staff.profile', tab='password'))

        try:
            cursor.execute("SELECT passwordhash FROM usercredentials WHERE staffid = %s AND usertype = 'staff'", (staff_id,))
            user = cursor.fetchone()

            if user and hashing.check_value(user[0], current_password, salt='abc123'):
                hashed_password = hashing.hash_value(new_password, salt='abc123')
                cursor.execute("UPDATE usercredentials SET passwordhash = %s WHERE staffid = %s AND usertype = 'staff'", (hashed_password, staff_id))
                cursor.execute("UPDATE staff SET passwordhash = %s WHERE staffid = %s", (hashed_password, staff_id))
                connection.commit()
                flash('Password updated successfully!', 'password_success')
                return redirect(url_for('staff.profile', tab='password'))
            else:
                flash('Invalid current password', 'password_error')
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
            connection.rollback()
        finally:
            cursor.close()
            connection.close()

    return redirect(url_for('staff.profile', tab='password'))


@staff_bp.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if not check_staff_role():
        return redirect(url_for('home_bp.home'))

    connection, cursor = get_db_connection()
    query = """
        SELECT p.productid, p.name, p.category, i.quantityavailable, i.lowstockthreshold
        FROM products p
        JOIN inventory i ON p.productid = i.productid
    """
    cursor.execute(query)
    products = cursor.fetchall()
    connection.close()
    return render_template('staff/inventory.html', products=products)


@staff_bp.route('/update_inventory/<int:product_id>', methods=['POST'])
def update_inventory(product_id):
    if not check_staff_role():
        return jsonify({'error': 'Unauthorized access'}), 403

    new_quantity = request.json.get('quantity')
    if new_quantity is None:
        return jsonify({'error': 'No quantity provided'}), 400

    try:
        connection, cursor = get_db_connection()
        update_query = """
            UPDATE inventory
            SET quantityavailable = %s
            WHERE productid = %s
        """
        cursor.execute(update_query, (new_quantity, product_id))
        connection.commit()

        fetch_query = """
            SELECT quantityavailable, lowstockthreshold, alert_sent
            FROM inventory
            WHERE productid = %s
        """
        cursor.execute(fetch_query, (product_id,))
        updated_quantity, low_threshold, alert_sent = cursor.fetchone()

        if updated_quantity <= low_threshold and not alert_sent:
            cursor.execute("UPDATE inventory SET alert_sent = TRUE WHERE productid = %s", (product_id,))
            connection.commit()
        elif updated_quantity > low_threshold and alert_sent:
            cursor.execute("UPDATE inventory SET alert_sent = FALSE WHERE productid = %s", (product_id,))
            connection.commit()

        cursor.close()
        connection.close()

        return jsonify({'success': True, 'product_id': product_id, 'new_quantity': updated_quantity})
    except mysql.connector.Error as err:
        print(f"Error updating inventory: {err}")
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({'error': str(e)}), 500


@staff_bp.route('/inventory/report', methods=['GET', 'POST'])
def inventory_report():
    if not check_staff_role():
        return redirect(url_for('home_bp.home'))

    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        try:
            connection, cursor = get_db_connection()
            print(f"Start Date: {start_date}, End Date: {end_date}")  # Debugging line
            query = """
                SELECT p.productid, p.name, p.category, i.quantityavailable, o.orderdate, oi.quantity
                FROM products p
                JOIN inventory i ON p.productid = i.productid
                LEFT JOIN orderitems oi ON p.productid = oi.productid
                LEFT JOIN orders o ON oi.orderid = o.orderid
                WHERE (o.orderdate BETWEEN %s AND %s) OR o.orderdate IS NULL
            """
            cursor.execute(query, (start_date, end_date))
            report_data = cursor.fetchall()
            connection.close()

            print(f"Report Data: {report_data}")  # Debugging line

            df = pd.DataFrame(report_data, columns=["Product ID", "Name", "Category", "Current Stock", "Order Date", "Quantity Sold"])

            return render_template('staff/inventory_report.html', tables=[df.to_html(classes='data')], titles=df.columns.values)
        except mysql.connector.Error as err:
            print(f"Error fetching report data: {err}")
            flash(f"Error fetching report data: {err}", 'danger')
            return redirect(url_for('staff.inventory'))
        except Exception as e:
            print(f"Unexpected error: {e}")
            flash(f"Unexpected error: {e}", 'danger')
            return redirect(url_for('staff.inventory'))

    return render_template('staff/inventory_report_form.html')


@staff_bp.route('/inventory/download_report', methods=['POST'])
def download_inventory_report():
    if not check_staff_role():
        return redirect(url_for('home_bp.home'))

    start_date = request.form['start_date']
    end_date = request.form['end_date']

    try:
        connection, cursor = get_db_connection()
        query = """
            SELECT p.productid, p.name, p.category, i.quantityavailable, COALESCE(SUM(oi.quantity), 0) as quantity_sold
            FROM products p
            JOIN inventory i ON p.productid = i.productid
            LEFT JOIN orderitems oi ON p.productid = oi.productid
            LEFT JOIN orders o ON oi.orderid = o.orderid AND (o.orderdate BETWEEN %s AND %s)
            GROUP BY p.productid, p.name, p.category, i.quantityavailable
        """
        cursor.execute(query, (start_date, end_date))
        report_data = cursor.fetchall()
        connection.close()

        df = pd.DataFrame(report_data, columns=["Product ID", "Name", "Category", "Current Stock", "Quantity Sold"])

        # Generate PDF
        pdf = FPDF()
        pdf.add_page()

        # Set font to Arial bold for the title
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Inventory Report", ln=True, align='C')

        # Set font back to Arial normal for the rest of the content
        pdf.set_font("Arial", size=10)

        column_widths = [20, 50, 40, 30, 30]  # Adjust column widths as needed
        headers = ["Product ID", "Name", "Category", "Current Stock", "Quantity Sold"]

        # Add table headers
        for header, width in zip(headers, column_widths):
            pdf.cell(width, 10, header, border=1, align='C')
        pdf.ln()

        # Add table rows
        for index, row in df.iterrows():
            for item, width in zip(row, column_widths):
                pdf.cell(width, 10, str(item), border=1, align='C')
            pdf.ln()

        pdf_output = pdf.output(dest='S').encode('latin1')
        return send_file(
            io.BytesIO(pdf_output),
            as_attachment=True,
            download_name="inventory_report.pdf"
        )
    except mysql.connector.Error as err:
        print(f"Error generating report: {err}")
        flash(f"Error generating report: {err}", 'danger')
        return redirect(url_for('staff.inventory'))
    except Exception as e:
        print(f"Unexpected error: {e}")
        flash(f"Unexpected error: {e}", 'danger')
        return redirect(url_for('staff.inventory'))
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@staff_bp.route('/menu', methods=['GET'])
def get_menu():
    connection, cursor = get_db_connection()
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('staff/menu.html', products=products)

@staff_bp.route('/menu/<int:productid>', methods=['GET'])
def get_product(productid):
    connection, cursor = get_db_connection()
    cursor.execute('SELECT * FROM products WHERE productid = %s', (productid,))
    product = cursor.fetchone()
    cursor.close()
    connection.close()
    if product:
        return jsonify(product)
    else:
        return jsonify({"error": "Product not found"}), 404

@staff_bp.route('/menu/add', methods=['POST'])
def add_product():
    name = request.form['name']
    description = request.form['description']
    category = request.form['category']
    price = request.form['price']
    image = request.files['image']
    
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image.save(os.path.join(UPLOAD_FOLDER, filename))
    else:
        flash('Invalid image format. Please upload a valid image.', 'danger')
        return redirect(url_for('staff.get_menu'))

    connection, cursor = get_db_connection()
    try:
        cursor.execute('INSERT INTO products (name, description, category, price, image) VALUES (%s, %s, %s, %s, %s)',
                       (name, description, category, price, filename))
        connection.commit()
        flash('Product added successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error adding product: {err}', 'danger')
        connection.rollback()
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('staff.get_menu'))

@staff_bp.route('/menu/update/<int:productid>', methods=['POST'])
def update_product(productid):
    name = request.form.get('name')
    description = request.form.get('description')
    category = request.form.get('category')
    price = request.form.get('price')
    image = request.files.get('image')

    if not all([name, description, category, price]):
        flash('All fields except image are required.', 'danger')
        return redirect(url_for('staff.get_menu'))

    connection, cursor = get_db_connection()

    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image.save(os.path.join(UPLOAD_FOLDER, filename))
    else:
        filename = request.form.get('image_url')  # Ensure there is a default image URL

    try:
        cursor.execute('UPDATE products SET name=%s, description=%s, category=%s, price=%s, image=%s WHERE productid=%s',
                       (name, description, category, price, filename, productid))
        connection.commit()
        flash('Product updated successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error updating product: {err}', 'danger')
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('staff.get_menu'))

@staff_bp.route('/menu/delete/<int:productid>', methods=['POST'])
def delete_product(productid):
    connection, cursor = get_db_connection()
    cursor.execute('DELETE FROM products WHERE productid=%s', (productid,))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('staff.get_menu'))

@staff_bp.route('/promotion', methods=['GET', 'POST'])
def promotion():
    if request.method == 'POST':
        code = request.form['code']
        description = request.form['description']
        discount_percent = request.form['discount_percent']
        valid_from = request.form['valid_from']
        valid_to = request.form['valid_to']
        product_id = request.form['product_id']

        connection, cursor = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                INSERT INTO promotions (code, description, discountpercent, validfrom, validto, productid) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (code, description, discount_percent, valid_from, valid_to, product_id))
            connection.commit()
            flash('Promotion code created successfully!', 'success')
        except mysql.connector.Error as err:
            if err.errno == mysql.connector.errorcode.ER_DUP_ENTRY:
                flash('Error: The promotion code already exists. Please use a different code.', 'danger')
            else:
                flash('An error occurred while creating the promotion code. Please try again.', 'danger')
            connection.rollback()
        finally:
            cursor.close()
            connection.close()
        
        return redirect(url_for('staff.promotion'))

    # Fetch products for the product selection dropdown
    connection, cursor = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT productid, name FROM products")
    products = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('staff/promotion.html', products=products)

@staff_bp.route('/messages', methods=['GET', 'POST'])
def messages():
    if 'username' not in session:
        flash('Please log in to view and send messages.', 'danger')
        return redirect(url_for('staff_bp.login'))

    staff_id = session.get('staff_id')
    user_type = 'staff'

    connection, cursor = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        content = request.json.get('content')
        receivertype = request.json.get('receivertype')
        receiver_username = request.json.get('receiver_username')

        if not content:
            return jsonify({'success': False, 'error': 'Message content cannot be empty.'}), 400

        try:
            # Selecting the ID based on the type of receiver
            if receivertype == 'customer':
                cursor.execute("SELECT customerid as id FROM customers WHERE username = %s LIMIT 1", (receiver_username,))
            elif receivertype == 'manager':
                cursor.execute("SELECT managerid as id FROM managers WHERE username = %s LIMIT 1", (receiver_username,))

            receiver_row = cursor.fetchone()
            if receiver_row:
                receiver_id = receiver_row['id']
                cursor.execute("""
                    INSERT INTO messages (senderid, receiverid, sendertype, receivertype, content)
                    VALUES (%s, %s, %s, %s, %s)
                """, (staff_id, receiver_id, user_type, receivertype, content))
                connection.commit()
                return jsonify({'success': True}), 201
            else:
                return jsonify({'success': False, 'error': 'No suitable receiver found.'}), 400
        except Exception as e:
            connection.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            cursor.close()
            connection.close()

    try:
        # Retrieve only relevant messages
        cursor.execute("""
            SELECT 
                m.messageid,
                m.senderid,
                m.receiverid,
                m.sendertype,
                m.receivertype,
                m.content,
                m.timestamp,
                CASE
                    WHEN m.sendertype = 'customer' THEN (SELECT CONCAT(username, ' (Customer)') FROM customers WHERE customerid = m.senderid)
                    WHEN m.sendertype = 'staff' THEN (SELECT CONCAT(username, ' (Staff)') FROM staff WHERE staffid = m.senderid)
                    WHEN m.sendertype = 'manager' THEN (SELECT CONCAT(username, ' (Manager)') FROM managers WHERE managerid = m.senderid)
                END AS sender_name,
                CASE
                    WHEN m.receivertype = 'customer' THEN (SELECT CONCAT(username, ' (Customer)') FROM customers WHERE customerid = m.receiverid)
                    WHEN m.receivertype = 'staff' THEN (SELECT CONCAT(username, ' (Staff)') FROM staff WHERE staffid = m.receiverid)
                    WHEN m.receivertype = 'manager' THEN (SELECT CONCAT(username, ' (Manager)') FROM managers WHERE managerid = m.receiverid)
                END AS receiver_name
            FROM 
                messages m
            WHERE 
                (m.senderid = %s AND m.sendertype = 'staff') OR
                (m.receiverid = %s AND m.receivertype = 'staff')
            ORDER BY 
                m.timestamp DESC;
        """, (staff_id, staff_id))
        messages = cursor.fetchall()
    except Exception as e:
        flash(f"Failed to load messages: {e}", 'danger')
        messages = []

    return render_template('staff/messages.html', messages=messages)


@staff_bp.route('/reply_message', methods=['POST'])
def reply_message():
    if 'username' not in session:
        flash('Please log in to reply to messages.', 'danger')
        return redirect(url_for('staff_bp.login'))

    staff_id = session.get('staff_id')
    user_type = 'staff'

    data = request.get_json()
    content = data.get('content')
    receiver_id = data.get('receiver_id')
    receivertype = data.get('receivertype')  # Customer or Manager

    if not content:
        return jsonify({'success': False, 'error': 'Message content cannot be empty.'}), 400

    connection, cursor = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        if receivertype == 'customer':
            cursor.execute("SELECT customerid as id FROM customers WHERE customerid = %s LIMIT 1", (receiver_id,))
        elif receivertype == 'manager':
            cursor.execute("SELECT managerid as id FROM managers WHERE managerid = %s LIMIT 1", (receiver_id,))
        else:
            return jsonify({'success': False, 'error': 'Invalid recipient type.'}), 400

        receiver_row = cursor.fetchone()
        if receiver_row:
            cursor.execute("""
                INSERT INTO messages (senderid, receiverid, sendertype, receivertype, content)
                VALUES (%s, %s, %s, %s, %s)
            """, (staff_id, receiver_id, user_type, receivertype, content))
            connection.commit()
            return jsonify({'success': True}), 201
        else:
            return jsonify({'success': False, 'error': 'No suitable receiver found.'}), 400
    except Exception as e:
        connection.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@staff_bp.route('/accommodation_management')
def accommodation_management():
    if not check_staff_role():
        return redirect(url_for('home_bp.home'))

    return render_template('staff/accommodation_management.html')

@staff_bp.route('/api/bookings', methods=['GET'])
def get_bookings():
    if not check_staff_role():
        return jsonify({'error': 'Unauthorized access'}), 403

    connection, cursor = get_db_connection()

    try:
        cursor.execute("""
            SELECT accommodationid, checkindate, checkoutdate, num_beds
            FROM bookings
            WHERE status = 'booked'
        """)
        bookings = cursor.fetchall()

        booked_dates = []
        for booking in bookings:
            accommodation_id = booking[0]
            checkin = booking[1]
            checkout = booking[2]
            num_beds = booking[3]
            current_date = checkin
            while current_date < checkout:
                booked_dates.append({
                    'accommodation_id': accommodation_id,
                    'date': current_date.strftime('%Y-%m-%d'),
                    'num_beds': num_beds
                })
                current_date += datetime.timedelta(days=1)

        return jsonify(booked_dates)
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        connection.close()
