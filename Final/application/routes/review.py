from datetime import datetime
from pytz import timezone
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
from flask_restful import  reqparse
from flask.helpers import flash
from flask_login import login_required, current_user
from application.error import APIException
from application.database import db
from application.models.deck import Card
from application.models.response_mode import ReviewCard, ReviewResponse
from application.routes.deck import get_all_cards as deck_get_all_cards, get as deck_get
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func

review = Blueprint('review', __name__)


review_req = reqparse.RequestParser()
review_req.add_argument("difficulty")
review_req.add_argument("next")
review_req.add_argument("response_id")

@review.route('/start_test/<int:deck_id>', methods=["GET"])
@login_required
def review_form(deck_id):
    deck = None
    card = None
    isFinish = False
    next_card = request.args.get('next_card') 
    final_cards = []
    final = {}
    if not next_card:
        next_card = 0
    else:
        next_card = int(next_card)
    try:
        
        deck=deck_get(deck_id)
        cards = deck_get_all_cards(deck_id)

        try:
            response_curr = db.session.query(ReviewResponse).filter(ReviewResponse.user_id == current_user.id).filter(ReviewResponse.deck_id == int(deck_id)).first()
            if response_curr:
                if response_curr.cards.count() == len(cards):
                    isFinish = True
                    final = response_curr
                    final_cards = response_curr.cards.with_entities(ReviewCard.difficulty, func.count(ReviewCard.difficulty)).group_by(ReviewCard.difficulty).all()
                    print(final_cards)
                else:
                    session['review_respose_id'] = response_curr.id

            else:
                new_response = ReviewResponse(
                    score = 0,
                    avg_time = 0,
                    user_id = int(current_user.id),
                    deck_id = int(deck_id),
                )
                db.session.add(new_response)
                db.session.commit()
                session['review_respose_id'] = new_response.id

        except Exception as e:
            flash(str(e), 'toast')

        if next_card + 1 > len(cards):
            isFinish = True
        else:
            card = cards[next_card]
            card['next'] = next_card + 1
        
        
    except Exception as e:
        print(str(e))
        flash(str(e), 'toast')

    return render_template("Review/Review.html", user=current_user, deck=deck, card=card, isFinish=isFinish, final=final, final_cards=final_cards)


@review.route('/next_test/<int:deck_id>', methods=["POST"])
@login_required
def review_form_post(deck_id):
    
    if request.method == "POST":
        try:
            
            args = review_req.parse_args()
            difficulty = args.get("difficulty", None)
            next_card = int(args.get("next", None))
            response_id = args.get("response_id", None)

            review_res_curr = db.session.query(ReviewCard).filter(ReviewCard.id == response_id).first()
            
            if review_res_curr:
                review_res_curr.difficulty = ReviewCard.Diffculty(difficulty).name

                db.session.add(review_res_curr)
                db.session.commit()

            
            response_curr = db.session.query(ReviewResponse).filter(ReviewResponse.user_id == current_user.id).filter(ReviewResponse.deck_id == int(deck_id)).first()
            if response_curr:
                response_curr.score = round((response_curr.cards.filter(ReviewCard.correct == True).count()/response_curr.cards.count()) * 100, 2)
                
                response_curr.avg_time = response_curr.avg_time_count()/response_curr.cards.count()

                response_curr.completed_at = datetime.now(timezone('Asia/Kolkata'))
                
                db.session.add(response_curr)
                db.session.commit()

            return redirect(url_for('review.review_form', deck_id=deck_id, next_card=next_card))
        except Exception as e:
            flash(str(e), 'toast')
    
    redirect(url_for('review.review_form', deck_id=deck_id, next_card=0))


@review.route('/review/check_answer')
@login_required
def check_answer():
    
    card_id = request.args.get('card_id')
    answer = request.args.get('answer')
    time_take = request.args.get('time')
    
    correct = False
    try:
        if card_id is None or not isinstance(card_id, str):
            raise APIException("400","card_id is required.")
        
        card = db.session.query(Card).filter(Card.id == int(card_id)).first()
        
        if answer == "" or answer is None or not isinstance(answer, str):
            raise APIException("400","Answer is required")
        
        if time_take == "" or time_take is None or not isinstance(time_take, str):
            raise APIException("400","time_take is required")

        if str(card.back).lower() == answer.strip().lower():
            correct = True
            
        new_response = ReviewCard(
            correct_option = str(card.back),
            selected_option = answer,
            time = int(time_take),
            correct = correct,
            card_id = int(card_id),
            review_respose_id = int(session['review_respose_id'])
        )

        db.session.add(new_response)
        db.session.commit()



        res = {
            "correct":correct,
            "answer":card.back,
            "response_id":new_response.id
        }
    except IntegrityError as e:
        res = {
            "correct":False,
            "answer":None,
            "error":str(e),
            "redirect":True,
        }
    except Exception as e:
        res = {
            "correct":False,
            "answer":None,
            "error":str(e)
        }

    return jsonify(res)
