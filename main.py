from flask import Flask, request, redirect, render_template, flash
from flask_sqlalchemy import SQLAlchemy
import datetime

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://build-a-blog:blogtownusa@localhost:8889/build-a-blog"
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)
app.secret_key = '44jjsslgqtg6s'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    db_title = db.Column(db.String(120))
    db_body = db.Column(db.String(10000))
    db_date = db.Column(db.String(120))
    deleted = db.Column(db.Boolean)

    def __init__(self, title, body, date):
        self.db_title = title
        self.db_body = body
        self.db_date = date
        self.deleted = False
    
    def __repr__(self):
        return "<Post %r>" % self.db_title

#function to retrieve the previous posts in reverse order
def get_posts():
    return Post.query.filter_by(deleted=False).order_by(Post.id.desc()).all()

#function to "delete" a post
@app.route("/del-post", methods=['POST'])
def del_post():
    post_id = request.form['post_id']
    print(post_id)
    
    deleted_post = Post.query.get(post_id)
    print(deleted_post)
    deleted_post.deleted = True
    db.session.add(deleted_post)
    db.session.commit()

    return redirect("/")

#function for rendering a post on its own page
@app.route("/post")
def single_post():
    post_id = request.args.get("id")
    display_post = Post.query.filter_by(id=post_id).first()

    if display_post not in get_posts():
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

    if request.method == "POST":
        new_title = request.form['title']
        new_body = request.form['body']

        """
        TODO: validate incoming data
        TODO: better error-handling with flash messages?

        """
    
    if new_title == "":
        flash("Please add a title. ", "error")
        no_error = False
    
    if new_body == "":
        flash("Cannot submit an empty post. ", "error")
        no_error = False

    if no_error:
        new_post = Post(new_title, new_body, get_date())

        db.session.add(new_post)
        db.session.commit()
        fetch_post = Post.query.filter_by(db_title=new_title).first()
        return redirect("/post?id="+str(fetch_post.id))
    
    else:
        return render_template('newpost.html',post_title=new_title, post_body=new_body)

def get_date():
    postdate = datetime.datetime.now()
    at_date = postdate.strftime("%b %d %Y")
    at_time = postdate.strftime("%I:%M %p")
    return at_time+" | "+at_date

@app.route("/")
def index():

    """
    TODO: Add some CSS styling
    """

    return render_template('posts.html', post_list=get_posts())

if __name__ == "__main__":
    app.run()