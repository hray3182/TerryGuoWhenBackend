import Key
from datetime import datetime
import hashlib
from database import database


class User:
    def __init__(
        self,
        username: str,
        create_time=datetime.now(),
        token: str = None,
        balance: int = 5000
    ) -> None:
        self.username = username
        self.token: str = token
        self.create_time = create_time
        self.balance = balance
        if self.token is None:
            self.__generate_token()

    def __str__(self) -> str:
        time = self.create_time.strftime("%Y-%m-%d %H:%M:%S")
        return f"username: {self.username}, create_time: {time}, token: \n{self.token}"

    def __generate_token(self):
        """
        新建使用者, 使用 username + 當下時間 + 一段密鑰生成 sha256 token
        """
        data = self.username + \
            self.create_time.strftime("%Y-%m-%d %H:%M:%S") + Key.key
        token = hashlib.sha256(data.encode('utf-8')).hexdigest()
        self.token = token

    def json(self):
        return {
            "username": self.username,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "token": self.token,
            "balance": self.balance
        }


    def save_to_db(self) -> str:
        """
        將使用者資料存入資料庫
        """
        if User.get_user_by_name(self.username) is not None:
            raise Exception("User already exists")

        try:
            result = database.db.execute("INSERT INTO User VALUES (?, ?, ?, ?)", (
                self.username, self.create_time, self.token, self.balance))
        except Exception as e:
            result = e
        print(result)
        return result
    
    def update_balance(self) -> str:
        """
        更新使用者餘額
        """
        try:
            result = database.db.execute("UPDATE User SET balance = ? WHERE username = ?", (
                self.balance, self.username))
        except Exception as e:
            result = e
        return result

    @classmethod
    def get_user_by_name(cls, username: str):
        """
        透過 username 取得使用者資料
        """
        result = database.db.execute(
            "SELECT * FROM User WHERE username = ?", (username,))
        if len(result) > 0 and len(result[0]) > 0:
            # parse data 2024-05-01 22:48:03.327078
            time = datetime.strptime(result[0][1], "%Y-%m-%d %H:%M:%S.%f")
            user = cls(result[0][0], time, result[0][2], result[0][3])
            return user
        return None

    @classmethod
    def get_users(cls):
        """
        取得所有使用者資料
        """
        result = database.db.execute("SELECT * FROM User", ())
        users = []
        for r in result:
            time = datetime.strptime(r[1], "%Y-%m-%d %H:%M:%S.%f")
            user = cls(r[0], time, r[2], r[3])
            users.append(user)
        return users

class LoginInfo:
    def __init__(self, username, token) -> None:
        self.username = username
        self.token = token

    def get_user(self) -> User:
        u = User.get_user_by_name(self.username)
        if u is not None and u.token == self.token:
            return u


if __name__ == "__main__":
    # 測試 User 類別
    input = "糖心蛋"
    user = User(input)
    print(user)

    # 初始化資料庫
    database.db.create_table()
    # 嘗試把 user 加到資料庫
    try:
        user.save_to_db()
    except Exception as e:
        print(e)


    user = User.get_user_by_name("糖心蛋")
    print(user)
    