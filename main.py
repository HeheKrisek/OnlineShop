from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_session import Session
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import RegisterForm, LoginForm, ReviewForm, AddProductForm, AddToCart, SearchForm, ShippingForm
from functools import wraps
from flask import abort
from flask_gravatar import Gravatar
import requests
import datetime

NAME="ExampleName"

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False, base_url=None)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# CONFIGURE TABLES

class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(250), unique=True, nullable=False)
    cat = db.Column(db.String(250), nullable=False)
    desc = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    reviews = relationship("Review", back_populates="parent_product")


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))

    reviews = relationship("Review", back_populates="review_author")
    orders = relationship("Order", back_populates="buyer")


class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    review_author = relationship("User", back_populates="reviews")
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    parent_product = relationship("Product", back_populates="reviews")
    text = db.Column(db.Text, nullable=False)


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    buyer = relationship("User", back_populates="orders")
    status = db.Column(db.String(20), nullable=False)
    date = db.Column(db.DateTime, nullable=False)

    country = db.Column(db.String(100), nullable=False)
    buyers_full_name = db.Column(db.String(100), nullable=False)
    buyers_address = db.Column(db.String(100), nullable=False)
    buyers_phone = db.Column(db.Integer, nullable=False)
    products_bought = db.Column(db.String(200), nullable=False)
    total_price = db.Column(db.Float, nullable=False)

# # used one time to create the database
# with app.app_context():
#     db.create_all()


login_manager = LoginManager()
login_manager.init_app(app)

admin_list = [1]


def is_admin():
    if current_user.is_authenticated and current_user.id in admin_list:
        return True
    else:
        return False


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            return abort(403)

        return f(*args, **kwargs)
    return decorated_function


def itemsincart():
    if session.get('cart'):
        itms = 0
        all_products_list = Product.query.order_by(Product.price).all()
        items = session.get('cart')
        for item in items:
            for key in item.keys():
                for product in all_products_list:
                    if key == product.name:
                        itms += item[key]

    else:
        itms = 0

    return itms


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    # print(current_user.id)
    best = Product.query.filter_by(id=1).first()
    return render_template("index.html", is_admin=is_admin(), itemsincart=itemsincart(), name=NAME, product=best)


@app.route('/about')
def about():
    return render_template("about.html", is_admin=is_admin(), itemsincart=itemsincart(), name=NAME)


@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)


@app.route('/search', methods=["POST"])
def search():
    all_products_list = Product.query
    form = SearchForm()
    if form.validate_on_submit():
        s = form.searched.data
        print(s)
        items = all_products_list.filter(Product.name.like('%' + s + '%')).order_by(Product.price).all()
        return render_template("search.html", is_admin=is_admin(), itemsincart=itemsincart(), name=NAME, form=form,
                                searched=s, items=items)

    else:
        return redirect(request.referrer)


@app.route('/contact')
def contact():
    return render_template("contact.html", is_admin=is_admin(), itemsincart=itemsincart(), name=NAME)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash("We cannot find an account with that email address.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, form.password.data):
            flash('Wrong password.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template('login.html', form=form, itemsincart=itemsincart(), name=NAME)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)

        return redirect(url_for("home"))

    return render_template("register.html", form=form, itemsincart=itemsincart(), name=NAME)


@app.route('/logout')
def logout():
    logout_user()
    if 'cart' in session:
        del session['cart']

    if 'total' in session:
        del session['total']

    return redirect(url_for('home'))


@app.route('/my_account')
def my_account():
    if not current_user.is_authenticated:
        return redirect(url_for('home'))

    return render_template("my_account.html", is_admin=is_admin(), itemsincart=itemsincart(), name=NAME)


@app.route('/allproducts')
def allproducts():
    all_products_list = Product.query.order_by(Product.price).all()
    return render_template("allproducts.html", list=all_products_list, itemsincart=itemsincart(), name=NAME)


@app.route('/allproductsd')
def allproductsd():
    all_products_list = Product.query.order_by(Product.price.desc()).all()
    return render_template("allproducts.html", list=all_products_list, itemsincart=itemsincart(), name=NAME)


@app.route('/add', methods=["GET", "POST"])
@admin_only
def add():
    form = AddProductForm()
    if form.validate_on_submit():
        if Product.query.filter_by(name=form.name.data).first():
            flash("This product is already for sale!")
            return redirect(url_for('add'))

        new_product = Product(
            name=form.name.data,
            cat=form.category.data,
            desc=form.description.data,
            price=form.price.data,
            img_url=form.img_url.data,
        )
        db.session.add(new_product)
        db.session.commit()

        flash("Product added successfully")
        return redirect(url_for("add"))

    return render_template('add.html', form=form, itemsincart=itemsincart(), name=NAME)


@app.route("/delete/<int:product_id>")
@admin_only
def delete_product(product_id):
    product_to_delete = Product.query.get(product_id)
    db.session.delete(product_to_delete)
    db.session.commit()
    return redirect(url_for('allproducts'))


@app.route("/product/<int:product_id>", methods=["GET", "POST"])
def product_page(product_id):
    form = ReviewForm()
    cart = AddToCart()
    requested_product = Product.query.get(product_id)
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        new_review = Review(
            text=form.content.data,
            review_author=current_user,
            parent_product=requested_product
        )
        db.session.add(new_review)
        db.session.commit()
        return redirect(request.referrer)

    if cart.validate_on_submit():
        if 'cart' in session:
            if not any(requested_product.name in d for d in session['cart']):
                session['cart'].append({requested_product.name: cart.quantity.data})

            elif any(requested_product.name in d for d in session['cart']):
                for d in session['cart']:
                    d.update((k, v+cart.quantity.data) for k, v in d.items() if k == requested_product.name)

        else:
            session['cart'] = [{requested_product.name: cart.quantity.data}]

        print(session.get('cart'))
        return redirect(request.referrer)

    return render_template("product.html", product=requested_product, form=form, cart=cart, is_admin=is_admin(), itemsincart=itemsincart(), name=NAME)


@app.route('/delete_review', methods=["GET", "POST"])
def delete_review():
    review_id = request.args.get('id')
    review_to_delete = Review.query.get(review_id)
    db.session.delete(review_to_delete)
    db.session.commit()
    return redirect(request.referrer)


@app.route("/delete_acc", methods=["GET", "POST"])
def del_acc():
    if 'cart' in session:
        del session['cart']

    if 'total' in session:
        del session['total']
    acc_id = request.args.get('acc_id')
    account_to_delete = User.query.get(acc_id)
    db.session.delete(account_to_delete)
    db.session.commit()
    return redirect(url_for("login"))


@app.route('/empty_cart', methods=["GET", "POST"])
def empty_cart():
    del session['cart']
    return redirect(request.referrer)


@app.route('/checkout', methods=["GET", "POST"])
def checkout():
    form = ShippingForm()

    if form.validate_on_submit():
        items = session.get('cart')
        all_products_list = Product.query.order_by(Product.price).all()
        p_list = []
        q_list = []
        products_bought = ""
        if items:
            for item in items:
                for key in item.keys():
                    p_list.append(key)
                    for product in all_products_list:
                        if product.name == key:
                            q_list += f"{item[key]}"

        print(p_list)
        for i in range (0, len(q_list)):
            products_bought += p_list[i]
            products_bought += " x "
            products_bought += q_list[i]
            if i < len(q_list) - 1:
                products_bought += ", "

        new_order = Order(
            buyer=current_user,
            status="received",
            date=func.now(),
            country=form.country.data,
            buyers_full_name=form.full_name.data,
            buyers_address=f"{form.address1.data}, {form.address2.data}, {form.postal_code.data}",
            buyers_phone=form.phone.data,
            products_bought=products_bought,
            total_price=session['total'],
        )
        db.session.add(new_order)
        db.session.commit()

        del session['cart']
        del session['total']

        return redirect((url_for('thankyou')))

    return render_template("checkout.html", form=form, is_admin=is_admin(), itemsincart=itemsincart(), name=NAME)


@app.route('/basket', methods=["GET", "POST"])
def basket():
    all_products_list = Product.query.order_by(Product.price).all()
    print(all_products_list)
    items = session.get('cart')
    total = 0
    if items:
        for item in items:
            for key in item.keys():
                for product in all_products_list:
                    if key == product.name:
                        total += product.price * item[key]
                        total = round(total, 2)
                        session['total'] = total

    return render_template("basket.html", items=items, total=total, list=all_products_list, itemsincart=itemsincart(), name=NAME)


@app.route('/thankyou', methods=["GET", "POST"])
def thankyou():

    return render_template("thankyou.html", itemsincart=itemsincart(), name=NAME)


@app.route('/my_orders', methods=["GET", "POST"])
def my_orders():
    if not current_user.is_authenticated:
        return redirect(url_for('home'))

    myorders = Order.query.filter_by(buyer_id=current_user.id).all()

    return render_template("my_orders.html", itemsincart=itemsincart(), name=NAME, orders=myorders)


if __name__ == "__main__":
    app.run(debug=True)