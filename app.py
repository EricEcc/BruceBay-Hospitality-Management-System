from db import app
from routes.home import home_bp
from routes.user import user_bp
from routes.staff import staff_bp
from routes.manager import manager_bp
from routes.accommodation import accommodation_bp  
import scheduler

app.register_blueprint(home_bp)
app.register_blueprint(user_bp, url_prefix='/user')
app.register_blueprint(staff_bp, url_prefix='/staff')
app.register_blueprint(manager_bp, url_prefix='/manager')
app.register_blueprint(accommodation_bp, url_prefix='/accommodation')  
scheduler.scheduler.start()

if __name__ == '__main__':
    app.run(debug=True)
