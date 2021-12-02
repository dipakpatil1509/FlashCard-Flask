from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, jsonify
from flask_restful import Resource, marshal_with, fields, reqparse, Api
from application.models.user_mode import User
from application.models.deck import Deck,Card
from application.database import db
from application.error import APIException
from sqlalchemy.exc import IntegrityError
from flask_login import login_required, current_user

deck_output_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "created_for": fields.String([x.name for x in User.Role]),
    "public_status": fields.Boolean,
    "created_at":fields.DateTime,
    "created_by_id": fields.Integer
}



deck_req = reqparse.RequestParser()
deck_req.add_argument("name")
deck_req.add_argument("public_status")
deck_req.add_argument("user_id")
deck_req.add_argument("created_for")


deck = Blueprint('deck', __name__)

@deck.route('/api/deck/<int:deck_id>', methods=['GET', 'PUT', "DELETE"])
def api_deck(deck_id):
    if request.method == "GET":
        return api_get(deck_id)
    elif request.method == "PUT":
        return api_put(deck_id)
    elif request.method == "DELETE":
        return delete(deck_id)

@marshal_with(deck_output_fields)
def api_get(deck_id):
    return get(deck_id), 200

#API GET
def get(deck_id):
    deck_curr = db.session.query(Deck).filter(Deck.id == int(deck_id)).first()
    if deck_curr:
        deck_curr.user = db.session.query(User).with_entities(User.name).filter(User.id == deck_curr.created_by_id).first()
        deck_curr.number_of_cards = deck_curr.cards.count()
        return deck_curr
    else:
        raise APIException("404", "Deck not found")

#API Delete
def delete(deck_id):

    deck_curr = db.session.query(Deck).filter(Deck.id == int(deck_id) and Deck.created_by_id==current_user.id).first()

    if deck_curr is None:
        raise APIException(404, "Deck not found")

    db.session.delete(deck_curr)
    db.session.commit()

    return Response("Successfully Deleted", 200)

#API PUT
@marshal_with(deck_output_fields)
def api_put(deck_id):
    return put(deck_id), 200
    
def put(deck_id):
    args = deck_req.parse_args()
    name = args.get("name", None)
    public_status = args.get("public_status", None)
    created_for = args.get("created_for", None)

    if name == "" or name is None or not isinstance(name, str) or name.isnumeric():
        raise APIException("400","Deck Name is required and should be string.")
    
    deck_curr = db.session.query(Deck).filter(Deck.id == int(deck_id) and Deck.created_by_id==current_user).first()

    if deck_curr is None:
        raise APIException("404", "Deck not found")

    deck_curr.name = name

    if public_status:
        deck_curr.public_status = bool(int(public_status))

    if created_for:
        deck_curr.created_for = created_for
    else:
        deck_curr.created_for = "ALL"


    try:
        
        db.session.add(deck_curr)
        db.session.commit()

        return deck_curr
    except IntegrityError:
        raise APIException("400", "Deck name already exists")
    except Exception as e:
        raise APIException("400", str(e))


@deck.route('/api/deck_cards/<int:deck_id>')
def api_get_all_cards(deck_id):
    return jsonify(get_all_cards(deck_id)), 200


def get_all_cards(deck_id):
    deck = None
    try:
        deck=get(deck_id)
        cards = deck.cards.all()
        return Card.serialize_list(cards)
    except Exception as e:
        raise APIException("400", str(e))

#API POST

@deck.route('/api/deck', methods=["POST"])
@marshal_with(deck_output_fields)
def post():
    args = deck_req.parse_args()
    name = args.get("name", None)
    public_status = args.get("public_status", None)
    user_id = args.get("user_id", None)
    created_for = args.get("created_for", None)

    if name == "" or name is None or not isinstance(name, str) or name.isnumeric():
        raise APIException("400","Deck Name is required and should be string.")

    if user_id is None or not isinstance(user_id, str):
        raise APIException("400","User id is required.")

    deck_curr = db.session.query(Deck).filter(Deck.name == name).first()

    if deck_curr:
        raise APIException("409", "Deck already exist")

    if created_for and (not isinstance(created_for, str) or created_for.isnumeric()):
        raise APIException("400","Deck Created for should be string.")

    user_curr = db.session.query(User).filter(User.id == int(user_id)).first()

    if user_curr is None:
        raise APIException("404", "User not found")
    
    try:
        
        new_deck = Deck(
            name=name,
            public_status=bool(int(public_status)), 
            created_by_id=int(user_id), 
            created_for=(created_for or "ALL")
        )

        db.session.add(new_deck)
        db.session.commit()

        return new_deck, 201
    except Exception as e:
        raise APIException("400", str(e))


#Get Deck with Login
@deck.route('/view_deck/<int:deck_id>')
@login_required
def view_deck(deck_id):
	deck = None
	try:
		deck=get(deck_id)
		cards = get_all_cards(deck_id)
	except APIException as e:
		flash(str(e), 'toast')
		if not deck:
			flash("No Deck Found", "toast")
			return redirect(url_for('profile.home'))
	return render_template("Deck/Card.html", user=current_user, deck=deck, cards=cards)


#Adding Deck With Login Required
@deck.route('/add_deck', methods=["POST"])
@login_required
def add_deck():
    if request.method == "POST":

        try:
            data = post()
            return redirect(url_for('deck.view_deck', deck_id=data[0]['id']))
        except APIException as e:
            flash(str(e), 'toast')
                

        return redirect(url_for('profile.home', isForm="1"))
        
    return redirect(url_for('profile.home'))


#Delete with Login

@deck.route('/delete_deck/<int:deck_id>')
@login_required
def delete_deck(deck_id):
    try:
        msg = delete(deck_id)
        flash("Successfully Deleted Deck", "toast")
        return redirect(url_for('profile.home'))
    except APIException as e:
        flash(str(e), 'toast')

    return redirect(url_for('deck.view_deck', deck_id=deck_id))


@deck.route('/update_deck/<int:deck_id>', methods=["POST"])
@login_required
def update_deck(deck_id):
    if request.method == "POST":

        try:
            data = put(deck_id)
            return redirect(url_for('deck.view_deck', deck_id=data.id))
        except APIException as e:
            flash(str(e), 'toast')

        return redirect(url_for('deck.view_deck', deck_id=deck_id))
        
    return redirect(url_for('deck.view_deck', deck_id=deck_id))



