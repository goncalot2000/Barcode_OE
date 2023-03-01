from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, current_user, logout_user, UserMixin
import sqlite3 as sql
from datetime import datetime
from django.views.decorators.cache import never_cache
#from django.contrib.auth.decorators import user_passes_test
#@user_passes_test(lambda user: User(user).role) #role ou é true (admin) ou false (user)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisismysecretkeydonotstealit'
#app.config['DATABASE'] = 'db.sqlite3'
app.config['DATABASE'] = 'barcode.db'

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    with sql.connect(app.config['DATABASE']) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM people WHERE ID=?", (user_id,))
        user = cursor.fetchone()
        if user is not None:
            return User(user)


class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data[0]
        self.name = user_data[1]
        self.username = user_data[2]
        self.password = user_data[3]
        self.role = user_data[4]

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_id(self):
        return self.id

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/profile')
@login_required
#@never_cache
def profile():
    return render_template('profile.html', name=current_user.name)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        with sql.connect(app.config['DATABASE']) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM people WHERE username=?", (username,))
            user = cursor.fetchone()

            if user is None or not User(user).check_password(password):
                flash('Please check your login details and try again.')
                return redirect(url_for('login'))

            login_user(User(user), remember=remember)

            return redirect(url_for('administrador'))
            #VERIFICA SE É EMPREGADO

            #VERIFICA SE É ADMIN


    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        password = request.form.get('password')
        #role = 'admin'
        role = 'user'

        with sql.connect(app.config['DATABASE']) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM people WHERE username=?", (username,))
            user = cursor.fetchone()

            if user:
                flash('Email address already exists.')
                return redirect(url_for('signup'))

            cursor.execute("INSERT INTO people (name, username, password, role) VALUES (?, ?, ?, ?)",
                           (name, username, generate_password_hash(password, method='sha256'), role))
            #user_id = cursor.lastrowid  # get the ID of the newly inserted user
            #cursor.execute("INSERT INTO empregado (ID) VALUES (?)", (user_id,))
            conn.commit()

            return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/logout')
@login_required
#@never_cache
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/people')
def people():
    try:
        with sql.connect(app.config['DATABASE']) as con:
            cursor = con.cursor()

            cursor.execute("SELECT username, name, role FROM people;")
            cursor.execute("SELECT username, name, role FROM people;")
            users = cursor.fetchall()
            cursor.close()

    except Exception as e:
        return "<h1>An error occurred.</h1>"

    return render_template('people.html', users=users)

@app.route('/obras')
@login_required
#@never_cache
def obras():
    try:
        with sql.connect(app.config['DATABASE']) as con:
            cursor = con.cursor()

            cursor.execute("SELECT * FROM obra;")
            obras = cursor.fetchall()
            cursor.close()

    except Exception as e:
        return "<h1>An error occurred.</h1>"

    return render_template('obras.html', obras=obras)

@app.route('/add_obra', methods=['GET', 'POST'])
def add_obra():
    if request.method == 'POST':
        id = request.form.get('id')
        name = request.form.get('name')

        try:
            with sql.connect(app.config['DATABASE']) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO obra VALUES(?, ?);", (id, name))
                conn.commit()

                return redirect(url_for('obras'))
        except Exception as e:
            return "<h1>An error occurred.</h1>"

    return render_template('add_obra.html')

@app.route('/caixas')
@login_required
#@never_cache
def material():
    try:
        with sql.connect(app.config['DATABASE']) as con:
            cursor = con.cursor()

            cursor.execute("SELECT * FROM caixas;")
            caixas = cursor.fetchall()
            cursor.close()

    except Exception as e:
        return "<h1>An error occurred.</h1>"

    return render_template('material.html', caixas=caixas)

@app.route('/add_material', methods=['GET', 'POST'])
def add_material():
    if request.method == 'POST':
        id = request.form.get('id')
        name = request.form.get('name')

        try:
            with sql.connect(app.config['DATABASE']) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO caixas VALUES(?, ?);", (id, name))
                conn.commit()

                return redirect(url_for('material'))

        except Exception as e:
            return "<h1>An error occurred.</h1>"

    return render_template('add_material.html')

@app.route('/administrador')
@login_required
#@never_cache
def administrador():
    return render_template('administrador.html')

@app.route('/novo_registo', methods=['GET', 'POST'])
@login_required
#@never_cache
def novo_registo():
    if request.method == 'POST':
        user = request.form.get('username')
        obra = request.form.get('obra')
        materials = []
        for key in request.form.keys():
            if key.startswith('material'):
                materials.append(request.form[key])
        timestamp = request.form.get('timestamp')
        timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')

        try:
            with sql.connect(app.config['DATABASE']) as conn:
                cursor = conn.cursor()

                for material in materials:
                    cursor.execute("INSERT INTO works_in (o_ID, g_ID, c_ID, data) VALUES (?, ?, ?, ?)",
                                   (obra, user, material, timestamp))

                conn.commit()
                return redirect(url_for('index'))

        except Exception as e:
            return "<h1>An error occurred.</h1>"

    return render_template('novo_registo.html')


@app.route('/registos')
@login_required
#@never_cache
def registos():
    try:
        with sql.connect(app.config['DATABASE']) as con:
            cursor = con.cursor()
            cursor.execute("SELECT o.name, p.name, c.name, w.data FROM works_in as w INNER JOIN obra AS o ON w.o_ID = o.ID INNER JOIN people AS p ON w.g_ID = p.ID	INNER JOIN caixas AS c ON w.c_ID = c.ID;")
            registos = cursor.fetchall()
            cursor.close()

    except Exception as e:
        return "<h1>An error occurred.</h1>"

    return render_template('registos.html', registos=registos)

@app.route('/registos_people_form')
@login_required
def registos_people_form():
    return render_template('registos_P_form.html')

@app.route('/registos_people', methods=['GET', 'POST'])
@login_required
#@never_cache
def registos_people():
    if request.method == 'POST':
        user = request.form.get('r_people')

    try:
        with sql.connect(app.config['DATABASE']) as con:
            cursor = con.cursor()
            cursor.execute("SELECT o.name, p.name, c.name, w.data FROM works_in as w INNER JOIN obra AS o ON w.o_ID = o.ID INNER JOIN people AS p ON w.g_ID = p.ID	INNER JOIN caixas AS c ON w.c_ID = c.ID WHERE g.ID=?;",
                           (user,))
            registos = cursor.fetchall()
            cursor.close()

    except Exception as e:
        return "<h1>An error occurred.</h1>"

    return render_template('registos_people.html', registos=registos)

@app.route('/registos_material_form')
@login_required
def registos_material_form():
    return render_template('registos_M_form.html')

@app.route('/registos_material', methods=['GET', 'POST'])
@login_required
#@never_cache
def registos_material():
    if request.method == 'POST':
        material = request.form.get('r_material')

    try:
        with sql.connect(app.config['DATABASE']) as con:
            cursor = con.cursor()
            cursor.execute("SELECT o.name, p.name, c.name, w.data FROM works_in as w INNER JOIN obra AS o ON w.o_ID = o.ID INNER JOIN people AS p ON w.g_ID = p.ID	INNER JOIN caixas AS c ON w.c_ID = c.ID WHERE c.ID=?;",
                           (material,))
            registos = cursor.fetchall()
            cursor.close()

    except Exception as e:
        return "<h1>An error occurred.</h1>"

    return render_template('registos_material.html', registos=registos)

@app.route('/registos_obras_form')
@login_required
def registos_obras_form():
    return render_template('registos_O_form.html')

@app.route('/registos_obras', methods=['GET', 'POST'])
@login_required
#@never_cache
def registos_obras():
    if request.method == 'POST':
        obra = request.form.get('r_obra')

    try:
        with sql.connect(app.config['DATABASE']) as con:
            cursor = con.cursor()
            cursor.execute("SELECT o.name, p.name, c.name, w.data FROM works_in as w INNER JOIN obra AS o ON w.o_ID = o.ID INNER JOIN people AS p ON w.g_ID = p.ID	INNER JOIN caixas AS c ON w.c_ID = c.ID WHERE o.ID=?;",
                           (obra,))
            registos = cursor.fetchall()
            cursor.close()

    except Exception as e:
        return "<h1>An error occurred.</h1>"

    return render_template('registos_obras.html', registos=registos)

@app.route('/registos_data_form')
@login_required
def registos_data_form():
    return render_template('registos_D_form.html')

@app.route('/registos_data', methods=['GET', 'POST'])
@login_required
#@never_cache
def registos_data():
    if request.method == 'POST':
        data = request.form.get('r_data')

    try:
        with sql.connect(app.config['DATABASE']) as con:
            cursor = con.cursor()
            cursor.execute("SELECT o.name, p.name, c.name, w.data FROM works_in as w INNER JOIN obra AS o ON w.o_ID = o.ID INNER JOIN people AS p ON w.g_ID = p.ID	INNER JOIN caixas AS c ON w.c_ID = c.ID WHERE DATE(w.data) = DATE(?);",
                           (data,))
            registos = cursor.fetchall()
            cursor.close()

    except Exception as e:
        return "<h1>An error occurred.</h1>"

    return render_template('registos_data.html', registos=registos)

@app.route('/del_registos')
def del_registos():
    try:
        with sql.connect(app.config['DATABASE']) as con:
            cursor = con.cursor()

            cursor.execute("DELETE FROM works_in;")
            cursor.close()

    except Exception as e:
        return "<h1>An error occurred.</h1>"

    return render_template('profile.html', name=current_user.name)

@app.route('/signup_admin', methods=['GET', 'POST'])
def signup_admin():
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        password = request.form.get('password')
        role = 'admin'

        with sql.connect(app.config['DATABASE']) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM people WHERE username=?", (username,))
            user = cursor.fetchone()

            if user:
                flash('Username already exists.')
                return redirect(url_for('signup_admin'))

            cursor.execute("INSERT INTO people (name, username, password, role) VALUES (?, ?, ?, ?)",
                           (name, username, generate_password_hash(password, method='sha256'), role))
            conn.commit()

            return redirect(url_for('index'))

    return render_template('signup_admin.html')

if __name__ == '__main__':
    app.run(debug=True)
