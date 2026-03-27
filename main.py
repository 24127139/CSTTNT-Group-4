from flask import Flask, render_template, jsonify
from pysol_cards.deal_game import Game
from pysol_cards.random_base import RandomBase
from pysol_cards.cards import CardRenderer
import random
app = Flask(__name__)


def randomBoard():
    layout = Game(
    game_id="freecell",
    game_num= random.randint(1,2000),
    which_deals=RandomBase.DEALS_MS,
    max_rank=13
    ).calc_layout_string(
        CardRenderer(print_ts=True)
    )
    board = []
    for line in layout.split("\n"):
        cards = line.split()
        board.append(cards)
    return board

initial_board = randomBoard()
@app.route("/")
def index():
    return render_template("index.html", board = initial_board)               
@app.route("/new-game")
def new_game():
    global initial_board
    initial_board = randomBoard()
    return render_template("index.html", board = initial_board)

if __name__ == "__main__":
    app.run(debug=True)