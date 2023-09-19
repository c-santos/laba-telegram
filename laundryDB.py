import sqlite3
import logging

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class LaundryDB:
    def __init__(self, dbname="user_config.sqlite") -> None:
        try:
            self._conn: sqlite3.Connection = sqlite3.connect(dbname)
            self._setup_table()
            logger.info("Connection to DB successful.")
        except Exception as e:
            logger.error(e)

    def _setup_table(self) -> None:
        qry: str = """
                CREATE TABLE IF NOT EXISTS user_laundry_days (
               user_id INT PRIMARY KEY NOT NULL,
               laundry_days TEXT,
               lon FLOAT,
               lat FLOAT
                )
               """
        try:
            self._conn.execute(qry)
            self._conn.commit()
            logger.info("Created user_laundry_days table")
        except Exception as e:
            logger.error(e)

    def close(self) -> None:
        self._conn.close()
        logger.info("Connection to DB closed.")

    def add_user(self, user_id: int):
        qry: str = "INSERT INTO user_laundry_days (user_id) VALUES (?)"
        args: tuple[int] = (user_id,)

        try:
            self._conn.execute(qry, args)
            self._conn.commit()
            logger.info(f"Added user {user_id}")
        except Exception as e:
            logger.error(e)

    def delete_entry(self, user_id: int) -> None:
        qry: str = "DELETE FROM user_laundry_days WHERE user_id=?"
        args: tuple[int] = (user_id,)

        self._conn.execute(qry, args)
        self._conn.commit()
        logger.info(f"Entry of {user_id} deleted.")

    def dump(self) -> list[any]:
        qry: str = "SELECT * FROM user_laundry_days"
        cursor: sqlite3.Cursor = self._conn.execute(qry)
        data: list[any] = cursor.fetchall()
        logger.debug(data)

        return data

    # -------------------LAUNDRY DAY FUNCTIONS

    def set_day(self, user_id: int, days: str) -> None:
        if self.get_day(user_id) == None:
            qry: str = (
                "INSERT INTO user_laundry_days (user_id, laundry_days) VALUES (?, ?)"
            )
            args: tuple[int, str] = (
                user_id,
                days,
            )

            self._conn.execute(qry, args)
            self._conn.commit()
            logger.info(f"{days} set for {user_id}.")

        else:
            logger.debug(f"{user_id} already exists. Updating instead.")
            self.update_day(user_id, days)

    def update_day(self, user_id: int, days: str) -> None:
        if self.get_day(user_id) != None:
            qry: str = "UPDATE user_laundry_days SET laundry_days=? WHERE user_id=?"
            args: tuple[str, int] = (
                days,
                user_id,
            )

            self._conn.execute(qry, args)
            self._conn.commit()
            logger.info(f"Updated to {days} for {user_id}.")

        else:
            logger.debug(f"{user_id} does not exist. Adding instead.")
            self.set_day(user_id, days)

    def clear_day(self, user_id: int) -> None:
        qry: str = "UPDATE user_laundry_days SET laundry_days=NULL WHERE user_id=?"
        args: tuple[int] = (user_id,)

        self._conn.execute(qry, args)
        self._conn.commit()
        logger.info(f"Cleared laundry days column of {user_id}.")

    def save_day(self, user_id: int, week_dict: dict) -> None:
        # Parse dictionary
        days: list[str] = [day for day, value in week_dict.items() if value == True]
        days: str = " ".join(days)

        # Set/update
        self.set_day(user_id, days)

        logger.info(days)

    def get_day(self, user_id) -> any:
        try:
            qry: str = "SELECT laundry_days FROM user_laundry_days WHERE user_id=?"
            args: tuple[int] = (user_id,)

            cursor: sqlite3.Cursor = self._conn.execute(qry, args)
            data = cursor.fetchone()

            return data

        except sqlite3.OperationalError as e:
            logger.error(e)
            return None

    # --------------------LOCATION FUNCTIONS

    def save_location(self, user_id: int, lon: float, lat: float) -> None:
        qry: str = """
                    UPDATE user_laundry_days 
                    SET 
                        lon=?, 
                        lat=? 
                    WHERE user_id=?"""
        args = (
            lon,
            lat,
            user_id,
        )

        self._conn.execute(qry, args)
        self._conn.commit()

        logger.info(f"Successfully saved user {user_id} location ({lon}, {lat})")

    def get_lon(self, user_id: int) -> float | None:
        try:
            qry: str = "SELECT lon FROM user_laundry_days WHERE user_id=?"
            args: tuple[int] = (user_id,)

            cursor: sqlite3.Cursor = self._conn.execute(qry, args)
            data = cursor.fetchone()
            return data[0]

        except sqlite3.OperationalError as e:
            logger.error(e)
            return None

    def get_lat(self, user_id: int) -> float | None:
        try:
            qry: str = "SELECT lat FROM user_laundry_days WHERE user_id=?"
            args: tuple[int] = (user_id,)

            cursor: sqlite3.Cursor = self._conn.execute(qry, args)
            data = cursor.fetchone()
            return data[0]

        except sqlite3.OperationalError as e:
            logger.error(e)
            return None


if __name__ == "__main__":
    db = LaundryDB()
    print(db.dump())
    db.close()
