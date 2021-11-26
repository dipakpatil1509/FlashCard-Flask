from flask import Blueprint, request, url_for, redirect, render_template, flash
from flask_login.utils import login_required, logout_user
from application.database import db
from application.models.user_mode import User
from flask_login import login_user
from werkzeug.security import generate_password_hash, check_password_hash

from flask_restful import abort
import email_validator

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template('Security/login_user.html')
    elif request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('pass')
        remember = request.form.get('remember')

        if remember is not None:
            remember = True
        
        try:
            valid = email_validator.validate_email(email)
            if valid:
                email = valid.email
                user = db.session.query(User).filter(User.email == email).first()
                if user:
                    if check_password_hash(user.password, password):
                        login_user(user, remember=remember)
                        return redirect(url_for('profile.home'))
                    else:
                        flash('Please check your login details and try again.')
                        return redirect(url_for('auth.login'))
                else:
                    new_user = User(
                        email=email,
                        password=generate_password_hash(password, method='sha256'),
                    )

                    db.session.add(new_user)

                    db.session.commit()

                    login_user(new_user, remember=remember)
                    return redirect(url_for('profile.profileFunc', isUpdate="1"))
        except Exception as e:
            flash(str(e))
            db.session.rollback()

        return redirect(url_for('auth.login'))
    else:
        abort(405, "The method is not allowed for the requested URL.")


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))