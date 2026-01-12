# engine/cards.py

# Card + RS + Generate 52 Cards# engine/cards.py

RANKS = "23456789TJQKA"
SUITS = "SHDC"

def standard_deck_rs():
    return [f"{r}{s}" for s in SUITS for r in RANKS]
