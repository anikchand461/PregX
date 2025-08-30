from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    user_type = SelectField('User Type', choices=[('patient', 'Patient'), ('driver', 'Driver')], validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is taken.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class BookAmbulanceForm(FlaskForm):
    patient_lat = FloatField('Your Latitude', validators=[Optional()])
    patient_lng = FloatField('Your Longitude', validators=[Optional()])
    submit = SubmitField('Book')

    def validate(self, extra_validators=None):
        if not super().validate():
            return False
        if not self.patient_lat.data or not self.patient_lng.data:
            raise ValidationError('Latitude and longitude must be provided, either manually or via geolocation.')
        return True

class UpdateLocationForm(FlaskForm):
    lat = FloatField('Current Latitude', validators=[Optional()])
    lng = FloatField('Current Longitude', validators=[Optional()])
    submit = SubmitField('Update Location')

    def validate(self, extra_validators=None):
        if not super().validate():
            return False
        if not self.lat.data or not self.lng.data:
            raise ValidationError('Latitude and longitude must be provided, either manually or via geolocation.')
        return True