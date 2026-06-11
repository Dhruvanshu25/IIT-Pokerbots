from pkbot.actions import ActionFold, ActionCall, ActionCheck, ActionRaise, ActionBid
from pkbot.states import GameInfo, PokerState
from pkbot.base import BaseBot
from pkbot.runner import parse_args, run_bot
import eval7
import random

RANK_ORDER     = "23456789TJQKA"
BIG_BLIND      = 20
STARTING_STACK = 5000

HU_EQUITY = {
    "AA":0.853,"KK":0.823,"QQ":0.797,"JJ":0.773,"TT":0.751,
    "99":0.720,"88":0.692,"77":0.664,"66":0.637,"55":0.609,
    "44":0.581,"33":0.554,"22":0.527,
    "AKs":0.673,"AQs":0.660,"AJs":0.648,"ATs":0.637,
    "A9s":0.619,"A8s":0.612,"A7s":0.605,"A6s":0.598,
    "A5s":0.605,"A4s":0.596,"A3s":0.590,"A2s":0.583,
    "KQs":0.632,"KJs":0.619,"KTs":0.608,"K9s":0.591,
    "K8s":0.575,"K7s":0.566,"K6s":0.558,"K5s":0.550,
    "K4s":0.543,"K3s":0.537,"K2s":0.531,
    "QJs":0.607,"QTs":0.596,"Q9s":0.578,"Q8s":0.562,
    "Q7s":0.546,"Q6s":0.541,"Q5s":0.535,"Q4s":0.528,
    "Q3s":0.522,"Q2s":0.516,
    "JTs":0.584,"J9s":0.566,"J8s":0.549,"J7s":0.533,
    "J6s":0.518,"J5s":0.513,"J4s":0.507,"J3s":0.501,"J2s":0.495,
    "T9s":0.562,"T8s":0.545,"T7s":0.528,"T6s":0.512,
    "T5s":0.499,"T4s":0.493,"T3s":0.487,"T2s":0.481,
    "98s":0.542,"97s":0.524,"96s":0.508,"95s":0.494,
    "87s":0.522,"86s":0.505,"85s":0.490,"84s":0.476,
    "76s":0.502,"75s":0.486,"74s":0.471,"73s":0.459,
    "65s":0.483,"64s":0.468,"63s":0.454,
    "54s":0.464,"53s":0.450,"52s":0.437,
    "43s":0.445,"42s":0.432,"32s":0.424,
    "AKo":0.651,"AQo":0.637,"AJo":0.624,"ATo":0.612,
    "A9o":0.593,"A8o":0.585,"A7o":0.577,"A6o":0.570,
    "A5o":0.578,"A4o":0.569,"A3o":0.562,"A2o":0.555,
    "KQo":0.608,"KJo":0.594,"KTo":0.582,"K9o":0.564,
    "K8o":0.547,"K7o":0.538,"K6o":0.529,"K5o":0.521,
    "K4o":0.514,"K3o":0.507,"K2o":0.500,
    "QJo":0.581,"QTo":0.569,"Q9o":0.551,"Q8o":0.534,
    "Q7o":0.517,"Q6o":0.511,"Q5o":0.505,"Q4o":0.498,
    "Q3o":0.491,"Q2o":0.485,
    "JTo":0.557,"J9o":0.538,"J8o":0.521,"J7o":0.504,
    "J6o":0.488,"J5o":0.482,"J4o":0.476,"J3o":0.469,"J2o":0.463,
    "T9o":0.535,"T8o":0.517,"T7o":0.500,"T6o":0.483,
    "T5o":0.469,"T4o":0.463,"T3o":0.456,"T2o":0.450,
    "98o":0.515,"97o":0.497,"96o":0.480,"95o":0.465,
    "87o":0.494,"86o":0.477,"85o":0.461,"84o":0.447,
    "76o":0.474,"75o":0.458,"74o":0.443,"73o":0.430,
    "65o":0.455,"64o":0.440,"63o":0.426,
    "54o":0.436,"53o":0.422,"52o":0.408,
    "43o":0.417,"42o":0.403,"32o":0.394,
}

HAND_SCORE = {
    "AA":10,"KK":9,"QQ":8,"JJ":7,"TT":6,"99":5,"88":5,"77":4,"66":4,"55":3,"44":3,"33":2,"22":2,
    "AKs":9,"AQs":8,"AJs":7,"ATs":7,"A9s":6,"A8s":6,"A7s":5,"A6s":5,"A5s":6,"A4s":5,"A3s":5,"A2s":5,
    "KQs":8,"KJs":7,"KTs":6,"K9s":5,"K8s":4,"K7s":4,"K6s":3,
    "QJs":7,"QTs":6,"Q9s":5,"Q8s":4,
    "JTs":7,"J9s":6,"J8s":5,"J7s":4,
    "T9s":6,"T8s":5,"T7s":4,"98s":5,"97s":4,"87s":5,"86s":4,"76s":5,"75s":4,"65s":5,"54s":4,"43s":3,
    "AKo":8,"AQo":7,"AJo":6,"ATo":6,"A9o":5,"A8o":4,"A7o":4,"A6o":3,"A5o":4,"A4o":3,"A3o":3,"A2o":3,
    "KQo":7,"KJo":6,"KTo":5,"K9o":4,
    "QJo":6,"QTo":5,"Q9o":4,
    "JTo":6,"J9o":5,"J8o":4,
    "T9o":5,"T8o":4,"98o":4,"87o":4,"76o":4,"65o":4,"54o":3,
}


class Player(BaseBot):

    ITERS = {
        "normal": {"auction": 100,  "flop": 300,  "turn": 500,   "river": 700},
        "low":    {"auction": 50,   "flop": 150,  "turn": 250,   "river": 350},
        "crit":   {"auction": 20,   "flop": 75,   "turn": 100,   "river": 150},
    }
    TIME_LOW  = 7.0
    TIME_CRIT = 3.0

    def __init__(self):
        self.total_hands = 0
        self._time_bank  = 20.0
        self._bankroll   = 0

        self._opp_has_our_card    = False
        self._we_won_auction      = False
        self._auction_happened    = False
        self._seen_card           = None
        self._seen_card_rank      = None
        self._opp_auction_bid_this_hand = 0

        self._flop_checked        = False
        self._i_bet_flop          = False
        self._i_bet_turn          = False
        self._i_bet_river         = False
        self._opp_raised_me       = False
        self._preflop_raised      = False
        self._bet_this_street     = False
        self._opp_streets_bet     = 0
        self._i_called_streets    = 0
        self._eq_flop             = None
        self._eq_turn             = None
        self._eq_river            = None
        self._we_3bet             = False
        self._auction_trap_hand   = False
        self._auction_context_set = False
        self._opp_bet_streets_this_hand = []

        self.opp_preflop_shoves   = 0
        self.opp_preflop_raises   = 0

        self._opp_bid_counts      = {}
        self._opp_bids_list       = []
        self._opp_max_bid_seen    = 0
        self._my_bid_this_hand    = 0
        self._opp_bets_this_hand  = 0

        # ── Inferred auction bid tracking (works for simultaneous auctions) ──
        # Since auctions are simultaneous, opp_bid_now is always 0 at decision time.
        # We infer opp bid from outcome: won → their bid < ours; lost → their bid > ours.
        self._inferred_opp_bids   = []   # inferred upper/lower bounds list
        self._inferred_opp_avg    = 50.0 # running estimate, starts neutral
        self._auction_count       = 0    # total auctions seen

        # ── Neutral Bayesian priors — adapts to any opponent ──
        # Starts balanced; updates toward actual opponent stats each hand.
        # EA-specific priors caused massive bleeding vs bots with fold_to_cbet~0.42.
        _P     = 8
        _VPIP  = 0.55
        _PFR   = 0.38
        _F3B   = 0.55
        _FCBET = 0.42   # neutral prior — updates per hand
        _AGG   = 0.45   # neutral prior — updates per hand

        self.opp_hands_seen  = 0
        self._prior_hands    = _P
        self.opp_vpip_n      = int(_P * _VPIP)
        self.opp_pfr_n       = int(_P * _PFR)
        self._vpip_denom     = _P

        self.opp_3bet_n      = 0
        self.opp_fold_3bet_n = int(_P * _F3B)
        self.opp_3bet_opps   = _P

        self.i_bet_street_n    = {"flop": _P,               "turn": _P,               "river": _P}
        self.opp_folded_to_bet = {"flop": int(_P * _FCBET), "turn": int(_P * _FCBET), "river": int(_P * _FCBET)}
        self.opp_bet_n         = {"flop": int(_P * _AGG),   "turn": int(_P * _AGG),   "river": int(_P * _AGG)}
        self.opp_check_n       = {"flop": int(_P*(1-_AGG)), "turn": int(_P*(1-_AGG)), "river": int(_P*(1-_AGG))}
        self.opp_call_my_bet   = {"flop": 0, "turn": 0, "river": 0}

        self.opp_auction_wins    = 0
        self.opp_auction_wins_wd = 0

        self._opp_pfr_this_hand  = False

    # ════════════════════════════════════════════════════════════
    # MONTE CARLO EQUITY
    # ════════════════════════════════════════════════════════════

    def mc_equity(self, my_hand, board, seen_card=None, iters=100, range_mult=1.0):
        try:
            my_cards    = [eval7.Card(c) for c in my_hand]
            board_cards = [eval7.Card(c) for c in board]
            known    = set(my_hand) | set(board)
            use_seen = bool(seen_card and seen_card not in known)
            if use_seen:
                known.add(seen_card)
            deck = [eval7.Card(r + s)
                    for r in "23456789TJQKA" for s in "cdhs"
                    if (r + s) not in known]
            seen_ev = eval7.Card(seen_card) if use_seen else None
            to_come = 5 - len(board)
            need    = to_come + (1 if seen_ev else 2)
            if len(deck) < need or need < 0:
                return 0.5
            wins = 0.0
            for _ in range(iters):
                sample = random.sample(deck, need)
                if seen_ev:
                    opp = [seen_ev, sample[0]]
                    run = board_cards + sample[1:1 + to_come]
                else:
                    opp = [sample[0], sample[1]]
                    run = board_cards + sample[2:2 + to_come]
                mv = eval7.evaluate(my_cards + run)
                ov = eval7.evaluate(opp + run)
                if   mv > ov:  wins += 1.0
                elif mv == ov: wins += 0.5
            return max(0.04, min(0.96, (wins / iters) * range_mult))
        except Exception:
            return 0.5

    def _iters(self, street):
        try:
            tb  = self._time_bank
            lvl = "crit" if tb <= self.TIME_CRIT else ("low" if tb <= self.TIME_LOW else "normal")
            return self.ITERS[lvl].get(street, 100)
        except Exception:
            return 100

    # ════════════════════════════════════════════════════════════
    # OPPONENT PROFILING
    # ════════════════════════════════════════════════════════════

    def vpip(self):
        return self.opp_vpip_n / max(self._vpip_denom, 1)

    def pfr(self):
        return self.opp_pfr_n / max(self._vpip_denom, 1)

    def pfr_freq(self):
        return self.opp_preflop_raises / max(self.opp_hands_seen, 1)

    def fold_to_3bet(self):
        return self.opp_fold_3bet_n / max(self.opp_3bet_opps, 1)

    def fold_to_cbet(self, street):
        n = self.i_bet_street_n.get(street, 1)
        return self.opp_folded_to_bet.get(street, 0) / max(n, 1)

    def opp_agg(self, street):
        b = self.opp_bet_n.get(street, 0)
        c = self.opp_check_n.get(street, 0)
        return b / max(b + c, 1)

    def opp_call_rate(self, street):
        calls = self.opp_call_my_bet.get(street, 0)
        folds = self.opp_folded_to_bet.get(street, 0)
        real_folds = max(folds - int(self._prior_hands * 0.88), 0)
        real_n     = calls + real_folds
        if real_n < 4:
            return 0.40   # neutral-lean: assume moderate calling until data arrives
        return calls / max(real_n, 1)

    def _confidence(self, n_real_hands, needed=10):
        return min(n_real_hands / needed, 1.0)

    def is_fish(self):
        c = self._confidence(self.opp_hands_seen)
        return c > 0.4 and self.vpip() > 0.70 and self.pfr() < 0.25

    def is_nit(self):
        c = self._confidence(self.opp_hands_seen)
        return c > 0.6 and self.vpip() < 0.28

    def is_lag(self):
        c = self._confidence(self.opp_hands_seen)
        return c > 0.6 and self.vpip() > 0.50 and self.pfr() > 0.38

    def is_maniac(self):
        c = self._confidence(self.opp_hands_seen, needed=8)
        return c > 0.6 and self.opp_agg("flop") > 0.55 and self.opp_agg("turn") > 0.45

    def is_preflop_maniac(self):
        if self.opp_hands_seen < 8:
            return False
        return self.pfr_freq() > 0.55

    def is_gto_like(self):
        if self.opp_hands_seen < 15:
            return False
        v   = self.vpip()
        p   = self.pfr()
        ftc = self.fold_to_cbet("flop")
        return (0.38 <= v <= 0.72 and p / max(v, 0.01) > 0.58 and ftc < 0.42)

    def is_extreme_folder(self):
        if self.opp_hands_seen < 8:
            return False   # wait for real data, don't assume EA-style folding
        return self.fold_to_cbet("flop") > 0.72 and self.fold_to_cbet("turn") > 0.65

    def is_high_folder(self):
        c = self._confidence(self.opp_hands_seen, needed=15)
        if c < 0.4:
            return False  # not enough data to classify
        return self.fold_to_cbet("flop") > 0.60 or self.vpip() < 0.50

    def is_value_bettor_only(self):
        if self.opp_hands_seen < 8:
            return False
        avg_agg = (self.opp_agg("flop") + self.opp_agg("turn") + self.opp_agg("river")) / 3
        return avg_agg < 0.38 and self.fold_to_cbet("flop") > 0.75

    def opp_shove_freq(self):
        return self.opp_preflop_shoves / max(self.opp_hands_seen, 1)

    def is_preflop_shover(self):
        return self.opp_hands_seen >= 8 and self.opp_shove_freq() > 0.04

    def preflop_shove_call_threshold(self):
        if self.is_preflop_shover():
            return 0.70
        if self.opp_shove_freq() > 0.30 and self.opp_hands_seen >= 8:
            return 0.52
        return 0.62

    # ── Auction bid profiling ──────────────────────────────────
    def opp_avg_bid(self):
        # Prefer real observed bids (sequential); fall back to inferred from outcomes
        valid = [b for b in self._opp_bids_list if b > 0]
        if valid:
            return sum(valid) / len(valid)
        if len(self._inferred_opp_bids) >= 3:
            return self._inferred_opp_avg
        return 50  # neutral default

    def is_high_bidder(self):
        """Opp consistently bids high (avg > 55)."""
        valid = [b for b in self._opp_bids_list if b > 0]
        if len(valid) >= 5:
            return sum(valid) / len(valid) > 55
        # Use inferred avg after 6 auctions
        if len(self._inferred_opp_bids) >= 6:
            return self._inferred_opp_avg > 55
        return False

    def is_low_bidder(self):
        """Opp bids very low (avg < 10)."""
        valid = [b for b in self._opp_bids_list if b > 0]
        if len(valid) >= 5:
            return sum(valid) / len(valid) < 10
        # Use inferred avg after 6 auctions
        if len(self._inferred_opp_bids) >= 6:
            return self._inferred_opp_avg < 12
        return False

    def is_medium_bidder(self):
        valid = [b for b in self._opp_bids_list if b > 0]
        return len(valid) >= 5 and 8 <= self.opp_avg_bid() <= 55

    def is_fixed_bidder(self):
        valid = {k: v for k, v in self._opp_bid_counts.items() if k > 0}
        if len(self._opp_bids_list) < 5 or not valid:
            return False
        top_count = max(valid.values())
        return top_count / max(len(self._opp_bids_list), 1) > 0.40

    def fixed_bid_amount(self):
        valid = {k: v for k, v in self._opp_bid_counts.items() if k > 0}
        if not valid:
            return 25
        return max(valid, key=valid.get)

    def _is_binary_bidder(self):
        valid = [b for b in self._opp_bids_list if b > 0]
        if len(valid) < 8:
            return False
        total = len(valid)
        low_bids  = sum(1 for b in valid if b <= 12)
        mid_bids  = sum(1 for b in valid if 13 <= b < 50)
        high_bids = sum(1 for b in valid if b >= 100)
        return (low_bids / total > 0.40) and (high_bids / total > 0.20) and (mid_bids / total < 0.25)

    def _binary_bidder_low_threshold(self):
        valid = [b for b in self._opp_bids_list if 0 < b <= 12]
        if not valid:
            return 8
        counts = {}
        for b in valid:
            counts[b] = counts.get(b, 0) + 1
        return max(counts, key=counts.get)

    def bid_pct(self, p=0.80):
        valid = sorted(b for b in self._opp_bids_list if b > 0)
        if len(valid) < 5:
            return 30
        return valid[min(int(len(valid) * p), len(valid) - 1)]

    def range_mult_facing_bet(self, street, i_was_aggressor=False, facing_raise=False):
        """EA bets value-heavy (28.7% freq, mostly after winning auction). Tighten."""
        base_mult = 1.0
        if self.is_maniac():
            base_mult = 0.97
        elif self.is_fish():
            base_mult = 0.90
        elif self.is_nit():
            base_mult = 0.82
        else:
            agg = self.opp_agg(street)
            base_mult = max(0.82, min(0.95, 0.82 + agg * 0.20))
        if self._opp_bets_this_hand >= 2:
            base_mult *= 0.82
        elif self._opp_bets_this_hand >= 1:
            base_mult *= 0.90
        if i_was_aggressor:
            if facing_raise:
                base_mult *= 0.72
            else:
                base_mult *= 0.93
        elif facing_raise:
            base_mult *= 0.82
        return base_mult

    def preflop_eq(self, hand):
        return HU_EQUITY.get(hand, 0.50)

    # ════════════════════════════════════════════════════════════
    # EQUITY TREND
    # ════════════════════════════════════════════════════════════

    def equity_trend(self, street):
        try:
            if street == "turn" and self._eq_flop is not None:
                return self._eq_turn - self._eq_flop if self._eq_turn is not None else 0.0
            if street == "river":
                if self._eq_turn is not None:
                    return self._eq_river - self._eq_turn if self._eq_river is not None else 0.0
                if self._eq_flop is not None:
                    return self._eq_river - self._eq_flop if self._eq_river is not None else 0.0
            return 0.0
        except Exception:
            return 0.0

    def trend_size_mult(self, street):
        try:
            trend = self.equity_trend(street)
            if   trend >  0.12: return 1.15
            elif trend >  0.06: return 1.08
            elif trend > -0.06: return 1.00
            elif trend > -0.12: return 0.92
            else:               return 0.82
        except Exception:
            return 1.00

    # ════════════════════════════════════════════════════════════
    # ACTION HELPERS
    # ════════════════════════════════════════════════════════════

    def raise_(self, state, frac):
        try:
            if not state.can_act(ActionRaise):
                return None
            mn, mx = int(state.raise_bounds[0]), int(state.raise_bounds[1])
            if mn > mx:
                return None
            amt = int(max(int(state.pot * frac), mn))
            amt = min(amt, mx)
            return ActionRaise(amt) if mn <= amt <= mx else None
        except Exception:
            return None

    def raise_to(self, state, amount):
        try:
            if not state.can_act(ActionRaise):
                return None
            mn, mx = int(state.raise_bounds[0]), int(state.raise_bounds[1])
            if mn > mx:
                return None
            amt = max(amount, mn)
            amt = min(amt, mx)
            return ActionRaise(amt) if mn <= amt <= mx else None
        except Exception:
            return None

    def raise_bb(self, state, num_bb):
        try:
            if not state.can_act(ActionRaise):
                return None
            mn, mx = int(state.raise_bounds[0]), int(state.raise_bounds[1])
            if mn > mx:
                return None
            amt = int(max(int(num_bb * BIG_BLIND), mn))
            amt = min(amt, mx)
            return ActionRaise(amt) if mn <= amt <= mx else None
        except Exception:
            return None

    def shove(self, state):
        try:
            if not state.can_act(ActionRaise):
                return None
            mn, mx = int(state.raise_bounds[0]), int(state.raise_bounds[1])
            return ActionRaise(mx) if mn <= mx else None
        except Exception:
            return None

    def safe_call(self, state):
        try:
            if state.can_act(ActionCall):  return ActionCall()
            if state.can_act(ActionCheck): return ActionCheck()
        except Exception:
            pass
        return ActionFold()

    def safe_check(self, state):
        try:
            if state.can_act(ActionCheck): return ActionCheck()
            if state.can_act(ActionCall):  return ActionCall()
        except Exception:
            pass
        return ActionFold()

    def pot_odds(self, state):
        try:
            if state.cost_to_call <= 0:
                return 0.0
            return state.cost_to_call / (state.pot + state.cost_to_call)
        except Exception:
            return 0.5

    def facing_shove(self, state):
        try:
            eff = min(state.my_chips, state.opp_chips)
            return state.cost_to_call > 0 and state.cost_to_call >= eff * 0.80
        except Exception:
            return False

    def spr(self, state):
        try:
            return state.my_chips / max(state.pot, 1)
        except Exception:
            return 10.0

    def risk_mult(self):
        try:
            br = self._bankroll
            if br < -3000: return 0.92
            if br < -1000: return 0.94
            if br > 3000:  return 1.06
            if br > 1000:  return 1.02
            return 1.00
        except Exception:
            return 1.00

    def bet_size_frac(self, eq, street):
        """
        Adaptive bet sizing. Capped at 1.5x pot normally to avoid overbetting.
        Only overbets when opponent confirmed as extreme folder.
        """
        edge = max(eq - 0.50, 0.0)
        frac = 0.50 + edge * 4.5   # neutral base
        frac = min(frac, 1.5)      # hard cap 1.5x — prevents avg 350+ chip bets
        if street == "river":
            frac = min(frac * 1.10, 1.0)
            if eq < 0.75:
                frac = min(frac, 0.70)  # cap medium-strength river bets
        # Only inflate sizing when fold rate is confirmed high
        if self.is_extreme_folder():
            frac = max(frac, 0.75)
            frac = min(frac * 1.20, 2.0)   # extreme folders: can overbet
        elif self.opp_call_rate(street) > 0.70:
            frac = min(frac * 0.85, 1.2)
        frac *= random.uniform(0.88, 1.12)
        return frac

    # ════════════════════════════════════════════════════════════
    # CARD STRENGTH HELPERS
    # ════════════════════════════════════════════════════════════

    def _card_rank_idx(self, card):
        try:
            return RANK_ORDER.index(card[0])
        except Exception:
            return 0

    def _card_connects_with_board(self, card, board):
        try:
            if not card or not board:
                return False
            r, s = card[0], card[1]
            brs = [c[0] for c in board]
            bss = [c[1] for c in board]
            if r in brs:
                return True
            sc = {}
            for bs in bss:
                sc[bs] = sc.get(bs, 0) + 1
            if sc.get(s, 0) >= 2:
                return True
            rv = RANK_ORDER.index(r)
            return any(abs(RANK_ORDER.index(br) - rv) <= 2 for br in brs)
        except Exception:
            return True

    def _seen_card_is_weak(self, board):
        if not self._seen_card:
            return False
        return not self._card_connects_with_board(self._seen_card, board)

    # ════════════════════════════════════════════════════════════
    # LIFECYCLE
    # ════════════════════════════════════════════════════════════

    def on_hand_start(self, game_info: GameInfo, current_state: PokerState) -> None:
        try:
            self.total_hands      += 1
            self._time_bank        = game_info.time_bank
            self._bankroll         = game_info.bankroll
            self._seen_card        = None
            self._seen_card_rank   = None
            self._opp_has_our_card = False
            self._we_won_auction   = False
            self._auction_happened = False
            self._auction_context_set = False
            self._opp_auction_bid_this_hand = 0
            self._flop_checked     = False
            self._i_bet_flop       = False
            self._i_bet_turn       = False
            self._i_bet_river      = False
            self._opp_raised_me    = False
            self._preflop_raised   = False
            self._bet_this_street  = False
            self._opp_streets_bet  = 0
            self._i_called_streets = 0
            self._eq_flop          = None
            self._eq_turn          = None
            self._eq_river         = None
            self._we_3bet          = False
            self._auction_trap_hand = False
            self._opp_bet_streets_this_hand = []
            self._my_bid_this_hand = 0
            self._opp_pfr_this_hand = False
            self._opp_bets_this_hand = 0
        except Exception:
            pass

    def on_hand_end(self, game_info: GameInfo, current_state: PokerState) -> None:
        try:
            self.opp_hands_seen += 1
            self._vpip_denom    += 1
            street = current_state.street
            ow     = int(getattr(current_state, 'opp_wager', 0) or 0)
            mw     = int(getattr(current_state, 'my_wager',  0) or 0)
            payoff = getattr(current_state, 'payoff', 0) or 0
            if self._opp_has_our_card:
                self.opp_auction_wins += 1
                if payoff < 0:
                    self.opp_auction_wins_wd += 1
            bet_streets = []
            if self._i_bet_flop:  bet_streets.append("flop")
            if self._i_bet_turn:  bet_streets.append("turn")
            if self._i_bet_river: bet_streets.append("river")
            if bet_streets:
                last_bet_street = bet_streets[-1]
                if payoff > 0:
                    self.opp_folded_to_bet[last_bet_street] = self.opp_folded_to_bet.get(last_bet_street, 0) + 1
                else:
                    self.opp_call_my_bet[last_bet_street]   = self.opp_call_my_bet.get(last_bet_street, 0) + 1
            if street in self.opp_bet_n:
                if ow > mw:
                    self.opp_bet_n[street]   = self.opp_bet_n.get(street, 0) + 1
                else:
                    self.opp_check_n[street] = self.opp_check_n.get(street, 0) + 1
            if payoff > 0 and self._we_3bet and street == "preflop":
                self.opp_fold_3bet_n += 1
            if self._opp_pfr_this_hand:
                self.opp_preflop_raises += 1

            # ── Infer opponent auction bid from outcome ──────────────────────
            # Auctions are simultaneous so opp_bid_now=0 during our decision.
            # After the hand: if we_won_auction → their bid < ours (infer low)
            #                 if opp_has_our_card → their bid > ours (infer high)
            if self._auction_happened and self._my_bid_this_hand > 0:
                my_bid = self._my_bid_this_hand
                self._auction_count += 1
                if self._we_won_auction:
                    # Their bid was less than my_bid.
                    # If we bid much more than our inferred avg (early overbid), they bid very little.
                    ratio = my_bid / max(self._inferred_opp_avg, 1)
                    if ratio > 1.5:
                        inferred = max(1, int(my_bid * 0.30))  # they bid far less
                    else:
                        inferred = max(1, int(my_bid * 0.50))
                elif self._opp_has_our_card:
                    # Their bid was more than my_bid — use my_bid * 1.5 as estimate
                    inferred = int(my_bid * 1.50)
                else:
                    inferred = my_bid  # no auction this hand, skip
                    self._auction_count -= 1
                if self._auction_count > 0:
                    self._inferred_opp_bids.append(inferred)
                    if len(self._inferred_opp_bids) > 60:
                        self._inferred_opp_bids.pop(0)
                    if len(self._inferred_opp_bids) >= 3:
                        self._inferred_opp_avg = sum(self._inferred_opp_bids) / len(self._inferred_opp_bids)
        except Exception:
            pass

    # ════════════════════════════════════════════════════════════
    # MAIN ROUTER
    # ════════════════════════════════════════════════════════════

    def get_move(self, game_info: GameInfo, current_state: PokerState):
        try:
            self._time_bank = game_info.time_bank
            self._bankroll  = game_info.bankroll
            s = current_state.street
            if s == "preflop": return self._preflop(current_state)
            if s == "auction": return self._auction(current_state)
            return self._postflop(current_state)
        except Exception:
            try:
                if current_state.can_act(ActionCheck): return ActionCheck()
                if current_state.can_act(ActionCall):  return ActionCall()
            except Exception:
                pass
            return ActionFold()

    # ════════════════════════════════════════════════════════════
    # PREFLOP
    # ════════════════════════════════════════════════════════════

    def _preflop(self, state):
        hand  = self.normalize(state.my_hand)
        sc    = self.hs(hand)
        eq    = self.preflop_eq(hand)
        is_bb = state.is_bb
        cost  = state.cost_to_call

        eff_stack = min(state.my_chips, state.opp_chips)
        eff_bb    = eff_stack / BIG_BLIND
        rm        = self.risk_mult()

        if eff_bb < 15:
            threshold = 5 if rm >= 1.0 else 6
            if sc >= threshold or (hand.endswith("s") and hand[0] == "A"):
                s = self.shove(state)
                return s if s else self.safe_call(state)
            return ActionFold()

        if self.facing_shove(state):
            threshold = self.preflop_shove_call_threshold()
            if self.opp_hands_seen >= 5:
                self.opp_preflop_shoves += 1
            if eq >= threshold:
                return self.safe_call(state)
            return ActionFold()

        if not is_bb:
            if cost > 0:
                self.opp_3bet_opps += 1
                self._opp_pfr_this_hand = True

                pfr_rate  = self.pfr_freq()
                # Ultra-wide: pfr > 45% means opp raises almost every hand
                # pot_odds-based calling is correct: need eq > cost/(pot+cost)
                ultra_wide = pfr_rate > 0.45 and self.opp_hands_seen >= 8
                wide_pfr   = pfr_rate > 0.35 and self.opp_hands_seen >= 10
                po         = self.pot_odds(state)   # e.g. 0.33 at raise-to-60

                if self.is_preflop_maniac() or ultra_wide:
                    # 3bet premium to punish wide range
                    if eq >= 0.68:
                        r = self.raise_bb(state, 12); self._preflop_raised = True; self._we_3bet = True
                        return r if r else self.safe_call(state)
                    # Call with pot-odds equity + small buffer
                    if eq >= po + 0.08:
                        return self.safe_call(state)
                    return ActionFold()

                if eq >= 0.77:
                    s = self.shove(state); self._preflop_raised = True; self._we_3bet = True
                    return s if s else self.safe_call(state)
                if eq >= 0.70:
                    r = self.raise_bb(state, 20); self._preflop_raised = True; self._we_3bet = True
                    return r if r else self.safe_call(state)
                if eq >= 0.65 - (0.05 if wide_pfr else 0.0):
                    return self.safe_call(state)
                if self.fold_to_3bet() > 0.65 and eq >= 0.56:
                    r = self.raise_bb(state, 15); self._preflop_raised = True; self._we_3bet = True
                    return r if r else self.safe_call(state)
                if wide_pfr and eq >= 0.54:
                    return self.safe_call(state)
                if eq >= 0.54 and self.vpip() > 0.65:
                    return self.safe_call(state)
                return ActionFold()
            else:
                # SB open — raise or fold, mirror bot3 thresholds
                if eq >= 0.77:
                    r = self.raise_bb(state, 4); self._preflop_raised = True
                    return r if r else self.safe_check(state)
                if eq >= 0.64:
                    r = self.raise_bb(state, 3); self._preflop_raised = True
                    return r if r else self.safe_check(state)
                if eq >= 0.54:
                    r = self.raise_bb(state, 2); self._preflop_raised = True
                    return r if r else self.safe_check(state)
                steal_prob = 0.60 if (self.is_nit() or self.opp_hands_seen < 10) else 0.35
                if eq >= 0.50 and random.random() < steal_prob:
                    r = self.raise_bb(state, 2); self._preflop_raised = True
                    return r if r else self.safe_check(state)
                return ActionFold()
        else:
            if cost > 0:
                self.opp_vpip_n += 1
                self.opp_pfr_n  += 1
                self._opp_pfr_this_hand = True

                pfr_rate   = self.pfr_freq()
                ultra_wide = pfr_rate > 0.45 and self.opp_hands_seen >= 8
                wide_pfr   = pfr_rate > 0.35 and self.opp_hands_seen >= 10
                po         = self.pot_odds(state)  # e.g. 0.33 at raise-to-60 from BB

                if self.is_preflop_maniac() or ultra_wide:
                    # 3bet to punish ultra-wide range
                    if eq >= 0.68:
                        r = self.raise_bb(state, 10); self._preflop_raised = True; self._we_3bet = True
                        if r: self.opp_3bet_opps += 1; return r
                        return self.safe_call(state)
                    # Call using pot-odds — BB is getting a great price (cost=40 into 120)
                    if eq >= po + 0.06:
                        return self.safe_call(state)
                    return ActionFold()

                if eq >= 0.77:
                    s = self.shove(state); self._preflop_raised = True; self._we_3bet = True
                    if s: self.opp_3bet_opps += 1; return s
                    return self.safe_call(state)
                if eq >= 0.70:
                    r = self.raise_bb(state, 12); self._preflop_raised = True; self._we_3bet = True
                    if r: self.opp_3bet_opps += 1; return r
                    return self.safe_call(state)
                if eq >= 0.60 - (0.05 if wide_pfr else 0.0):
                    return self.safe_call(state)
                if self.is_fish() and eq >= 0.52:
                    return self.safe_call(state)
                if wide_pfr and eq >= 0.52:
                    return self.safe_call(state)
                if self.pot_odds(state) < 0.28 and eq >= 0.54:
                    return self.safe_call(state)
                return ActionFold()
            else:
                _opp_wager_now = int(getattr(state, 'opp_wager', 0) or 0)
                if _opp_wager_now > 0:
                    self.opp_vpip_n += 1
                if eq >= 0.70:
                    s = self.shove(state); self._preflop_raised = True
                    return s if s else self.safe_check(state)
                if eq >= 0.60:
                    r = self.raise_bb(state, 4); self._preflop_raised = True
                    return r if r else self.safe_check(state)
                return self.safe_check(state)

    # ════════════════════════════════════════════════════════════
    # AUCTION
    # ════════════════════════════════════════════════════════════

    def _auction(self, state):
        """
        Smart auction: profile opponent bid style, then counter-bid efficiently.

        vs HIGH bidder (bot3-style: bids ~eq*200, avg > 55):
          Mirror strategy — their equity ≈ (1-our_eq), their bid ≈ mirror formula.
          When ahead (eq > 0.52): bid their mirror + 1 for a cheap win.
          When behind (eq <= 0.52): bid 1 — save chips.

        vs LOW bidder (bot4-style: avg ~22, lots of 1s):
          Bid opp_avg + 2 when we have equity — cheap wins.

        vs UNKNOWN (early game < 5 samples):
          Moderate equity-scaled bids that compete without over-committing.
        """
        try:
            pot   = state.pot
            stack = state.my_chips
            board = state.board

            opp_bid_now = int(getattr(state, 'opp_wager', 0) or 0)
            if opp_bid_now > 0:
                if len(self._opp_bids_list) >= 60:
                    self._opp_bids_list.pop(0)
                self._opp_bids_list.append(opp_bid_now)
                self._opp_bid_counts[opp_bid_now] = self._opp_bid_counts.get(opp_bid_now, 0) + 1
                self._opp_max_bid_seen = max(self._opp_max_bid_seen, opp_bid_now)
                self._opp_auction_bid_this_hand = opp_bid_now

            eq = self.mc_equity(state.my_hand, board, iters=self._iters("auction"))
            self._auction_happened = True

            # ── React to opp's known bid (we see theirs first) ──────────────
            if opp_bid_now > 0:
                if opp_bid_now <= 15:
                    if eq > 0.38:
                        win_bid = min(opp_bid_now + 1, int(stack * 0.10))
                        win_bid = max(win_bid, opp_bid_now + 1)
                        self._my_bid_this_hand = win_bid
                        return ActionBid(win_bid)
                    self._my_bid_this_hand = 1
                    return ActionBid(1)
                elif opp_bid_now <= 60:
                    if eq > 0.50:
                        win_bid = min(opp_bid_now + 1, int(stack * 0.18))
                        self._my_bid_this_hand = win_bid
                        return ActionBid(win_bid)
                    elif eq > 0.42:
                        contest_bid = max(opp_bid_now - 5, 1)
                        self._my_bid_this_hand = contest_bid
                        return ActionBid(contest_bid)
                    self._my_bid_this_hand = 1
                    return ActionBid(1)
                else:
                    # High bid: need real equity advantage
                    if eq > 0.68:
                        win_bid = min(opp_bid_now + 1, int(stack * 0.20))
                        self._my_bid_this_hand = win_bid
                        return ActionBid(win_bid)
                    self._my_bid_this_hand = 1
                    return ActionBid(1)

            # ── We bid first (opp_bid_now == 0) ─────────────────────────────

            # Fixed bidder: beat their fixed amount by 1
            if self.is_fixed_bidder() and len(self._opp_bids_list) >= 5:
                fixed_amt = self.fixed_bid_amount()
                if eq > 0.35:
                    target = min(fixed_amt + 1, int(stack * 0.25))
                    target = max(target, 1)
                    self._my_bid_this_hand = target
                    return ActionBid(target)
                self._my_bid_this_hand = 1
                return ActionBid(1)

            # Near-certain win: trap with low bid (let them overpay)
            if eq > 0.84:
                self._auction_trap_hand = True
                bid = max(1, int(stack * 0.006))
                self._my_bid_this_hand = bid
                return ActionBid(bid)

            # Near-certain loss: save chips
            if eq < 0.16:
                self._my_bid_this_hand = 1
                return ActionBid(1)

            opp_avg = self.opp_avg_bid()   # now uses inferred bids if no real bids
            n_bids  = len(self._opp_bids_list)
            n_inferred = len(self._inferred_opp_bids)

            # ── HIGH BIDDER (PA2/bot3-style avg>55): mirror-equity counter ───
            if self.is_high_bidder() or (n_bids >= 3 and opp_avg > 55) or (n_inferred >= 6 and self._inferred_opp_avg > 55):
                their_eq  = 1.0 - eq
                their_bid = int(12 + max(their_eq - 0.40, 0) * 500)
                their_bid = min(their_bid, int(their_eq * 200))
                if eq > 0.52:
                    win_bid = their_bid + 1
                    win_bid = min(win_bid, int(stack * 0.16))
                    win_bid = max(win_bid, 3)
                    self._my_bid_this_hand = win_bid
                    return ActionBid(win_bid)
                else:
                    self._my_bid_this_hand = 1
                    return ActionBid(1)

            # ── LOW BIDDER (SluggishBays/DivineMind avg<12): cheap wins ──────
            if self.is_low_bidder() or (n_inferred >= 6 and self._inferred_opp_avg < 12):
                beat_amount = max(int(opp_avg) + 2, 3)
                beat_amount = min(beat_amount, 16)
                if eq > 0.42:
                    self._my_bid_this_hand = beat_amount
                    return ActionBid(beat_amount)
                self._my_bid_this_hand = 1
                return ActionBid(1)

            # ── MEDIUM BIDDER (avg 12-55): use inferred avg + margin ──────────
            if n_bids >= 5 or n_inferred >= 8:
                # Use real pct80 if available, otherwise use inferred avg
                if n_bids >= 5:
                    pct80 = self.bid_pct(0.80)
                    target_base = int(pct80 * 1.05) + 2
                else:
                    target_base = int(opp_avg * 1.25) + 3  # inferred: add buffer
                if eq > 0.55:
                    target = min(target_base, int(stack * 0.14))
                    target = max(target, int(opp_avg) + 1)
                    self._my_bid_this_hand = target
                    return ActionBid(target)
                elif eq > 0.48:
                    target = int(opp_avg * 1.05) + 1
                    target = min(target, int(stack * 0.08))
                    target = max(target, 5)
                    self._my_bid_this_hand = target
                    return ActionBid(target)
                else:
                    self._my_bid_this_hand = 1
                    return ActionBid(1)

            # ── EARLY GAME (< 8 auction outcomes): moderate equity-scaled bids ─
            # Must compete with high bidders without over-committing vs low bidders
            if eq >= 0.60:
                bid = int(eq * 130)          # 78 at 0.60, 104 at 0.80
                bid = min(bid, int(stack * 0.13))
            elif eq >= 0.52:
                bid = int(eq * 110)          # 57 at 0.52, 66 at 0.60
                bid = min(bid, int(stack * 0.09))
            elif eq >= 0.46:
                bid = int(eq * 65)           # 30 at 0.46, 34 at 0.52
                bid = min(bid, int(stack * 0.05))
            else:
                bid = 1

            bid = max(bid, 1)
            bid = min(bid, int(stack))
            self._my_bid_this_hand = bid
            return ActionBid(bid)

        except Exception:
            return ActionBid(15)

    # ════════════════════════════════════════════════════════════
    # POSTFLOP
    # ════════════════════════════════════════════════════════════

    def _set_auction_context(self, state, street):
        if self._auction_context_set:
            return
        if not self._auction_happened:
            self._auction_context_set = True
            return
        try:
            if state.opp_revealed_cards:
                card = state.opp_revealed_cards[0]
                self._seen_card      = card
                self._seen_card_rank = self._card_rank_idx(card)
                self._we_won_auction   = True
                self._opp_has_our_card = False
            else:
                self._opp_has_our_card = True
                self._we_won_auction   = False
                self._seen_card        = None
        except Exception:
            pass
        self._auction_context_set = True

    def _postflop(self, state):
        street = state.street
        board  = state.board
        pot    = state.pot
        cost   = state.cost_to_call

        self._set_auction_context(state, street)

        try:
            if state.opp_revealed_cards and not self._seen_card:
                self._seen_card = state.opp_revealed_cards[0]
                self._seen_card_rank = self._card_rank_idx(self._seen_card)
        except Exception:
            pass

        seen = self._seen_card

        if street == "flop":
            self._flop_checked    = False
            _already_bet = self._bet_this_street
            self._bet_this_street = False
        elif street in ("turn", "river"):
            _already_bet = self._bet_this_street
            self._bet_this_street = False
        else:
            _already_bet = False

        if cost > 0 and street in ("flop", "turn", "river"):
            self._opp_bets_this_hand += 1

        i_was_aggressor = (
            (street == "turn"  and self._i_bet_flop and cost > 0) or
            (street == "river" and (self._i_bet_turn or self._i_bet_flop) and cost > 0)
        )
        facing_raise = (cost > 0 and _already_bet)
        if cost > 0 and i_was_aggressor:
            self._opp_raised_me = True

        if cost > 0 and street in ("flop", "turn", "river"):
            self._opp_streets_bet += 1
            self._opp_bet_streets_this_hand.append((street, cost))

        rm = self.range_mult_facing_bet(street, i_was_aggressor, facing_raise) if cost > 0 else 1.0

        if self._opp_has_our_card:
            rm = min(rm, 0.65)

        eq = self.mc_equity(state.my_hand, board,
                            seen_card=seen,
                            iters=self._iters(street),
                            range_mult=rm)

        if   street == "flop":  self._eq_flop  = eq
        elif street == "turn":  self._eq_turn  = eq
        elif street == "river": self._eq_river = eq

        po   = self.pot_odds(state)
        spr  = self.spr(state)

        opp_knows_our_hand   = self._opp_has_our_card
        we_know_their_card   = self._we_won_auction and seen is not None
        their_card_is_weak   = we_know_their_card and self._seen_card_is_weak(board)
        their_card_is_strong = we_know_their_card and self._card_connects_with_board(seen, board)

        opp_won_high_bid = opp_knows_our_hand and (
            self._opp_auction_bid_this_hand > self.opp_avg_bid() * 1.5 or
            self._opp_auction_bid_this_hand > 55
        )

        def opp_small_bet_big_river():
            if street != "river" or cost <= 0:
                return False
            prior_bets = [(s, c) for s, c in self._opp_bet_streets_this_hand if s != "river"]
            if len(prior_bets) < 2:
                return False
            all_small = all(c < 80 for _, c in prior_bets)
            river_bet_big = cost > pot * 0.55
            return all_small and river_bet_big

        # ═══════════════════════════════════════════════════════
        # SPR COMMIT
        # ═══════════════════════════════════════════════════════
        commit_spr = {"flop": 4.0, "turn": 2.8, "river": 1.8}.get(street, 2.8)
        commit_eq  = 0.65 if cost > 0 else 0.60
        if opp_knows_our_hand:
            commit_eq = 0.82
        # On river, require near-nuts to commit (avoid calling off with marginal hands)
        if street == "river":
            commit_eq = max(commit_eq, 0.78)
        if spr < commit_spr and eq > commit_eq:
            if cost > 0:
                if opp_knows_our_hand and facing_raise:
                    return ActionFold()
                s = self.shove(state)
                return s if s else self.safe_call(state)
            if eq > 0.62:
                s = self.shove(state)
                return s if s else self.safe_check(state)

        # ═══════════════════════════════════════════════════════
        # FACING ALL-IN
        # ═══════════════════════════════════════════════════════
        if self.facing_shove(state):
            if opp_knows_our_hand:
                if eq > 0.72: return self.safe_call(state)
                return ActionFold()
            if eq > 0.58:
                s = self.shove(state)
                return s if s else self.safe_call(state)
            if eq > po + 0.06:
                return self.safe_call(state)
            return ActionFold()

        # ═══════════════════════════════════════════════════════
        # FACING A BET
        # EA bets value-heavy (28.7% freq). His bets are real.
        # But he makes small bets (avg 27) as probes → call those.
        # Big bets = genuine value — be careful.
        # ═══════════════════════════════════════════════════════
        if cost > 0:
            if opp_small_bet_big_river():
                if eq > 0.60:
                    self._i_called_streets += 1
                    return self.safe_call(state)
                return ActionFold()

            if opp_knows_our_hand and facing_raise:
                if eq > 0.78: return self.safe_call(state)
                return ActionFold()

            if opp_won_high_bid:
                if facing_raise:
                    if eq > po + 0.30: return self.safe_call(state)
                    return ActionFold()
                else:
                    if eq > po + 0.22: return self.safe_call(state)
                    return ActionFold()

            # Small bets (EA's probe sizing ≤50): call with decent equity
            if cost <= 50 and not facing_raise and not opp_knows_our_hand:
                if eq > po + 0.05:
                    self._i_called_streets += 1
                    return self.safe_call(state)

            if cost > pot * 0.5:
                # Big bet — calibrate tightness based on opponent type
                ev_call = eq * (pot + cost) - cost
                agg_adj = self.opp_agg(street)
                # If opp rarely calls (bot4-type: high fold rate), they only big-bet strong hands
                # If opp calls more (bot3-type), their big bets include some bluffs
                call_rate = self.opp_call_rate(street)
                call_eq_thresh = 0.58 + agg_adj * 0.05
                if call_rate < 0.25:
                    # bot4-type: only calls with strong hands, so only big-bets value
                    call_eq_thresh = max(call_eq_thresh, 0.65)
                if facing_raise:
                    call_eq_thresh += 0.08
                if ev_call > 0 and eq >= call_eq_thresh:
                    self._i_called_streets += 1
                    return self.safe_call(state)
                # Multi-street big bets: fold unless very strong
                if self._opp_bets_this_hand >= 2 and eq < 0.65:
                    return ActionFold()
                if eq > 0.50 and po < 0.35 and not facing_raise and call_rate > 0.30:
                    self._i_called_streets += 1
                    return self.safe_call(state)
                return ActionFold()

            if their_card_is_strong:
                if facing_raise:
                    if eq > po + 0.20: return self.safe_call(state)
                    return ActionFold()
                else:
                    if eq > po + 0.10: return self.safe_call(state)
                    return ActionFold()

            # Raise vs opp bets when we have a strong hand
            # vs folders (bot3): raise threshold lower — they'll fold
            # vs callers (bot4): keep threshold higher — they call with strong hands
            call_rate = self.opp_call_rate(street)
            if call_rate < 0.25:
                # bot4-type caller: only raise for value (they call with strong hands)
                raise_thresh = 0.80 if street == "river" else 0.72
            else:
                # bot3-type: more willing to raise for value/semi-bluff
                raise_thresh = 0.72 if street == "river" else 0.65
            if facing_raise:
                raise_thresh = max(raise_thresh, 0.82)
            if self.is_value_bettor_only() and not facing_raise:
                raise_thresh = max(raise_thresh, 0.72)

            if eq > raise_thresh:
                if opp_knows_our_hand:
                    self._i_called_streets += 1
                    return self.safe_call(state)
                frac = self.bet_size_frac(eq, street) * self.trend_size_mult(street)
                r = self.raise_(state, frac)
                if r:
                    self._mark_bet(street)
                    return r
                return self.safe_call(state)

            if opp_knows_our_hand:
                tight_threshold = max(po + 0.15, 0.52)
                if eq > tight_threshold:
                    self._i_called_streets += 1
                    return self.safe_call(state)
                return ActionFold()

            if their_card_is_weak and cost > 0:
                if eq > max(po - 0.05, 0.33):
                    self._i_called_streets += 1
                    return self.safe_call(state)

            call_threshold = po * (1.0 / max(rm, 0.85))
            if facing_raise:
                # Facing a re-raise is a strong signal — tighten, but not too much
                # vs bot4 (strong re-raiser): need po+0.20
                # vs bot3 (occasional bluff-raiser): po+0.12 is fine
                # Use observed aggression to calibrate
                agg_now = self.opp_agg(street)
                if street == "river" and agg_now > 0.50:
                    # High-agg opp re-raising river = very strong signal
                    call_threshold = max(call_threshold, 0.75)
                elif self.opp_call_rate(street) < 0.25:
                    # Low caller = bot4-type who only re-raises strong
                    call_threshold = max(call_threshold, po + 0.20)
                else:
                    call_threshold = max(call_threshold, po + 0.14)
            elif i_was_aggressor:
                call_threshold = max(call_threshold, po + 0.06)

            if self.is_gto_like():
                if facing_raise:        call_threshold += 0.12
                elif street == "river": call_threshold += 0.08
                elif street == "turn":  call_threshold += 0.05
                else:                   call_threshold += 0.03

            # EA is a value bettor — calls for fewer streets → tighten calls
            if self.is_value_bettor_only():
                call_threshold += 0.10
            elif self.opp_agg(street) < 0.40:
                call_threshold += 0.05

            if eq > call_threshold:
                if self.is_nit() and eq < po + 0.08:
                    return ActionFold()
                self._i_called_streets += 1
                return self.safe_call(state)

            if street in ("flop", "turn") and eq > 0.38 and po < 0.28 and not facing_raise and not i_was_aggressor:
                self._i_called_streets += 1
                return self.safe_call(state)

            if seen and not self._card_connects_with_board(seen, board):
                if eq > 0.40 and self.opp_agg(street) > 0.50 and not facing_raise:
                    return self.safe_call(state)

            if street == "river" and self._opp_streets_bet >= 3 and self._i_called_streets >= 2:
                if eq > 0.42 and not facing_raise:
                    return self.safe_call(state)

            return ActionFold()

        # ═══════════════════════════════════════════════════════
        # CHECKED TO US — adaptive, EV-gated betting
        # ═══════════════════════════════════════════════════════

        # He has our card — bet only near-nuts
        if opp_knows_our_hand:
            if eq > 0.82:
                frac = self.bet_size_frac(eq, street) * self.trend_size_mult(street)
                r = self.raise_(state, frac)
                if r:
                    self._mark_bet(street)
                    return r
            if street == "flop":
                self._flop_checked = True
            return self.safe_check(state)

        if opp_won_high_bid:
            if eq > 0.92:
                frac = self.bet_size_frac(eq, street) * self.trend_size_mult(street)
                r = self.raise_(state, frac)
                if r:
                    self._mark_bet(street)
                    return r
            if street == "flop":
                self._flop_checked = True
            return self.safe_check(state)

        if their_card_is_strong:
            if eq > 0.82:
                frac = self.bet_size_frac(eq, street) * self.trend_size_mult(street)
                r = self.raise_(state, frac)
                if r:
                    self._mark_bet(street)
                    return r
            if street == "flop":
                self._flop_checked = True
            return self.safe_check(state)

        # Weak opp card — bet aggressively, they have little equity
        if their_card_is_weak and eq > 0.45:
            frac = self.bet_size_frac(max(eq, 0.60), street) * self.trend_size_mult(street) * 1.2
            r = self.raise_(state, frac)
            if r:
                self._mark_bet(street)
                return r

        # Probe turn if both checked flop
        if street == "turn" and self._flop_checked and eq > 0.48:
            if random.random() < 0.75:
                frac = self.bet_size_frac(max(eq, 0.55), street)
                r = self.raise_(state, frac)
                if r:
                    self._mark_bet(street)
                    return r

        # Near-nuts: always bet for value
        if eq > 0.72:
            _nuts_freq = 1.0 if self.is_extreme_folder() else 0.95
            if random.random() < _nuts_freq:
                frac = self.bet_size_frac(eq, street) * self.trend_size_mult(street)
                r = self.raise_(state, frac)
                if r:
                    self._mark_bet(street)
                    return r
            if street == "flop":
                self._flop_checked = True
            return self.safe_check(state)

        # Solid value (eq 0.58-0.72) — bet frequently, scale with opponent fold rate
        if eq > 0.58:
            fold_rate = self.fold_to_cbet(street)
            _solid_freq = 0.98 if (self.is_extreme_folder() or fold_rate > 0.55) else (0.90 if self.is_high_folder() else 0.82)
            if random.random() < _solid_freq:
                frac = self.bet_size_frac(eq, street) * self.trend_size_mult(street)
                r = self.raise_(state, frac)
                if r:
                    self._mark_bet(street)
                    return r
            if street == "flop":
                self._flop_checked = True
            return self.safe_check(state)

        # Thin value (eq 0.52-0.58): flop/turn only
        if eq > 0.52 and street != "river":
            _trend = self.equity_trend(street)
            _thin_freq = 0.85 if self.is_extreme_folder() else (0.72 if self.is_high_folder() else 0.55)
            if not self.is_nit() and _trend >= -0.06 and random.random() < _thin_freq:
                r = self.raise_(state, self.bet_size_frac(eq, street) * self.trend_size_mult(street))
                if r:
                    self._mark_bet(street)
                    return r
            if street == "flop":
                self._flop_checked = True
            return self.safe_check(state)

        # River value — bet strong hands, scale threshold by opponent call rate
        if street == "river":
            call_rate = self.opp_call_rate(street)
            # vs callers (bot3-type): bet with eq > 0.62 for value
            # vs folders (bot4-type): only bet very strong (already extracted by bluffing)
            river_bet_thresh = 0.62 if call_rate > 0.35 else 0.72
            if eq > river_bet_thresh:
                _trend = self.equity_trend(street)
                if _trend >= -0.06:
                    frac = self.bet_size_frac(eq, street) * self.trend_size_mult(street)
                    # Cap medium-strength river bets to avoid over-committing
                    if eq < 0.85:
                        frac = min(frac, 0.75)
                    r = self.raise_(state, frac)
                    if r:
                        self._mark_bet(street)
                        return r
            return self.safe_check(state)

        # EV-gated semi-bluff on wet boards (flop/turn only)
        wet = self._wet(board)
        if eq > 0.38 and wet and street in ("flop", "turn"):
            fold = self.fold_to_cbet(street)
            bet_chips = pot * 0.65
            ev_bet   = fold * pot + (1 - fold) * (eq * (pot + bet_chips) - bet_chips)
            ev_check = eq * pot * 0.85
            if ev_bet > ev_check and not self.is_fish():
                if random.random() < 0.55:
                    r = self.raise_(state, 0.65)
                    if r:
                        self._mark_bet(street)
                        return r
            if street == "flop":
                self._flop_checked = True
            return self.safe_check(state)

        # EV-gated pure bluff (flop/turn) — only when fold equity justifies it
        if street != "river" and not self.is_fish():
            frac = 0.70
            bet_chips = pot * frac
            fold = self.fold_to_cbet(street)
            if seen and not self._card_connects_with_board(seen, board):
                fold = min(fold + 0.35, 0.95)
            if self.is_nit(): fold = max(fold, 0.55)
            if self.is_high_folder(): fold = max(fold, 0.52)
            bluff_freq = 0.55 if self.is_high_folder() else 0.35
            if fold * pot - (1 - fold) * bet_chips > 0:
                if random.random() < bluff_freq:
                    r = self.raise_(state, frac)
                    if r:
                        self._mark_bet(street)
                        return r

        # River bluff — only when fold equity is confirmed high
        if street == "river" and not self.is_fish():
            frac = 0.70
            bet_chips = pot * frac
            fold = self.fold_to_cbet(street)
            if seen and not self._card_connects_with_board(seen, board):
                fold = min(fold + 0.35, 0.95)
            if self.is_nit(): fold = max(fold, 0.55)
            if self.is_high_folder(): fold = max(fold, 0.52)
            if fold > 0.72 and fold * pot - (1 - fold) * bet_chips > 0:
                if random.random() < 0.20:
                    r = self.raise_(state, frac)
                    if r:
                        self._mark_bet(street)
                        return r

        if street == "flop":
            self._flop_checked = True
        return self.safe_check(state)

    def _mark_bet(self, street):
        self._bet_this_street = True
        if street == "flop":
            self._i_bet_flop  = True
            self.i_bet_street_n["flop"]  = self.i_bet_street_n.get("flop", 0) + 1
        elif street == "turn":
            self._i_bet_turn  = True
            self.i_bet_street_n["turn"]  = self.i_bet_street_n.get("turn", 0) + 1
        elif street == "river":
            self._i_bet_river = True
            self.i_bet_street_n["river"] = self.i_bet_street_n.get("river", 0) + 1

    # ════════════════════════════════════════════════════════════
    # BOARD HELPERS
    # ════════════════════════════════════════════════════════════

    def normalize(self, cards):
        try:
            r1, s1 = cards[0][0], cards[0][1]
            r2, s2 = cards[1][0], cards[1][1]
            if RANK_ORDER.index(r1) > RANK_ORDER.index(r2):
                h, l = (r1, s1), (r2, s2)
            else:
                h, l = (r2, s2), (r1, s1)
            suited = h[1] == l[1]
            return (h[0] + l[0]) if h[0] == l[0] else (h[0] + l[0] + ("s" if suited else "o"))
        except Exception:
            return "22"

    def hs(self, h):
        return HAND_SCORE.get(h, 2)

    def _dry(self, board):
        return not self._wet(board)

    def _wet(self, board):
        try:
            if len(board) < 3:
                return False
            sc = {}
            for c in board:
                sc[c[1]] = sc.get(c[1], 0) + 1
            if any(v >= 2 for v in sc.values()):
                return True
            rv = sorted(RANK_ORDER.index(c[0]) for c in board)
            return any(abs(rv[i] - rv[i+1]) <= 2 for i in range(len(rv) - 1))
        except Exception:
            return False

    def _connects(self, card, board):
        return self._card_connects_with_board(card, board)


if __name__ == '__main__':
    run_bot(Player(), parse_args())
