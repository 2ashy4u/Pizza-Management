from flask import Flask,render_template, request, redirect, url_for, session, flash, jsonify
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin,LoginManager,login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from datetime import datetime


# instantiate app
app = Flask(__name__)

# creating an sqlite database 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Final.db'
# gets rid of annoying terminal warnings that are not needed
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#for session cookies
app.config['SECRET_KEY'] = 'secret'


db = SQLAlchemy(app)
#this is used for migration(Model changes)
migrate = Migrate(app,db)
admin = Admin(app)
login_manager = LoginManager(app)

class Users(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(30), unique=True)
    customer = db.relationship('Customers', backref='user', uselist=False)
    employee = db.relationship('Employees', backref='user', uselist=False)
    manager = db.relationship('Managers', backref='user', uselist=False)

class Customers(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id',name='fk_customers_users'), unique=True)
    name = db.Column(db.String(30))
    email = db.Column(db.String(40))
    address = db.Column(db.String(50))
    phone = db.Column(db.Integer)

class Employees(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_employees_users'), unique=True)
    name = db.Column(db.String(30))
    phone = db.Column(db.Integer)
    # shifts = db.relationship('Shifts', backref='employee', lazy=True, cascade='all, delete-orphan')

class Managers(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_managers_users'), unique=True)
    name = db.Column(db.String(30))

class Shifts(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    shift_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', name='fk_shifts_employees'))
    employee = db.relationship('Employees', backref=db.backref('shifts', lazy=True))

class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', name='fk_orders_customers'))
    customer = db.relationship('Customers', backref=db.backref('orders', lazy=True))
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Pizzas(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=True)

class Carts(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id',name='fk_cart_customers'))
    customer = db.relationship('Customers', backref=db.backref('cart', lazy=True))
    pizza_id = db.Column(db.Integer, db.ForeignKey('pizzas.id'))
    pizza = db.relationship('Pizzas', backref=db.backref('cart', lazy=True))
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    order = db.relationship('Orders', backref=db.backref('cart', lazy=True))
    quantity = db.Column(db.Integer, nullable=False)








#adds the tables to the admin (so data can be modified through admin)
    admin.add_view(ModelView(Users,db.session))
    admin.add_view(ModelView(Customers,db.session))
    admin.add_view(ModelView(Employees,db.session))
    admin.add_view(ModelView(Managers,db.session))
    admin.add_view(ModelView(Shifts,db.session))
    admin.add_view(ModelView(Orders,db.session))
    

@login_manager.user_loader
def load_user(user_id):
   #returns the user from the database
   return Users.query.get(int(user_id))

@app.route('/',methods=["GET", "POST"])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        address = request.form['address']
        phone = request.form['phone']
        username = request.form['username']
        password = request.form['password']

        if not name or not email or not address or not phone or not username or not password:
            flash('Please fill in all fields', 'error')
            return redirect(url_for('signup'))

        existing_user = Users.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken', 'error')
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password, method='sha256')
        new_user = Users(username=username, password=hashed_password)
        new_customer = Customers(name=name, email=email, address=address, phone=phone, user=new_user)
        db.session.add(new_user)
        db.session.add(new_customer)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('signup.html')




@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = Users.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password, password):
            return "Incorrect username or password"
        
        login_user(user)
        # store user info into session 
        session['id'] = user.id
        
        return redirect(url_for("dashboard"))
    return render_template("login.html")
    


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():  
    if len(session) > 0: # we have session data, someone is logged in
        user_id = session['id']
        employee = Employees.query.filter(Employees.user_id == user_id).first()
        manager = Managers.query.filter(Managers.user_id == user_id).first()
        customer = Customers.query.filter(Customers.user_id == user_id).first()
        if employee:
            #get all of the orders to display
            #return the employee_dashboard (or the endpoint)
            return redirect(url_for('customer_orders'))
#customer_orders
        elif manager:
            #get all of the employees shifts to display in a table
            #return the manager_dashboard (or the endpoint)
            return redirect(url_for('all_employee_shifts'))

        elif customer:
            #get the menu items to be displayed 
            return redirect(url_for('order_menu'))

        
        else:
            return render_template("dashboard.html")

@app.route("/menu")
def order_menu():
    pizzas = Pizzas.query.all()
    user_id = session['id']
    customer = Customers.query.filter(Customers.user_id == user_id).first()
    cart_items = Carts.query.filter(Carts.customer_id == customer.id, Carts.order_id == None).all()
    total_cost = calculate_total_cost(cart_items)
    return render_template("order_menu.html", pizzas=pizzas, cart_items=cart_items, total_cost=total_cost)

@app.route("/add_to_cart/<int:pizza_id>", methods=["POST"])
@login_required
def add_to_cart(pizza_id):
    user_id = session['id']
    customer = Customers.query.filter(Customers.user_id == user_id).first()
    cart_item = Carts.query.filter(Carts.customer_id == customer.id, Carts.pizza_id == pizza_id).first()

    if cart_item:
        cart_item.quantity += 1
        
    else:
        cart_item = Carts(customer_id=customer.id, pizza_id=pizza_id, quantity=1)

    db.session.add(cart_item)
    db.session.commit()
    return redirect(url_for("order_menu"))

@app.route("/remove_from_cart/<int:pizza_id>", methods=["POST"])
@login_required
def remove_from_cart(pizza_id):
    user_id = session['id']
    customer = Customers.query.filter(Customers.user_id == user_id).first()
    cart_item = Carts.query.filter(Carts.customer_id == customer.id, Carts.pizza_id == pizza_id).first()

    if cart_item:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            db.session.delete(cart_item)
        db.session.commit()

    return redirect(url_for("order_menu"))


@app.route("/checkout", methods=["POST"])
@login_required
def checkout():
    user_id = session['id']
    customer = Customers.query.filter(Customers.user_id == user_id).first()
    cart_items = Carts.query.filter(Carts.customer_id == customer.id, Carts.order_id == None).all()

    if not cart_items:
        flash('Your cart is empty', 'error')
        return redirect(url_for("order_menu"))

    new_order = Orders(customer_id=customer.id)
    db.session.add(new_order)
    db.session.commit()

    for item in cart_items:
        item.order_id = new_order.id
        db.session.add(item)
    db.session.commit()

    
    return render_template("order_confirmation.html")

@app.route('/employee/orders', methods=['GET', 'POST'])
def customer_orders():
    orders = Orders.query.all()
    return render_template('employee_dashboard.html', orders=orders)

@app.route('/employee/update_orders', methods=['POST'])
def update_orders():
    completed_orders = request.form.getlist('completed_orders')
    for order_id in completed_orders:
        order = Orders.query.get(order_id)
        db.session.delete(order)
    db.session.commit()
    return redirect(url_for('customer_orders'))



@app.route('/employee_shifts', methods=['GET', 'POST'])
@login_required
def employee_shifts():
    # Get the logged-in employee
    employee = Employees.query.filter_by(user_id=current_user.id).first()

    # Get the employee's shifts
    employee_shifts = Shifts.query.filter_by(employee_id=employee.id).all()

    # Convert the shifts data to a format suitable for the template
    shifts_data = [
        {
            'date': shift.shift_date.strftime('%Y-%m-%d'),
            'start_time': shift.start_time.strftime('%H:%M'),
            'end_time': shift.end_time.strftime('%H:%M'),
        } for shift in employee_shifts
    ]

    return render_template('employee_shifts.html', employee_name=employee.name, shifts_data=shifts_data)

@app.route('/all_employee_shifts', methods=['GET'])
@login_required
def all_employee_shifts():
    # Get all employees' shifts
    all_shifts = Shifts.query.all()

    # Convert the shifts data to a format suitable for the template
    shifts_data = [
    {
        'id': shift.id,
        'date': shift.shift_date.strftime('%Y-%m-%d'),
        'start_time': shift.start_time.strftime('%H:%M:%S'),
        'end_time': shift.end_time.strftime('%H:%M:%S'),
        'employee_name': shift.employee.name if shift.employee is not None else 'Not assigned',
    }
    for shift in all_shifts
]


    return render_template('manager_dashboard.html', shifts_data=shifts_data)

from datetime import datetime

@app.route('/add_shift', methods=['GET', 'POST'])
@login_required
def add_shift():
    if request.method == 'POST':
        # Extract data from the form
        employee_name = request.form.get('employee_name')
        shift_date = request.form.get('shift_date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')

        # Check if any data is missing
        if not all([employee_name, shift_date, start_time, end_time]):
            flash('Missing data', 'error')
            return redirect(url_for('add_shift'))

        # Convert string data to the appropriate data types
        shift_date = datetime.strptime(shift_date, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time, '%H:%M').time()
        end_time = datetime.strptime(end_time, '%H:%M').time()

        # Find the employee by their name
        employee = Employees.query.filter_by(name=employee_name).first()

        # If the employee is not found, show an error message
        if not employee:
            flash(f'Employee with name "{employee_name}" not found', 'error')
            return redirect(url_for('add_shift'))

        # Create a new shift object and save it to the database
        new_shift = Shifts(shift_date=shift_date, start_time=start_time, end_time=end_time, employee_id=employee.id)
        db.session.add(new_shift)
        db.session.commit()

        flash('Shift assigned successfully', 'success')
        return redirect(url_for('all_employee_shifts'))

    return render_template('add_shift.html')

@app.route('/current_employees', methods=['GET'])
@login_required
def current_employees():
    employees = Employees.query.all()

    employees_data = [
        {
            'id': employee.id,
            'name': employee.name,
            'phone': employee.phone
        } for employee in employees
    ]

    return render_template('edit_employees.html', employees_data=employees_data)

@app.route('/delete_employees', methods=['POST'])
@login_required
def delete_employees():
    selected_employee_ids = request.form.getlist('selected_employees')

    for employee_id in selected_employee_ids:
        employee = Employees.query.get(employee_id)
        
        if employee:
            # Delete the employee's user account
            user = Users.query.get(employee.user_id)
            db.session.delete(user)

            # Delete the employee
            db.session.delete(employee)
            db.session.commit()
    
    flash('Selected employees deleted successfully', 'success')
    return redirect(url_for('current_employees'))

def calculate_total_cost(cart_items):
    total_cost = 0
    for item in cart_items:
        total_cost += item.pizza.price * item.quantity
    return total_cost

@app.route("/logout")
def logout():
   logout_user()
   # delete the user info from the session
   session.pop('id', None)
   return redirect(url_for("login"))


if __name__== '__main__':
    app.run(debug=True)

#creates all the models
with app.app_context():
    db.create_all()
  