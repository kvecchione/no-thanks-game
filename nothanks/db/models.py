from mongoengine import *


class Player(EmbeddedDocument):
    name = StringField()
    token = StringField()
    chips = IntField(default=0)
    cards = ListField(IntField())
    score = IntField(default=0)


class LogItem(EmbeddedDocument):
    datestamp = DateTimeField()
    message = StringField()


class Game(Document):
    game_id = SequenceField()
    players = EmbeddedDocumentListField(Player)
    status = StringField(default='new', choices=['new', 'active', 'complete'])
    cards_left_in_deck = IntField(default=0)
    deck = ListField(IntField())
    face_up_card = IntField()
    chips_on_card = IntField(default=0)
    winner = StringField(default='')
    log = EmbeddedDocumentListField(LogItem)
    current_player = StringField(default='')

