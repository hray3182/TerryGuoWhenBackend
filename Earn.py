from setting import BEETING_ODDS

class Earn:
    def __init__(
        self,
        id: str,
        game_id: str,
        user_id: str,
        bet_id: str,
        game_num: list,
        bet_num: list,
        bet_amount: int,
        hit_num: int = None,
        betting_odds: int = None, 
        win_amount: int = None
    ) -> None:
        self.id = id
        self.game_id = game_id
        self.user_id = user_id
        self.bet_id = bet_id
        self.game_num = game_num
        self.bet_num = bet_num
        self.bet_amount = bet_amount
        self.hit_num = hit_num
        self.betting_odds = betting_odds
        self.win_amount = win_amount

        if self.hit_num is None:
            self.hit_num = self.count_hit_num()
            self.betting_odds = BEETING_ODDS[self.hit_num]
            self.win_amount = self.bet_amount * self.betting_odds
        

    def __str__(self) -> str:
        return f"
        id: {self.id},
        game_id: {self.game_id},
        user_id: {self.user_id},
        bet_id: {self.bet_id},
        game_num: {self.game_num},
        bet_num: {self.bet_num},
        bet_amount: {self.bet_amount},
        hit_num: {self.hit_num},
        betting_odds: {self.betting_odds},
        win_amount: {self.win_amount}"
    
    def count_hit_num(self) -> int:
        return 6 - len(set(self.game_num) - set(self.bet_num))
    
    # TODO save to db