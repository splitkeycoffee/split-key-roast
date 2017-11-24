from wtforms import Form, StringField, PasswordField, IntegerField, validators


class LoginForm(Form):
    """Login form validator."""
    email = StringField('email', [validators.Length(min=6, max=35)])
    password = PasswordField('password', [validators.DataRequired()])


class RegisterForm(Form):
    """Register form."""
    email = StringField('email', [validators.Length(min=6, max=35)])
    first_name = StringField('first_name', [validators.Length(min=1, max=35)])
    last_name = StringField('last_name', [validators.Length(min=1, max=35)])
    password = PasswordField('password', [
        validators.DataRequired(),
        validators.EqualTo('password_confirm', message='Passwords must match')
    ])
    password_confirm = PasswordField('password_confirm')


class ChangePasswordForm(Form):
    """Change password form."""
    password = PasswordField('password', [
        validators.DataRequired(),
        validators.EqualTo('password_confirm', message='Passwords must match')
    ])
    password_confirm = PasswordField('password_confirm')
    user_id = StringField('user_id', [validators.Length(min=1, max=35)])


class AccountSettingsForm(Form):
    """Account settings form."""
    email = StringField('email', [validators.Length(min=6, max=35)])
    first_name = StringField('first_name', [validators.Length(min=1, max=35)])
    last_name = StringField('last_name', [validators.Length(min=1, max=35)])
    user_id = StringField('user_id', [validators.Length(min=1, max=35)])


class InventoryForm(Form):
    """Inventory form validator."""
    label = StringField('label', [validators.Length(min=1, max=35)])
    origin = StringField('origin', [validators.Length(min=1, max=35)])
    method = StringField('process', [validators.Length(min=1, max=35)])
    stock = StringField('stock', [validators.Length(min=1, max=35)])


class ProfileForm(Form):
    """Profile form validator."""
    coffee = StringField('coffee', [validators.Length(min=1, max=35)])
    roast = StringField('roast', [validators.Length(min=1, max=35)])
    drop_temp = StringField('drop_temp', [validators.Length(min=1, max=35)])
    notes = StringField('notes', [validators.Length(min=0, max=255)])