from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from datetime import datetime

from dotenv import load_dotenv
import os
load_dotenv()


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
migrate = Migrate(app, db)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"
    

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    author = db.relationship('User', backref=db.backref('posts', lazy=True))

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))







@app.route('/')
def index():
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('index.html', posts=posts)








@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Vérifier si le nom d'utilisateur ou l'email est déjà pris
        user_by_username = User.query.filter_by(username=username).first()
        user_by_email = User.query.filter_by(email=email).first()
        
        if user_by_username:
            flash('Le nom d\'utilisateur est déjà pris. Veuillez en choisir un autre.', 'danger')
        elif user_by_email:
            flash('L\'adresse e-mail est déjà utilisée. Veuillez en choisir une autre.', 'danger')
        else:
            # Créer un nouvel utilisateur
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Votre compte a été créé ! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('index'))
    
    return render_template('register.html')









@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Vous êtes connecté !', 'success')
            return redirect(url_for('index'))  # Rediriger vers une page d'accueil après connexion
        else:
            flash('Identifiants incorrects. Veuillez réessayer.', 'danger')
    return render_template('login.html')







@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous êtes déconnecté !', 'success')
    return redirect(url_for('login'))









@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if password:
            hashed_password = generate_password_hash(password, method='sha256')
            current_user.password = hashed_password
        current_user.username = username
        current_user.email = email
        db.session.commit()
        flash('Vos informations ont été mises à jour !', 'success')
        return redirect(url_for('account'))
    return render_template('account.html', user=current_user)







@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        # Créer un nouvel article
        new_post = Post(title=title, content=content, author=current_user)
        db.session.add(new_post)
        db.session.commit()
        flash('Votre article a été créé avec succès !', 'success')
        return redirect(url_for('index'))
    
    return render_template('create_post.html')






@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author != current_user:
        flash('Vous n\'êtes pas autorisé à supprimer cet article.', 'danger')
        return redirect(url_for('index'))

    db.session.delete(post)
    db.session.commit()
    flash('Votre article a été supprimé avec succès.', 'success')
    return redirect(url_for('index'))






@app.route("/post/<int:post_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        flash('Vous ne pouvez modifier que vos propres articles.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        db.session.commit()
        flash('Votre article a été mis à jour avec succès.', 'success')
        return redirect(url_for('index'))
    
    return render_template('edit_post.html', post=post)





@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post_detail.html', post=post)



@app.route('/profile')
@login_required
def profile():
    posts = Post.query.filter_by(author=current_user).order_by(Post.date_posted.desc()).all()
    return render_template('profile.html', posts=posts)





if __name__ == '__main__':
    app.run(debug=True)

