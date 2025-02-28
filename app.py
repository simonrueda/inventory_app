from flask import Flask, render_template, request
import csv
from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
# here im importing all of the needed modules for future needs of the aplication
app = Flask(__name__)
app.secret_key = 'C0MPUT3RSC13NC3' 
# initializing flask and encrypting data for security measures
login_manager = LoginManager()  
login_manager.init_app(app)
login_manager.login_view = 'login'  
# creating a login system so only authorized users can access the web app

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id  # Unique ID for the user
        self.username = username  # Username of the user
        self.password = password  # Password
# this class handles user authentication 
users = {
    "user1": User(1, "departamentoing", "1NG3N13R14"),
    "user2": User(2, "departamentoinv", "1NV3NT4R10"),
    "user3": User(3, "departamentocompras", "C0MPR45")
}
# defining all of the predetermined users because the client only needs 3, there´s no need of creating a sign up system.

@login_manager.user_loader
def load_user(user_id):
    for user in users.values():
        if user.id == int(user_id):
            return user
    return None
# this function searchs a user for its ID to check a initiated session, important to check if the user is an admin user or not

@app.route('/')
def home():
    return render_template('home.html')
# just to show the home page of the web app

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # asks for a username and its password
        for user in users.values():
            if user.username == username and user.password == password:
                login_user(user)
                return redirect(url_for('search'))  # if login is correct, it redirect to search

        # If login is incorrect, it returns to login page with an error message
        return render_template('login.html', error="Invalid username or password. Please try again.")

    return render_template('login.html')
# this is responsible of making the log in work correctly, without it, it wouldn´t be possible to log in
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
# this is responsible of giving the user the possibility of loging out and potentially use another username

def read_inventory():
    with open('data.csv', 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        return list(reader)  # Convert CSV rows into a list of dictionaries
# this function reads the CSV data

def write_inventory(data):
    with open('data.csv', 'w', encoding='utf-8-sig', newline='') as file:
        fieldnames = ['PARTE_NUMERO', 'DESCRIPCION', 'CANTIDAD_REQUERIDA', 'CANTIDAD_STOCK', 'PROVEEDOR_SELECIONADO', 'VALOR_UNITARIO']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()  # Write column headers
        writer.writerows(data)  # Write the updated inventory
# this function uploads writen data into the CSV, kind of editing the "inventory"
# Manage Inventory Page (Add, Edit, Delete)
@app.route('/manage_inventory', methods=['GET', 'POST'])
@login_required
def manage_inventory():
    if current_user.username != "departamentocompras":
        return render_template('search.html', error="Acceso denegado, solo el usuario administrador puede modificar el inventario"), 403  # Error 403 = Forbidden
    inventory = read_inventory()  # Loads the inventory from CSV
    # this conditional is responsible of making sure only the admin user (user 3) can access the manage inventory system
    if request.method == 'POST':
        action = request.form['action']
        part_number = request.form['part_number'].strip().upper()
        
        # Convert numeric values and check if they are valid
        try:
            required_quantity = int(request.form.get('required_quantity', '0'))
            stock_quantity = int(request.form.get('stock_quantity', '0'))
            unit_value = float(request.form.get('unit_value', '0'))

            if required_quantity < 0 or stock_quantity < 0 or unit_value < 0:
                return render_template('manage_inventory.html', inventory=inventory, error="Error. los valores no pueden ser negativos")
        # here the conditional is making sure that users can´t enter a negative number or any invalid format so that the web app doesn´t crash
        except ValueError:
            return render_template('manage_inventory.html', inventory=inventory, error="Error. formato invalido")
        # the same, returns an error if the format is invalid
        if action == "add":
            # part of the manage inventory function, this one adds new data to the CSV, in other words, the inventory
            new_part = {
                'PARTE_NUMERO': request.form['part_number'].strip().upper(),
                'DESCRIPCION': request.form['description'],
                'CANTIDAD_REQUERIDA': request.form['required_quantity'],
                'CANTIDAD_STOCK': request.form['stock_quantity'],
                'PROVEEDOR_SELECIONADO': request.form['supplier'],
                'VALOR_UNITARIO': request.form['unit_value']
            }
            inventory.append(new_part)  # Add new part to inventory
            write_inventory(inventory) # prints the updated inventory

        elif action == "edit":
            # this one is for editing already existing parts
            part_number = request.form['part_number'].strip().upper()
            for part in inventory:
                if part['PARTE_NUMERO'] == part_number:
                    part['DESCRIPCION'] = request.form['description']
                    part['CANTIDAD_REQUERIDA'] = request.form['required_quantity']
                    part['CANTIDAD_STOCK'] = request.form['stock_quantity']
                    part['PROVEEDOR_SELECIONADO'] = request.form['supplier']
                    part['VALOR_UNITARIO'] = request.form['unit_value']
            write_inventory(inventory) # also for printing updated inventory

        elif action == "delete":
            # last one is for removing any data from the inventory
            part_number = request.form.get('part_number', '').strip().upper()
            if not part_number:
                return render_template('manage_inventory.html', inventory=inventory, error=" Error: Please enter a part number to delete.") 
            
            matching_parts = [part for part in inventory if part['PARTE_NUMERO'] == part_number]
            if not matching_parts:
                return render_template('manage_inventory.html', inventory=inventory, error=f" Error: Part '{part_number}' not found in inventory.")
            
            inventory = [part for part in inventory if part['PARTE_NUMERO'] != part_number]
            write_inventory(inventory)

        return redirect(url_for('manage_inventory'))  # here it refreshes the page after any changes

    return render_template('manage_inventory.html', inventory=inventory)

@app.route('/search', methods=['GET', 'POST'])
@login_required 
def search():
    if request.method == 'POST':
        serial_number = request.form['serial_number'].strip().upper()

        with open('data.csv', 'r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            reader.fieldnames = [name.lstrip('\ufeff') for name in reader.fieldnames]
            # this little part is responsible of reading the CSV document properly, to avoid Keyerrors
            print("CSV Column Names:", reader.fieldnames)
            # prints the columns for debugging
            for row in reader:
                print("Row Data:", row)  # Print each row

                
                part_number = row.get('PARTE_NUMERO')
                # gets the serial number of the part that the user is looking for
                print(f"Extracted PARTE_NUMERO: {part_number}")  # Debugging
                
                # If part_number is None, print an alert
                if part_number is None:
                    print("ALERT: 'PARTE_NUMERO' key is missing or has a bad format!")
                    continue  # Skip this row

                # continue with the search if part_number is valid
                if part_number.strip().upper() == serial_number:
                    descripcion = row.get('DESCRIPCION', 'No Description')
                    stock = row.get('CANTIDAD_STOCK', '0')
                    proveedor = row.get('PROVEEDOR_SELECIONADO', 'Unknown Supplier')

                    if int(stock) > 0:
                        success_msg =  f"Parte: {descripcion} (Serial: {serial_number}) está en stock: existen {stock} unidades."
                        return render_template('search.html', success=success_msg)
                    # if the part IS in stock the app shows the existing units on stock
                    else:
                        no_stock_msg = f"Parte: {descripcion} (Serial: {serial_number}) no hay stock. Contacte al proovedor: {proveedor}."
                        return render_template('search.html', no_stock=no_stock_msg)
                    # in this conditional, if the part is out of stock, the app shows that there´s no stock and wich provider to contact
        return render_template('search.html', error="No se encuentra esta parte. por favor revise el número de serie.")
     # if the part is not found, the app returns to the search page with an error message

    return render_template('search.html')
# this function (search) is responsible for the search menu, so that users can navigate trough the inventory without modifying it. it has 3 outputs for the 3 diferent situations. 1. part on tock 2. part out of stock and 3. part non existing

if __name__ == '__main__':
    app.run(host='0.0.0.0.', port=10000) 
