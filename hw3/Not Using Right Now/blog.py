import os
import re 
from string import letters

import webapp2
import jinja2

from google.appengine.ext import db

# The hash secret for cookies. Stored in this file for learning purposes.
secret = "OMG,_I'm_actually_programming!"

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)
    
def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

def make_secure_val(val):
    return "%s|%s" % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

#Sets a hashed cookie of the name and value entered.
def set_secure_cookie(self,name,val):
    cookie_val = make_secure_val(val)
    self.response.headers.add_header('Set-Cookie','%s=%s; Path=/' % (name, cookie_val))
    
def read_secure_cookie(self, name):
    cookie_val = self.request.cookies.get(name)
    return cookie_val and check_secure_val(cookie_val)

#Sets the cookie.
def login(self, user):
    self.set_secure_cookie('user_id', str(user.key().id()))

#Resets the cookie's value to null values.
def logout(self):
    self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

#Whenever the webapp launches, check to see if there are any user_id 
def initialize(self, *a, **kw):
    webapp2.RequestHandler.initialize(self, *a, **kw)
    uid = self.read_secure_cookie('user_id')
    self.user = uid and User.by_id(int(uid))
    

def make_pw_hash(name, user, salt=None):
    if not salt:
        salt = make_salt()
        h = hashlib.sha256(name+user+salt).hexdigest()
    return '%s, %s' % (salt, h)

def valid_pw(name, password, h):
    salt = h.split (',')[0]
    return h == make_pw_hash(name, password, salt)



def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

def render_post(response, post):
    response.out.write('<b>' + post.subject + '</b><br>')
    response.out.write(post.content)

class MainPage(BlogHandler):
  def get(self):
      self.write('Hello, Udacity!')

##### blog stuff

def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self)

class BlogFront(BlogHandler):
    def get(self):
        posts = db.GqlQuery("select * from Post order by created desc limit 10")
        self.render('front.html', posts = posts)

class PostPage(BlogHandler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        self.render("permalink.html", post = post)

class NewPost(BlogHandler):
    def get(self):
        self.render("newpost.html")

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            p = Post(parent = blog_key(), subject = subject, content = content)
            p.put()
            self.redirect('/blog/%s' % str(p.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content, error=error)

class Register(Signup):
    def done(self):
        #make sure the user doesn't already exist
        u = User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('signup-form.html', error_username = msg(
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()
                
            self.login(u)
            self.redirect('/unit2/welcome')

class User(db.Model):
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()
    
    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key())

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get()
        return u
        
# Takes a name, password and email, and creates a new user object. ((What is its name?))
    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return User(parent = users_key(),
                    name = name,
                    pw_hash = pw_hash,
                    email = email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u



###### Unit 2 HW's
class Rot13(BlogHandler):
    def get(self):
        self.render('rot13-form.html')

    def post(self):
        rot13 = ''
        text = self.request.get('text')
        if text:
            rot13 = text.encode('rot13')

        self.render('rot13-form.html', text = rot13)


USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

class Signup(BlogHandler):


   # def valid_pw(name+pw+salt).hexdigest():
    #    salt = h.split(',')[1]
   #     return h == make_pw_hash(name, pw, salt)

    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        username = self.request.get('username')
     #   name = self.request.cookies.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        params = dict(username = username,
                      email = email)

        if not valid_username(username):
            params['error_username'] = "That's not a valid username."
            have_error = True
        if self.request.cookies.get('nameu')==username:
            params['error_username'] = "That user already exists."
            have_error = True
        if not valid_password(password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif password != verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
             
        else:
            self.done()
    
            
    def done(self, *a, **kw):
        raise NotImplementedError
        

            
        #Self.done()... Look up explanation.

          #  nameu = str(username)
          #  h = make_username_hash(nameu
            username = str(username)
            self.response.headers.add_header("Set-Cookie", "nameu="+username+"; Path = /")
          #  self.write(username)
            self.redirect('/unit2/welcome')


class Welcome(BlogHandler):
    def get(self):
        if self.user:
            self.render('welcome.html', username = self.user.name)
        else:
            self.redirect('/unit2/signup')
          #  username = self.request.cookies.get('nameu')
      #  username = self.request.cookies.get('nameu')
       # self.write(username)
        if valid_username(username):
            self.render('welcome.html', username = self.request.cookies.get('nameu'))
        else:
            self.redirect('/unit2/signup')

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/unit2/rot13', Rot13),
                               ('/unit2/signup', Signup),
                               ('/unit2/welcome', Welcome),
                               ('/blog/?', BlogFront),
                               ('/blog/([0-9]+)', PostPage),
                               ('/blog/newpost', NewPost),
                               ],
                              debug=True)
