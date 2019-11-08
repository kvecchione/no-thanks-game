import json
import random

from flask import Response, jsonify, request

from flask_restplus import Resource, fields
from nothanks.api.api import api
from nothanks.db.models import Game, LogItem, Player
from nothanks.functions.functions import *


MIN_PLAYERS = 3
MAX_PLAYERS = 5


ns = api.namespace('game', description='Operations related to gameplay')

# Models
player_name_input_model = api.model('PlayerNameInput', {
    'name': fields.String(description='player name', required=True)
})

token_input_model = api.model('PlayerTokenInput', {
    'token': fields.String(description='player token', required=True)
})

play_input_model = api.model('Play', {
    'token': fields.String(description='player token', required=True),
    'action': fields.String(description='action to take', required=True, enum=['take', 'pass'])
})

player_model = api.model('Player', {
    'name': fields.String(description='player name'),
    'token': fields.String(description='player token *private*'),
    'chips': fields.Integer(description='player chip count *private*'),
    'cards': fields.List(fields.String, description='player cards in hand'),
    'score': fields.Integer(description='player final score')
})

log_model = api.model('LogEntry', {
    'message': fields.String(description='message'),
    'datestamp': fields.DateTime(dt_format='rfc822', description='message date/time')
})

game_model = api.model('Game', {
    'game_id': fields.Integer(description='game ID'),
    'players': fields.List(fields.Nested(player_model), description='players in game'),
    'status': fields.String(description='game status', enum=['new', 'active', 'complete']),
    'cards_left_in_deck': fields.Integer(description='count of cards left face down in deck'),
    'deck': fields.List(fields.String, description='cards left in deck *private*'),
    'face_up_card': fields.Integer(description='value of face up card'),
    'chips_on_card': fields.Integer(description='value of chips on active card'),
    'winner': fields.String(description='winner name'),
    'log': fields.List(fields.Nested(log_model), description='game log'),
    'current_player': fields.String(description='current player name')
})

game_list_model = api.model('GameList', {
    'game_id': fields.Integer(description='game ID'),
    'players': fields.List(fields.String, decription='list of players'),
    'status': fields.String(description='game status', enum=['new', 'active', 'complete'])
})


@ns.route('/')
class GameList(Resource):
    @ns.marshal_with(game_list_model)
    def get(self):
        games = Game.objects()
        game_list = []
        for game in games:
            game_list.append({
                'status': game.status,
                'players': [p.name for p in game.players],
                'game_id': game.game_id
            })
        return game_list


@ns.route('/')
class GameCreate(Resource):
    @ns.marshal_with(game_model)
    def post(self):
        g = Game()
        g.deck = create_shuffled_deck()
        g.save()
        return public_game_state(g)


@ns.route('/<int:game_id>')
@ns.doc(params={'game_id': 'Game ID'})
class GameState(Resource):
    @ns.marshal_with(game_model)
    def get(self, game_id):
        try:
            g = Game.objects.get(game_id=game_id)
        except:
            return "Game not found", 404
        
        return public_game_state(g)

    @ns.expect(token_input_model)
    @ns.marshal_with(game_model)
    def post(self, game_id):
        try:
            g = Game.objects.get(game_id=game_id)
        except:
            return "Game not found", 404

        data = api.payload

        if 'token' not in data:
            return public_game_state(g)
        else:
            return private_game_state(g, data['token'])


@ns.route('/<int:game_id>/register')
@ns.doc(params={'game_id': 'Game ID'})
class GameRegister(Resource):
    @ns.expect(player_name_input_model)
    @ns.marshal_with(player_model)
    def post(self, game_id):
        data = api.payload
        if 'name' not in data:
            return "Missing player name", 400
        try:
            g = Game.objects.get(game_id=game_id)
        except:
            return "Game not found", 404

        for player in g.players:
            if data['name'] == player.name:
                return "Name already in use", 400
        
        if len(g.players) == MAX_PLAYERS:
            return "Game is full", 400

        p = Player(name=data['name'], token=generate_token())

        g.players.append(p)
        g.save()

        return p.to_mongo().to_dict()
    

@ns.route('/<int:game_id>/start')
@api.doc(params={'game_id': 'Game ID'})
class GameStart(Resource):
    @ns.expect(token_input_model)
    @ns.marshal_with(game_model)
    def put(self, game_id):
        data = api.payload
        if 'token' not in data:
            return "Missing player token", 400
        try:
            g = Game.objects.get(game_id=game_id)
        except:
            return "Game not found", 404
        if g.status == 'active':
            return "Cannot start game, already in progress", 400
        elif g.status == 'complete':
            return "Cannot start game, already finished", 400
        elif len(g.players) < MIN_PLAYERS:
            return "Cannot start game, not enough players", 400

        player_name = player_name_from_token(g, data['token'])
        if player_name == 'unknown':
            return "Cannot start game, not a participant", 400

        add_log_message(g, "Game started by " + player_name)
        g.status = 'active'
        random.shuffle(g.players)
        deal_initial_chips(g)
        g.current_player = g.players[0].name
        draw_card(g)
        g.cards_left_in_deck = len(g.deck)
        g.save()

        return public_game_state(g)


@ns.route('/<int:game_id>/play')
@ns.doc(params={'game_id': 'Game ID'})
class GamePlay(Resource):
    @ns.expect(play_input_model)
    @ns.marshal_with(game_model)
    def post(self, game_id):
        data = api.payload
        if 'token' not in data:
            return "Missing player token", 400
        if 'action' not in data:
            return "Missing player action", 400
        try:
            g = Game.objects.get(game_id=game_id)
        except:
            return "Game not found", 404
        
        if g.status != 'active':
            return "Game is not currently active", 400   
    
        for player in g.players:
            if data['token'] == player.token and player.name == g.current_player:
                break
        else:
            return "Not your turn yet! (current turn: " +g.current_player + ')', 400

        for player in g.players:
            if player.name == g.current_player:
                break

        if player.chips == 0:
            add_log_message(g, player.name + ' has no chips, forced to take card')
            play_take(g)
        elif data['action'] == 'take':
            play_take(g)
        elif data['action'] == 'pass':
            play_pass(g)
        else:
            return "Invalid action!", 400
        
        g.cards_left_in_deck = len(g.deck)
        g.save()
        
        return public_game_state(g)
