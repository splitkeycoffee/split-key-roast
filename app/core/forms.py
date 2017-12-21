"""Various forms used within the application."""
from wtforms import (
    Form, StringField, PasswordField, validators, SelectMultipleField,
    BooleanField
)


class LoginForm(Form):

    """Login form validator."""

    username = StringField('username', [validators.Length(min=6, max=35)])
    password = PasswordField('password', [validators.DataRequired()])


class RegisterForm(Form):

    """Register form."""

    username = StringField('username', [validators.Length(min=6, max=35)])
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
    organic = StringField('organic', [validators.Length(min=1, max=35)])
    fair_trade = StringField('fair_trade', [validators.Length(min=1, max=35)])


class ProfileForm(Form):

    """Profile form validator."""

    coffee = StringField('coffee', [validators.Length(min=1, max=35)])
    roast = StringField('roast', [validators.Length(min=1, max=35)])
    drop_temp = StringField('drop_temp', [validators.Length(min=1, max=35)])
    notes = StringField('notes', [validators.Length(min=0, max=255)])
    choices = [('pour_over', 'pour_over'), ('french_press', 'french_press'),
               ('espresso', 'espresso'), ('siphon', 'siphon'),
               ('cold_brew', 'cold_brew')]
    brew_methods = SelectMultipleField(choices=choices)


class IntegrationTwitterbot(Form):

    """Integration Twitter Bot form validator."""

    status = BooleanField('status')
    consumer_key = StringField('consumer_key', [validators.required()])
    consumer_secret = StringField('consumer_secret', [validators.required()])
    access_token_key = StringField('access_token_key', [validators.required()])
    access_token_secret = StringField('access_token_secret', [validators.required()])
    tweet_roast_begin = BooleanField('tweet_roast_begin', default=False)
    tweet_roast_progress = BooleanField('tweet_roast_progress', default=False)
    tweet_roast_complete = BooleanField('tweet_roast_complete', default=False)


class BrewForm(Form):

    """Brew form validator."""

    roast_id = StringField('roast_id', [validators.required()])
    brew_method = StringField('brew_method', [validators.required()])
    input_weight = StringField('input_weight', [validators.required()])
    output_weight = StringField('output_weight', [validators.required()])
    brew_time = StringField('brew_time', [validators.required()])
    dry_smell = StringField('dry_smell', [validators.required()])
    grind_smell = StringField('grind_smell', [validators.required()])
    wet_smell = StringField('wet_smell', [validators.required()])
    tasting_notes = StringField('tasting_notes', [validators.required()])
