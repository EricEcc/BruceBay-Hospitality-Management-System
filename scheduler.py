from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
import mysql.connector
from db import get_db_connection
import logging

scheduler = BackgroundScheduler()
scheduler_started = False

def start_scheduler():
    global scheduler_started
    if not scheduler_started:
        scheduler.start()
        scheduler_started = True

def update_order_status(order_id, new_status):
    logging.debug(f"Updating order {order_id} to status {new_status}")
    connection, cursor = get_db_connection()
    try:
        cursor.execute("UPDATE orders SET status = %s WHERE orderid = %s", (new_status, order_id))
        connection.commit()
        logging.info(f"Order {order_id} updated to status {new_status}")
    except mysql.connector.Error as err:
        logging.error(f"Error updating order status for order {order_id}: {err}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

def schedule_status_update(order_id, new_status, run_time):
    scheduler.add_job(
        func=update_order_status,
        trigger=DateTrigger(run_date=run_time),
        args=[order_id, new_status],
        id=f"update_order_status_{order_id}_{new_status}",
        replace_existing=True
    )

def set_preparing_status():
    connection, cursor = get_db_connection()
    try:
        cursor.execute("SELECT orderid FROM orders WHERE status = 'confirmed' AND ordertype = 'now' AND orderdate < NOW() - INTERVAL 2 MINUTE")
        orders = cursor.fetchall()
        for order in orders:
            schedule_status_update(order[0], 'preparing', datetime.now() + timedelta(minutes=8))
    except mysql.connector.Error as err:
        logging.erro(f"Error fetching orders for preparing status: {err}")
    finally:
        cursor.close()
        connection.close()

def set_ready_status():
    connection, cursor = get_db_connection()
    try:
        cursor.execute("SELECT orderid FROM orders WHERE status = 'preparing' AND ordertype = 'now' AND orderdate < NOW() - INTERVAL 8 MINUTE")
        orders = cursor.fetchall()
        for order in orders:
            schedule_status_update(order[0], 'ready', datetime.now() + timedelta(minutes=2))
    except mysql.connector.Error as err:
        logging.error(f"Error fetching orders for ready status: {err}")
    finally:
        cursor.close()
        connection.close()

def set_preparing_status_later():
    connection, cursor = get_db_connection()
    try:
        cursor.execute("SELECT orderid, scheduledate, scheduletime FROM orders WHERE status = 'confirmed' AND ordertype = 'later'")
        orders = cursor.fetchall()
        for order in orders:
            scheduled_date = order[1]
            scheduled_time = order[2]
            if isinstance(scheduled_time, timedelta):
                scheduled_time = (datetime.min + scheduled_time).time()
            scheduled_datetime = datetime.combine(scheduled_date, scheduled_time)
            schedule_status_update(order[0], 'preparing', scheduled_datetime - timedelta(minutes=8))
    except mysql.connector.Error as err:
        logging.error(f"Error fetching orders for preparing status later: {err}")
    finally:
        cursor.close()
        connection.close()

def set_ready_status_later():
    connection, cursor = get_db_connection()
    try:
        cursor.execute("SELECT orderid, scheduledate, scheduletime FROM orders WHERE status = 'preparing' AND ordertype = 'later'")
        orders = cursor.fetchall()
        for order in orders:
            scheduled_date = order[1]
            scheduled_time = order[2]
            if isinstance(scheduled_time, timedelta):
                scheduled_time = (datetime.min + scheduled_time).time()
            scheduled_datetime = datetime.combine(scheduled_date, scheduled_time)
            schedule_status_update(order[0], 'ready', scheduled_datetime)
    except mysql.connector.Error as err:
        logging.error(f"Error fetching orders for ready status later: {err}")
    finally:
        cursor.close()
        connection.close()

# Schedule the jobs to run every 5 hours
scheduler.add_job(set_preparing_status, 'interval', hours=5, id='set_preparing_status', replace_existing=True)
scheduler.add_job(set_ready_status, 'interval', hours=5, id='set_ready_status', replace_existing=True)
scheduler.add_job(set_preparing_status_later, 'interval', hours=5, id='set_preparing_status_later', replace_existing=True)
scheduler.add_job(set_ready_status_later, 'interval', hours=5, id='set_ready_status_later', replace_existing=True)
