from copy import deepcopy
from enum import Enum
import tracemalloc
import time


class Suit(Enum):
    """Card suits"""
    SPADE = 'S'
    HEART = 'H'
    DIAMOND = 'D'
    CLUB = 'C'


class Rank(Enum):
    """Card ranks with numeric values"""
    ACE = ('A', 1)
    TWO = ('2', 2)
    THREE = ('3', 3)
    FOUR = ('4', 4)
    FIVE = ('5', 5)
    SIX = ('6', 6)
    SEVEN = ('7', 7)
    EIGHT = ('8', 8)
    NINE = ('9', 9)
    TEN = ('T', 10)
    JACK = ('J', 11)
    QUEEN = ('Q', 12)
    KING = ('K', 13)
    
    def __init__(self, symbol, numeric_value):
        self.symbol = symbol
        self.numeric_value = numeric_value


class Card:
    """Represents a single card"""
    
    def __init__(self, rank, suit):
        self.rank = rank  # Rank enum
        self.suit = suit  # Suit enum
    
    def __repr__(self):
        return f"{self.rank.symbol}{self.suit.value}"
    
    def __eq__(self, other):
        if other is None:
            return False
        return self.rank == other.rank and self.suit == other.suit
    
    def __hash__(self):
        return hash((self.rank, self.suit))
    
    def is_red(self):
        """Heart and Diamond are red"""
        return self.suit in [Suit.HEART, Suit.DIAMOND]
    
    def is_black(self):
        """Spade and Club are black"""
        return self.suit in [Suit.SPADE, Suit.CLUB]
    
    def copy(self):
        """Create a copy of the card"""
        return Card(self.rank, self.suit)


class GameState:
    """
    Represents a FreeCell game state.
    
    Layout:
    - 8 cascades (columns) - indexed 0-7
    - 4 free cells - indexed 0-3
    - 4 foundations - one for each suit
    """
    
    def __init__(self):
        """Initialize an empty game state"""
        self.cascades = [[] for _ in range(8)]  # 8 columns
        self.free_cells = [None, None, None, None]  # 4 free cells
        self.foundations = {suit: 0 for suit in Suit}  # Track highest rank in each foundation
        self.move_count = 0  # Track number of moves
    
    def copy(self):
        """Create a deep copy of the state"""
        new_state = GameState()
        new_state.cascades = [[card.copy() for card in col] for col in self.cascades]
        new_state.free_cells = [card.copy() if card else None for card in self.free_cells]
        new_state.foundations = dict(self.foundations)
        new_state.move_count = self.move_count
        return new_state
    
    def to_hashable(self):
        """
        Convert state to tuple for use in sets (visited states)
        """
        # Convert cascades to tuples of card strings
        cascades_tuple = tuple(
            tuple((card.rank.symbol + card.suit.value) for card in col)
            for col in self.cascades
        )
        
        # Convert free cells to tuple
        free_cells_tuple = tuple(
            (card.rank.symbol + card.suit.value) if card else None
            for card in self.free_cells
        )
        
        # Convert foundations to tuple
        foundations_tuple = tuple(
            self.foundations[suit] for suit in [Suit.SPADE, Suit.HEART, Suit.DIAMOND, Suit.CLUB]
        )
        
        return (cascades_tuple, free_cells_tuple, foundations_tuple)
    
    def is_goal(self):
        """Check if all cards are in foundations (game won)"""
        for suit in Suit:
            if self.foundations[suit] != 13:  # K = 13
                return False
        return True
    
    def get_empty_free_cells(self):
        """Count empty free cells"""
        return sum(1 for cell in self.free_cells if cell is None)
    
    def get_empty_cascades(self):
        """Count empty cascades"""
        return sum(1 for col in self.cascades if len(col) == 0)
    
    def get_max_sequence_length(self):
        """
        Calculate max sequence length that can be moved.
        Formula: (num_empty_free_cells + 1) * (num_empty_cascades + 1)
        """
        empty_free = self.get_empty_free_cells()
        empty_cascades = self.get_empty_cascades()
        return (empty_free + 1) * (empty_cascades + 1)


class Move:
    """Represents a single move in the game"""
    
    def __init__(self, source_type, source_idx, dest_type, dest_idx, cards_count=1):
        """
        source_type: 'cascade', 'freecell'
        dest_type: 'cascade', 'freecell', 'foundation'
        """
        self.source_type = source_type
        self.source_idx = source_idx
        self.dest_type = dest_type
        self.dest_idx = dest_idx
        self.cards_count = cards_count
    
    def __repr__(self):
        return f"Move({self.source_type}[{self.source_idx}] -> {self.dest_type}[{self.dest_idx}], count={self.cards_count})"
    
    def to_dict(self):
        """Convert move to dictionary for sending to frontend"""
        return {
            'source_type': self.source_type,
            'source_idx': self.source_idx,
            'dest_type': self.dest_type,
            'dest_idx': self.dest_idx,
            'cards_count': self.cards_count
        }


class FreeCell:
    """FreeCell game with all rules and logic"""
    
    # Rank values for easy comparison
    RANK_VALUES = {rank.symbol: rank.numeric_value for rank in Rank}
    
    def __init__(self):
        """Initialize a new game"""
        self.state = GameState()
    
    @staticmethod
    def can_stack_on(card1, card2):
        """
        Check if card1 can be placed on card2 in a cascade.
        Rules:
        - card2 rank must be exactly 1 higher than card1
        - card1 and card2 must have opposite colors
        """
        if card2 is None:
            return False
        
        rank1 = card1.rank.numeric_value
        rank2 = card2.rank.numeric_value
        
        if rank1 != rank2 - 1:
            return False
        
        if card1.is_red() == card2.is_red():  # Same color
            return False
        
        return True
    
    @staticmethod
    def can_move_to_foundation(card, foundation_value, foundation_suit):
        """
        Check if card can be moved to foundation.
        Rules:
        - Card suit must match foundation
        - Card rank must be exactly 1 higher than current foundation top
        """
        if card.suit != foundation_suit:
            return False
        
        if card.rank.numeric_value != foundation_value + 1:
            return False
        
        return True
    
    @staticmethod
    def is_valid_cascade_sequence(cards):
        """
        Check if a sequence of cards is valid (proper descending order with alternating colors).
        """
        if len(cards) == 0:
            return False
        
        if len(cards) == 1:
            return True
        
        for i in range(len(cards) - 1):
            if not FreeCell.can_stack_on(cards[i], cards[i + 1]):
                return False
        
        return True
    
    def get_possible_moves(self, state):
        """
        Generate all possible moves from the current state.
        Returns: list of Move objects
        """
        moves = []
        
        # 1. Try moving cards from cascades
        for col_idx, cascade in enumerate(state.cascades):
            if len(cascade) == 0:
                continue
            
            # For each card in cascade (starting from bottom)
            for card_idx in range(len(cascade)):
                cards_to_move = cascade[card_idx:]
                
                # Check if this is a valid sequence
                if not self.is_valid_cascade_sequence(cards_to_move):
                    continue
                
                card = cascade[card_idx]
                cards_count = len(cards_to_move)
                
                # Check if we can move this many cards
                if cards_count > state.get_max_sequence_length():
                    continue
                
                # 1a. Try moving to other cascades
                for other_col_idx in range(8):
                    if other_col_idx == col_idx:
                        continue
                    
                    other_cascade = state.cascades[other_col_idx]
                    
                    # Empty cascade
                    if len(other_cascade) == 0:
                        moves.append(Move('cascade', col_idx, 'cascade', other_col_idx, cards_count))
                    # Top card of other cascade
                    elif self.can_stack_on(card, other_cascade[-1]):
                        moves.append(Move('cascade', col_idx, 'cascade', other_col_idx, cards_count))
                
                # 1b. Try moving to empty free cells (only single cards)
                if cards_count == 1:
                    for cell_idx, cell in enumerate(state.free_cells):
                        if cell is None:
                            moves.append(Move('cascade', col_idx, 'freecell', cell_idx, 1))
                
                # 1c. Try moving to foundations (only single cards)
                if cards_count == 1:
                    for suit in Suit:
                        if self.can_move_to_foundation(card, state.foundations[suit], suit):
                            moves.append(Move('cascade', col_idx, 'foundation', suit.value, 1))
        
        # 2. Try moving cards from free cells
        for cell_idx, card in enumerate(state.free_cells):
            if card is None:
                continue
            
            # 2a. Try moving to cascades
            for col_idx in range(8):
                cascade = state.cascades[col_idx]
                
                # Empty cascade
                if len(cascade) == 0:
                    moves.append(Move('freecell', cell_idx, 'cascade', col_idx, 1))
                # Top card of cascade
                elif self.can_stack_on(card, cascade[-1]):
                    moves.append(Move('freecell', cell_idx, 'cascade', col_idx, 1))
            
            # 2b. Try moving to foundations
            for suit in Suit:
                if self.can_move_to_foundation(card, state.foundations[suit], suit):
                    moves.append(Move('freecell', cell_idx, 'foundation', suit.value, 1))
        
        return moves
    
    def apply_move(self, state, move):
        """
        Apply a move to a state and return the new state.
        Does NOT modify the original state.
        """
        new_state = state.copy()
        
        # Remove cards from source
        if move.source_type == 'cascade':
            cards = new_state.cascades[move.source_idx][-move.cards_count:]
            del new_state.cascades[move.source_idx][-move.cards_count:]
        else:  # freecell
            cards = [new_state.free_cells[move.source_idx]]
            new_state.free_cells[move.source_idx] = None
        
        # Place cards in destination
        if move.dest_type == 'cascade':
            new_state.cascades[move.dest_idx].extend(cards)
        elif move.dest_type == 'freecell':
            new_state.free_cells[move.dest_idx] = cards[0]
        elif move.dest_type == 'foundation':
            suit = Suit(move.dest_idx)
            new_state.foundations[suit] += len(cards)
        
        new_state.move_count += 1
        return new_state
    
    def load_from_board(self, board):
        """
        Load game state from board string (from pysol_cards).
        board: list of lists of card strings like [['AS', '2H'], ['3D', ...], ...]
        """
        self.state = GameState()
        
        # Parse board and fill cascades (ONLY FIRST 8!)
        for col_idx, column in enumerate(board[:8]):
            for card_str in column:
                if card_str == "":
                    continue
                
                rank_char = card_str[0]
                suit_char = card_str[1]
                
                # Map character to Rank
                rank_map = {
                    'A': Rank.ACE, '2': Rank.TWO, '3': Rank.THREE,
                    '4': Rank.FOUR, '5': Rank.FIVE, '6': Rank.SIX,
                    '7': Rank.SEVEN, '8': Rank.EIGHT, '9': Rank.NINE,
                    'T': Rank.TEN, 'J': Rank.JACK, 'Q': Rank.QUEEN,
                    'K': Rank.KING
                }
                
                # Map character to Suit
                suit_map = {
                    'S': Suit.SPADE, 'H': Suit.HEART,
                    'D': Suit.DIAMOND, 'C': Suit.CLUB
                }
                
                rank = rank_map.get(rank_char)
                suit = suit_map.get(suit_char)
                
                if rank and suit:
                    card = Card(rank, suit)
                    self.state.cascades[col_idx].append(card)
                    
# Test the game logic 
if __name__ == "__main__":
    from pysol_cards.deal_game import Game
    from pysol_cards.random_base import RandomBase
    from pysol_cards.cards import CardRenderer
    import random
    
    # Generate a board
    layout = Game(
        game_id="freecell",
        game_num=1,
        which_deals=RandomBase.DEALS_MS,
        max_rank=13
    ).calc_layout_string(CardRenderer(print_ts=True))
    
    board = []
    for line in layout.split("\n"):
        cards = line.split()
        board.append(cards)
    
    print("Board:", board)
    print()
    
    # Test game logic
    game = FreeCell()
    game.load_from_board(board)
    
    print("Initial state:")
    for i, col in enumerate(game.state.cascades):
        print(f"Cascade {i}: {col}")
    
    print("\nPossible moves from initial state:")
    moves = game.get_possible_moves(game.state)
    for move in moves[:10]:  # Print first 10
        print(f"  {move}")
    
    print(f"\nTotal possible moves: {len(moves)}")