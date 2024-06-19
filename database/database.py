import sqlite3

DB_NAME = "data.db"


class db:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.commit()
        self.close()

    @classmethod
    def execute(cls, sql, params):
        with cls() as db:
            db.cursor.execute(sql, params)
            return db.cursor.fetchall()

    @classmethod
    def create_table(cls):
        cls.execute("CREATE TABLE IF NOT EXISTS User (username TEXT PRIMARY KEY NOT NULL, create_time DATETIME NOT NULL, token TEXT NOT NULL, balance INTEGER NOT NULL)", ())
        cls.execute("CREATE TABLE IF NOT EXISTS Game (id TEXT PRIMARY KEY NOT NULL, create_time TEXT NOT NULL, nums TEXT NOT NULL)", ())
        cls.execute("CREATE TABLE IF NOT EXISTS Bet (id TEXT PRIMARY KEY NOT NULL, create_time TEXT NOT NULL, game_id TEXT NOT NULL, username TEXT NOT NULL, bet_nums TEXT NOT NULL, amount INTEGER NOT NULL)", ())
        cls.execute("CREATE TABLE IF NOT EXISTS EarnRecord (game_id TEXT NOT NULL, game_nums TEXT NOT NULL, username TEXT NOT NULL, user_nums TEXT NOT NULL, bet_amount INTEGER NOT NULL, hit_amount INTEGER NOT NULL, earn_amount INTEGER NOT NULL)", ())
        print("Database initialized")
