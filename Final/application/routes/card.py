from flask import Blueprint, abort, json, render_template, request, redirect, url_for, flash, Response, send_file
from flask_restful import Resource, marshal_with, fields, reqparse, Api
from application.models.user_mode import User
from application.models.deck import Deck, Card
from application.database import db
from application.error import APIException
from sqlalchemy.exc import IntegrityError
from flask_login import login_required, current_user
from application.routes.deck import get_all_cards, get as deck_get
from io import BytesIO
import pandas as pd

card = Blueprint('card', __name__)


card_output_fields = {
    "id": fields.Integer,
    "front": fields.String,
    "back": fields.String,
    "options": fields.String,
    "created_at":fields.DateTime,
    "created_by_id": fields.Integer,
    "deck_id":fields.Integer,
}



card_red = reqparse.RequestParser()
card_red.add_argument("front")
card_red.add_argument("back")
card_red.add_argument("options")
card_red.add_argument("deck_id")
card_red.add_argument("user_id")


@card.route('/api/card/<int:card_id>', methods=['GET', 'PUT', "DELETE"])
def api_deck(card_id):
    if request.method == "GET":
        return api_get(card_id)
    elif request.method == "PUT":
        return api_put(card_id)
    elif request.method == "DELETE":
        return delete(card_id)

@marshal_with(card_output_fields)
def api_get(card_id):
    data = get(card_id)
    data.options = ",".join(data.options)
    return data, 200

#API GET
def get(card_id):
    card_curr = db.session.query(Card).filter(Card.id == int(card_id)).first()
    if card_curr:
        card_curr.deck = db.session.query(Deck).filter(Deck.id == card_curr.deck_id).first()
        if(card_curr.options):
            card_curr.options = card_curr.options.split(',')
        return card_curr
    else:
        raise APIException("404", "Card not found")

#API Delete
def delete(card_id):

    card_curr = db.session.query(Card).filter(Card.id == int(card_id) and Card.created_by_id==current_user.id).first()

    if card_curr is None:
        raise APIException(404, "Card not found")

    db.session.delete(card_curr)
    db.session.commit()

    return Response("Successfully Deleted", 200)

#API PUT
@marshal_with(card_output_fields)
def api_put(card_id):
    return put(card_id), 200
    
def put(card_id):
    args = card_red.parse_args()
    front = args.get("front", None)
    back = args.get("back", None)
    options = args.get("options", None)
    deck_id = args.get("deck_id", None)

    if front == "" or front is None or not isinstance(front, str):
        raise APIException("400","Front is required.")
    
    if back == "" or back is None or not isinstance(back, str):
        raise APIException("400","Back is required.")
    
    if options == "" or options is None or not isinstance(options, str) or options.isnumeric():
        raise APIException("400","Options should be string.")
    
    card_curr = db.session.query(Card).filter(Card.id == int(card_id)).first()

    if card_curr is None:
        raise APIException("404", "Card not found")

    card_curr.front = front
    card_curr.back = back

    card_curr.options = options

    card_curr.deck_id = int(deck_id)
    try:
        
        db.session.add(card_curr)
        db.session.commit()
        print(card_curr.options)

        return card_curr
    except IntegrityError:
        raise APIException("400", "Card already exists")
    except Exception as e:
        raise APIException("400", str(e))


#API POST

@card.route('/api/card', methods=["POST"])
@marshal_with(card_output_fields)
def post():
    args = card_red.parse_args()
    front = args.get("front", None)
    back = args.get("back", None)
    options = args.get("options", None)
    deck_id = args.get("deck_id", None)
    user_id = args.get("user_id", None)

    if front == "" or front is None or not isinstance(front, str):
        raise APIException("400","Front is required.")
    
    if back == "" or back is None or not isinstance(back, str):
        raise APIException("400","Back is required.")
    
    if options == "" or options is None or not isinstance(options, str) or options.isnumeric():
        raise APIException("400","Options should be string.")
    
    try:

        user = current_user.id if current_user.is_active else user_id
        new_card = Card(
            front=front,
            back= back, 
            options = options,
            deck_id=int(deck_id), 
            created_by_id=user
        )

        db.session.add(new_card)
        db.session.commit()

        return new_card, 201
    except Exception as e:
        raise APIException("400", str(e))


#Get Deck with Login
@card.route('/view_card/<int:card_id>')
@login_required
def view_card(card_id):
    data = None
    try:
        data=get(card_id)
    except APIException as e:
        flash(str(e), 'toast')
    return redirect(url_for('deck.view_deck', deck_id=data.deck_id))


@card.route('/add_card', methods=["GET", "POST"])
@login_required
def add_card():
    deck_id = request.args.get('deck_id')
    if request.method == "POST":
        try:
            data = post()
        except APIException as e:
            flash(str(e), 'toast')
    
    print(deck_id)
    if deck_id:
        deck_id = int(deck_id)
    return render_template('Deck/Add_Card.html', user=current_user, deck_id=deck_id)


@card.route('/add_card/<int:card_id>', methods=["GET", "POST"])
@login_required
def edit_card(card_id):
    if request.method == "POST":
        try:
            data = put(card_id)
            return redirect(url_for('deck.view_deck', deck_id=data.deck_id))
        except APIException as e:
            flash(str(e), 'toast')

    card = get(card_id)
    if(card.options):
        card.options = ",".join(card.options)
    return render_template('Deck/Add_Card.html', user=current_user, card=card)


@card.route('/delete_card/<int:deck_id>/<int:card_id>', methods=["GET", "POST"])
@login_required
def delete_card(card_id, deck_id):
    try:
        msg = delete(card_id)
        flash("Successfully Deleted Card", "toast")
    except APIException as e:
        flash(str(e), 'toast')

    return redirect(url_for('deck.view_deck', deck_id=deck_id))


@card.route('/import_card/<int:deck_id>', methods=["POST"])
@login_required
def import_card(deck_id):
    try:
        file = request.files.get('importFile')
        excel = pd.read_excel(file)
        skipped_rows = 0
        for i, item in excel.iterrows():
            try:  
                front = item['front']
                back = item['back']
                options = item['options']
                if front == "" or front is None:
                    raise Exception("Front is necessay")
                
                if back == "" or back is None:
                    raise Exception("Back is required")
                
                if options == "" or options is None or not isinstance(options, str):
                    raise Exception("Options are required and should be string.")

                user = current_user.id
                new_card = Card(
                    front=front,
                    back= back, 
                    options = options,
                    deck_id=int(deck_id), 
                    created_by_id=user
                )

                db.session.add(new_card)
                db.session.commit()

            except Exception as e:
                print(str(e))
                skipped_rows += 1

        flash(f'Successfully Added Cards. Skipped Rows {skipped_rows}' , "toast")
    except APIException as e:
        flash(str(e), 'toast')

    return redirect(url_for('deck.view_deck', deck_id=deck_id))


@card.route('/download_card/<int:deck_id>')
@login_required
def download_excel(deck_id):
    try:
        deck = deck_get(deck_id)
        cards = get_all_cards(deck_id)
        df = pd.DataFrame.from_dict(cards)
        df = df.drop(['id', 'deck_id', 'created_by_id'], axis=1)
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine="xlsxwriter")
        df.to_excel(writer, sheet_name='Sheet1')
        writer.save()
        output.seek(0)
        return send_file(output, attachment_filename=f'{deck.name} cards.xlsx', as_attachment=True)
    except Exception as e:
        flash(str(e), 'toast')

    return redirect(url_for('deck.view_deck', deck_id=deck_id))