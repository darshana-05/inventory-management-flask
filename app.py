from flask import Flask, request, redirect
import sqlite3
import uuid
STYLE = """
<style>
    body {
        font-family: Arial, sans-serif;
        background-color: #f4f6f8;
        padding: 20px;
    }
    .container {
        background: white;
        padding: 20px;
        max-width: 800px;
        margin: auto;
        border-radius: 8px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    h2, h3 {
        color: #2c3e50;
    }
    a {
        text-decoration: none;
        color: #2980b9;
    }
    button {
        background-color: #2980b9;
        color: white;
        padding: 6px 12px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    button:hover {
        background-color: #1f618d;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 15px;
    }
    table, th, td {
        border: 1px solid #ccc;
    }
    th {
        background-color: #2980b9;
        color: white;
    }
    th, td {
        padding: 8px;
        text-align: center;
    }
</style>
"""


app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('inventory.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS product (
            product_id TEXT PRIMARY KEY,
            name TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS location (
            location_id TEXT PRIMARY KEY,
            name TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS product_movement (
            movement_id TEXT PRIMARY KEY,
            product_id TEXT,
            from_location TEXT,
            to_location TEXT,
            qty INTEGER
        )
    ''')

    conn.commit()
    conn.close()

@app.route('/')
def home():
    return STYLE + '''
    <div class="container">
        <h2>Inventory Management System</h2>
        <ul>
            <li><a href="/products">📦 Products</a></li>
            <li><a href="/locations">🏬 Locations</a></li>
            <li><a href="/movements">🔄 Product Movements</a></li>
            <li><a href="/report">📊 Balance Report</a></li>
        </ul>
    </div>
    '''


@app.route('/products', methods=['GET', 'POST'])
def products():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        cur.execute(
            'INSERT INTO product VALUES (?, ?)',
            (request.form['product_id'], request.form['name'])
        )
        conn.commit()
        return redirect('/products')

    products = cur.execute('SELECT * FROM product').fetchall()
    conn.close()

    html = '''
        <h3>Add Product</h3>
        <form method="post">
            ID: <input name="product_id">
            Name: <input name="name">
            <button>Add</button>
        </form><hr>
        <ul>
    '''
    for p in products:
        html += f"<li>{p['product_id']} - {p['name']}</li>"
    html += '</ul>'
    return html

@app.route('/locations', methods=['GET', 'POST'])
def locations():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        cur.execute(
            'INSERT INTO location VALUES (?, ?)',
            (request.form['location_id'], request.form['name'])
        )
        conn.commit()
        return redirect('/locations')

    locations = cur.execute('SELECT * FROM location').fetchall()
    conn.close()

    html = '''
        <h3>Add Location</h3>
        <form method="post">
            ID: <input name="location_id">
            Name: <input name="name">
            <button>Add</button>
        </form><hr>
        <ul>
    '''
    for l in locations:
        html += f"<li>{l['location_id']} - {l['name']}</li>"
    html += '</ul>'
    return html

@app.route('/movements', methods=['GET', 'POST'])
def movements():
    conn = get_db_connection()
    cur = conn.cursor()

    products = cur.execute('SELECT * FROM product').fetchall()
    locations = cur.execute('SELECT * FROM location').fetchall()

    if request.method == 'POST':
        movement_id = str(uuid.uuid4())
        product_id = request.form['product_id']
        from_location = request.form['from_location'] or None
        to_location = request.form['to_location'] or None
        qty = int(request.form['qty'])

        cur.execute(
            'INSERT INTO product_movement VALUES (?, ?, ?, ?, ?)',
            (movement_id, product_id, from_location, to_location, qty)
        )
        conn.commit()
        return redirect('/movements')

    html = '''
        <h3>Product Movement</h3>
        <form method="post">
            Product:
            <select name="product_id">
    '''

    for p in products:
        html += f"<option value='{p['product_id']}'>{p['name']}</option>"

    html += '''
            </select><br><br>

            From Location:
            <select name="from_location">
                <option value="">--None--</option>
    '''

    for l in locations:
        html += f"<option value='{l['location_id']}'>{l['name']}</option>"

    html += '''
            </select><br><br>

            To Location:
            <select name="to_location">
                <option value="">--None--</option>
    '''

    for l in locations:
        html += f"<option value='{l['location_id']}'>{l['name']}</option>"

    html += '''
            </select><br><br>

            Quantity: <input type="number" name="qty"><br><br>
            <button>Add Movement</button>
        </form>
    '''

    conn.close()
    return html
@app.route('/report')
def report():
    conn = get_db_connection()
    cur = conn.cursor()

    query = '''
        SELECT 
            p.name AS product,
            l.name AS location,
            SUM(
                CASE
                    WHEN pm.to_location = l.location_id THEN pm.qty
                    WHEN pm.from_location = l.location_id THEN -pm.qty
                    ELSE 0
                END
            ) AS quantity
        FROM product_movement pm
        JOIN product p ON pm.product_id = p.product_id
        JOIN location l 
            ON l.location_id = pm.to_location 
            OR l.location_id = pm.from_location
        GROUP BY p.name, l.name
    '''

    rows = cur.execute(query).fetchall()
    conn.close()

    html = '''
        <h2>Inventory Balance Report</h2>
        <table border="1" cellpadding="5">
            <tr>
                <th>Product</th>
                <th>Warehouse</th>
                <th>Quantity</th>
            </tr>
    '''

    for r in rows:
        html += f'''
            <tr>
                <td>{r['product']}</td>
                <td>{r['location']}</td>
                <td>{r['quantity']}</td>
            </tr>
        '''

    html += '</table>'
    return html


if __name__ == '__main__':
    create_tables()
    app.run(debug=True)


