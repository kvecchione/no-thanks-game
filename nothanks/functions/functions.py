import datetime
import json
import random
import string

from nothanks.db.models import LogItem


def generate_token():
    return ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(8)])


def add_log_message(game, message):
    log_item = LogItem(datestamp=datetime.datetime.now(), message=message)
    game.log.append(log_item)
    game.save()


def player_name_from_token(game, token):
    player_name = 'unknown'
    for player in game.players:
        if player.token == token:
            player_name = player.name  
            break  

    return player_name


def create_shuffled_deck():
    deck = list(range(3, 36))
    random.shuffle(deck)
    for _ in range(9):
        random_card = random.choice(deck)
        deck.remove(random_card)
    return deck


def deal_initial_chips(game):
    for player in game.players:
        player.chips = 11
    game.save()


def public_game_state(game):
    data = game.to_mongo().to_dict()

    if game.status != 'complete':
        # remove deck
        del data['deck']

        # remove player tokens and chips
        for player in data['players']:
            del player['token']
            del player['chips']
    
    return data


def private_game_state(game, token):
    data = game.to_mongo().to_dict()

    # remove deck
    del data['deck']

    # remove other player tokens and chips
    for player in data['players']:
        if player['token'] != token:
            del player['token']
            del player['chips']

    return data


def draw_card(game):
    game.face_up_card = game.deck.pop()
    game.save()


def play_pass(game):
    total_players = len(game.players)
    c = 0
    for player in game.players:
        if player.name == game.current_player:
            current_player_name = player.name
            current_player_index = c
            next_player_index = (c + 1) % total_players
            break
        c += 1

    add_log_message(game, current_player_name + ' says no thanks!')
    game.players[current_player_index].chips -= 1
    game.chips_on_card += 1
    game.current_player = game.players[next_player_index].name
    game.save()


def play_take(game):
    c = 0
    for player in game.players:
        if player.name == game.current_player:
            current_player_index = c
            current_player_name = player.name
            break 
        c += 1
    
    add_log_message(game, current_player_name + ' took card ' + str(game.face_up_card) + ' and ' + str(game.chips_on_card) + ' chips.')
    game.players[current_player_index].cards.append(game.face_up_card)
    game.players[current_player_index].chips += game.chips_on_card
    game.chips_on_card = 0
    if len(game.deck) > 0:
        draw_card(game)
    else:
        game.save()
        calculate_winner(game)


def calculate_points(player):
    points = 0
    cards = list(reversed(sorted(player.cards)))
    for card in cards:
        if card - 1 in cards:
            continue
        else:
            points += card

    points = points - player.chips
    return points


def calculate_winner(game):
    current_min = 1000
    winners = []
    for player in game.players:
        points = calculate_points(player)
        add_log_message(game, player.name + ' has ' + str(points) + ' points')
        player.score = points
        if points < current_min:
            winners = [player.name]
            current_min = points
        elif points == current_min:
            winners.append(player.name)
    
    if len(winners) == 1:
        add_log_message(game, winners[0] + ' WINS!')
    else:
        add_log_message(game, " and ".join(winners) + ' TIED!')
    
    game.winner = ','.join(winners)
    game.status = 'complete'
    game.save()
