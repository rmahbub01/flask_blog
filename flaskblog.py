import os
import json
from datetime import datetime
import math
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail


with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__,static_url_path='', 
            static_folder='static',
            template_folder='templates')
app.secret_key = 'falleninlovewithflask'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD=  params['gmail-password']
)
mail = Mail(app)

if params['local_uri']:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]


db = SQLAlchemy(app)


##### contact models ######
class Contact(db.Model):
    __tablename__ = 'Contact'
    sl = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    phone_no = db.Column(db.String(14), nullable=False)
    msg = db.Column(db.String(180), nullable=False)
    date_created = db.Column(db.String(50), nullable=True, default= datetime.utcnow().strftime("%d %B, %Y"))
    email = db.Column(db.String(30), nullable=False)


    def __repr__(self):
        return f"Contact('{self.name}','{self.phone_no}','{self.email}')"


class Post(db.Model):
    sl = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(50), nullable=True,default= datetime.utcnow().strftime("%d %B, %Y"))
    img_file = db.Column(db.String(60), nullable=True)

    def __repr__(self):
        return f"Post('{self.title}','{self.slug}')"



@app.route('/')
def home():
    posts = Post.query.filter_by().all()[::-1]
    total_page = math.ceil(len(posts)/params['no_of_posts'])
    page = request.args.get('page')   # args.get() returns int type

    if not str(page).isnumeric():
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]


    if page==1:
        prev = "/?page=" + str(page)
        next = "/?page="+ str(page+1)
    elif page== total_page:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page)
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', params=params, posts=posts,prev=prev,next=next)

@app.route('/about')
def about():
    return render_template('about.html',params=params)

@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        message = request.form.get('message')
        email = request.form.get('email')
        date_posted= datetime.utcnow().strftime("%d %B, %Y")
        entry = Contact(
            name=name,
            phone_no=phone,
            msg=message,
            email=email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients = [params['gmail-user']],
                          body = message + "\n" + phone + "\n" + date_posted)

        flash('Email has been sent')

    return render_template('contact.html', title='Contact', params=params)

@app.route('/post/<string:sl>', methods=['GET'])
def post_route(sl):
    post = Post.query.filter_by(sl=sl).first()
    return render_template('post.html', params=params, post=post)



@app.route('/edit/<string:sl>', methods=['GET','POST'])
def edit(sl):
    if 'user' in session and session['user']==params['admin_user']:
        if request.method == 'POST':
            box_title = request.form.get('title')
            box_slug = request.form.get('slug')
            box_content = request.form.get('content')
            img_file = request.form.get('img_file')
            if sl == '0':
                post = Post(title=box_title,slug=box_slug,content=box_content,img_file=img_file)
                db.session.add(post)
                db.session.commit()
                flash('Post Added')
            else:
                post = Post.query.filter_by(sl=sl).first()
                post.title = box_title
                post.slug = box_slug
                post.content = box_content
                post.img_file = img_file
                db.session.commit()
                flash('Post Edited')

        post = Post.query.filter_by(sl=sl).first()
        return render_template('edit.html', params=params,post=post,sl=sl)

@app.route('/delete/<string:sl>', methods=['GET','POST'])
def delete(sl):
    if 'user' in session and session['user']==params['admin_user']:
        post = Post.query.filter_by(sl=sl).first()
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted successfully')
    return redirect('/dashboard')

@app.route('/dashboard', methods=["GET","POST"])
def dashboard():
    if 'user' in session and session['user']== params['admin_user']:
        posts = Post.query.all()
        return render_template('dashboardlogin.html',params=params,posts=posts)
    if request.method=="POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if username==params['admin_user'] and password==params['admin_pass']:
            session['user'] = username
            posts = Post.query.all()
            flash('Logged in Successfully')
        return render_template('dashboardlogin.html',params=params,posts=posts)

    else:
        return render_template('dashboard.html',params=params)

@app.route('/uploader', methods=['GET','POST'])
def uploader():
    if 'user' in session and session['user']== params['admin_user']:
        if request.method == 'POST':
            file = request.files['file']
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename) ))
            flash_msg= flash("Uploaded Successfully")
            return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')


if __name__=='__main__':
     app.run(debug=True)