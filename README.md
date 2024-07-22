# Bruce Bay Beans and Bunks Web Application

## Description

Bruce Bay Beans and Bunks is a comprehensive web application designed to manage various aspects of hospitality services. It provides functionalities for different types of users, including customers, staff, and managers. The application allows users to register, log in, manage profiles, place orders, book accommodations, and perform role-specific tasks based on their permissions.

This project was undertaken as part of my master's degree in Applied Computing at the Lincoln University. Throughout this project, I received invaluable support and help from Wei Hong Low, Allen Zhang, Flora Zhang, and Ziqi Su. Thanks to their effort and dedication, we successfully developed this web application.

## Sample Accounts for Testing

| Role    | Log-in Username | Log-in Password |
|---------|-----------------|-----------------|
| User    | emmasmith       | Abc12345?       |
| Staff   | gracekelly      | Abc12345?       |
| Manager | alicecooper     | Abc12345?       |

## Functionality

### General Features

- **Login:** Registered users can log in to the system using their credentials.
- **Role-Based Access Control:** The system implements role-based access control, allowing customers, staff, and managers to access different features and functionalities based on their roles.
- **Main Navigation:** Clear navigation menu directing to sections like food & drink orders, accommodation bookings, merchandise, and user profiles.
- **Welcome Banner:** Dynamic banner showcasing seasonal offers and new items.
- **Quick Access Tiles:** Icons for daily specials, top-rated menu items, and last-minute room availability.

### User Dashboard

- **Profile Overview:** Display user information including name, email, and contact details with options to modify personal data and update security settings such as passwords.
- **Order History:** Provide a list of past orders with details like order date, items purchased, and total amount. Include re-order functionality and display the status of current orders.
- **Booking Overview:** Show a summary of bookings including room type, dates, and total cost, with options to modify or cancel reservations.
- **Menu:** Allow users to browse and order drinks and food, with options to place orders for immediate delivery or schedule for a later time.
- **Accommodation:** Enable users to book accommodations by selecting from three room types: dorm, queen, and twin. Provide detailed descriptions, availability, and pricing for each room type.
- **Merchandise:** Offer a variety of merchandise for purchase, including caps and insect spray. Display product details, prices, and availability.
- **Inbox:** Allow users to send and receive messages to and from staff or the manager. Provide a user-friendly interface for composing and reading messages.
- **News:** Display the latest news and promotions related to Bruce Bay Beans and Bunks, including special offers, events, and updates.
- **Promotional Codes:** Apply promotional codes at checkout for discounts.

### Staff Dashboard

- **Order Management:** Real-time display of current and upcoming orders with status update capabilities.
- **Booking Management:** Overview of room bookings, room status updates, and guest requirement management.
- **Inventory Management:** Interface to monitor and update stock levels, add products, and set low stock alerts.
- **Accommodation Management:** Overview of the availability calendar for each room.
- **Menu Management:** Edit existing products and add new products to the menu.
- **Messages:** Receive messages from customers and reply to them.
- **Promotional Management:** Create new promotional codes for any products.

### Manager Dashboard

- **Full Access Control:** Comprehensive control over all system aspects, including user management, financial reports, and settings.
- **User Management:** Tools to manage staff accounts, set permissions, and review activity logs.
- **Promotions Management:** Create promotional offers and manage discount codes.
- **News Management:** Send news to be displayed on customer dashboards and the homepage.
- **Inventory Management:** Interface to monitor and update stock levels, add products, and set low stock alerts.
- **Accommodation Management:** Block dates for rooms and view availability on each room in the calendar.
- **Reporting & Analytics:** Generate transaction and financial reports. Detailed sales reports for tracking performance and making informed decisions, and tools to generate financial summaries for tracking revenue and transactions.
- **Messages:** Receive messages from customers and reply to them.

### Order Management

- **Shopping Cart:** Add multiple items and adjust quantities before finalizing the order.
- **Order Now/Later:** Option to order for immediate service or schedule for later.
- **Special Requests and Customizations:** Specify dietary restrictions and preferences.
- **Order Customization:** Allows customers to customize orders with various options.
- **Order Tracking:** Real-time order tracking from preparation to delivery/pickup.

### Booking System

- **Accommodation Booking:** Interface for booking rooms with a real-time availability calendar.
- **Booking Management:** Manage bookings, including changes and cancellations.
- **Booking Summary:** Detailed summary before finalizing the booking, including dates, room type, total cost, and cancellation policy.
- **Confirmation Process:** Option to confirm the booking and proceed to payment, with a confirmation message and booking reference number.

### Inventory and Stock Management

- **Inventory Tracking:** Monitor stock levels and update them as items are sold or replenished.
- **Sold Out Status Management:** Mark items as unavailable to prevent ordering.

### Payment and Promotions

- **Payment Information Collection:** Secure form for card information entry during checkout.
- **Confirmation:** Confirm that payment information is received.
- **Promotion Management:** Create and manage promotional codes with automatic expiry.

### Customer Interactions

- **Customer Messaging:** Direct communication between customers and the business for support.

## System Features

### System Architecture and Framework

- **Flask Framework:** Utilizes Flask for building the backend, allowing flexibility and scalability.
- **Bootstrap Framework:** Utilizes Bootstrap for building a responsive and user-friendly frontend.
- **JavaScript:** Enhances interactivity and functionality on the client side.
- **Python:** Core programming language used for backend development.
- **SQL Database Integration:** Uses an SQL-based database system for data storage.
- **Responsive Design:** Ensures frontend responsiveness across devices.

### Database Management

- **SQL Database Integration:** Uses an SQL-based database system for data storage.
- **Database Schema Design:** Efficient design for handling and querying data.

### Security and Data Protection

- **Secure Authentication:** Implementation of secure authentication mechanisms.
- **Data Encryption:** Encrypts sensitive data in transit and at rest.

### System Administration Tools

- **Manager Dashboard:** Comprehensive backend interface for managing various system aspects.
- **User Role Management:** Assign roles and permissions to system users.

### Payment Integration

- **Financial Reporting:** Tools for generating financial reports and tracking revenue.

## Deployment

To deploy Bruce Bay Beans and Bunks, follow these steps:

1. Clone the repository to your local machine.
2. Install the necessary dependencies specified in the `requirements.txt` file.
3. Configure the database settings in the application configuration file.
4. Run the application using a Python web server such as Flask.
5. Access the application through a web browser using the provided URL.
