import sqlite3

class LaundryDB:
    def __init__(self, dbname='user_config.sqlite'):
        try: 
            self.conn = sqlite3.connect(dbname)
            self._setup()
            print('Connection to DB successful.')
        except Exception as e:
            print(e)

    def _setup(self) -> None:
        qry = '''
                CREATE TABLE IF NOT EXISTS user_laundry_days (
               user_id INT PRIMARY KEY NOT NULL,
               laundry_days TEXT
                )
               '''
        try:
            self.conn.execute(qry)
            self.conn.commit()

        except Exception as e:
            print(e)

    def dump(self) -> list[any]:
        qry = 'SELECT * FROM user_laundry_days'
        cursor = self.conn.execute(qry)
        data = cursor.fetchall()
        print(data)

        return data

    def set_day(self, user_id, days) -> None:

        if self.get_day(user_id) == None:
            qry = 'INSERT INTO user_laundry_days (user_id, laundry_days) VALUES (?, ?)'
            args = (user_id, days, )

            self.conn.execute(qry, args)
            self.conn.commit()
            print(f'{days} set for {user_id}.')

        else:

            print(f'{user_id} already exists. Updating instead.')
            self.update_day(user_id, days)

    def update_day(self, user_id, days) -> None:

        if self.get_day(user_id) != None:
            qry = 'UPDATE user_laundry_days SET laundry_days=? WHERE user_id=?'
            args = (days, user_id,)

            self.conn.execute(qry, args)
            self.conn.commit()
            print(f'Updated to {days} for {user_id}.')

        else:
            print(f'{user_id} does not exist. Adding instead.')
            self.set_day(user_id, days)

    def delete_entry(self, user_id) -> None:
        qry = "DELETE FROM user_laundry_days WHERE user_id=?"
        args = (user_id, )

        self.conn.execute(qry, args)
        self.conn.commit()
        print(f'Entry of {user_id} deleted.')

    def clear_day(self, user_id) -> None:
        qry = "UPDATE user_laundry_days SET laundry_days=NULL WHERE user_id=?"
        args = (user_id,)

        self.conn.execute(qry, args)
        self.conn.commit()
        print(f'Cleared laundry days column of {user_id}.')

    def get_day(self, user_id) -> any:
        try:
            qry = 'SELECT laundry_days FROM user_laundry_days WHERE user_id=?'
            args = (user_id, )

            cursor = self.conn.execute(qry, args)
            data = cursor.fetchone()
            
            # print(f'{user_id}:{data[0]}.')

            # print(data, type(data), data[0], type(data[0]))
            return data

        except sqlite3.OperationalError as e:
            print(e)
            return None

    def save(self, user_id, week_dict: dict) -> None:

        # Parse dictionary
        days = [day for day, value in week_dict.items() if value == True]
        days = ' '.join(days)

        # Set/update
        self.set_day(user_id, days)

        print(days)

    def close(self) -> None:
        self.conn.close()
        print('Connection to DB closed.')