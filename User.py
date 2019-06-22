from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

salt = '$9abc'

class User(UserMixin):
    def __init__(self,id,password):
        UserMixin.__init__(self)
        self.id = id
        self.password_hash = password

    def check_password(self, password):
        return check_password_hash(self.password_hash,salt + password)


