import telebot
from telebot import types
import db_operations2 as db
import texts

# bot = telebot.TeleBot('6841977939:AAFb210K7AtWWetz2II7teWopt9F3zY5O7A')  # Test bot
bot = telebot.TeleBot('7085626865:AAH5j5rtpcxO-pKesZl2oU2K-SJ-NBC3hEY')
# bot_username = 'Laspiks_test_bot'
# info_channel = 'laspiks_test_channel'
bot_username = 'picardia_bot'
info_channel = 'picardia_ton'
shop_group = 'shop_staff_pic'
users_chat_history = '@users_dialogs'

db.create_table()

##########################################


start_markup = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
    types.KeyboardButton('🔥 Чекай правила!'),
    types.KeyboardButton('Баланс\Balance 🪙')
).add(
    types.KeyboardButton('Кошелек\Wallet 👛')
).add(
    types.KeyboardButton('Задания\Tasks 📋'),
    types.KeyboardButton('Terms [ENG] 📌')
).add(
    types.KeyboardButton('Магазин\Shop 🛒')
)

check_member_markup = types.InlineKeyboardMarkup().add(
    types.InlineKeyboardButton('Проверить🧾', callback_data='check_group_member')
)

change_wallet_markup = types.InlineKeyboardMarkup().add(
    types.InlineKeyboardButton('Изменить 📝', callback_data='change_wallet')
)

shop_markup = types.InlineKeyboardMarkup(row_width=1).add(
    types.InlineKeyboardButton('Telegram Premium на месяц', callback_data='buy_premium')
)

back_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1).add(
    types.KeyboardButton('🚫 Отмена')
)


##########################################

@bot.message_handler(commands=['create_promo'])
def create_promo(message):
    if message.chat.id == 927254012:
        try:
            promocode, prize, users_limit = message.text.split('/create_promo')[1].strip().split(' ')
            db.create_promo(promocode, prize, users_limit)
            bot.send_message(message.chat.id, f'Промокод создан:\n'
                                              f': {promocode}\n'
                                              f': {prize} $PICAR\n'
                                              f': {users_limit}')

        except Exception as err:
            bot.send_message(message.chat.id, f'[Error] {err}')


@bot.message_handler(commands=['add_balace'])  # /add_balace user_id +money
def create_promo(message):
    if message.chat.id == 927254012:
        try:
            user_id, money = message.text.split('/add_balace ')[1].split(' ')
            db.add_balance(user_id, int(money))
            bot.send_message(message.chat.id, f"Баланс пользователя {user_id} +{money}")
        except Exception as err:
            bot.send_message(message.chat.id, f'[Error] {err}')


@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type == 'private':
        print(f'{message.chat.id} | Start')
        if db.is_new_user(message.chat.id):  # Нет в базе данных (не является пользователем бота)
            if len(message.text.split()) > 1 and 'ref' in message.text:  # Рефка
                invited_id = message.text.split('ref')[1]
                if invited_id != str(message.chat.id):  # Если юзаешь свою рефку
                    check_member_markup_ref = types.InlineKeyboardMarkup().add(
                        types.InlineKeyboardButton('Проверить🧾', callback_data=f'check_group_member_ref:{invited_id}')
                    )
                    bot.send_message(message.chat.id, texts.SUBSCRIBE_TO_CHANEL.format(info_channel),
                                     reply_markup=check_member_markup_ref)

            else:
                bot.send_message(message.chat.id, texts.SUBSCRIBE_TO_CHANEL.format(info_channel),
                                 reply_markup=check_member_markup)
            # END
        else:  # Уже есть в базе данных
            if len(message.text.split()) > 1 and 'ref' in message.text:  # Рефка
                # start ref6840241903
                invited_id = message.text.split('ref')[1]
                if invited_id != str(message.chat.id):  # Если юзаешь свою рефку
                    print(f'ADD REF | invited_id = {invited_id} | referral_id = {message.chat.id}')
                    if db.is_already_referral(message.chat.id) is None:
                        db.add_referral(message.chat.id, invited_id)
                        bot.send_message(invited_id,
                                         texts.NEW_REFERRAL_MESSAGE.format(db.get_referrals_amount(int(invited_id))))

                        user_prize_info = db.give_ref_prize_if_need(int(invited_id))
                        if user_prize_info[0] == 1:
                            ref_status, invited_refs, user_prize = user_prize_info
                            bot.send_message(invited_id, texts.REFERAL_BONUS.format(invited_refs, user_prize))

            add_friend_markup = types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton('Пригласить друга 👥',
                                           url=f'https://t.me/share/url?url=https://t.me/{bot_username}?start=ref{message.chat.id}'))

            bot.send_message(message.chat.id, '🔝 Главное Меню', reply_markup=start_markup)
            bot.send_message(message.chat.id, texts.AIRDROP_PICARDIA_COIN, reply_markup=add_friend_markup)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == 'check_group_member':
        if is_member(call.message.chat.id):  # Подписан на канал
            db.add_user(call.message.chat.id,
                        call.from_user.username,
                        call.from_user.first_name,
                        call.from_user.last_name)

            add_friend_markup = types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton('Пригласить друга 👥',
                                           url=f'https://t.me/share/url?url=https://t.me/{bot_username}?start=ref{call.message.chat.id}'))

            bot.send_message(call.message.chat.id, '🔝 Главное Меню', reply_markup=start_markup)
            bot.send_message(call.message.chat.id, texts.AIRDROP_PICARDIA_COIN, reply_markup=add_friend_markup)

        else:  # Не подписан на канал
            bot.edit_message_text(text=f'Ты не подписан на канал!',
                                  chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  reply_markup=None)
            bot.send_message(call.message.chat.id,
                             texts.SUBSCRIBE_TO_CHANEL.format(info_channel),
                             reply_markup=check_member_markup)

    elif 'check_group_member_ref' in call.data:
        invited_id = call.data.split(':')[1]

        if is_member(call.message.chat.id):  # Подписан на канал
            db.add_user(call.message.chat.id,
                        call.from_user.username,
                        call.from_user.first_name,
                        call.from_user.last_name)

            if db.is_already_referral(call.message.chat.id) is None:
                db.add_referral(call.message.chat.id, invited_id)
                bot.send_message(invited_id,
                                 texts.NEW_REFERRAL_MESSAGE.format(db.get_referrals_amount(int(invited_id))))

                user_prize_info = db.give_ref_prize_if_need(int(invited_id))

                if user_prize_info[0] == 1:
                    ref_status, invited_refs, user_prize = user_prize_info
                    bot.send_message(invited_id, texts.REFERAL_BONUS.format(invited_refs, user_prize))

                elif user_prize_info[0] == 2:
                    bot.send_message(invited_id, texts.REFERAL_NFT_BONUS)

            add_friend_markup = types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton('Пригласить друга 👥',
                                           url=f'https://t.me/share/url?url=https://t.me/{bot_username}?start=ref{call.message.chat.id}'))

            bot.send_message(call.message.chat.id, '🔝 Главное Меню', reply_markup=start_markup)
            bot.send_message(call.message.chat.id, texts.AIRDROP_PICARDIA_COIN, reply_markup=add_friend_markup)

        else:  # Не подписан на канал
            check_member_markup_ref = types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton('Проверить🧾', callback_data=f'check_group_member_ref:{invited_id}')
            )
            bot.edit_message_text(text=f'Ты не подписан на канал!',
                                  chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  reply_markup=None)
            bot.send_message(call.message.chat.id,
                             texts.SUBSCRIBE_TO_CHANEL.format(info_channel),
                             reply_markup=check_member_markup_ref)

    elif call.data == 'change_wallet':
        print(f'{call.message.chat.id} | Change wallet')
        mess = bot.send_message(call.message.chat.id, texts.WALLET_TEXT, reply_markup=types.ReplyKeyboardRemove(),
                                parse_mode='html')
        bot.register_next_step_handler(mess, add_wallet)

    elif call.data == 'buy_premium':
        confirm_premium = types.InlineKeyboardMarkup(row_width=2).add(
            types.InlineKeyboardButton('Купить\Buy 💵', callback_data='confirm_premium')
        )
        bot.send_message(call.message.chat.id, texts.BUY_PREMIUM, reply_markup=confirm_premium)

    elif call.data == 'confirm_premium':
        # print(call.from_user)
        if call.from_user.is_premium is None and db.is_premium(call.message.chat.id) is None:
            if db.get_balance(call.message.chat.id) >= 10000:

                contact_with_user = types.InlineKeyboardMarkup(row_width=1).add(
                    types.InlineKeyboardButton('Написать пользователю от имени бота',
                                               callback_data=f'type{call.from_user.id}')
                )

                bot.send_message(f'@{shop_group}', f'<b>TELEGRAM PREMIUM</b>\n\n'
                                                   f'User id: {call.from_user.id}\n'
                                                   f'Username: {call.from_user.username}\n'
                                                   f'First name: {call.from_user.first_name}\n'
                                                   f'Last name: {call.from_user.last_name}\n'
                                                   f'Link: https://t.me/{call.from_user.username}',
                                 disable_web_page_preview=True, parse_mode='html', reply_markup=contact_with_user)

                bot.edit_message_text(f'С вами свяжутся ✅', call.message.chat.id, call.message.message_id)
                db.add_to_premium_users(call.message.chat.id)
                bot.send_message(call.message.chat.id, f'-10.000 $PICAR', reply_markup=start_markup)
                db.add_balance(call.message.chat.id, -10000)
            else:
                bot.send_message(call.message.chat.id, 'Недостаточно средств :(\n\n'
                                                       'Not enough funds :(', reply_markup=start_markup)
        else:
            bot.send_message(call.message.chat.id, f'Ты уже купил премиум 🤷‍♂️', reply_markup=start_markup)

    elif 'type' in call.data:
        user_id = call.data.split('type')[1]
        mess = bot.send_message(call.from_user.id, 'Напиши сообщение которое перешлётся пользователю:',
                                reply_markup=back_markup)
        bot.register_next_step_handler(mess, send_message_to_user, user_id)

    elif 'answer_to_admin' in call.data:
        admin_id = call.data.split('answer_to_admin')[1]
        mess = bot.send_message(call.from_user.id, 'Напиши сообщение которое перешлётся админу:\n\n'
                                                   'Write a message that will be forwarded to the admin:',
                                reply_markup=back_markup)
        bot.register_next_step_handler(mess, send_message_to_admin, admin_id)


def send_message_to_user(message, user_id):
    # print(f'[send_message_to_user] {message}')
    if message.text != '🚫 Отмена':

        print(f'{user_id = }')

        contact_with_admin = types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton('Ответить\Answer', callback_data=f'answer_to_admin{message.chat.id}')
        )
        bot.send_message(message.chat.id, f'🔝 Главное Меню', reply_markup=start_markup)

        bot.copy_message(user_id, message.chat.id, message.message_id, reply_markup=contact_with_admin)
        bot.send_message(users_chat_history, f'Сообщение админа ({message.chat.id}) пользователю ({user_id})⬇️')
        bot.forward_message(users_chat_history, message.chat.id, message.message_id)

    else:
        bot.send_message(message.chat.id, f'🔝 Главное Меню', reply_markup=start_markup)


def send_message_to_admin(message, admin_id):
    # print(f'[send_message_to_admin] {message}')
    if message.text != '🚫 Отмена':
        print(f'{admin_id = }')

        contact_with_user = types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton('Написать пользователю от имени бота', callback_data=f'type{message.chat.id}')
        )
        bot.send_message(message.chat.id, f'🔝 Главное Меню', reply_markup=start_markup)

        bot.send_message(admin_id,
                         f'Сообщение от пользователя \n{message.chat.id} | {message.from_user.first_name} | {message.from_user.last_name}',
                         reply_markup=start_markup)
        bot.copy_message(admin_id, message.chat.id, message.message_id, reply_markup=contact_with_user)
        bot.send_message(users_chat_history, f'Сообщение пользователя ({message.chat.id}) админу ({admin_id})⬇️')
        bot.forward_message(users_chat_history, message.chat.id, message.message_id)

    else:
        bot.send_message(message.chat.id, f'🔝 Главное Меню', reply_markup=start_markup)


@bot.message_handler(content_types=['text'])
def text(message):
    if message.chat.type == 'private':

        if message.text == 'Баланс\Balance 🪙':
            print(f'{message.chat.id} | Balance')
            user_balance, ref_balance, tasks_balance = db.count_user_balance(message.chat.id)
            bot.send_message(message.chat.id, texts.BAlANCE.format(user_balance, ref_balance, tasks_balance))

        elif message.text == '🔥 Чекай правила!':
            print(f'{message.chat.id} | Rules')
            add_friend_markup = types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton('Пригласить друга 👥',
                                           url=f'https://t.me/share/url?url=https://t.me/{bot_username}?start=ref{message.chat.id}'))

            bot.send_message(message.chat.id,
                             texts.TERMS_AND_CONDITIONALS.format(info_channel, generate_link(message.chat.id)),
                             reply_markup=add_friend_markup)

        elif message.text == 'Задания\Tasks 📋':
            task = db.get_task_by_status('active')
            if task is not None:
                task_id, task_name, users_passed = task
                bot.send_message(message.chat.id, texts.TASK.format(task_id, task_name), parse_mode='html')
            else:
                bot.send_message(message.chat.id, texts.NO_TASKS_NOW)

        elif message.text == 'Terms [ENG] 📌':
            print(f'{message.chat.id} | Rules')
            add_friend_markup = types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton('Invite a friend 👥',
                                           url=f'https://t.me/share/url?url=https://t.me/{bot_username}?start=ref{message.chat.id}'))

            bot.send_message(message.chat.id,
                             texts.TERMS_AND_CONDITIONALS_ENG.format(info_channel, generate_link(message.chat.id)),
                             reply_markup=add_friend_markup)

        elif message.text == 'Кошелек\Wallet 👛':
            print(f'{message.chat.id} | Wallet')
            if db.is_wallet_added(message.chat.id) is None:
                mess = bot.send_message(message.chat.id, texts.WALLET_TEXT, reply_markup=back_markup,
                                        parse_mode='html')
                bot.register_next_step_handler(mess, add_wallet)
            else:

                bot.send_message(message.chat.id, f'Твой кошелек: {db.get_wallet(message.chat.id)}',
                                 reply_markup=change_wallet_markup)

        elif message.text == 'Магазин\Shop 🛒':
            bot.send_message(message.chat.id, f'Доступный товар ⬇️', reply_markup=shop_markup)

        else:
            promo_callback, cost = db.use_promo(message.text, message.chat.id)
            if promo_callback is True:
                bot.send_message(message.chat.id, texts.USE_PROMO.format(cost))
            else:
                bot.send_message(message.chat.id, texts.BAD_PROMO)


def add_wallet(message):
    wallet = message.text
    if wallet != '🚫 Отмена':
        db.set_wallet(message.chat.id, wallet)
        print(f'{message.chat.id} | Set wallet: {wallet}')
        bot.send_message(message.chat.id, f'🔝 Главное Меню', reply_markup=start_markup)
        bot.send_message(message.chat.id, f'Твой кошелек: {db.get_wallet(message.chat.id)}',
                         reply_markup=change_wallet_markup)
    else:
        bot.send_message(message.chat.id, f'🔝 Главное Меню', reply_markup=start_markup)


def is_member(user_id, chat_id=f'@{info_channel}') -> bool:
    print(bot.get_chat_member(chat_id, user_id).status)
    return bot.get_chat_member(chat_id, user_id).status == 'member' \
        or bot.get_chat_member(chat_id, user_id).status == 'creator' \
        or bot.get_chat_member(chat_id, user_id).status == 'administrator'


def generate_link(user_id):
    return f'https://t.me/{bot_username}?start=ref{user_id}'


def main():
    bot.polling(interval=1, timeout=3, non_stop=True)
    print('END')


if __name__ == '__main__':
    main()
