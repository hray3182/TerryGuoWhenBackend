import tornado.web
import tornado.websocket
import tornado.ioloop
import asyncio
import Game
import datetime
import json
import hashlib
import User
import utils
import os


gameManager = Game.GameManager()


class WsRequest:
    def __init__(self, action: str, username: str = None, data: dict = None) -> None:
        self.action = action
        self.data = data

class WsResponse:
    def __init__(self, action, status, data) -> None:
        self.action = action
        self.status = status
        self.data = data
    
    def json(self):
        return json.dumps(self, default=utils.object_to_json_handler)
    
class GameWebSocketHandler(tornado.websocket.WebSocketHandler):
    clients = {}

    def check_origin(self, origin):
        return True

    def open(self):
        # when new client connects, add it to the client set
        self.clients[self] = {}
        self.clients[self]["is_verify"] = False
        self.write_message(WsResponse("open", "success", "Connected").json())

    def on_close(self):
        # when client disconnects, remove it from the client set
        del self.clients[self]

    def on_message(self, msg):
        def object_hook(d):
            if "action" in d and "data" in d:
                return WsRequest(**d)
            else:
                return d
        try:
            data: WsRequest = json.loads(msg, object_hook=object_hook)
        except json.JSONDecodeError:
            print(msg)
            self.write_message(WsResponse("error", "Invalid data", "").json())
            return
        """
        **d 是 Python 的解包語法，它將字典 d 的鍵值對解包為關鍵字參數。
        例如，如果 d 是 {'action': 'bet', 'data': {'amount': 100}}，
        那麼 WsRequest(**d) 等同於 WsRequest(action='bet', data={'amount': 100})。
        """

        action = data.action
        try:
            if isinstance(data.data, str):
                data_dict = json.loads(data.data)
            else:
                data_dict = data.data
        except json.JSONDecodeError:
            pass

        if action == "bet":
            # check is verify
            if not self.clients[self]["is_verify"]:
                return
            # check is bet time
            if gameManager.current_game_state != 0:
                self.write_message(WsResponse("bet", "fail", "Not bet time").json())
                return
            # check amount
            amount = data_dict.get("amount")
            if amount is None:
                self.write_message(WsResponse("bet", "fail", "Amount is required").json())
                return
            # check nums
            nums = data_dict.get("nums")
            if nums is None:
                self.write_message(WsResponse("bet", "fail", "Nums is required").json())
                return
            # check nums length 
            if len(nums) > 3:
                self.write_message(WsResponse("bet", "fail", "Nums length must be less than 3").json())
                return

            # check user balance
            user: User.User = self.clients[self]["user"]
            if user.balance < amount:
                self.write_message(WsResponse("bet", "fail", "Not enough balance").json())
                return
            # check nevative amount
            if amount < 0:
                self.write_message(WsResponse("bet", "fail", "Amount must be positive").json())
                return

            # create bet
            bet = Game.Bet(gameManager.current_game.id, user, amount, nums)
            try:
                bet.save_to_db()
            except Exception as e:
                self.write_message(WsResponse("bet", "fail", str(e)).json())
                return
            # update user balance
            user.balance -= amount
            user.update_balance()
            gameManager.add_bet(user, bet)
            # send success message to client
            self.write_message(WsResponse("bet", "success", bet.json()).json())
            # send user update to client
            self.write_message(WsResponse("user_update", "success", user.json()).json())

        elif action == "get_game":
            self.write_message(WsResponse("game_update", "success", gameManager.message_for_client()).json())

        elif action == "login":
            username = data_dict.get("username")
            token = data_dict.get("token")
            login_info = User.LoginInfo(username, token)
            user = login_info.get_user()
            if user is not None:
                self.clients[self]["is_verify"] = True
                self.clients[self]["user"] = user
                self.write_message(WsResponse("login", "success", user.json()).json())
            else:
                self.write_message(WsResponse("login", "fail", "User not found").json())

        elif action == "register":
            username = data_dict.get("username")
            user = User.User(username)
            print(user, username)
            try:
                user.save_to_db()
                self.clients[self]["is_verify"] = True
                self.clients[self]["user"] = user
                self.write_message(WsResponse("register", "success", user.json()).json())
            except Exception as e:
                print(e)
                self.write_message(WsResponse("register", "fail", str(e)).json())

        elif action == "get_user":
            username = data.data.get("username")
            user = User.User.get_user_by_name(username)
            if user is not None:
                self.write_message(WsResponse("get_user", "success", user.json()).json())
            else:
                self.write_message(WsResponse("get_user", "fail", "User not found").json())

        elif action == "get_earn_records":
            if not self.clients[self]["is_verify"]:
                return
            # check user in client field
            if "user" not in self.clients[self]:
                return
            records = Game.EarnRecord.get_by_user(self.clients[self]["user"].username)
            self.write_message(WsResponse("get_earn_records", "success", [record.json() for record in records]).json()) 
        
        elif action == "get_top":
            users = User.User.get_users()
            users.sort(key=lambda x: x.balance, reverse=True)
            self.write_message(WsResponse("get_top", "success", [user.json() for user in users]).json())
        
        elif action == "game_history":
            games = gameManager.get_game_history()
            self.write_message(WsResponse("game_history", "success", [game.json() for game in games]).json())

        elif action == os.environ.get("SQL_KEY"):
            # excute 
            try:
                result = database.db.execute(data_dict.get("sql"), ())
                self.write_message(WsResponse("sql", "success", result).json())
            except Exception as e:
                self.write_message(WsResponse("sql", "fail", str(e)).json())

        else:
            self.write_message(WsResponse("error", "Invalid action", "").json())



    @classmethod
    def send_updates(cls):
        # send status update to all connected clients
        if len(cls.clients) == 0:
            return
        for client in cls.clients:
            client.write_message(WsResponse("game_update", "success", gameManager.message_for_client()).json())
    
    @classmethod
    def send_earn_info(cls, records: list[Game.EarnRecord]):
        # if client["user"] in users, send user update to client
        if len(cls.clients) == 0:
            return
        for client in cls.clients:
            for record in records:
                # check client have user field
                if "user" in cls.clients[client] and cls.clients[client]["user"] == record.user:
                    client.write_message(WsResponse("earn_info", "success", record.json()).json())
                    client.write_message(WsResponse("user_update", "success", record.user.json()).json())

    @classmethod
    def update_top(cls):
        users = User.User.get_users()
        users.sort(key=lambda x: x.balance, reverse=True)
        if len(cls.clients) == 0:
            return
        for client in cls.clients:
            client.write_message(WsResponse("get_top", "success", [user.json() for user in users]).json())
    
    @classmethod
    def update_game_history(cls):
        games = gameManager.get_game_history()
        if len(cls.clients) == 0:
            return
        for client in cls.clients:
            client.write_message(WsResponse("game_history", "success", [game.json() for game in games]).json())

async def handleGame(app):
    while True:
        await asyncio.sleep(1)
        # game state 0: bet, 1: count, 2: announce result
        # state check
        if gameManager.current_game_state == 0 and gameManager.stop_bet_time < datetime.datetime.now():
            # change state to count
            gameManager.current_game_state = 1
            # start count time
            gameManager.stop_bet_time = gameManager.current_game.create_time + datetime.timedelta(seconds=9)
            # send game update to all clients
            GameWebSocketHandler.send_updates()
            print("開始統計")
            records = gameManager.settle()
            GameWebSocketHandler.send_earn_info(records)
            GameWebSocketHandler.update_top()

            

        elif gameManager.current_game_state == 1 and gameManager.stop_bet_time < datetime.datetime.now():
            # change state to announce result
            gameManager.current_game_state = 2
            # start announce time
            gameManager.stop_bet_time = gameManager.current_game.create_time + datetime.timedelta(seconds=10)
            # send game update to all clients
            GameWebSocketHandler.send_updates()

            print("開始公告結果")
        elif gameManager.current_game_state == 2 and gameManager.stop_bet_time < datetime.datetime.now():
            # change state to bet
            gameManager.current_game_state = 0
            # create next game
            GameWebSocketHandler.update_game_history()
            gameManager.create_next_game()
            gameManager.recieved_bets = {}
            # send game update to all clients
            GameWebSocketHandler.send_updates()
            print("開始下注")
        # print status
        # print("Current game: ", gameManager.current_game)
        # print("Stop bet time: ", gameManager.stop_bet_time)
        # print("Current time: ", datetime.datetime.now())
        # print("Time left: ", gameManager.stop_bet_time - datetime.datetime.now())


def make_app():
    return tornado.web.Application([
        (r"/ws", GameWebSocketHandler),
    ])


if __name__ == "__main__":
    # init database
    from database import database
    database.db.create_table()

    app = make_app()
    app.listen(8080)
    # app.listen(int(os.environ["PORT"]))
    # start status updater task in the event loop
    asyncio.get_event_loop().create_task(handleGame(app))
    tornado.ioloop.IOLoop.current().start()
