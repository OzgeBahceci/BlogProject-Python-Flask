from flask import Flask, render_template, flash, session, request, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import yaml
from yaml import Loader, Dumper
import os
from flask_ckeditor import CKEditor

app = Flask(__name__)
Bootstrap(app)

db = yaml.load(open('db.yaml'), Loader=Loader)
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['MYSQL_CURSORCLASS'] = db['DictCursor']

mysql = MySQL(app)
app.config['SECRET_KEY'] = os.urandom(24)
CKEditor(app)


@app.route('/')
def index():
    cur = mysql.connection.cursor()
    resultValue = cur.execute("SELECT * FROM blog")
    if resultValue > 0:
        blogs = cur.fetchall()
        cur.close()
        return render_template('index.html', blogs=blogs)
    cur.close()
    return render_template('index.html', blogs=None)

@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        userDetails = request.form
        print(userDetails)
        
        # Alan kontrolü
        if (
            userDetails.get('Password') != userDetails.get('confirm_password') or
            not userDetails.get('Firstname') or
            not userDetails.get('Lastname') or
            not userDetails.get('Username') or
            not userDetails.get('Email')
        ):
            flash('Invalid registration data. Please check your input.', 'danger')
            return render_template('register.html')

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (Firstname, Lastname, Username, Email, Password) VALUES (%s, %s, %s, %s, %s)",
                    (userDetails.get('Firstname'), userDetails.get('Lastname'), userDetails.get('Username'),
                     userDetails.get('Email'), generate_password_hash(userDetails.get('Password'))
                     )
        )
        mysql.connection.commit()
        cur.close()
        flash('Register successful! Please Login', 'success')
        return redirect('/login')
    return render_template('register.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        userDetails = request.form
        Username = userDetails['Username']
        cur = mysql.connection.cursor()
        resultValue = cur.execute("SELECT * FROM users WHERE Username = %s", ([Username]))
        if resultValue > 0:
            user = cur.fetchone()
            if check_password_hash(user['Password'], userDetails['Password']):
                session['login'] = True
                session['Firstname'] = user['Firstname']
                session['Lastname'] = user['Lastname']
                flash('Hoş geldiniz ' + session['Firstname'] + ', başarılı bir şekilde giriş yaptınız.', 'success')
                return redirect('/')
            else:
                cur.close()
                flash('Şifre uyuşmuyor', 'danger')
        else:
            cur.close()
            flash('User not found', 'danger')

    return render_template('login.html')

@app.route('/write-blog/', methods=['GET', 'POST'])
def write_blog():
    if request.method == "POST":
        blogpost = request.form
        title = blogpost.get('title')
        body = blogpost.get('body')
        author = session.get('Firstname', '') + ' ' + session.get('Lastname', '')
        if title and body:  # Eksik olmayan başlık ve içeriği kontrol edin
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO blog (title, body, author) VALUES (%s, %s, %s)", (title, body, author))
            mysql.connection.commit()
            cur.close()
            flash("Başarılı bir şekilde yeni blog yazısı oluşturuldu.", "success")
            return redirect('/')
    return render_template('write-blog.html')


@app.route('/my-blogs/', methods=['GET', 'POST'])
def my_blogs():
    if session.get('login'):
        author = session.get('Firstname') + ' ' + session.get('Lastname')
        cur = mysql.connection.cursor()
        resultValue = cur.execute("SELECT * FROM blog WHERE author = %s", (author,))
        if resultValue > 0:
            myBlogs = cur.fetchall()
            return render_template('my-blogs.html', myBlogs=myBlogs)
        else:
            myBlogs = []  # Eğer sonuç yoksa, boş bir liste oluştur
            return render_template('my-blogs.html', myBlogs=myBlogs)
    else:
        flash('You must be logged in to view your blogs', 'info')
        return redirect('/login')





@app.route('/edit-blog/<int:id>/', methods=['GET', 'POST'])
def edit_blog(id):
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        Title = request.form['Title']
        Body = request.form['Body']
        cur.execute("UPDATE blog SET Title=%s, Body=%s WHERE BlogID=%s", (Title, Body, id))
        mysql.connection.commit()
        cur.close()
        flash('Blog updated successfully', 'success')
        return redirect('/my-blogs')
    cur = mysql.connection.cursor()
    resultValue = cur.execute("SELECT * FROM blog WHERE BlogID = %s", (id,))
    if resultValue > 0:
        blog = cur.fetchone()
        blog_form = {}
        blog_form['Title'] = blog['Title']
        blog_form['Body'] = blog['Body']
        return render_template('edit-blog.html', blog_form=blog_form)




@app.route('/delete-blog/<int:id>/', methods=['POST'])
def delete_blog(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM blog WHERE BlogID = %s", (id,))
    mysql.connection.commit()
    cur.close()
    flash('Your blog has been deleted', 'success')
    return redirect('/my-blogs')


@app.route('/blogs/<int:id>/')
def blogs(id):
    cur = mysql.connection.cursor()
    resultValue = cur.execute("SELECT * FROM blog WHERE BlogID = %s", (id,))
    
    if resultValue > 0:
        blog = cur.fetchone()
        cur.close()
        return render_template('blogs.html', blog=blog)
    
    cur.close()
    return render_template('blogs.html', blog=None)


@app.route('/logout/')
def logout(id):
    session.clear()
    flash('Your have been logged out','info')
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
