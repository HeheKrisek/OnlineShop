from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, FloatField, IntegerField
from wtforms.validators import DataRequired, URL, Email, NumberRange
from wtforms_validators import AlphaSpace
from flask_ckeditor import CKEditorField


class AddProductForm(FlaskForm):
    name = StringField("Product name", validators=[DataRequired()])
    category = StringField("Product category", validators=[DataRequired()])
    description = CKEditorField("Description of the product", validators=[DataRequired()])
    price = FloatField("Product price", validators=[DataRequired()])
    img_url = StringField("Product Image URL", validators=[DataRequired(), URL()])
    submit = SubmitField("Add this product")


class RegisterForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class ReviewForm(FlaskForm):
    content = CKEditorField("Your review:", validators=[DataRequired()])
    submit = SubmitField("Submit")


class AddToCart(FlaskForm):
    quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(1, 20)], default=1)
    submit = SubmitField("Add to cart")


# not used

# class UpdateQuantity(FlaskForm):
#     quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(1, 20)], default=1)
#     submit = SubmitField("Update quantity")


class SearchForm(FlaskForm):
    searched = StringField("Search for a product", validators=[DataRequired()])
    submit = SubmitField("Search")


class ShippingForm(FlaskForm):
    country = StringField("Country", validators=[DataRequired(), AlphaSpace()])
    full_name = StringField("Full name", validators=[DataRequired(), AlphaSpace()])
    address1 = StringField("Address line 1", validators=[DataRequired()])
    address2 = StringField("Address line 2 (optional)")
    postal_code = IntegerField("Postal code", validators=[DataRequired()])
    city = StringField("City", validators=[DataRequired(), AlphaSpace()])
    phone = IntegerField("Phone number", validators=[DataRequired()])
    submit = SubmitField("Place the order")