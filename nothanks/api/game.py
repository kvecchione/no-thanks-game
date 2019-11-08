import datetime
import json
import random
import string

from flask import Response, jsonify, request

from flask_restplus import Resource, fields
from nothanks.api.restplus import api
from nothanks.db.models import Game, LogItem, Player
from nothanks.functions.functions import *

ns = api.namespace('game', description='Operations related to gameplay')

player_fields = ns.model('game', {
    'name': fields.String,
})


@ns.route('/')
class GameList(Resource):
    def get(self):
        games = Game.objects()
        return jsonify([g.game_id for g in games])


@ns.route('/')
class GameCreate(Resource):
    def put(self):
        g = Game()
        g.deck = create_shuffled_deck()
        g.save()
        return jsonify(g.game_id)


@ns.route('/<int:id>')
class GameState(Resource):
    def get(self, id):
        try:
            g = Game.objects.get(game_id=id)
        except:
            return "Game not found", 404

        
        return jsonify(public_game_state(g))

    def post(self, id):
        try:
            g = Game.objects.get(game_id=id)
        except:
            return "Game not found", 404

        data = api.payload

        if 'token' not in data:
            return jsonify(public_game_state(g))
        else:
            return jsonify(private_game_state(g, data['token']))

@ns.route('/<int:id>/register')
class GameRegister(Resource):
    def post(self, id):
        data = api.payload
        if 'name' not in data:
            return "Missing player name", 400
        try:
            g = Game.objects.get(game_id=id)
        except:
            return "Game not found", 404

        for player in g.players:
            if data['name'] == player.name:
                return "Name already in use", 400

        p = Player(name=data['name'], token=''.join([random.choice(string.ascii_letters + string.digits) for _ in range(8)]))

        g.players.append(p)
        g.save()

        return jsonify(json.loads(p.to_json()))
    

@ns.route('/<int:id>/start')
class GameStart(Resource):
    def put(self, id):
        data = api.payload
        if 'token' not in data:
            return "Missing player token", 400
        try:
            g = Game.objects.get(game_id=id)
        except:
            return "Game not found", 404
        if g.status == 'active':
            return "Cannot start game, already in progress", 400
        elif g.status == 'complete':
            return "Cannot start game, already finished", 400
        elif len(g.players) < 3:
            return "Cannot start game, not enough players", 400
        player_name = player_name_from_token(g, data['token'])
        if player_name == 'unknown':
            return "Cannot start game, not a participant", 400
        add_log_message(g, "Game started by " + player_name)
        g.status = 'active'
        random.shuffle(g.players)
        deal_initial_chips(g)
        g.cards_left_in_deck = len(g.deck)
        g.current_player = g.players[0].name
        draw_card(g)
        g.cards_left_in_deck = len(g.deck)
        g.save()

        return jsonify(public_game_state(g))


@ns.route('/<int:id>/play')
class GamePlay(Resource):
    def post(self, id):
        data = api.payload
        if 'token' not in data:
            return "Missing player token", 400
        if 'action' not in data:
            return "Missing player action", 400
        try:
            g = Game.objects.get(game_id=id)
        except:
            return "Game not found", 404
        
        if g.status != 'active':
            return "Game is not currently active", 400   
    
        # for player in g.players:
        #     if data['token'] == player.token and player.name == g.current_player:
        #         break
        # else:
        #     return "Not your turn yet! (current turn: " +g.current_player + ')', 400

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
        
        return jsonify(public_game_state(g))
