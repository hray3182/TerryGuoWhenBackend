import datetime
import random
from database import database
import json
import User
import utils
from User import User
from typing import List
from Bet import Bet


class Game:
    def __init__(self, id: str, create_time=datetime.datetime.now()) -> None:
        self.id = id
        self.nums = []
        self.create_time = create_time
        self.__generate_nums()

    def __str__(self) -> str:
        return f"id: {self.id}, nums: {self.nums}"

    def __generate_nums(self):
        self.nums = (random.sample(range(1, 11), 3))
        self.nums.sort()

    def save_to_db(self) -> str:
        try:
            result = database.db.execute("INSERT INTO Game VALUES (?, ?, ?)", (
                self.id, self.create_time, str(self.nums)))
        except Exception as e:
            result = e
        return result
    
    def json(self):
        return {
            "game_id": self.id,
            "game_nums": str(self.nums),
        }

    @classmethod
    def get_num_of_todays_game(cls) -> int:
        today = datetime.datetime.now().date().strftime("%Y-%m-%d")
        count = 0
        try:
            result = database.db.execute("SELECT COUNT(*) FROM Game WHERE DATE(create_time) = ?", (today,))
            count = int(result[0][0])
        except Exception as e:
            result = e
            return result
        return count
    
    

class EarnRecord:
    def __init__(self, game_id, game_nums, user, user_nums, bet_amount, hit_amount, earn_amount) -> None:
        self.game_id = game_id
        self.game_nums = game_nums
        self.user: User = user
        self.user_nums = user_nums
        self.bet_amount = bet_amount
        self.hit_amount = hit_amount
        self.earn_amount = earn_amount
    
    def json(self):
        return {
            "game_id": self.game_id,
            "game_nums": self.game_nums,
            "user": self.user,
            "user_nums": self.user_nums,
            "bet_amount": self.bet_amount,
            "hit_amount": self.hit_amount,
            "earn_amount": self.earn_amount
        }
    
    def save_to_db(self) -> str:
        try:
            result = database.db.execute("INSERT INTO EarnRecord VALUES (?, ?, ?, ?, ?, ?, ?)", (
                self.game_id, str(self.game_nums), self.user.username, str(self.user_nums), self.bet_amount, self.hit_amount, self.earn_amount))
        except Exception as e:
            result = e
        return result
    
    def get_by_user(username) -> List["EarnRecord"]:
        try:
            result = database.db.execute("SELECT * FROM EarnRecord WHERE username = ?", (username,))
            records = []
            for r in result:
                record = EarnRecord(r[0], r[1], User.get_user_by_name(r[2]), r[3], r[4], r[5], r[6])
                records.append(record)
        except Exception as e:
            # 拋出錯誤
            raise e
        return records


class GameManager():
# A game lasts one munite, 40 second to accept bets, 10 second to count, 10 second to announce the result
    def __init__(self) -> None:
        # game id should be like 
        todays_count = Game.get_num_of_todays_game()
        # game id should be like yyyy-mm-dd-0001
        today = datetime.datetime.now().date().strftime("%Y-%m-%d")
        self.current_game = Game(f"{today}-{todays_count + 1}")
        self.current_game.save_to_db()
        self.stop_bet_time = self.current_game.create_time + datetime.timedelta(seconds=8)
        self.current_game_state = 0
        self.recieved_bets: dict[User, List[Bet]] = {}
        # user: [bet]
        print(f"創建新遊戲: {self.current_game}")
            
    def __str__(self) -> str:
        return f"Current game: {self.current_game}, stop bet time: {self.stop_bet_time}"

    
    def json(self):
        return json.dumps(self, default=utils.object_to_json_handler)

    def create_next_game(self):
        today = datetime.datetime.now().date().strftime("%Y-%m-%d")
        todays_count = Game.get_num_of_todays_game()
        self.current_game = Game(f"{today}-{todays_count + 1}", datetime.datetime.now())
        self.current_game.save_to_db()
        self.stop_bet_time = self.current_game.create_time + datetime.timedelta(seconds=8)
        print(f"創建新遊戲: {self.current_game}")
        
    def message_for_client(self):
        # json format
        return {
            "game_id": self.current_game.id,
            "game_state": self.current_game_state,
        }
    
    def add_bet(self, user: User, bet: Bet):
        if user not in self.recieved_bets:
            self.recieved_bets[user] = []
        self.recieved_bets[user].append(bet)
        print(f"收到下注: {bet}")
        print(f"目前下注: {self.recieved_bets}")

    def get_bets(self):
        return self.recieved_bets
    
    # 對每個下注的人進行結算
    def settle(self) -> List[EarnRecord]:
    #     # hit 3: 50 times, hit 2: 3 times, hit 1: 1 times
        records = []
        for user, bets in self.recieved_bets.items():
            for bet in bets:
                hit_count = len(set(bet.bet_nums) & set(self.current_game.nums))
                if hit_count > 0:
                    earn = 0

                    if hit_count == 3:
                        earn += bet.amount * 50
                    elif hit_count == 2:
                        earn += bet.amount * 3
                    elif hit_count == 1:
                        earn += bet.amount
                    user.balance += earn
                    print(f"結算: {bet.user.username}, {hit_count} 中獎, 餘額: {bet.user.balance}")
                    record = EarnRecord(self.current_game.id, self.current_game.nums, user, bet.bet_nums, bet.amount, hit_count, earn)
                    record.save_to_db()
                    records.append(record)
            user.update_balance()
        self.recieved_bets = {}
        print("結算完成")
        print(f"目前下注: {self.recieved_bets}")
        print(f"目前遊戲: {self.current_game}")
        # return 中獎名單
        return records

    # 獲取前100次遊戲記錄
    @classmethod
    def get_game_history(cls) -> List[Game]:
        try:
            result = database.db.execute("SELECT * FROM Game ORDER BY create_time DESC LIMIT 100 OFFSET 1", ())
            games = []
            for r in result:
                game = Game(r[0], r[1])
                game.nums = json.loads(r[2])
                games.append(game)
        except Exception as e:
            # 拋出錯誤
            raise e
        return games





if __name__ == "__main__":
    database.db.create_table()
    
    # Game("123").save_to_db()
    # Game("456").save_to_db()

    # print(Game.get_num_of_todays_game())
    # print(GameManager().json())
    # games = GameManager.get_game_history()
    # for game in games:
    #     print(game)
    # records = EarnRecord.get_by_user("@")
    # for record in records:
    #     print(record)