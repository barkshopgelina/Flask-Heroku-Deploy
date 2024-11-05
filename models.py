# models.py

class User:
    def __init__(self, username, email):
        self.username = username
        self.email = email

class Admin(User):
    def __init__(self, username, email):
        super().__init__(username, email)
        self.admin_level = 'superuser'
