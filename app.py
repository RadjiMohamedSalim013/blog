from flask import Flask, render_template, redirect, request, url_for, flash, abort
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.utils import secure_filename
from sqlalchemy import desc






app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '5f89fa56ea3bf3e8385e14b600c4e4a7f557c4418c707eecbd423a3d8921dcf0'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    profile_image = db.Column(db.String(128), nullable=True)  # Chemin de l'image de profil

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('posts', lazy=True))
    # On peut ajouter d'autres champs comme la date de publication, les tags, etc.

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    post = db.relationship('Post', backref=db.backref('comments', lazy=True))





@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#Route pour les Inscription
@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if current_user.is_authenticated:
        return redirect(url_for('index'))  # Rediriger l'utilisateur déjà connecté
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Ce nom d\'utilisateur est déjà utilisé. Veuillez en choisir un autre.', 'danger')
            return redirect(url_for('inscription'))
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Félicitations ! Vous êtes maintenant inscrit. Vous pouvez vous connecter.', 'success')
        return redirect(url_for('connexion'))
    return render_template('inscription.html')



#Route pour la connexion
@app.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if current_user.is_authenticated:
        return redirect(url_for('index'))  # Rediriger l'utilisateur déjà connecté
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        flash('Nom d\'utilisateur ou mot de passe incorrect. Veuillez réessayer.', 'danger')
    return render_template('connexion.html')


#Route pour la déconnexion
@app.route('/deconnexion')
@login_required
def deconnexion():
    logout_user()
    return redirect(url_for('home'))



#Route pour la creation d'article 
@app.route('/nouvel_article', methods=['GET', 'POST'])
@login_required
def nouvel_article():
    if request.method == 'POST':
        titre = request.form['titre']
        contenu = request.form['contenu']
        if not titre or not contenu:
            flash('Veuillez remplir tous les champs.', 'danger')
            return redirect(url_for('nouvel_article'))
        nouvel_article = Post(title=titre, content=contenu, user=current_user)
        db.session.add(nouvel_article)
        db.session.commit()
        flash('Votre nouvel article a été créé avec succès !', 'success')
        return redirect(url_for('articles'))
    return render_template('nouvel_article.html')



#route pour editr un article
@app.route('/articles/<int:article_id>/editer', methods=['GET', 'POST'])
@login_required
def editer_article(article_id):
    article = Post.query.get_or_404(article_id)
    if article.user != current_user:
        # Vérifie si l'utilisateur actuel est l'auteur de l'article
        abort(403)  # Interdit l'accès si ce n'est pas l'auteur
    if request.method == 'POST':
        article.title = request.form['titre']
        article.content = request.form['contenu']
        db.session.commit()
        flash('L\'article a été mis à jour avec succès !', 'success')
        return redirect(url_for('articles'))
    return render_template('editer_article.html', article=article)


#route pour afficher tous les articles 
@app.route('/articles')
def articles():
    page = request.args.get('page', 1, type=int)
    articles = Post.query.order_by(desc(Post.id)).paginate(page=page, per_page=5)
    return render_template('articles.html', articles=articles)



#route pour supprimer un article
@app.route('/articles/<int:article_id>/supprimer')
@login_required
def supprimer_article(article_id):
    article = Post.query.get_or_404(article_id)
    if article.user != current_user:
        abort(403)  # Interdit l'accès si ce n'est pas l'auteur
    db.session.delete(article)
    db.session.commit()
    flash('L\'article a été supprimé avec succès !', 'success')
    return redirect(url_for('articles'))




#Route pour afficher le profile
@app.route('/profil/<username>')
def profil(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('profil.html', user=user)


@app.route('/')
def home():
    return render_template('index.html')





if __name__ == '__main__':
    app.run(debug=True)