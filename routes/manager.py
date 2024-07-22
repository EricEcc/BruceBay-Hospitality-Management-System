import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from db import get_db_connection, hashing
import mysql.connector
from datetime import datetime, timedelta
import pandas as pd
from fpdf import FPDF
import io
import decimal

manager_bp = Blueprint("manager", __name__, static_folder="static", template_folder="templates")

# Manager dashboard route
@manager_bp.route('/dashboard')
def dashboard():
    return render_template('manager/manager_dashboard.html')

# User management route
@manager_bp.route('/user_management')
def user_management():
    if 'username' not in session or session.get('usertype') != 'manager':
        flash('You need to log in first', 'danger')
        return redirect(url_for('user.login'))

    connection, cursor = get_db_connection()
    if connection is None:
        flash('Database connection failed.', 'danger')
        return render_template('manager/user_management.html', users=[])

    try:
        cursor.execute("SELECT userid, username, usertype, customerid, staffid, managerid FROM usercredentials")
        users = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        users = []
    finally:
        cursor.close()
        connection.close()

    return render_template('manager/user_management.html', users=users)

# Add user route
@manager_bp.route('/add_user', methods=['POST'])
def add_user():
    if 'username' not in session or session.get('usertype') != 'manager':
        flash('You need to log in first', 'danger')
        return redirect(url_for('user.login'))

    username = request.form['username']
    password = request.form['password']
    usertype = request.form['usertype']

    hashed_password = hashing.hash_value(password, salt='abc123')

    connection, cursor = get_db_connection()
    if connection is None:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('manager.user_management'))

    try:
        if usertype == 'customer':
            cursor.execute("INSERT INTO customers (username, email, passwordhash) VALUES (%s, %s, %s)",
                           (username, f'{username}@example.com', hashed_password))
            customer_id = cursor.lastrowid
            cursor.execute("INSERT INTO usercredentials (username, passwordhash, usertype, customerid) VALUES (%s, %s, %s, %s)",
                           (username, hashed_password, usertype, customer_id))
        elif usertype == 'staff':
            cursor.execute("INSERT INTO staff (username, email, passwordhash) VALUES (%s, %s, %s)",
                           (username, f'{username}@example.com', hashed_password))
            staff_id = cursor.lastrowid
            cursor.execute("INSERT INTO usercredentials (username, passwordhash, usertype, staffid) VALUES (%s, %s, %s, %s)",
                           (username, hashed_password, usertype, staff_id))
        elif usertype == 'manager':
            cursor.execute("INSERT INTO managers (username, email, passwordhash) VALUES (%s, %s, %s)",
                           (username, f'{username}@example.com', hashed_password))
            manager_id = cursor.lastrowid
            cursor.execute("INSERT INTO usercredentials (username, passwordhash, usertype, managerid) VALUES (%s, %s, %s, %s)",
                           (username, hashed_password, usertype, manager_id))

        connection.commit()
        flash('New user added successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('manager.user_management'))

# Edit user route
@manager_bp.route('/edit_user', methods=['POST'])
def edit_user():
    if 'username' not in session or session.get('usertype') != 'manager':
        flash('You need to log in first', 'danger')
        return redirect(url_for('user.login'))

    userid = request.form['userid']
    username = request.form['username']
    usertype = request.form['usertype']

    connection, cursor = get_db_connection()
    if connection is None:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('manager.user_management'))

    try:
        cursor.execute("UPDATE usercredentials SET username=%s, usertype=%s WHERE userid=%s", (username, usertype, userid))

        if usertype == 'customer':
            cursor.execute("UPDATE customers SET username=%s WHERE customerid=%s", (username, userid))
        elif usertype == 'staff':
            cursor.execute("UPDATE staff SET username=%s WHERE staffid=%s", (username, userid))
        elif usertype == 'manager':
            cursor.execute("UPDATE managers SET username=%s WHERE managerid=%s", (username, userid))

        connection.commit()
        flash('User details updated successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('manager.user_management'))

# Delete user route
@manager_bp.route('/delete_user/<int:userid>')
def delete_user(userid):
    if 'username' not in session or session.get('usertype') != 'manager':
        flash('You need to log in first', 'danger')
        return redirect(url_for('user.login'))

    connection, cursor = get_db_connection()
    if connection is None:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('manager.user_management'))

    try:
        cursor.execute("DELETE FROM usercredentials WHERE userid=%s", (userid,))
        connection.commit()
        flash('User deleted successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('manager.user_management'))

# Get user route
@manager_bp.route('/get_user/<int:userid>')
def get_user(userid):
    connection, cursor = get_db_connection()
    if connection is None:
        return jsonify(success=False, message="Database connection failed.")

    try:
        cursor.execute("SELECT userid, username, usertype, customerid, staffid, managerid FROM usercredentials WHERE userid = %s", (userid,))
        user = cursor.fetchone()
        if user:
            user_data = {
                'userid': user[0],
                'username': user[1],
                'usertype': user[2],
                'customerid': user[3],
                'staffid': user[4],
                'managerid': user[5]
            }
            return jsonify(user_data)
        else:
            return jsonify(success=False, message="User not found.")
    except mysql.connector.Error as err:
        return jsonify(success=False, message=str(err))
    finally:
        cursor.close()
        connection.close()


@manager_bp.route('/promotions_management', methods=['GET', 'POST'])
def promotions_management():
    if 'username' not in session or session.get('usertype') != 'manager':
        flash('You need to log in first', 'danger')
        return redirect(url_for('user.login'))
    
    connection, cursor = get_db_connection()

    if request.method == 'POST':
        # Handle form submission for editing a promotion
        promotion_id = request.form['promotion_id']
        code = request.form['code']
        description = request.form['description']
        discount_percent = request.form['discount_percent']
        valid_from = request.form['valid_from']
        valid_to = request.form['valid_to']
        product_id = request.form['product_id']

        update_query = """
            UPDATE promotions
            SET code=%s, description=%s, discountpercent=%s, validfrom=%s, validto=%s, productid=%s
            WHERE promotionid=%s
        """
        cursor.execute(update_query, (code, description, discount_percent, valid_from, valid_to, product_id, promotion_id))
        connection.commit()
        flash('Promotion updated successfully', 'success')

    # Fetch promotions and products for display
    cursor.execute("SELECT promotionid, code, description, discountpercent, validfrom, validto, productid FROM promotions")
    promotions = cursor.fetchall()
    
    cursor.execute("SELECT productid, name FROM products")
    products = cursor.fetchall()
    
    connection.close()
    
    return render_template('manager/promotions_management.html', promotions=promotions, products=products)
def check_manager_role():
    return 'username' in session and session.get('usertype') == 'manager'

# Inventory management route
@manager_bp.route('/inventory_management', methods=['GET', 'POST'])
def inventory_management():
    if not check_manager_role():
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
    return render_template('manager/inventory_management.html', products=products)

@manager_bp.route('/update_inventory_management/<int:product_id>', methods=['POST'])
def update_inventory_management(product_id):
    if not check_manager_role():
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

@manager_bp.route('/inventory_management/report', methods=['GET', 'POST'])
def inventory_report_management():
    if not check_manager_role():
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

            return render_template('manager/inventory_report.html', tables=[df.to_html(classes='data')], titles=df.columns.values)
        except mysql.connector.Error as err:
            print(f"Error fetching report data: {err}")
            flash(f"Error fetching report data: {err}", 'danger')
            return redirect(url_for('manager.inventory_management'))
        except Exception as e:
            print(f"Unexpected error: {e}")
            flash(f"Unexpected error: {e}", 'danger')
            return redirect(url_for('manager.inventory_management'))

    return render_template('manager/inventory_report_form.html')

@manager_bp.route('/inventory_management/download_report', methods=['POST'])
def download_inventory_report_management():
    if not check_manager_role():
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
        return redirect(url_for('manager.inventory_management'))
    except Exception as e:
        print(f"Unexpected error: {e}")
        flash(f"Unexpected error: {e}", 'danger')
        return redirect(url_for('manager.inventory_management'))

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@manager_bp.route('/accommodation_management')
def accommodation_management():
    if 'username' not in session or session.get('usertype') != 'manager':
        flash('You need to log in first', 'danger')
        return redirect(url_for('user.login'))

    connection, cursor = get_db_connection()
    cursor.execute("""
        SELECT aa.accommodationid, p.name, aa.date, aa.availablerooms
        FROM accommodationavailability aa
        JOIN accommodations a ON aa.accommodationid = a.accommodationid
        JOIN products p ON a.productid = p.productid
    """)
    availability = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('manager/accommodation_management.html', availability=availability)

# Reporting and analytics route
@manager_bp.route('/reporting_analytics')
def reporting_analytics():
    if 'username' not in session or session.get('usertype') != 'manager':
        flash('You need to log in first', 'danger')
        return redirect(url_for('user.login'))

    return render_template('manager/reporting_analytics.html')

# News and announcements route
@manager_bp.route('/news_announcements')
def news_announcements():
    if 'username' not in session or session.get('usertype') != 'manager':
        flash('You need to log in first', 'danger')
        return redirect(url_for('user.login'))

    return render_template('manager/news_announcements.html')

# Update availability route
@manager_bp.route('/update_availability', methods=['POST'])
def update_availability():
    data = request.json
    room_type = data.get('roomType')
    date = data.get('date')
    available_rooms = data.get('availableRooms')
    changed_by = session.get('username')  # Assuming the username is stored in the session

    connection, cursor = get_db_connection()

    # Check if the record exists
    cursor.execute("""
        SELECT availablerooms
        FROM accommodationavailability
        WHERE accommodationid = %s AND date = %s
    """, (room_type, date))
    result = cursor.fetchone()

    if result:
        # Record exists, update it
        current_available_rooms = result[0]
        cursor.execute("""
            UPDATE accommodationavailability
            SET availablerooms = %s, old_availablerooms = %s, changed_by = %s, changed_at = NOW()
            WHERE accommodationid = %s AND date = %s
        """, (available_rooms, current_available_rooms, changed_by, room_type, date))
    else:
        # Record does not exist, insert a new one
        cursor.execute("""
            INSERT INTO accommodationavailability (accommodationid, date, availablerooms, old_availablerooms, changed_by, changed_at)
            VALUES (%s, %s, %s, NULL, %s, NOW())
        """, (room_type, date, available_rooms, changed_by))

    connection.commit()
    connection.close()

    return jsonify({'message': 'Availability updated successfully'})

# Block room route

@manager_bp.route('/block_room', methods=['POST'])
def block_room():
    data = request.json
    room_type = data.get('roomType')
    start_date = datetime.strptime(data.get('startDate'), '%Y-%m-%d')
    end_date = datetime.strptime(data.get('endDate'), '%Y-%m-%d')

    connection, cursor = get_db_connection()
    try:
        current_date = start_date
        while current_date <= end_date:
            cursor.execute('INSERT INTO blocked_dates (accommodationid, date) VALUES (%s, %s)', (room_type, current_date))
            current_date += timedelta(days=1)
        connection.commit()
    except mysql.connector.Error as err:
        connection.rollback()
        return jsonify({'message': f'Error: {err}'}), 400
    finally:
        cursor.close()
        connection.close()

    return jsonify({'message': 'Dates blocked successfully'}), 200


# Get blocked dates route
@manager_bp.route('/get_blocked_dates', methods=['GET'])
def get_blocked_dates():
    connection, cursor = get_db_connection()
    cursor.execute("""
        SELECT p.name, bd.date
        FROM blocked_dates bd
        JOIN accommodations a ON bd.accommodationid = a.accommodationid
        JOIN products p ON a.productid = p.productid
        ORDER BY bd.date
    """)
    blocked_dates = cursor.fetchall()
    connection.close()

    blocked_dates_dict = {}
    for row in blocked_dates:
        room_type = row[0]
        date = row[1]
        if room_type not in blocked_dates_dict:
            blocked_dates_dict[room_type] = []
        blocked_dates_dict[room_type].append(date)

    blocked_dates_list = []
    for room_type, dates in blocked_dates_dict.items():
        dates.sort()
        start_date = dates[0]
        end_date = dates[0]
        for i in range(1, len(dates)):
            if dates[i] == end_date + timedelta(days=1):
                end_date = dates[i]
            else:
                blocked_dates_list.append({
                    'room_type': room_type,
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d')
                })
                start_date = dates[i]
                end_date = dates[i]
        blocked_dates_list.append({
            'room_type': room_type,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        })

    return jsonify(blocked_dates_list)


# Get availability changes route
@manager_bp.route('/get_availability_changes', methods=['GET'])
def get_availability_changes():
    connection, cursor = get_db_connection()
    cursor.execute("""
        SELECT p.name, aa.date, aa.old_availablerooms, aa.availablerooms, aa.changed_by, aa.changed_at
        FROM accommodationavailability aa
        JOIN accommodations a ON aa.accommodationid = a.accommodationid
        JOIN products p ON a.productid = p.productid
        WHERE aa.old_availablerooms IS NOT NULL
        ORDER BY aa.changed_at DESC
    """)
    availability_changes = cursor.fetchall()
    connection.close()

    availability_changes_list = [{
        'room_type': row[0],
        'date': row[1].strftime('%Y-%m-%d'),
        'old_availablerooms': row[2],
        'new_availablerooms': row[3],
        'changed_by': row[4],
        'changed_at': row[5].strftime('%Y-%m-%d %H:%M:%S')
    } for row in availability_changes]

    return jsonify(availability_changes_list)

@manager_bp.route('/api/bookings', methods=['GET'])
def get_bookings():
    if 'username' not in session or session.get('usertype') != 'manager':
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
                current_date += timedelta(days=1)

        return jsonify(booked_dates)
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        connection.close()
        
@manager_bp.route('/transaction')
def transaction():
    if 'username' not in session or session.get('usertype') != 'manager':
        flash('You need to log in first', 'danger')
        return redirect(url_for('user.login'))

    # Get the filters from query parameters
    month = request.args.get('month')
    year = request.args.get('year', datetime.now().year)
    product_name = request.args.get('product_name', '').strip()
    category = request.args.get('category', '').strip()

    if not month:
        month = datetime.now().month

    month = int(month)
    year = int(year)

    # Get database connection and cursor
    connection, cursor = get_db_connection()

    # Build the SQL query for orders with filters
    query = """
        SELECT o.orderid, o.customerid, o.orderdate, o.totalprice, p.name AS product_name, p.category AS product_category
        FROM orders o
        JOIN orderitems oi ON o.orderid = oi.orderid
        JOIN products p ON oi.productid = p.productid
        WHERE MONTH(o.orderdate) = %s AND YEAR(o.orderdate) = %s
    """
    params = [month, year]

    if product_name:
        query += " AND p.name LIKE %s"
        params.append(f"%{product_name}%")

    if category:
        query += " AND p.category = %s"
        params.append(category)

    cursor.execute(query, tuple(params))
    orders = cursor.fetchall()

    # Calculate GST and net price for orders
    gst_rate = decimal.Decimal('0.15')
    detailed_orders = []
    total_totalprice = decimal.Decimal('0')
    total_netprice = decimal.Decimal('0')
    total_gst = decimal.Decimal('0')

    for order in orders:
        total_price = order[3]
        gst = total_price * gst_rate
        net_price = total_price - gst

        total_totalprice += total_price
        total_netprice += net_price
        total_gst += gst

        detailed_orders.append(order + (net_price, gst))

    # Build the SQL query for accommodation bookings with filters
    accommodation_query = """
        SELECT b.bookingid, p.name AS product_name, DATEDIFF(b.checkoutdate, b.checkindate) AS days,
               (DATEDIFF(b.checkoutdate, b.checkindate) * p.price) AS total_price,
               ((DATEDIFF(b.checkoutdate, b.checkindate) * p.price) / (1 + %s)) AS net_price,
               ((DATEDIFF(b.checkoutdate, b.checkindate) * p.price) - ((DATEDIFF(b.checkoutdate, b.checkindate) * p.price) / (1 + %s))) AS gst
        FROM bookings b
        JOIN accommodations a ON b.accommodationid = a.accommodationid
        JOIN products p ON a.productid = p.productid
        WHERE MONTH(b.checkindate) = %s AND YEAR(b.checkindate) = %s
    """
    accommodation_params = [gst_rate, gst_rate, month, year]

    if product_name:
        accommodation_query += " AND p.name LIKE %s"
        accommodation_params.append(f"%{product_name}%")

    if category and category == 'accommodation':
        accommodation_query += " AND p.category = %s"
        accommodation_params.append(category)

    cursor.execute(accommodation_query, tuple(accommodation_params))
    accommodation_orders = cursor.fetchall()

    # Calculate totals for accommodation bookings
    total_accommodation_totalprice = decimal.Decimal('0')
    total_accommodation_netprice = decimal.Decimal('0')
    total_accommodation_gst = decimal.Decimal('0')

    for booking in accommodation_orders:
        total_accommodation_totalprice += booking[3]
        total_accommodation_netprice += booking[4]
        total_accommodation_gst += booking[5]

    # Calculate total revenue of the month
    total_revenue = total_totalprice + total_accommodation_totalprice

    # Close cursor and connection
    cursor.close()
    connection.close()

    return render_template('manager/transaction.html', 
                           orders=detailed_orders, 
                           month=month, 
                           year=year, 
                           product_name=product_name, 
                           category=category, 
                           total_totalprice=total_totalprice, 
                           total_netprice=total_netprice, 
                           total_gst=total_gst,
                           accommodation_orders=accommodation_orders,
                           total_accommodation_totalprice=total_accommodation_totalprice,
                           total_accommodation_netprice=total_accommodation_netprice,
                           total_accommodation_gst=total_accommodation_gst,
                           total_revenue=total_revenue)

# Add a context processor to provide the current date and time to all templates
@manager_bp.app_context_processor
def inject_now():
    return {'now': datetime.now()}


@manager_bp.route('/financial_report')
def financial_report():
    if 'username' not in session or session.get('usertype') != 'manager':
        flash('You need to log in first', 'danger')
        return redirect(url_for('user.login'))

    connection, cursor = get_db_connection()

    # Revenue Analysis for the current month
    cursor.execute("""
        SELECT SUM(p.price * oi.quantity) AS Revenue, p.category
        FROM orderitems oi
        JOIN products p ON oi.productid = p.productid
        WHERE p.category IN ('food', 'drink') 
        AND oi.orderid IN (SELECT orderid FROM orders WHERE status = 'completed' AND orderdate BETWEEN CURDATE() - INTERVAL 1 MONTH AND CURDATE())
        GROUP BY p.category;
    """)
    revenue_breakdown = cursor.fetchall()

    total_revenue_current_month = sum(revenue[0] for revenue in revenue_breakdown if revenue[1] in ['food', 'drink']) or 0

    # Revenue Analysis for the previous month
    cursor.execute("""
        SELECT SUM(totalprice) AS TotalRevenue
        FROM orders
        WHERE status = 'completed' AND orderdate BETWEEN CURDATE() - INTERVAL 2 MONTH AND CURDATE() - INTERVAL 1 MONTH;
    """)
    total_revenue_previous_month = cursor.fetchone()[0] or 0

    revenue_growth_rate = ((total_revenue_current_month - total_revenue_previous_month) / total_revenue_previous_month * 100) if total_revenue_previous_month else 0

    cursor.execute("""
        SELECT SUM(p.price * oi.quantity) AS Revenue, p.category
        FROM orderitems oi
        JOIN products p ON oi.productid = p.productid
        WHERE p.category IN ('food', 'drink') 
        AND oi.orderid IN (SELECT orderid FROM orders WHERE status = 'completed' AND orderdate BETWEEN CURDATE() - INTERVAL 1 MONTH AND CURDATE())
        GROUP BY p.category;
    """)
    revenue_breakdown = cursor.fetchall()

    # Accommodation Revenue Analysis
    cursor.execute("""
        SELECT SUM(total_cost) AS TotalAccommodationRevenue
        FROM bookings
        WHERE status = 'booked' AND checkindate BETWEEN CURDATE() - INTERVAL 1 MONTH AND CURDATE();
    """)
    total_accommodation_revenue_current_month = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT SUM(total_cost) AS TotalAccommodationRevenue
        FROM bookings
        WHERE status = 'booked' AND checkindate BETWEEN CURDATE() - INTERVAL 2 MONTH AND CURDATE() - INTERVAL 1 MONTH;
    """)
    total_accommodation_revenue_previous_month = cursor.fetchone()[0] or 0

    accommodation_revenue_growth_rate = ((total_accommodation_revenue_current_month - total_accommodation_revenue_previous_month) / total_accommodation_revenue_previous_month * 100) if total_accommodation_revenue_previous_month else 0

    cursor.execute("""
        SELECT SUM(b.total_cost) AS Revenue, a.room_type
        FROM bookings b
        JOIN accommodations a ON b.accommodationid = a.accommodationid
        WHERE b.status = 'booked' 
        AND b.checkindate BETWEEN CURDATE() - INTERVAL 1 MONTH AND CURDATE()
        GROUP BY a.room_type;
    """)
    accommodation_revenue_breakdown = cursor.fetchall()

    # Order and Sales Analysis
    cursor.execute("""
        SELECT COUNT(*) AS TotalOrders 
        FROM orders 
        WHERE status = 'completed' AND orderdate BETWEEN CURDATE() - INTERVAL 1 MONTH AND CURDATE();
    """)
    total_orders = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT AVG(totalprice) AS AverageOrderValue 
        FROM orders 
        WHERE status = 'completed' AND orderdate BETWEEN CURDATE() - INTERVAL 1 MONTH AND CURDATE();
    """)
    average_order_value = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT p.name, SUM(oi.quantity) AS QuantitySold
        FROM orderitems oi
        JOIN products p ON oi.productid = p.productid
        WHERE oi.orderid IN (SELECT orderid FROM orders WHERE status = 'completed' AND orderdate BETWEEN CURDATE() - INTERVAL 1 MONTH AND CURDATE())
        GROUP BY p.name
        ORDER BY QuantitySold DESC
        LIMIT 5;
    """)
    top_selling_products = cursor.fetchall()

    # Inventory Analysis
    cursor.execute("""
        SELECT p.name, i.quantityavailable
        FROM inventory i
        JOIN products p ON i.productid = p.productid;
    """)
    inventory_levels = cursor.fetchall()

    cursor.execute("""
        SELECT p.name, i.quantityavailable, i.lowstockthreshold
        FROM inventory i
        JOIN products p ON i.productid = p.productid
        WHERE i.quantityavailable < i.lowstockthreshold;
    """)
    low_stock_alerts = cursor.fetchall()

    # Net Profit Margin Calculation
    total_expenses = 500  # Example fixed expenses, replace with actual calculation if available
    net_profit = total_revenue_current_month + total_accommodation_revenue_current_month - total_expenses
    net_profit_margin = (net_profit / (total_revenue_current_month + total_accommodation_revenue_current_month) * 100) if (total_revenue_current_month + total_accommodation_revenue_current_month) else 0

    cursor.close()
    connection.close()

    # Calculate date range for the report
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    return render_template('manager/financial_report.html', 
                           total_revenue=total_revenue_current_month, 
                           revenue_breakdown=revenue_breakdown, 
                           total_accommodation_revenue=total_accommodation_revenue_current_month,
                           accommodation_revenue_breakdown=accommodation_revenue_breakdown,
                           total_orders=total_orders, 
                           average_order_value=average_order_value, 
                           top_selling_products=top_selling_products, 
                           inventory_levels=inventory_levels, 
                           low_stock_alerts=low_stock_alerts, 
                           revenue_growth_rate=revenue_growth_rate, 
                           accommodation_revenue_growth_rate=accommodation_revenue_growth_rate,
                           net_profit_margin=net_profit_margin,
                           start_date=start_date.strftime('%Y-%m-%d'),
                           end_date=end_date.strftime('%Y-%m-%d'))


@manager_bp.route('/messages', methods=['GET', 'POST'])
def messages():
    if 'username' not in session:
        flash('Please log in to view and send messages.', 'danger')
        return redirect(url_for('manager.login'))

    manager_id = session.get('manager_id')
    user_type = 'manager'

    connection, cursor = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == 'POST':
        content = request.form.get('content')
        receivertype = request.form.get('receivertype')

        if not content:
            flash('Message content cannot be empty.', 'error')
            return redirect(url_for('manager.messages'))

        try:
            if receivertype == 'customer':
                receiver_id = 1  # Replace with logic to get the customer ID
            elif receivertype == 'staff':
                receiver_id = 2  # Replace with logic to get the staff ID

            insert_query = """
                INSERT INTO messages (senderid, receiverid, sendertype, receivertype, content)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (manager_id, receiver_id, user_type, receivertype, content))
            connection.commit()
            flash('Message sent successfully!', 'success')
        except Exception as e:
            connection.rollback()
            flash('Failed to send message: ' + str(e), 'error')
        finally:
            cursor.close()
            connection.close()

        return redirect(url_for('manager.messages'))

    # Retrieve messages from the database
    try:
        fetch_messages_query = """
            SELECT 
                m.messageid,
                m.senderid,
                m.receiverid,
                m.sendertype,
                m.receivertype,
                m.content,
                m.timestamp,
                CONCAT((SELECT username FROM customers WHERE customerid = m.senderid), ' (', m.sendertype, ')') AS sender_name,
                CONCAT((SELECT username FROM staff WHERE staffid = m.receiverid), ' (', m.receivertype, ')') AS receiver_name
            FROM 
                messages m
            WHERE 
                m.senderid = %s OR m.receiverid = %s
            ORDER BY 
                m.timestamp DESC;
        """
        cursor.execute(fetch_messages_query, (manager_id, manager_id))
        messages = cursor.fetchall()
    except Exception as e:
        flash(f"Failed to load messages: {e}", 'danger')
        messages = []
    finally:
        cursor.close()
        connection.close()

    return render_template('manager/messages.html', messages=messages)


@manager_bp.route('/reply_message', methods=['POST'])
def reply_message():
    if 'username' not in session or session.get('usertype') != 'manager':
        flash('Please log in to reply to messages.', 'danger')
        return redirect(url_for('user.login'))

    manager_id = session.get('manager_id')
    user_type = 'manager'

    data = request.get_json()
    content = data.get('content')
    receiver_id = data.get('receiver_id')
    receivertype = data.get('receivertype')

    if not content:
        return jsonify({'success': False, 'error': 'Message content cannot be empty.'}), 400

    connection, cursor = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        if receivertype == 'customer':
            receiver_table = 'customers'
            receiver_id_field = 'customerid'
        elif receivertype == 'staff':
            receiver_table = 'staff'
            receiver_id_field = 'staffid'
        else:
            return jsonify({'success': False, 'error': 'Invalid recipient type.'}), 400

        query = f"SELECT {receiver_id_field} as id FROM {receiver_table} WHERE {receiver_id_field} = %s LIMIT 1"
        cursor.execute(query, (receiver_id,))
        receiver_row = cursor.fetchone()

        if receiver_row:
            cursor.execute("""
                INSERT INTO messages (senderid, receiverid, sendertype, receivertype, content)
                VALUES (%s, %s, %s, %s, %s)
            """, (manager_id, receiver_row['id'], user_type, receivertype, content))
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

@manager_bp.route('/news')
def list_news():
    if 'username' not in session or session.get('usertype') != 'manager':
        flash('You need to log in as a manager to view news.', 'danger')
        return redirect(url_for('user.login'))

    connection, cursor = get_db_connection()
    try:
        cursor.execute("SELECT newsid, title, content, publishedat FROM news ORDER BY publishedat DESC")
        news_items = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    return render_template('manager/news_list.html', news_items=news_items)

@manager_bp.route('/news/add', methods=['GET', 'POST'])
def add_news():
    if 'username' not in session or session.get('usertype') != 'manager':
        flash('You need to log in as a manager to add news.', 'danger')
        return redirect(url_for('user.login'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')

        connection, cursor = get_db_connection()
        try:
            cursor.execute(
                "INSERT INTO news (managerid, title, content) VALUES (%s, %s, %s)",
                (session.get('manager_id'), title, content)
            )
            connection.commit()
            flash('News added successfully!', 'success')
            return redirect(url_for('manager.list_news'))
        except mysql.connector.Error as err:
            connection.rollback()
            flash(f'Failed to add news: {err}', 'danger')
        finally:
            cursor.close()
            connection.close()

    return render_template('manager/news_add.html')

@manager_bp.route('/news/edit/<int:news_id>', methods=['GET', 'POST'])
def edit_news(news_id):
    if 'username' not in session or session.get('usertype') != 'manager':
        flash('You need to log in as a manager to edit news.', 'danger')
        return redirect(url_for('user.login'))

    connection, cursor = get_db_connection()
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        published_at = request.form.get('published_at')

        try:
            cursor.execute(
                "UPDATE news SET title=%s, content=%s, publishedat=%s WHERE newsid=%s",
                (title, content, published_at, news_id)
            )
            connection.commit()
            flash('News updated successfully!', 'success')
            return redirect(url_for('manager.list_news'))
        except mysql.connector.Error as err:
            connection.rollback()
            flash(f'Failed to update news: {err}', 'danger')
        finally:
            cursor.close()
            connection.close()
    else:
        cursor.execute("SELECT newsid, title, content, publishedat FROM news WHERE newsid = %s", (news_id,))
        news_item = cursor.fetchone()
        cursor.close()
        connection.close()
        if not news_item:
            flash('News item not found.', 'danger')
            return redirect(url_for('manager.list_news'))

        return render_template('manager/news_edit.html', news=news_item, edit_mode=True)

@manager_bp.route('/news/delete/<int:news_id>', methods=['POST'])
def delete_news(news_id):
    if 'username' not in session or session.get('usertype') != 'manager':
        flash('You need to log in as a manager to delete news.', 'danger')
        return redirect(url_for('user.login'))

    connection, cursor = get_db_connection()
    try:
        cursor.execute("DELETE FROM news WHERE newsid = %s", (news_id,))
        connection.commit()
        flash('News deleted successfully!', 'success')
    except mysql.connector.Error as err:
        connection.rollback()
        flash(f'Failed to delete news: {err}', 'danger')
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('manager.list_news'))

@manager_bp.route('/promotion', methods=['GET', 'POST'])
def promotion():
    if 'username' not in session or session.get('usertype') != 'manager':
        flash('You need to log in first', 'danger')
        return redirect(url_for('user.login'))

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
        
        return redirect(url_for('manager.promotion'))

    # Fetch products for the product selection dropdown
    connection, cursor = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT productid, name FROM products")
        products = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f"Error fetching products: {err}", 'danger')
        products = []
    finally:
        cursor.close()
        connection.close()

    return render_template('manager/promotions_management.html', products=products)