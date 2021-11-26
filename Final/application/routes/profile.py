from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask.helpers import flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from application.models.response_mode import ReviewCard
from application.models.response_mode import ReviewResponse
from application.models.user_mode import User
from application.models.deck import Deck, Card
from application.database import db
from sqlalchemy.sql import func

profile = Blueprint('profile', __name__)

@profile.route('/')
@login_required
def home():
    
    isForm = request.args.get('isForm')
    flag = request.args.get('flag')
    decks = []
    
    try:
        if flag is None or flag == "0":
            decks = db.session.query(Deck).filter(Deck.public_status == True).all()
        elif flag == "1":
            decks = db.session.query(Deck).filter(Deck.public_status == True).filter(Deck.created_for.in_(i for i in Deck.Type if i.value == current_user.role.value)).all()
        elif flag == "2":
            decks = current_user.decks.all()
        elif flag == "3":
            decks = current_user.decks.filter(Deck.public_status == False).all()
        
        for i, item in enumerate(decks):
            decks[i].user = db.session.query(User).with_entities(User.name).filter(User.id == item.created_by_id).first()
            decks[i].number_of_cards = item.cards.count()
    except Exception as e:
        print(str(e))
        flash(str(e), "toast")
        decks = []

    return render_template('Deck/Deck.html', user=current_user, decks=decks, flag=flag, isForm=isForm)

@profile.route('/profile')
@login_required
def profileFunc():
    isUpdate = request.args.get('isUpdate')
    all = current_user.reviewResponses.order_by(ReviewResponse.completed_at).all()
    final = None
    final_cards= []
    remain = []

    if all:
        final = all[-1]
        final_cards = final.cards.with_entities(ReviewCard.difficulty, func.count(ReviewCard.difficulty)).group_by(ReviewCard.difficulty).all()
        final.deck = db.session.query(Deck).filter(Deck.id==final.deck_id).first()

        all.reverse()

        if len(all) > 1:
            remain = all[1:]
            
            for i,item in enumerate(remain):
                remain[i].deck = db.session.query(Deck).filter(Deck.id == item.deck_id).first()

    return render_template('Dashboard/Profile.html', user=current_user, isUpdate=isUpdate, final=final, final_cards=final_cards, decks=remain)


@profile.route('/profile/update', methods=['POST'])
@login_required
def profileUpdate():
    user = db.session.query(User).filter(User.id == current_user.id).first()
    name = request.form.get('name')
    if name:
        user.name = name
    
    
    role = request.form.get('role')
    if role:
        user.role = role
    
    currentPassword = request.form.get('currentPassword')
    if currentPassword:
        if check_password_hash(user.password, currentPassword):
            newPassword = request.form.get('newPassword')
            confirmNewPassword = request.form.get('confirmNewPassword')
            if newPassword != confirmNewPassword:
                flash('Passwords not matching', 'error')
                return redirect(url_for('profile.profileFunc', isUpdate="1"))
            
            user.password = generate_password_hash(newPassword, method='sha256')
        else:
            flash('Current password is wrong', 'error')
            return redirect(url_for('profile.profileFunc', isUpdate="1"))

    try:
        db.session.add(user)
        db.session.commit()
        flash("Profile Updated Successfully", 'toast')
        return redirect(url_for('profile.profileFunc'))
    except Exception as e:
        db.session.rollback()
        flash(str(e))
        return redirect(url_for('profile.profileFunc', isUpdate="1"))
    


@profile.route('/get_score', methods=['GET'])
@login_required
def get_score():
    user_id = request.args.get('user_id')
    user_score = db.session.query(User).with_entities(User.review_response()).filter(User.id == int(user_id)).first()
    if user_score:
        return jsonify({
            "user_score":user_score,
        })
    return jsonify({
        "error":"User Exist"
    })
