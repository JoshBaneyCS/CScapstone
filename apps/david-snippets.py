"""Cards."""

import random
from collections import Counter
from enum import Enum, IntEnum, auto
from typing import Self  # Python 3.11+ only

# ruff: noqa: S311, INP001


class Rank(IntEnum):
    """Enum for card rank (2, 3, J, Q, etc).

    Assumes Ace > King.

    """

    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


class Suit(Enum):
    """Enum for card suit (clubs, diamonds, hearts, spades)."""

    CLUBS = auto()
    DIAMONDS = auto()
    HEARTS = auto()
    SPADES = auto()


class Card:
    """Class for a playing card.

    Args:
        rank (Rank): rank of the card

        suit (Suit): suit of the card

    Usage:
        card = Card(Rank.ACE, Suit.SPADES)

    """

    def __init__(self, rank: Rank, suit: Suit) -> None:
        """Initialize a card."""
        self.rank = rank
        self.suit = suit

    def __str__(self) -> str:
        """Show the string representation of the card.

        Returns:
            str: string representation of the card (e.g., "Ace of Spades")

        """
        return f"{self.rank.name.title()} of {self.suit.name.title()}"

    @classmethod
    def random_card(cls) -> Self:
        """Generate a random card of a given class/subclass."""
        return cls(random.choice(list(Rank)), random.choice(list(Suit)))

    @classmethod
    def generate_deck(cls) -> list[Self]:
        """Generate a new 52-card deck as a list of Card objects.

        Returns:
            list[Self]: list of Cards/subclass of Cards representing a standard 52-card deck

        """
        return [cls(rank, suit) for suit in Suit for rank in Rank]


class BlackjackCard(Card):
    """Blackjack card."""

    @property
    def value(self) -> int:
        """Get the blackjack value of the card."""
        if self.rank in [Rank.JACK, Rank.QUEEN, Rank.KING]:
            return 10  # if it's a jack, queen, or king, return 10
        if self.rank == Rank.ACE:
            return 11  # if it's an ace, return 11
        return self.rank.value  # else, return the value given in the Rank enum


class BlackjackHand:
    """Dataclass for blackjack hands.

    Args:
        cards (list[BlackjackCard], optional): list of blackjack cards in the hand

    Usage:
        hand = BlackjackHand([BlackjackCard(Rank.ACE, Suit.SPADES), ...])

    """

    def __init__(self, cards: list[BlackjackCard]) -> None:
        """Initialize a blackjack hand."""
        self.cards = cards

    @property
    def value(self) -> int:
        """Get the total value of a blackjack hand.

        Args:
            hand (list[BlackjackCard]): list of blackjack cards

        Returns:
            int: total value of the hand

        """
        total = sum(card.value for card in self.cards)  # initial total of the hand
        aces = sum(1 for card in self.cards if card.rank == Rank.ACE)  # count the number of aces

        # while total is over 21 and aces are left
        while total > 21 and aces:  # noqa: PLR2004
            total -= 10  # convert an ace from 11 to 1
            aces -= 1  # decrement the number of aces left to convert
        return total


class PokerCard(Card):
    """Poker card."""


class PokerHandRank(IntEnum):
    """Enum for poker hand ranks, e.g., high card, pair, two pair, etc.

    You can compare the ranks.
    PokerHandRank.ROYAL_FLUSH > PokerHandRank.STRAIGHT_FLUSH returns True.
    """

    HIGH_CARD = 1
    ONE_PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10


class PokerHand:
    """Class for poker hands.

    Args:
        cards (list[PokerCard], optional): list of poker cards in the hand

    Usage:
        hand = PokerHand([PokerCard(Rank.ACE, Suit.SPADES), PokerCard(Rank.KING, Suit.SPADES), ...])

    """

    def __init__(self, cards: list[PokerCard]) -> None:
        """Initialize a poker hand."""
        self.cards = cards

    @property
    def rank(self) -> PokerHandRank:  # noqa: C901, PLR0911
        """Evaluate the poker hand and determine its rank.

        Returns:
            PokerHandRank: rank of the poker hand

        """
        maximum_hand_size = 5
        if len(self.cards) != maximum_hand_size:
            msg = "A poker hand must contain exactly 5 cards."
            raise ValueError(msg)

        # Normalize ranks and suits
        ranks = [card.rank.value for card in self.cards]
        suits = [card.suit for card in self.cards]

        # Count occurrences of each rank
        counts = Counter(ranks)
        counts_values = sorted(counts.values(), reverse=True)

        # Check for flush (all suits equal)
        is_flush = len(set(suits)) == 1

        # Check for straight. Handle wheel (A-2-3-4-5).
        unique_ranks = sorted(set(ranks))
        is_straight = False
        if len(unique_ranks) == len(self.cards):
            max_rank = max(unique_ranks)
            min_rank = min(unique_ranks)
            if max_rank - min_rank == len(self.cards) - 1 or set(unique_ranks) == {
                Rank.ACE,
                Rank.TWO,
                Rank.THREE,
                Rank.FOUR,
                Rank.FIVE,
            }:
                is_straight = True

        # Determine hand rank in order of strength
        if is_straight and is_flush:
            # Check for royal flush
            if set(ranks) >= {Rank.TEN, Rank.JACK, Rank.QUEEN, Rank.KING, Rank.ACE}:
                return PokerHandRank.ROYAL_FLUSH
            return PokerHandRank.STRAIGHT_FLUSH

        if 4 in counts_values:  # noqa: PLR2004
            return PokerHandRank.FOUR_OF_A_KIND

        if counts_values[:2] == [3, 2]:
            return PokerHandRank.FULL_HOUSE

        if is_flush:
            return PokerHandRank.FLUSH

        if is_straight:
            return PokerHandRank.STRAIGHT

        if 3 in counts_values:  # noqa: PLR2004
            return PokerHandRank.THREE_OF_A_KIND

        if counts_values.count(2) >= 2:  # noqa: PLR2004
            return PokerHandRank.TWO_PAIR

        if 2 in counts_values:  # noqa: PLR2004
            return PokerHandRank.ONE_PAIR

        return PokerHandRank.HIGH_CARD

    @property
    def rank_cards(self) -> list[PokerCard]:  # noqa: C901, PLR0911
        """Get the cards that form the winning rank.

        For example, in a pair of Aces, returns the two Aces.
        In a full house, returns the three of a kind and the pair.

        Returns:
            list[PokerCard]: cards that form the winning rank

        """
        maximum_hand_size = 5
        if len(self.cards) != maximum_hand_size:
            msg = "A poker hand must contain exactly 5 cards."
            raise ValueError(msg)

        # Normalize ranks and suits
        ranks = [card.rank.value for card in self.cards]

        # Count occurrences of each rank
        counts = Counter(ranks)

        if self.rank in (PokerHandRank.ROYAL_FLUSH, PokerHandRank.STRAIGHT_FLUSH):
            # All cards form the rank
            return sorted(self.cards, key=lambda c: c.rank.value, reverse=True)

        if self.rank == PokerHandRank.FOUR_OF_A_KIND:
            # Find the four cards of the same rank
            four_rank = next(rank for rank, count in counts.items() if count == 4)  # noqa: PLR2004
            return sorted(
                [card for card in self.cards if card.rank.value == four_rank],
                key=lambda c: c.rank.value,
                reverse=True,
            )

        if self.rank == PokerHandRank.FULL_HOUSE:
            # Find the three of a kind and the pair
            three_rank = next(rank for rank, count in counts.items() if count == 3)  # noqa: PLR2004
            pair_rank = next(rank for rank, count in counts.items() if count == 2)  # noqa: PLR2004
            three_cards = [card for card in self.cards if card.rank.value == three_rank]
            pair_cards = [card for card in self.cards if card.rank.value == pair_rank]
            return sorted(three_cards + pair_cards, key=lambda c: c.rank.value, reverse=True)

        if self.rank == PokerHandRank.FLUSH:
            # All cards form the rank (flush)
            return sorted(self.cards, key=lambda c: c.rank.value, reverse=True)

        if self.rank == PokerHandRank.STRAIGHT:
            # All cards form the rank (straight)
            if {Rank.ACE, Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE}.issubset(set(ranks)):
                return sorted(
                    [
                        card
                        for card in self.cards
                        if card.rank.value in {Rank.ACE, Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE}
                    ],
                    key=lambda c: c.rank.value if c.rank != Rank.ACE else 1,
                )
            return sorted(self.cards, key=lambda c: c.rank.value, reverse=True)

        if self.rank == PokerHandRank.THREE_OF_A_KIND:
            # Find the three cards of the same rank
            three_rank = next(rank for rank, count in counts.items() if count == 3)  # noqa: PLR2004
            return sorted(
                [card for card in self.cards if card.rank.value == three_rank],
                key=lambda c: c.rank.value,
                reverse=True,
            )

        if self.rank == PokerHandRank.TWO_PAIR:
            # Find the two pairs
            pair_ranks = sorted(
                [rank for rank, count in counts.items() if count == 2],  # noqa: PLR2004
                reverse=True,
            )
            two_pair_cards = [card for card in self.cards if card.rank.value in pair_ranks]
            return sorted(two_pair_cards, key=lambda c: c.rank.value, reverse=True)

        if self.rank == PokerHandRank.ONE_PAIR:
            # Find the pair
            pair_rank = next(rank for rank, count in counts.items() if count == 2)  # noqa: PLR2004
            return sorted(
                [card for card in self.cards if card.rank.value == pair_rank],
                key=lambda c: c.rank.value,
                reverse=True,
            )

        # HIGH_CARD: return the highest card
        return sorted(self.cards, key=lambda c: c.rank.value, reverse=True)[:1]

    @property
    def kickers(self) -> list[PokerCard]:
        """Get the kicker cards (cards not part of the winning rank).

        Returns:
            list[PokerCard]: kicker cards sorted by rank in descending order

        """
        rank_card_set = {id(card) for card in self.rank_cards}
        kicker_list = [card for card in self.cards if id(card) not in rank_card_set]
        return sorted(kicker_list, key=lambda c: c.rank.value, reverse=True)


if __name__ == "__main__":
    # Example usage
    deck = PokerCard.generate_deck()
    while True:
        random_hand = random.sample(deck, 5)
        poker_hand = PokerHand(random_hand)
        # Look for a certain hand for testing
        if poker_hand.rank == PokerHandRank.STRAIGHT and Rank.ACE in [
            card.rank for card in poker_hand.cards
        ]:
            print("Hand:", ", ".join(str(card) for card in poker_hand.cards))
            print("Hand Rank:", poker_hand.rank.value)
            print("Rank Cards:", ", ".join(str(card) for card in poker_hand.rank_cards))
            print("Kickers:", ", ".join(str(card) for card in poker_hand.kickers))
            break
