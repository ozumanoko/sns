from sqlalchemy.orm import synonym
from werkzeug.security import check_password_hash, generate_password_hash

from baboo import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default='', nullable=False)
    #email = db.Column(db.String(100), unique=True, nullable=False)
    _password = db.Column('password', db.String(100), nullable=False)

    def _get_password(self):
        return self._password
    def _set_password(self, password):
        if password:
            password = password.strip()
        self._password = generate_password_hash(password)
    password_descriptor = property(_get_password, _set_password)
    password = synonym('_password', descriptor=password_descriptor)

    def check_password(self, password):
        password = password.strip()
        if not password:
            return False
        return check_password_hash(self.password, password)

    @classmethod
    def authenticate(cls, query, name, password):
        user = query(cls).filter(cls.name==name).first()
        if user is None:
            return None, False
        return user, user.check_password(password)

    def __repr__(self):
        return u'<User id={self.id} name={self.name}>'.format(
            self=self
        )

class Post_Data(db.Model):
    __tablename__ = 'postdata'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    name = db.Column(db.String(100), default='', nullable=False)
    text = db.Column(db.Text)

    def __repr__(self):
        return '<post_date id={self.id}>'.format(
            self=self
        )

class Follow(db.Model):
    __tablename__ = 'follow'

    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer)
    follow_id = db.Column(db.Integer)

    def __repr__(self):
        return '<follow id={self.id}>'.format(
            self=self
        )

def init():
    db.create_all()