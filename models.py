from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, inspect, Column, String
from sqlalchemy.exc import OperationalError

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    company = db.Column(db.String(150))
    pre_signup = db.Column(db.String(50))
    interest = db.Column(db.String(50))
    message = db.Column(db.Text)
    totp_secret = db.Column(db.String(150))
    org = db.Column(db.String(150))

    def set_password(self, password):
        if password is not None:
            self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if password is not None:
            return check_password_hash(self.password_hash, password)
        

def add_missing_column(engine, table_name, column_name, column_type):
    with engine.connect() as conn:
        # Check if the column already exists
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        if column_name not in columns:
            # Add the new column
            conn.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}')
            print(f'Column {column_name} added to {table_name}')
        else:
            print(f'Column {column_name} already exists in {table_name}')


def add_user(name, email, phone, company, pre_signup, interest, message,org):
    try:
        new_user = User(name=name, email=email, phone=phone, \
                        company=company, pre_signup=pre_signup, \
                        interest=interest, message=message, org=org)
        db.session.add(new_user)
        db.session.commit()
    except OperationalError as e:
        # Extract the missing column from the error message
        missing_column = str(e).split(":")[-1].strip().split(" ")[-1]
        if 'no such column' in str(e):
            add_missing_column(db.engine, 'user', missing_column, 'TEXT')
            add_user(name, email, phone, company, pre_signup, interest, message,org)  # Try to add the user again
        else:
            raise e
        

    @property
    def is_active(self):
        # You can implement more complex logic here, if needed.
        return True