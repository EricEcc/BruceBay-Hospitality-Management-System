from flask import Blueprint, render_template
from db import get_db_connection

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def home():
    connection, cursor = get_db_connection()
    if connection is None:
        return render_template('home.html', food_products=[], accommodation_products=[], merchandise_products=[], recent_news=[])

    try:
        # Fetch food and drink products
        cursor.execute("SELECT productid, name, description, price, image FROM products WHERE category IN ('food', 'drink')")
        food_products = cursor.fetchall()

        # Fetch accommodation products
        cursor.execute("SELECT productid, name, description, price, image FROM products WHERE category = 'accommodation'")
        accommodation_products = cursor.fetchall()

        # Fetch merchandise products
        cursor.execute("SELECT productid, name, description, price, image FROM products WHERE category = 'merchandise'")
        merchandise_products = cursor.fetchall()

        # Fetch the most recent three news items
        cursor.execute("SELECT newsid, title, content FROM news ORDER BY publishedat DESC LIMIT 3")
        recent_news = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

    return render_template('home.html', food_products=food_products, accommodation_products=accommodation_products, merchandise_products=merchandise_products, recent_news=recent_news)

@home_bp.route('/about')
def about():
    return render_template('about.html')

@home_bp.route('/contact')
def contact():
    return render_template('contact.html')
