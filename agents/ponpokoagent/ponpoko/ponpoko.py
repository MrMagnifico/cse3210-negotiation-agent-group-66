import logging
from decimal import Decimal
from math import isclose
from random import randint
from time import time_ns
from typing import cast
from typing import Dict
from typing import Set

from geniusweb.actions.Accept import Accept
from geniusweb.actions.Action import Action
from geniusweb.actions.LearningDone import LearningDone
from geniusweb.actions.Offer import Offer
from geniusweb.actions.Vote import Vote
from geniusweb.actions.Votes import Votes
from geniusweb.bidspace.AllBidsList import AllBidsList
from geniusweb.inform.ActionDone import ActionDone
from geniusweb.inform.Finished import Finished
from geniusweb.inform.Inform import Inform
from geniusweb.inform.OptIn import OptIn
from geniusweb.inform.Settings import Settings
from geniusweb.inform.Voting import Voting
from geniusweb.inform.YourTurn import YourTurn
from geniusweb.issuevalue.Bid import Bid
from geniusweb.party.Capabilities import Capabilities
from geniusweb.party.DefaultParty import DefaultParty
from geniusweb.profile.utilityspace.UtilitySpace import UtilitySpace
from geniusweb.profileconnection.ProfileConnectionFactory import ProfileConnectionFactory
from geniusweb.progress.ProgressRounds import ProgressRounds
from geniusweb.progress.ProgressTime import ProgressTime
from geniusweb.utils import val

from .patterns import PatternGeneratorType
from .patterns import Patterns


class PonPokoParty(DefaultParty):
    """
    PonPoko offers bids with a randomly selected pattern each session.

    Offers random bids within a particular utility value
    range until opponent accepts a generated bid or
    opponent offers a bid falling within the utility
    value range.
    """

    def __init__(self):
        super().__init__()
        self._profile = None
        self._lastReceivedBid: Bid = None
        self._FALLBACK_BID_UTIL_RANGE = 0.05
        self._utility_generator = Patterns(PatternGeneratorType.Opponent)
        self._utility_func = next(self._utility_generator)
        self._PATTERN_CHANGE_DELAY = -1
        self._receivedBids = []
        self._OPPONENT_EPSILON_HIGHER = 0.25
        self._OPPONENT_EPSILON_LOWER = 0.1
        self._moveCounts: Dict[str, int] = {
            "conceder": 0,
            "hardliner": 0,
            "neutral": 0
        }
        self._opponentModeled = False

    # Override
    def notifyChange(self, info: Inform):
        if isinstance(info, Settings):
            self._settings: Settings = cast(Settings, info)
            self._me = self._settings.getID()
            self._protocol: str = str(self._settings.getProtocol().getURI())
            self._progress = self._settings.getProgress()

            self._processParameters()
            self._pattern_change_count = self._PATTERN_CHANGE_DELAY

            if "Learn" == self._protocol:
                self.getConnection().send(LearningDone(self._me))  #type:ignore
            else:
                self._profile = ProfileConnectionFactory.create(
                    info.getProfile().getURI(), self.getReporter())
            self._opponentModeled = False

        elif isinstance(info, ActionDone):
            action: Action = cast(ActionDone, info).getAction()
            if isinstance(action, Offer):
                self._lastReceivedBid = cast(Offer, action).getBid()

        elif isinstance(info, YourTurn):
            self._myTurn()
            if isinstance(self._progress, ProgressRounds):
                self._progress = self._progress.advance()

        elif isinstance(info, Finished):
            self.terminate()

        elif isinstance(info, Voting):
            # MOPAC protocol
            self._lastvotes = self._vote(cast(Voting, info))
            val(self.getConnection()).send(self._lastvotes)

        elif isinstance(info, OptIn):
            val(self.getConnection()).send(self._lastvotes)

        else:
            self.getReporter().log(logging.WARNING,
                                   "Ignoring unknown info " + str(info))

    # Override
    def getCapabilities(self) -> Capabilities:
        return Capabilities(
            set(["SAOP", "Learn", "MOPAC"]),
            set(['geniusweb.profile.utilityspace.LinearAdditive']))

    # Override
    def getDescription(self) -> str:
        return """
        PonPokoAgent with a few tricks up its sleeve. See accompanying report.
        """

    # Override
    def terminate(self):
        self.getReporter().log(logging.INFO, "party is terminating:")
        super().terminate()
        if self._profile is not None:
            self._profile.close()
            self._profile = None

    def _myTurn(self):
        if self._pattern_change_count == 0:
            self.getReporter().log(
                logging.INFO,
                f"Changing utility function to {self._utility_generator._index}"
            )
            self._utility_func = next(self._utility_generator)
            self._pattern_change_count = self._PATTERN_CHANGE_DELAY
        else:
            self._pattern_change_count -= 1
        if ((self._OPPONENT_EPSILON_HIGHER != -1
             or self._OPPONENT_EPSILON_LOWER != -1)
                and self._utility_generator._type
                == PatternGeneratorType.Opponent):
            self._updateMoves()

        if self._isGood(self._lastReceivedBid):
            action = Accept(self._me, self._lastReceivedBid)
        else:
            bid = self._getBid()
            action = Offer(self._me, bid)

        self.getConnection().send(action)

    def _isGood(self, bid: Bid) -> bool:
        high, low = self._utility_func(self._getTimeFraction(), 0.0)

        if bid is None:
            return False
        profile = self._profile.getProfile()
        if isinstance(profile, UtilitySpace):
            return profile.getUtility(bid) >= low and profile.getUtility(
                bid) <= high
        raise Exception("Can not handle this type of profile")

    def _getBid(self):
        allBids = AllBidsList(self._profile.getProfile().getDomain())
        candidate_found = False
        if ((self._OPPONENT_EPSILON_HIGHER != -1
             or self._OPPONENT_EPSILON_LOWER != -1) and
                self._utility_generator._type == PatternGeneratorType.Opponent
                and self._getTimeFraction() >= 0.3):
            self._utility_generator._opponent = max(self._moveCounts,
                                                    key=self._moveCounts.get)
            self._utility_func = next(self._utility_generator)

        high, low = self._utility_func(self._getTimeFraction(), 1.0)
        self.getReporter().log(logging.INFO, f"Utility range [{low}, {high}]")

        median = (high + low) / 2
        close_to_median = []

        for _attempt in range(allBids.size()):
            bid = allBids.get(_attempt)

            # Update bids close to median utility
            current_bid_diff = abs(self._profile.getProfile().getUtility(bid)
                                   - Decimal(median))
            if isclose(current_bid_diff,
                       0,
                       abs_tol=self._FALLBACK_BID_UTIL_RANGE):
                close_to_median.append(bid)

            if self._isGood(bid):
                candidate_found = True
                break

        if not candidate_found:
            try:
                bid = close_to_median[randint(0, len(close_to_median) - 1)]
            except ValueError:
                pass
        return bid

    def _updateMoves(self):

        def _util(bid):
            return self._profile.getProfile().getUtility(bid)

        if len(self._receivedBids) == 0:
            self._receivedBids.append(self._lastReceivedBid)
            return

        self._receivedBids.append(self._lastReceivedBid)
        if (_util(self._lastReceivedBid) - _util(
                self._receivedBids[-1])) > self._OPPONENT_EPSILON_HIGHER:
            self._moveCounts["conceder"] += 1
        elif (_util(self._lastReceivedBid)
              - _util(self._receivedBids[-1])) < self._OPPONENT_EPSILON_LOWER:
            self._moveCounts["hardliner"] += 1
        else:
            self._moveCounts["neutral"] += 1

    def _vote(self, voting: Voting) -> Votes:
        """
        @param voting the {@link Voting} object containing the options.

        @return our next Votes.
        """
        val = self._settings.getParameters().get("minPower")
        minpower: int = val if isinstance(val, int) else 2
        val = self._settings.getParameters().get("maxPower")
        maxpower: int = val if isinstance(val, int) else 9999999

        votes: Set[Vote] = set([
            Vote(self._me, offer.getBid(), minpower, maxpower)
            for offer in voting.getOffers() if self._isGood(offer.getBid())
        ])
        return Votes(self._me, votes)

    def _getTimeFraction(self) -> float:
        """Calculate time value as fraction of negotiation time elapsed."""
        elapsed_time = 0
        if isinstance(self._progress, ProgressRounds):
            elapsed_time = self._progress.getCurrentRound(
            ) / self._progress.getDuration()
        elif isinstance(self._progress, ProgressTime):
            elapsed_time = self._progress.get(time_ns() // 1e6)
        return elapsed_time

    def _processParameters(self):
        """Save any passed parameter values."""
        if self._settings.getParameters().containsKey("generatorType"):
            var = int(self._settings.getParameters().get("generatorType"))
            self._utility_generator._type = PatternGeneratorType(var)
            self.getReporter().log(logging.INFO, f"Generator type {var}")
            self._utility_func = next(self._utility_generator)

        if self._settings.getParameters().containsKey("patternChangeDelay"):
            self._PATTERN_CHANGE_DELAY = int(
                self._settings.getParameters().get("patternChangeDelay"))
            self.getReporter().log(
                logging.INFO,
                f"Pattern change frequency set to {self._PATTERN_CHANGE_DELAY}"
            )
        if self._settings.getParameters().containsKey("fallbackBidUtilRange"):
            self._FALLBACK_BID_UTIL_RANGE = float(
                self._settings.getParameters().get("fallbackBidUtilRange"))
            self.getReporter().log(
                logging.INFO,
                f"Fallback bid utility range set to {self._FALLBACK_BID_UTIL_RANGE}"
            )
        if self._settings.getParameters().containsKey("opponentEpsilonLower"):
            self._OPPONENT_EPSILON_LOWER = float(
                self._settings.getParameters().get("opponentEpsilonLower"))
            self.getReporter().log(
                logging.INFO,
                f"Opponent epsilon lower bound set to {self._OPPONENT_EPSILON_LOWER}"
            )
        if self._settings.getParameters().containsKey("opponentEpsilonHigher"):
            self._OPPONENT_EPSILON_HIGHER = float(
                self._settings.getParameters().get("opponentEpsilonHigher"))
            self.getReporter().log(
                logging.INFO,
                f"Opponent epsilon upper bound set to {self._OPPONENT_EPSILON_HIGHER}"
            )
