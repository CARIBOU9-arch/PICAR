import sqlite3

referal_cost = 200
DB_LOCATION = "database.db"


# DB_LOCATION = "test.db"


class DatabaseConnector:
    def __init__(self, db_name):
        self.db_name = db_name
        self.connection = None

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            try:
                self.connection = sqlite3.connect(self.db_name, isolation_level=None)
                connection, cursor = self.connection, self.connection.cursor()
                print("OPENED", end=' | ')
                result = func(cursor, *args, **kwargs)
                connection.commit()
                if self.connection:
                    self.connection.close()
                    print("CLOSED\n")
                return result
            except Exception as err:
                print(f'{err}')
                return

        return wrapper


@DatabaseConnector(DB_LOCATION)
def is_new_user(cur, user_id):
    return cur.execute('''SELECT * FROM users WHERE user_id = ?''', (user_id,)).fetchone() is None


@DatabaseConnector(DB_LOCATION)
def is_already_referral(cur, user_id):
    referal_field = cur.execute('''SELECT * FROM referrals WHERE referral_id = ?''', (user_id,)).fetchone()
    return referal_field


@DatabaseConnector(DB_LOCATION)
def is_wallet_added(cur, user_id):
    try:
        ton_wallet = cur.execute('''SELECT ton_wallet FROM users WHERE user_id = ?''', (user_id,)).fetchone()[0]
        # print(ton_wallet)
        return ton_wallet

    except TypeError:
        return None


@DatabaseConnector(DB_LOCATION)
def set_wallet(cur, user_id, wallet: str):
    try:
        cur.execute('''UPDATE users SET ton_wallet = ? WHERE user_id = ?''', (wallet, user_id))
    except Exception as err:
        print(err)


@DatabaseConnector(DB_LOCATION)
def get_wallet(cur, user_id):
    try:
        wallet = cur.execute('''SELECT ton_wallet FROM users WHERE user_id = ?''', (user_id,)).fetchone()[0]
        return wallet
    except Exception as err:
        print(err)
        return '(|Ошибка! напишите /start|)'


@DatabaseConnector(DB_LOCATION)
def add_user(cur, user_id, username, first_name, second_name):
    """add a new user to USERS table"""
    if is_new_user(user_id):
        cur.execute('''INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (int(user_id), username, first_name, second_name, 0, 0, None))


@DatabaseConnector(DB_LOCATION)
def add_balance(cur, user_id, how_much):
    print(f'ADD BALANCE {user_id} | {how_much}')
    """Add balance to user with USER_ID"""
    try:
        current_balance = cur.execute('''SELECT balance FROM users WHERE user_id = ?''', (user_id,)).fetchone()[0]
        # print(current_balance)
        cur.execute('''UPDATE users SET balance = ? WHERE user_id = ?''', (current_balance + how_much, user_id))
    except Exception as err:
        print(err)


@DatabaseConnector(DB_LOCATION)
def get_balance(cur, user_id):
    try:
        current_balance = cur.execute('''SELECT balance FROM users WHERE user_id = ?''', (user_id,)).fetchone()[0]
        return current_balance

    except Exception as err:
        print(err)
        return '(|Ошибка! напишите /start|)'


@DatabaseConnector(DB_LOCATION)
def get_task_by_status(cur, status: str):
    """get a task by STATUS"""
    # STATUSES: [ waiting | ended | active ]
    task = cur.execute('''SELECT * FROM tasks WHERE status = ?''', (status,)).fetchone()
    if task is not None:
        task_id, task_name, users_passed, status, = task
        return task_id, task_name, users_passed
    else:
        return None


@DatabaseConnector(DB_LOCATION)
def count_user_balance(cur, user_id):
    """count user REF balance and TAKS balance"""
    try:
        user_referrals, user_balance = cur.execute('''SELECT referrals, balance FROM users WHERE user_id = ?''',
                                                   (user_id,)).fetchone()
        ref_balance = user_referrals * referal_cost
        tasks_balance = user_balance - ref_balance

        return user_balance, ref_balance, tasks_balance
    except Exception as err:
        print(f'[count_user_balance]: {err}')


@DatabaseConnector(DB_LOCATION)
def get_referrals_amount(cur, user_id):
    try:
        current_referrals = cur.execute('''SELECT referrals FROM users WHERE user_id = ?''', (user_id,)).fetchone()[0]
        return current_referrals

    except Exception as err:
        print(err)
        return '(|Ошибка! напишите /start|)'


@DatabaseConnector(DB_LOCATION)
def add_referral(cur, referral_id, invited_id):
    """Add referral to invited_id and balance to referral_id"""
    try:
        if cur.execute('''SELECT * FROM referrals WHERE referral_id = ?''', (referral_id,)).fetchone() is None:
            cur.execute('''INSERT INTO referrals VALUES (?, ?)''', (referral_id, invited_id))
            invited_referrals = \
                cur.execute('''SELECT referrals FROM users WHERE user_id = ?''', (invited_id,)).fetchone()[0]

            cur.execute('''UPDATE users SET referrals = ? WHERE user_id = ?''', (invited_referrals + 1, invited_id))
            add_balance(invited_id, referal_cost)

    except Exception as err:
        print(err)


@DatabaseConnector(DB_LOCATION)
def give_ref_prize_if_need(cur, user_id):
    try:
        refs_prizes = {
            50: 5000,
            100: 10000,
            200: 20000
        }
        user_refs = get_referrals_amount(user_id)
        if user_refs in refs_prizes.keys():
            user_prize = refs_prizes[user_refs]
            print(f'Add to {user_id} [{user_refs} refs] +{user_prize} $PICAR')
            add_balance(user_id, user_prize)
            return 1, user_refs, user_prize

        else:
            return 0,

    except Exception as err:
        print(f'[give_ref_prize_if_need] ERR | {err}')
        return 0,


@DatabaseConnector(DB_LOCATION)
def use_promo(cur, promocode, user_id) -> bool:
    """return True is all good else returns False"""
    try:
        promo_info = cur.execute(
            """SELECT promocode, used, users_limit, cost FROM promocodes WHERE promocode = ?""",
            (promocode,)).fetchone()
        if promo_info is not None and promo_info[1] < promo_info[2]:
            if cur.execute("""SELECT * FROM used_promo WHERE user_id = ? AND promocode = ?""",
                           (user_id, promocode)).fetchone() is None:
                promocode, used, users_limit, promo_cost = promo_info

                add_balance(user_id, promo_cost)
                cur.execute("""UPDATE promocodes SET used = ? WHERE promocode = ?""", (used + 1, promocode))
                cur.execute("""INSERT INTO used_promo VALUES(?, ?)""", (user_id, promocode))
                return True, promo_cost

            else:
                return False, 0

        else:
            return False, 0
    except Exception as err:
        print(f'[use promo] ERR {user_id}{promocode} |: {err}')


@DatabaseConnector(DB_LOCATION)
def create_promo(cur, promocode, prize, users_limit):
    """create promo"""
    try:
        cur.execute("""INSERT INTO promocodes VALUES(?, ?, ?, ?)""", (promocode, int(prize), 0, int(users_limit)))
        print(f'[+] Promocode created {promocode} | {promocode} | {users_limit}')

    except Exception as err:
        print(f'[create promo] ERR {promocode} |: {err}')


@DatabaseConnector(DB_LOCATION)
def is_premium(cur, user_id):
    """create promo"""
    try:
        user = cur.execute("""SELECT user_id FROM bought_premium WHERE user_id = ?""", (user_id,)).fetchone()
        print(f'[+] Bought premium {user_id}')
        return user

    except Exception as err:
        print(f'[add_to_premium_users] ERR {user_id = } |: {err}')


@DatabaseConnector(DB_LOCATION)
def add_to_premium_users(cur, user_id):
    """create promo"""
    try:
        cur.execute("""INSERT INTO bought_premium VALUES(?)""", (user_id,))
        print(f'[+] Bought premium {user_id}')

    except Exception as err:
        print(f'[add_to_premium_users] ERR {user_id = } |: {err}')


@DatabaseConnector(DB_LOCATION)
def create_table(cur):
    """create a database table if it does not exist already"""
    cur.execute('''CREATE TABLE IF NOT EXISTS users(user_id integer,
                                                            username text,
                                                            first_name text,
                                                            second_name text,
                                                            referrals integer,
                                                            balance integer,
                                                            ton_wallet text)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS referrals(referral_id integer,
                                                            invited_id integer)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS tasks(task_id primary key,
                                                        name text,
                                                        users_passed integer,
                                                        status text)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS promocodes(promocode text,
                                                         cost integer,
                                                         used integer,
                                                         users_limit integer)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS used_promo(user_id, promocode)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS bought_premium(user_id)''')


if __name__ == '__main__':
    create_table()
    # print(get_task_by_status('active'))
