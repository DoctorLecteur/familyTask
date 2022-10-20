from app import photos
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateTimeField, DateField, IntegerField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, NumberRange
from app.models import Users
from flask_babel import _, lazy_gettext as _l

class LoginForm(FlaskForm):
    username = StringField(_l('Username'),
                           validators=[DataRequired(),
                            Length(min=5, max=64, message=_l('Name length must be between %(min)d and %(max)d characters', min=5, max=64))])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember me'))
    submit = SubmitField(_l('Sign In'))

class RegistrationForm(FlaskForm):
    username = StringField(_l('Username'),
                           validators=[DataRequired(),
                                       Length(min=5, max=64, message=_l('Name length must be between %(min)d and %(max)d characters', min=5, max=64))])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Register'))

    def validate_username(self, username):
        user = Users.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_('Please use a different username.'))

    def validate_email(self, email):
        user = Users.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_('Please use a different email address.'))

class SearchUserForm(FlaskForm):
    username = StringField(_l('Username'),
                           validators=[DataRequired(),
                                       Length(min=5, max=64, message=_l('Name length must be between %(min)d and %(max)d characters', min=5, max=64))])


class EditProfileForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])

class AddTaskForm(FlaskForm):
    type_task = IntegerField(_l('Type task'))
    period_count = IntegerField(_l('Period Count'), validators=[NumberRange(min=1)])
    period_time = StringField(_l('Period Time'))
    title = StringField(_l('Title'),
                        validators=[DataRequired(),
                                    Length(min=5, max=64, message=_l('Name length must be between %(min)d and %(max)dcharacters', min=5, max=64))])
    priority = IntegerField(_l('Priority'))
    complexity = IntegerField(_l('Complexity'))
    category = IntegerField(_l('Category'))
    deadline = DateField(_l('Deadline'), format='%Y-%m-%d')
    description = TextAreaField(_l('Description'))

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')

class ShowTaskForm(FlaskForm):
    title = StringField(_l('Title'),
                        validators=[DataRequired(),
                                    Length(min=5, max=64,
                                           message=_l('Name length must be between %(min)d and %(max)dcharacters', min=5, max=64))])
    type_task = StringField(_l('Type task'))
    period_count = IntegerField(_l('Period Count'), validators=[NumberRange(min=1)])
    period_time = StringField(_l('Period Time'))
    status = StringField(_l('Status'))
    description = TextAreaField(_l('Description'))
    user = StringField(_l('Performer'))
    priority = StringField(_l('Priority'))
    complexity = StringField(_l('Complexity'))
    category = StringField(_l('Category'))
    deadline = DateField(_l('Deadline'), format='%Y-%m-%d')
    submit = SubmitField(_l('Save'))

class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Request Password Reset'))

class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(_l('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Request Password Reset'))

class UploadForm(FlaskForm):
    photo = FileField(validators=[FileAllowed(photos, 'Images'), FileRequired('File')])
    submit = SubmitField(_l('Upload'))