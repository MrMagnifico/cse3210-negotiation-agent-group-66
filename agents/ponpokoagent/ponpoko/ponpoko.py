import logging
from decimal import Decimal
from math import isclose
from random import randint
from time import time_ns
from typing import Dict, cast
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
from geniusweb.issuevalue.Domain import Domain
from geniusweb.opponentmodel.FrequencyOpponentModel import FrequencyOpponentModel
from geniusweb.party.Capabilities import Capabilities
from geniusweb.party.DefaultParty import DefaultParty
from geniusweb.profile.utilityspace.UtilitySpace import UtilitySpace
from geniusweb.profileconnection.ProfileConnectionFactory import ProfileConnectionFactory
from geniusweb.progress.ProgressRounds import ProgressRounds
from geniusweb.progress.ProgressTime import ProgressTime
from geniusweb.utils import val

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
        self._utility_generator = Patterns(False)
        self._utility_func = next(self._utility_generator)
        self._PATTERN_CHANGE_FREQUENCY = -1
        self._receivedBids = []
        self._opponentEpsilonHigher = -1
        self._opponentEpsilonLower = -1
        self._moveCounts: Dict[str, int] = {"conceder": 0, "hardliner": 0, "neutral": 0}
        self._opponentModeled = False

    # Override
    def notifyChange(self, info: Inform):
        if isinstance(info, Settings):
            self._settings: Settings = cast(Settings, info)
            self._me = self._settings.getID()
            self._protocol: str = str(self._settings.getProtocol().getURI())
            self._progress = self._settings.getProgress()
            
            if self._settings.getParameters().containsKey("patternChangeFrequency"):
                self._PATTERN_CHANGE_FREQUENCY = int(self._settings.getParameters().get("patternChangeFrequency"))
                self.getReporter().log(
                    logging.INFO,
                    f"Pattern change frequency set to {self._PATTERN_CHANGE_FREQUENCY}")
            self._pattern_change_count = self._PATTERN_CHANGE_FREQUENCY

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
        Offers random bids until a bid with sufficient utility (> 0.7) is offered.
        Parameters minPower and maxPower can be used to control voting behaviour.
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
            self._pattern_change_count = self._PATTERN_CHANGE_FREQUENCY
        else:
            self._pattern_change_count -= 1
        if self._opponentEpsilonHigher != -1 and self._opponentEpsilonLower != -1:
            self._updateMoves(self._opponentEpsilonHigher, self._opponentEpsilonLower)
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
        if self._opponentEpsilonHigher != -1 and self._opponentEpsilonLower != -1 and self._getTimeFraction() >= 0.3:
            self._utility_generator._opponent = max(self._moveCounts, key=self._moveCounts.get)
            self._utility_func = next(self._utility_generator)
        high, low = self._utility_func(self._getTimeFraction(), 1.0)
        self.getReporter().log(logging.INFO,
                                f"Utility range [{low}, {high}]")

        median = (high + low) / 2
        close_to_median = []

        for _attempt in range(allBids.size()):
            bid = allBids.get(_attempt)

            # Update bids close to median utility
            current_bid_diff = abs(
                self._profile.getProfile().getUtility(bid)
                - Decimal(median))
            if isclose(current_bid_diff, 0, abs_tol=0.05):
                close_to_median.append(bid)

            if self._isGood(bid):
                candidate_found = True
                break

        if not candidate_found:
            bid = close_to_median[randint(0, len(close_to_median) - 1)]
        return bid

    def _updateMoves(self, epsilonHigher, epsilonLower):
        if len(self._receivedBids) == 0:
            self._receivedBids.append(self._lastReceivedBid)
        else:
            self._receivedBids.append(self._lastReceivedBid)
            util = lambda bid : self._profile.getProfile().getUtility(bid)
            if (util(self._lastReceivedBid) - util(self._receivedBids[-1])) > epsilonHigher:
                self._moveCounts["conceder"] += 1
            elif (util(self._lastReceivedBid) - util(self._receivedBids[-1])) < epsilonLower:
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
