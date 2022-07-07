import uuid, os, hashlib, pymysql
from flask import Flask, request, render_template, redirect, url_for, session, abort, flash, jsonify
app = Flask(__name__)

# Register the setup page and import create_connection()
from utils import create_connection, setup
app.register_blueprint(setup)



@app.before_request
def restrict():

    restricted_pages = [
        'list_users',
        'view_user',
        'edit_user',
        'delete_user',
        'add_subject'
        'list_subject',
        'edit_subject',
        'edit_subject',
        'delete_subject'
        ]
    admin_only = [
        'list_users'
        'list_subject'
    ]
    if 'logged_in' not in session and request.endpoint in restricted_pages:
        flash("You are not logged in!")
        return redirect('/login')

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        password = request.form['password']
        encrypted_password = hashlib.sha256(password.encode()).hexdigest()

        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = """SELECT * FROM users WHERE email = %s AND password = %s"""
                values = (
                    request.form['email'],
                    encrypted_password
                )
                cursor.execute(sql, values)
                result = cursor.fetchone()

            if result:
                session['logged_in'] = True
                session['first_name'] = result['first_name']
                session['role'] = result['role']
                session['user_id'] = result['user_id']
                return redirect (url_for('view_user', user_id=session['user_id']))
            else:
                flash("Invalid username or password.")
                return redirect('/login')
    else:
        return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# TODO: Add a '/register' (add_user) route that uses INSERT
@app.route('/register', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':

        password = request.form['password']
        encrypted_password = hashlib.sha256(password.encode()).hexdigest()

        if request.files['avatar'].filename:
            avatar_image = request.files["avatar"]
            ext = os.path.splitext(avatar_image.filename)[1]
            avatar_filename = str(uuid.uuid4())[:8] + ext
            avatar_image.save("static/images/" + avatar_filename)
        else:
            avatar_filename = None

        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = """INSERT INTO users 
                    (first_name, last_name, email, password, avatar)
                    VALUES (%s, %s, %s, %s, %s)"""
                values = (
                    request.form['first_name'],
                    request.form['last_name'],
                    request.form['email'],
                    encrypted_password,
                    avatar_filename
                )
                try:
                    cursor.execute(sql, values)
                    connection.commit()
                except pymysql.err.IntegrityError:
                    flash('Email has already been taken.')
                    return redirect('/register')

# Login in the user after they sign up and take them to their profile page
                sql = """SELECT * FROM users WHERE email = %s AND password = %s"""
                values = (
                    request.form['email'],
                    encrypted_password
                )
                cursor.execute(sql, values)
                result = cursor.fetchone()

            if result:
                session['logged_in'] = True
                session['first_name'] = result['first_name']
                session['role'] = result['role']
                session['user_id'] = result['user_id']
                return redirect (url_for('view_user', user_id=session['user_id']))

    return render_template('users_add.html')


@app.route('/dashboard')
def list_users():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            result = cursor.fetchall()
    return render_template('users_list.html', result=result)

@app.route('/subject')
def list_subject():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM subject")
            result = cursor.fetchall()
    return render_template('subject_list.html', result=result)






@app.route('/view')
def view_user():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""SELECT * FROM users WHERE user_id = %s""", request.args['user_id'])
            result = cursor.fetchone()
    return render_template('users_view.html', result=result)

@app.route('/viewstudent')
def view_usersubject():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = """SELECT * From users 
                     JOIN users_subject ON users_subject.user_id=users.user_id
                     JOIN subject ON subject.subject_id=users_subject.subject_id
                     where subject.subject_id=%s"""
            values = (
                request.args['subject_id']
                )
            cursor.execute(sql, values)
            result = cursor.fetchall()

            sql = """SELECT * FROM subject
                     WHERE subject.subject_id = %s"""
            values = (
                request.args['subject_id']
                )
            cursor.execute(sql, values)
            subject = cursor.fetchone()
    return render_template('users_subject.html', result=result, subject=subject)

@app.route('/chosen')
def chosen_subject():
    if session['role'] != 'admin' and str(session['user_id']) != request.args['user_id']: 
        flash("You don't have persmission to view the chosen subject for this user")
        return redirect('/chosen?user_id=' + str(session['user_id']))

    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = """SELECT * FROM users
                     JOIN users_subject ON users_subject.user_id = users.user_id
                     JOIN subject ON subject.subject_id = users_subject.subject_id 
                     WHERE users.user_id = %s"""
            values = (
                request.args['user_id']
                )
            cursor.execute(sql, values)
            result = cursor.fetchall()
            sql = """SELECT * FROM users
                     WHERE users.user_id = %s"""
            values = (
                request.args['user_id']
                )
            cursor.execute(sql, values)
            student = cursor.fetchone()
    return render_template('chosen_list.html', result=result, student=student)


@app.route('/addsub')
def add_sub():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = """INSERT INTO users_subject (user_id, subject_id) VALUES (%s, %s) """
            values = (
                session['user_id'],
                request.args['subject_id']
            )
            cursor.execute(sql, values)
            connection.commit()
    return redirect ('/chosen?user_id=' + str(session['user_id']))    


@app.route('/addsubject', methods=['GET', 'POST'])
def add_subject():
    if request.method == 'POST':
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = """INSERT INTO subject (subject) VALUES (%s)"""
                values = (
                    request.form['subject']
                )
                try:
                    cursor.execute(sql, values)
                    connection.commit()
                except pymysql.err.IntegrityError:
                    flash('Subject name has already exist.')
                    return redirect ('/addsubject')

        return redirect('/subject')

    return render_template ('subject_add.html')

# TODO: Add a '/delete_user' route that uses DELETE
@app.route('/delete')
def delete_user():
    if session['role'] != 'admin' and str(session['user_id']) != request.args['user_id']: 
        flash("You don't have persmission to delete this user")
        return redirect('/view?user_id=' + request.args['user_id'])
    with create_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE user_id=%s", request.args['user_id'])
                connection.commit()
                
    return redirect ('/dashboard')

@app.route('/deletesub')
def delete_subject():
    with create_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM users_subject WHERE subject_id=%s", request.args['subject_id'])
                connection.commit()
            return redirect('/subject')
    return redirect ('/deletesub?subject_id=' + request.args['subject_id'])

@app.route('/edit', methods=['GET', 'POST'])
def edit_user():

    if session['role'] != 'admin' and str(session['user_id']) != request.args['id']:
        flash("You don't have permission to edit this user.")
        return redirect('/view?user_id=' + request.args['id'])

    if request.method == 'POST':
        if request.files['avatar'].filename:
            avatar_image = request.files["avatar"]
            ext = os.path.splitext(avatar_image.filename)[1]
            avatar_filename = str(uuid.uuid4())[:8] + ext
            avatar_image.save("static/images/" + avatar_filename)
            if request.form['old_avatar'] != 'None':
                os.remove("static/images/" + request.form['old_avatar'])
        elif request.form['old_avatar'] != 'None':
            avatar_filename = request.form['old_avatar']
        else:
            avatar_filename = None

        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = """UPDATE users SET
                    first_name = %s,
                    last_name = %s,
                    email = %s,
                    avatar = %s
                WHERE user_id = %s"""
                values = (
                    request.form['first_name'],
                    request.form['last_name'],
                    request.form['email'],
                    avatar_filename,
                    request.form['user_id']
                )
                cursor.execute(sql, values)
                connection.commit()
        return redirect('/view?user_id=' + request.form['user_id'])
    else:
        with create_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE user_id = %s", request.args['user_id'])
                result = cursor.fetchone()
        return render_template('users_edit.html', result=result)

@app.route('/editsub', methods=['GET', 'POST'])
def edit_subject():
    if request.method == 'POST':
        with create_connection() as connection:
            with connection.cursor() as cursor:
                sql = """UPDATE subject SET
                    subject = %s
                WHERE subject_id = %s"""
                values = (
                    request.form['subject'],
                    request.form['subject_id']
                )
                cursor.execute(sql, values)
                connection.commit()
            return redirect('/subject')
    else:
        with create_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM subject WHERE subject_id = %s", request.args['subject_id'])
                result = cursor.fetchone()
    return render_template('subject_edit.html', result=result)

@app.route('/checkemail')
def check_email():
    with create_connection() as connection:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM users WHERE email = %s"
            values = (
                request.args['email']
            )
            cursor.execute(sql, values)
            result = cursor.fetchone()
    if result:
        return jsonify({ 'status': 'Error' })
    else:
        return jsonify({ 'status': 'OK' })

if __name__ == '__main__':
    import os

    # This is required to allow flashing messages. We will cover this later.
    app.secret_key = os.urandom(32)

    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT, debug=True)