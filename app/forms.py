from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateTimeField, DateField, IntegerField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from app.models import Users

class LoginForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(),
                            Length(min=5, max=64, message='Name length must be between %(min)d and %(max)dcharacters')])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(),
                                       Length(min=5, max=64, message='Name length must be between %(min)d and %(max)d characters')])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = Users.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = Users.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class SearchUserForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(),
                                       Length(min=5, max=64, message='Name length must be between %(min)d and %(max)d characters')])


class EditProfileForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])

class AddTaskForm(FlaskForm):
    type_task = IntegerField('Type task')
    title = StringField('Title',
                        validators=[DataRequired(),
                                    Length(min=5, max=64, message='Name length must be between %(min)d and %(max)dcharacters')])
    priority = IntegerField('Priority')
    complexity = IntegerField('Complexity')
    #format='%Y-%m-%d %H:%M:%S'
    deadline = DateField('Deadline', format='%Y-%m-%d')
    description = TextAreaField('Description', validators=[DataRequired(),
                                                         Length(min=5, max=1024, message='Name length must be between %(min)d and %(max)d characters')])

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')

class ShowTaskForm(FlaskForm):
    title = StringField('Title',
                        validators=[DataRequired(),
                                    Length(min=5, max=64,
                                           message='Name length must be between %(min)d and %(max)dcharacters')])
    status = StringField('Status')
    description = TextAreaField('Description', validators=[DataRequired(),
                                                           Length(min=5, max=1024,
                                                                  message='Name length must be between %(min)d and %(max)d characters')])
    user = StringField('Performer')
    priority = StringField('Priority')
    complexity = StringField('Complexity')
    deadline = DateField('Deadline', format='%Y-%m-%d')
    submit = SubmitField('Save')