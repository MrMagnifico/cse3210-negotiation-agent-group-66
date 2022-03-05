import logging
from decimal import Decimal
from math import isclose
from random import randint
from time import time_ns
from typing import cast
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

    # Override
    def notifyChange(self, info: Inform):
        if isinstance(info, Settings):
            self._settings: Settings = cast(Settings, info)
            self._me = self._settings.getID()
            self._protocol: str = str(self._settings.getProtocol().getURI())
            self._progress = self._settings.getProgress()

            if "Learn" == self._protocol:
                self.getConnection().send(LearningDone(self._me))  #type:ignore
            else:
                self._profile = ProfileConnectionFactory.create(
                    info.getProfile().getURI(), self.getReporter())

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
        A clean-room implementation of PonPokoAgent from ANAC 2017:
        https://homepages.cwi.nl/~baarslag/pub/ANAC_2017-Repeated_Multilateral_Negotiation_League.pdf
        """

    # Override
    def terminate(self):
        self.getReporter().log(logging.INFO, "PonPokoAgent is terminating:")
        super().terminate()
        if self._profile is not None:
            self._profile.close()
            self._profile = None

    def _myTurn(self):
        if self._isGood(self._lastReceivedBid):
            action = Accept(self._me, self._lastReceivedBid)
        else:
            allBids = AllBidsList(self._profile.getProfile().getDomain())
            candidate_found = False
            high, low = self._utility_func(self._getTimeFraction(), 1.0)
            self.getReporter().log(logging.INFO,
                                   f"Utility range [{low}, {high}]")

            for _attempt in range(allBids.size()):
                bid = allBids.get(_attempt)
                if self._isGood(bid):
                    break
                
            action = Offer(self._me, bid)
        self.getConnection().send(action)

    def _isGood(self, bid: Bid) -> bool:
        high, low = self._utility_func(self._getTimeFraction(), 0.0)

        if bid is None:
            return False
        profile = self._profile.getProfile()
        if isinstance(profile, UtilitySpace):
            return profile.getUtility(bid) >= low and profile.getUtility(bid) <= high
        raise Exception("Cannot handle this type of profile")

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
