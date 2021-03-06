from flask import Flask, request, redirect, render_template, flash, session
from flask_sqlalchemy import SQLAlchemy
import datetime
from hashutils import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://blogz:sucrose1617@localhost:8889/blogz"
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)
app.secret_key = '44jjsslgqtg6s'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    db_title = db.Column(db.String(120))
    db_body = db.Column(db.String(10000))
    db_date = db.Column(db.String(120))
    deleted = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, date, author):
        self.db_title = title
        self.db_body = body
        self.db_date = date
        self.deleted = False
        self.author = author
    
    def __repr__(self):
        return "<Post %r>" % self.db_title

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    db_email = db.Column(db.String(120), unique=True)
    db_password = db.Column(db.String(120))
    db_postcount = db.Column(db.Integer)
    db_nickname = db.Column(db.String(120), unique=True)
    db_posts = db.relationship('Post', backref='author')

    def __init__(self, email, password, nickname):
        self.db_email = email
        self.db_password = make_pw_hash(password)
        self.db_nickname = nickname
        self.db_postcount = 0
    
    # def __repr__(self):
    #     return self.db_nickname

#function to get date at time of post submission
def get_date():
    postdate = datetime.datetime.now()
    at_date = postdate.strftime("%b %d %Y")
    at_time = postdate.strftime("%I:%M %p")
    return at_time+" | "+at_date

#function to determine is session is active, return user
def in_session():

    if 'email' in session:
        current_user = User.query.filter_by(db_email=session['email']).first()
        print("-----IN SESSION-----")
        return current_user 
    else:
        print("-----NOT IN SESSION-----")
        return False

#function to retrieve the previous posts in reverse order
def get_posts(author_id):
    if author_id.isdigit():
        return Post.query.filter_by(deleted=False, author_id=author_id).order_by(Post.id.desc())
    else:
        return Post.query.filter_by(deleted=False).order_by(Post.id.desc())

#function to retrieve the previous posts in reverse order
def get_authors():
    return User.query.order_by(User.id).all()


#function to require login, prevent navigation if already logged in
@app.before_request
def logged_in():

    print("-----BEFORE REQUEST-----")
    allowed_routes = ['login', 'signup', 'index', 'authors']

    if request.endpoint not in allowed_routes and 'email' not in session and '/static/' not in request.path:
        flash("Login or Signup required.", "error")
        return redirect('/login')

    if request.endpoint in allowed_routes[0:2] and 'email' in session:
        flash("Already logged in!", "error")
    #     return redirect('/')
    
#function to log a user in
@app.route("/login", methods=['POST', 'GET'])
def login():

    if request.method == 'POST':
        login_email = request.form['user_login']
        login_pass = request.form['user_pass']

        user = User.query.filter_by(db_email=login_email).first()
        
        if user and check_pw_hash(login_pass, user.db_password):
            session['email'] = login_email
            flash("Welcome {0}, you are logged in.".format(user.db_nickname), "greenlight")
            return redirect("/")
        elif not user:
            flash("User not found.", "error")
        else:
            flash("Incorrect password.", "error")

    return render_template('login.html')

#function to validate new user input
def validated(email, pass1, pass2, nick):

    if email == "" or pass1 == "":
        flash("Please enter an email/password.", "error")
        return False

    if "@" not in list(email) or "." not in list(email):
        flash("Invalid email.", "error")
        return False

    if len(pass1) < 4 or len(pass1) > 20:
        flash("Password must be between 4 and 20 characters.", "error")
        return False

    if pass1 != pass2:
        flash("Passwords do not match.", "error")
        return False
        
    return True

#function to add a new user (signup)
@app.route("/signup", methods=['POST', 'GET'])
def signup():

    if request.method == 'POST':
        reg_email = request.form['new_user']
        reg_password = request.form['new_pass']
        verify = request.form['new_pass_2']
        reg_nick = request.form['new_nick']
    
        if validated(reg_email, reg_password, verify, reg_nick):
            exist_user = User.query.filter_by(db_email=reg_email).first()
            if not exist_user:
                user = User(reg_email, reg_password, reg_nick)
                db.session.add(user)
                db.session.commit()
                session['email'] = reg_email
                flash("New user account created for {0}".format(reg_email), "greenlight")
                return redirect('/')
            else:
                flash("User already exists.", "error")
        
    return render_template('signup.html')

#function to logout
@app.route('/logout')
def logout():
    if 'email' in session:
        flash("User succesfully logged out.", "greenlight")
        del session['email']
        return redirect('/')

#function to "delete" a post

"""
TODO: Fix delete to ONLY delete post if current user is owner
"""

@app.route("/del-post", methods=['POST'])
def del_post():
    post_id = request.form['post_id']
       
    deleted_post = Post.query.get(post_id)

    deleted_post.deleted = True
    db.session.add(deleted_post)
    db.session.commit()
    
    return redirect("/")

#function for rendering a post on its own page
@app.route("/post")
def single_post():
    post_id = request.args.get("id")

    display_post = Post.query.filter_by(id=post_id).first()

    if display_post not in get_posts("").all():
        flash("Post ID '{0}' does not exist. ".format(post_id), "error")
        return redirect("/")

    return render_template('singlepost.html', post=display_post)

#function for rendering the "new post" page
@app.route("/new-post")
def new_post():
    return render_template('newpost.html')

#function to add a new post to the db
@app.route("/add-post", methods=['GET', 'POST'])
def add_post():
    no_error = True
    author = User.query.filter_by(db_email=session['email']).first()

    if request.method == "POST":
        new_title = request.form['title']
        new_body = request.form['body']
    
    if new_title == "":
        flash("Please add a title. ", "error")
        no_error = False
    
    if new_body == "":
        flash("Cannot submit an empty post. ", "error")
        no_error = False

    if no_error:
        new_post = Post(new_title, new_body, get_date(), author)

        fetch_user = User.query.filter_by(db_email=session['email']).first()
        fetch_user.db_postcount += 1
                
        db.session.add(new_post)
        db.session.add(fetch_user)
        db.session.commit()

        fetch_post = Post.query.filter_by(db_title=new_title).first()
        return redirect("/post?id="+str(fetch_post.id))
    
    else:
        return render_template('newpost.html', post_title=new_title, post_body=new_body)

#return a list of authors
@app.route("/authors")
def authors():
    
    return render_template('authors.html', author_list=get_authors())

#return posts authored by the logged-in user
@app.route("/selfpost")
def self_post():
    self_author = User.query.filter_by(db_email=session['email']).first()
    return redirect("/blog?id="+str(self_author.id))

#return posts by a specific author
@app.route("/blog")
def author_posts():
    
    by_author = request.args.get("id")
    blog_author = User.query.get(by_author)

    if blog_author not in get_authors():
        flash("Author ID '{0}' does not exist. ".format(by_author), "error")
        return redirect("/")

    return render_template('posts.html', post_list=get_posts(by_author).all(), author=blog_author)

def get_title():
    title = request.endpoint
    print(title)
    if title not in ["login", "signup", "authors"]:
        title = ""
    else:
        title = "- "+title
    return title

#set a new color in session when color palette selected
@app.route("/color")
def set_color():

    color = request.args.get("color")

    if color in ["red", "blue", "green", "purple"]:
        session['color'] = color
    else: session['color'] = "red"
    return redirect(request.referrer or '/')

#sets default color to red, checks session for changes
def get_color():
    if 'color' in session:
        return session['color']
    else:
        return "red"

#common template handlers
@app.context_processor
def template_fillers():
    return dict(palette=get_color(), loggedin=in_session(), title=get_title())

#return all blog posts
@app.route("/")
def index():

    page = request.args.get('page', 1, type=int)
    posts = get_posts("").paginate(page, 4, False)
    if posts.has_next:
        next_url = page=posts.next_num
    else: next_url = ""
    if posts.has_prev:
        prev_url = page=posts.prev_num
    else: prev_url = ""

    return render_template('posts.html', post_list=posts.items, next_url=next_url, prev_url=prev_url)

if __name__ == "__main__":
    app.run()