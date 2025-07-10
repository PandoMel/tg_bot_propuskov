import asyncio
import logging
from array import *

from aiogram.exceptions import TelegramBadRequest

from config import *
from logging.handlers import RotatingFileHandler
import aiogram.utils.keyboard
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, BotCommand, ChatMemberUpdated, ChatMemberMember, ReplyKeyboardRemove
from aiogram.filters import Command, IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from aiogram.utils.chat_member import USERS
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder, KeyboardBuilder
from datetime import datetime, timedelta




logging.handlers.RotatingFileHandler(filename="KPP.html", maxBytes=10, backupCount=50)
dp = Dispatcher()
router = Router()
router_admins = Router()
chat_event_router = Router()
#Test token and group
bot = Bot(token=bot_token) # Объект бота с указанием токена
OHRANA_ID = OHRANA # Канал куда отправлять заявку пользователя
CHANNEL_ID = CHANNEL # Группа-база данных, откуда бот будет проверять наличие доступа к своим функциям -4507599030




#настройка логгеров, ротация bot.log
date_format = '%Y-%m-%d %H:%M:%S'
handlerRotateLog = RotatingFileHandler(
    'bot.log',  # Используйте абсолютный путь
    maxBytes=15 * 1024 * 1024,  # Максимальный размер файла 10 МБ
    backupCount=50,  # Количество резервных копий
    encoding='utf-8')
root_logger= logging.getLogger()
handlerRotateLog.setFormatter(logging.Formatter('%(asctime)s %(name)s %(message)s', date_format))


root_logger.setLevel(logging.INFO) # or whatever
handler = logging.FileHandler('bot.log', 'a', 'utf-8') # or whatever
handler.setFormatter(logging.Formatter('%(asctime)s %(name)s %(message)s', date_format)) # or whatever
root_logger.addHandler(handler)

handlerKPPlogs = RotatingFileHandler(
    'KPP.log',  # Используйте абсолютный путь
    maxBytes=1 * 1024 * 1024,  # Максимальный размер файла 10 МБ
    backupCount=200,  # Количество резервных копий
    encoding='utf-8')
# вызов ротации
def rotate_logs():
    root_logger.addHandler(handlerRotateLog)
    root_logger.addHandler(handlerKPPlogs)
rotate_logs()

ohrana_logger = logging.getLogger('KPP')
ohrana_logger.setLevel(logging.INFO)
test_handler = logging.FileHandler('KPP.log', 'a', 'utf-8')
test_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s', date_format))
ohrana_logger.addHandler(test_handler)




# Словарь для хранения сообщений:
sent_messages = {}
TIME_WINDOW = timedelta(minutes=45)  # интервал проверки


#Список команд бота:
bot_commands = [
    BotCommand(command="/start", description="Запуск"),
    #BotCommand(command="/order", description="Заказать пропуск"),
    BotCommand(command="/status", description="Статус доступа"),
    BotCommand(command="/help", description="Помощь")]

#кнопки
builder = InlineKeyboardBuilder()
builder.add(types.InlineKeyboardButton(
    text="Заказать гостевой пропуск",
    callback_data="Заказать пропуск"))

adm_button = InlineKeyboardBuilder()
adm_button.add(types.InlineKeyboardButton(
    text="Администраторское меню",
    callback_data="admins"))


keys_after_send = [[types.InlineKeyboardButton(text='Для авто инструкция', callback_data='man_avto')],
                   [types.InlineKeyboardButton(text='Для пешего инструкция', callback_data='man_pesh')],
                   [types.InlineKeyboardButton(text="Создать еще заявку",callback_data="Заказать пропуск")]]
builder2 = InlineKeyboardBuilder(keys_after_send)


key_builder = ReplyKeyboardBuilder()
key_builder.add(types.KeyboardButton(text="Отправить номер телефона", request_contact=True))

# builder3 = InlineKeyboardBuilder()
# builder3.add(types.InlineKeyboardButton(
#     text="start bot",
#     callback_data="start"))



admKeyList = [
[types.InlineKeyboardButton(text='Перечитать БД в кэш', callback_data='load_bd')],
    [types.InlineKeyboardButton(text='Искать, удалить в БД', callback_data='find_bd')],
    [types.InlineKeyboardButton(text='Редактировать в БД', callback_data='edit_bd')],
    [types.InlineKeyboardButton(text='Удалить из БД', callback_data='del_bd')],
    #[types.InlineKeyboardButton(text='Удалить из группы пользователя', callback_data='del_users_from_group')],
    [types.InlineKeyboardButton(text='Показать(файл) БД', callback_data='cat_bd')],
    #[types.InlineKeyboardButton(text="Заказать пропуск", callback_data="Заказать пропуск")],
    #[types.InlineKeyboardButton(text='Инструкция пешего', callback_data='man_pesh')],
    #[types.InlineKeyboardButton(text='Инструкция авто', callback_data='man_pesh')],
    [types.InlineKeyboardButton(text='Регистрация в БД админа', callback_data='reg')],
    [types.InlineKeyboardButton(text='Последние заявки', callback_data='cat_KPP')],
    [types.InlineKeyboardButton(text='Показать логи', callback_data='cat_log')],
    [types.InlineKeyboardButton(text='Номера телефонов', callback_data='phone')]
    #[types.InlineKeyboardButton(text='Список пользователей группы', callback_data='all_members')]
]
adm_keys = InlineKeyboardBuilder(admKeyList)



#переменные для функций поиска и работы с файлом bd.txt
id = array('w',[]) # dict()#
company = array('w',[]) # dict() #
tmp_l = dict() #array('w',[])
company=['None'] #company=['Вектор','Эхо','Администрация','Biotechfarm']
id= ['None'] #id= ['111', '222', '333', '444']
fio= ['None']
phone= ['None']

a:int=0
l=len(id)

## поиск организации по a = ID пользователя. Передать в формате str
def find_in_bd(usr_id:str):
    z=-1
    print(usr_id)
    for j in range(len(id)): # j=id.index(a)
        #print(j)
        if str(id[j])==str(usr_id):
            z=j
    if z==-1:
        c="null"
    else:
        c=company[z]
    return c

## поиск организации по имени возвращает номер в массиве найденого названия или ID ,-1 ничего не найдено ,-2 найдено более одного
def find_by_name(a:str):
    if len(id)==0:
        print(id)
        load_bd()
    c=-1
    n=0
    a=a.lower()
    for j in range(len(company)): # j=id.index(a)
      b=company[j].lower()
      if b.find(a)>-1:
        c=j
        n=n+1
    if c==-1:
        for j in range(len(id)):  # j=id.index(a)
            if id[j].find(a)>-1:
                c = j
                n=n+1
    if n>1:
        c=-2
    return c


#Ввод данных в бд, добавление в конец массива переменных id, company
def input_bd(usr_id, company_usr, phone_contact):  # Добавить в базу id, компанию и телефон
    # Убираем символы новой строки из названия компании
    company_usr = company_usr.replace('\n', ' ')
    # Добавляем данные в соответствующие списки
    id.append(str(usr_id))  # Добавляем ID пользователя
    company.append(str(company_usr))  # Добавляем название компании
    print(phone.append(str(phone_contact)))  # Добавляем номер телефона (новое поле)
    phone.append(str(phone_contact))
    return ()

def del_bd(a:int): #удаление резидента по номеру в массиве
    if len(id)==0:
        load_bd()
    id.pop(a)
    company.pop(a)
    phone.pop(a)
    save_bd()


#сохраить базу данных из массива переменных id, company в файл
def save_bd():
    # Открываем файл для записи
    with open('bd.txt', 'w', encoding='utf-8') as f:
        # Записываем количество записей (минус заголовок, если он есть)
        l = len(id)
        f.write(str(l - 1) + '\n')  # Предполагаем, что первый элемент — заголовок

        # Записываем данные для каждого пользователя
        for i in range(1, l):
            f.write(str(id[i]) + ';')  # ID пользователя
            f.write(str(company[i]) + ';')  # Компания
            f.write(str(phone[i]) + '\n')  # Номер телефона
    return


#При вызове функции загружает в переменные id, company массивы значений построчно(разделяя) из bd.txt
def load_bd():
#    tmp_l=dict(    )
    if len(id)>1:     #проверка
        return ()
    company[0] = "None"  # company=['Вектор','Эхо','Администрация','Biotechfarm']
    id[0] = "None"
    phone[0] = "None"
    f = open('bd.txt', 'r', encoding='utf-8')
    tmp_l = f.read().splitlines()
    f.close()
    print('База данных загружена из файла', len(tmp_l)) #, tmp_l)
    ll = int(tmp_l[0])
    # Загружаем данные
    for i in range(ll):
        data = tmp_l[i + 1].split(";")  # Разделяем строку на поля
        id.append(data[0])               # ID
        company.append(data[1])          # Компания+Фамилия
        phone.append(data[2])    # Номер телефона (новое поле)
    return ()


def to_html(new_propusk:str): # заполняет html пропусками за сегодняшний день
    rez=6 # !!!!   количество строк в файле зарезервированных под заголовок            !!!!!!
    #with open('propuska.html', 'a') as safe:pass #создать если отсутствует
    d=str(datetime.now())[0:10] # текущая дата
    if new_propusk.find('дминистрация')>-1:
        new_propusk='<font color="#ff0e0e">'+new_propusk+'</font>'
    f=open('index.html', 'r')
    tmp_l = f.read().splitlines()
    f.close()
    dd=str(tmp_l[0]) # дата которая будет записана в новый фаил
    l=len(tmp_l)
    # print('d=',len(d),'dd=',len(dd))
    if d!=dd:
    #   print('НОВЫЙ ваил')
        l=rez-1
        dd=d # новая дата новый фаил

    f = open('index.html', 'w')
    tmp_l[0]=dd
    # print('l=', l, 'rez=', rez)
    for i in range(0,(rez-1)):              # переносим шапку
       # print('i=', i, 'mass=', tmp_l[i])
        f.write(str(tmp_l[i]) + '\n')       # переносим шапку

    f.write("<p>"+str(new_propusk)+"</p>"+'\n') # новый пропуск

    if l>=rez:
        for i in range((rez-1),l):              # старые пропуска
         #   print('i=',i,'mass=',tmp_l[i])
            f.write(str(tmp_l[i]) + '\n')
    f.close()
    return ()


#пробуем использовать машину состояний для регистрации и направления диалога:
class Form(StatesGroup):
    fio = State()
    company_stat = State()
    sms = State()
    status = State()
    adm_find = State()
    edit_db_new = State()
    edit_db_old = State()
    del_elm = State()
    num_phone = State()





#Функция статуса пользователя, проверяет есть ли пользователь в группе CHANNEL_ID:
async def check_members(message: types.Message):
    user_channel = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=message.from_user.id)
    if (user_channel.status != "left") and (user_channel.status != "kicked"):
        await message.answer("Есть разрешение доступа к функционалу бота.") #Статус: {user_channel.status}")
        #print(f'user_channel.status True: {user_channel.status}')
        #logger.info(f'function check_members run, access user: {user_channel.user.username}, status: {user_channel.status}')
    else:
        await message.answer(f'Разрешение доступа отсутствует. Обратитесь к Коменданту Технопарка. Статус: {user_channel.status}')
        root_logger.info(f'function check_members run, access denied user {user_channel.user.username}, status: {user_channel.status}')

#Сообщение в группу от бота при добавлении участника
# @dp.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
# async def new_members_handler(event: ChatMemberUpdated):
#     b = await bot.get_chat_member(chat_id=CHANNEL_ID,user_id=event.from_user.id)
#     print(b)
#     await bot.send_message(chat_id=b.user.id, text='Привет, нажми старт')
#     await event.answer(text=f"Добро пожаловать @{event.from_user.full_name}",
#                        disable_notification=True, reply_markup=builder3.as_markup())

# Если вышел пользователь из группы
# @dp.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
# async def members_exit(event: ChatMemberUpdated):
#     b = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=event.from_user.id)
#     print(b)
#     find = find_in_bd(usr_id=str(event.from_user.id))
#     print(find)
#     if find == 'null':
#         find = 'Пользователь не был зарегистрирован в базе.'
#     await bot.send_message(chat_id=OHRANA_ID, text=f'Техническое оповещение. {find} покинул группу доступа(для заказа пропусков)'
#                                                    f' @{event.from_user.username} {event.from_user.full_name}, ID {event.from_user.id}.')
#                                                    #f'\nПропуска от пользователя не принимать.')#,disable_notification=False)
#     root_logger.warning(f'user left the group: {event.from_user.username} {event.from_user.full_name}, ID {event.from_user.id}, {find}')






#Сообщение при новом пользователе Бота
@chat_event_router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def user_joined_chat(event: ChatMemberUpdated, bot: Bot):
    admin_ids = ADMINS
    user = event.new_chat_member.user
    user_id = user.id
    username = f"@{user.username}" if user.username else "отсутствует"
    full_name = user.full_name
    chat_id = event.chat.id
    message_sms = (
        f"Новый пользователь вступил в чат:\n"
        f"ID: {user_id}\n"
        f"ChatID: {chat_id}\n"
        f"Name: {username}, full: {full_name}"
    )
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, message_sms)
        except Exception as e:
            print(f"Не удалось отправить сообщение администратору {admin_id}: {e}")


#Сообщение при покидании  пользователем чата Бота
@chat_event_router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_MEMBER >> IS_NOT_MEMBER))
async def user_joined_chat(event: ChatMemberUpdated, bot: Bot):
    admin_ids = ADMINS
    user = event.new_chat_member.user
    user_id = user.id
    username = f"@{user.username}" if user.username else "отсутствует"
    full_name = user.full_name
    chat_id = event.chat.id
    message_sms = (
        f"Новый пользователь вступил в чат:\n"
        f"ID: {user_id}\n"
        f"ChatID: {chat_id}\n"
        f"Name: {username}, full: {full_name}"
    )
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, message_sms)
        except Exception as e:
            print(f"Не удалось отправить сообщение администратору {admin_id}: {e}")




# Ловим команду /start и обрабатываем:
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
        await state.clear()
        load_bd()
        test1 = str(message.from_user.id)
        #print(f'id в поиске: {test1}')
        id_find = find_in_bd(test1)  # вызов поиска в бд по айди
        root_logger.info(f'id_find: {id_find}')
# Проверки
        check_usr = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=message.from_user.id)
        if (check_usr.status != "left") and (check_usr.status != "kicked"): #пользователь в группе CHANNEL_ID ?
            root_logger.info(f'/start: access user: {check_usr.user.username}, status: {check_usr.status}')
            print(f'user_channel.status True for user: {check_usr.user.username}, статус: {check_usr.status}')
            if id_find == "null": #Если нет id в bd.txt
                await message.answer('Необходимо пройти регистрацию. '
                                     'Пожалуйста, поделитесь своим номером телефона, это необходимо для отправки пропусков.'
                                     '\nНажмите кнопку "Отправить номер телефона"',
                                     reply_markup=key_builder.as_markup(resize_keyboard=True, one_time_keyboard=True))
                await state.set_state(Form.num_phone)
            else:
                await message.answer(f'Ваши данные: {id_find}')
                await state.update_data(company_stat=id_find)
                await message.answer(f"Для оформления разового пропуска для посетителя технопарка нажмите кнопку", reply_markup=builder.as_markup())
        else:
            await message.answer("Отказано. Вы должны состоять в специальной группе.")
            root_logger.info(f'/start: access denied user: {check_usr.user.username}, status: {check_usr.status}')
            await state.clear()
            print(f"Отказано пользователю: {check_usr.user.username}.Статус пользователя: {check_usr.status}")
# админ меню
        if (check_usr.status == "creator") or (check_usr.status == 'administrator'):
            await asyncio.sleep(0.3)
            await message.answer('Вы администратор', reply_markup=adm_button.as_markup())
            root_logger.warning(f'Admin: {check_usr.status}. ID: {message.from_user.id}')
            #await state.set_state(Form.company_stat)



@dp.message(lambda message: message.contact is not None, Form.num_phone)
async def get_contact_keyboard(message: types.Message, state: FSMContext):
    # Получаем номер телефона из контакта
    phone_number = message.contact.phone_number
    print(f"Номер телефона: {phone_number}")
    # Сохраняем номер телефона в состояние
    await state.update_data(num_phone=phone_number)
    # Убираем клавиатуру с кнопкой "Поделиться контактом"
    await message.answer(
        "Теперь введите наименование вашей организации",
        reply_markup=ReplyKeyboardRemove()  # Удаляем клавиатуру
    )
    # Переходим к следующему этапу
    await state.set_state(Form.company_stat)



#ввод данных компании
@dp.message(Form.company_stat)
async def input_company(message: types.Message, state: FSMContext):
     await state.update_data(company_stat=message.text) #Записываем текст в company_stat
     await message.answer('Введите ваши фамилию и инициалы')
     await state.set_state(Form.fio) #Переход в диалоге к хэндлеру Form.fio
     # logger.warning(f'Add in bd.txt: {get_usr_company} id:{message.from_user.id} from username: {message.from_user.username}')




@dp.message(Form.fio)
async def names(message: types.Message, state: FSMContext):
    await state.update_data(fio=message.text)
    data = await state.get_data()
    get_fio = data.get('fio')
    get_usr_company = data.get('company_stat')
    get_phone = data.get('num_phone')
    data_comp = str(get_fio) + str(get_usr_company) + str(get_phone)
    print(f'data_comp={data_comp}')

    #Ввод регистрационных данных в массив
    input_bd(usr_id=message.from_user.id,
             company_usr=get_usr_company+", "+get_fio,
             phone_contact='+'+get_phone)
    print(get_phone)
    save_bd() #сохранить в файл bd.txt
    await state.clear()
    root_logger.warning(f'Input bd.txt id: {message.from_user.id}, '
                        f'{get_usr_company} {get_fio} '
                        f'user: {message.from_user.full_name}, '
                        f'phone: {get_phone}')
    await cmd_start(message, state)



#ловим команду статус
@dp.message(Command("status"))
async def cmd_answer(message: types.Message, state: FSMContext):
    await check_members(message)
    #logger.info(f'command /status: cmd_answer run')
#хелп, описание
@dp.message(Command("help"))
async def cmd_hello(message: Message):
    await message.answer(help_comand)

#обработка кнопки Заказать пропуск:
@dp.callback_query(F.data == "Заказать пропуск")
async def send_zakazat_propusk(query: types.CallbackQuery, state: FSMContext):
#await query.message.delete_reply_markup()
    await query.answer()
    await query.message.edit_reply_markup()
    load_bd()
    find_in_bd(usr_id=str(query.from_user.id))
    check_usr = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=query.from_user.id)
    print(check_usr)
    if check_usr.status == 'left':
        print(check_usr)
        print(check_usr.status)
        await state.clear()
        await query.message.answer('Доступ запрещен')
        return ()
    data = await state.get_data()
    data.get('company_stat')
    #print_data = data.get('company_stat')
    #print(print_data)
    if data.get('company_stat') == None:
        load_bd()
        from_state = (find_in_bd(usr_id=str(query.from_user.id)))
        await state.update_data(company_stat=from_state)
        print(f'Данные из бд в from_state: {from_state}')

    await query.message.answer(text=f"Введите данные:\nФИО посетителя, либо полный номер автомобиля")
    root_logger.warning(f'Load bd. id: {query.from_user.id}')
    await state.set_state(Form.sms)
# async def del_button(message: types.Message):
#     await message.delete_reply_markup()

#ловим данные из ответа пользователя, выдаем кнопки подтверждения:
@dp.message(Form.sms)
async def capture_sms(message: Message, state: FSMContext):
    # async with ChatActionSender.typing(bot=bot, chat_id=message.chat.id):
    #     await asyncio.sleep(0.2)
    check_sms = message.text
    await state.update_data(sms=check_sms)
    keyboard_list = [
        [types.InlineKeyboardButton(text="✅Подтвердить", callback_data="yes_send_button")],
        [types.InlineKeyboardButton(text="❌Отменить", callback_data="cancel")]]
    key_cnf = InlineKeyboardBuilder(keyboard_list)
    #print('capture_sms Text:\n'+check_sms)
    data = await state.get_data()
    msg_text = (f'Подтвердите данные:'
                f'\n{data.get("sms")}')
    await message.answer(msg_text, reply_markup=key_cnf.as_markup())

#Обработка кнопки подтверждения и пересыл в OHRANA_ID данных пользователя:
@dp.callback_query(F.data == "yes_send_button")
async def callb_msg(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    await bot.edit_message_text(text='Заявка в обработке...', chat_id=query.message.chat.id,
                                message_id=query.message.message_id)

    #await query.message.delete_reply_markup()
    usr = query.from_user
    data = await state.get_data()
    usr_comp = data.get('company_stat')
    sms = data.get("sms")
    usr_fname = usr.first_name
    usr_lname = usr.last_name
    usr_name = usr.username




    if sms == None:
        await query.message.answer('Ошибка, данные сообщения утеряны. Пожалуйста, начните с начала командой: /start')
        await state.clear()  # сброс
        return
    else: #убрать отсутствующие значения в имени юзера
        if usr_name is not None: #если юзернэйм присутствует
            usr_name = str('@' + usr_name)
        elif usr_name is None: # если его нет
            usr_name = ''
        if usr_fname is None:
            usr_fname = ''
        if usr_lname is None:
            usr_lname = ''



        # Обработка текста сообщения: заменяем переносы строк на запятые
        sms_processed = sms.replace('\n', ', ')
        msg_text = (f'От: {usr_name} {usr_fname} {usr_lname} {usr_comp}\n'
                    f'Для: {sms_processed}')

        # Проверка на возможность отправки сообщения
        if not await can_send_message(sms_processed):
            await query.message.answer(f"Такое сообщение уже было оформлено в последние {TIME_WINDOW} минут, поэтому Ваше сообщение не доставлено."
                                       "\nИспользуйте команду: /start")
            return

        try:
            await bot.send_message(chat_id=OHRANA_ID, text=msg_text)  # отправка сообщения в группу охраны
        except:
            await query.message.answer(f"Не удалось отправить сообщение в группу охраны. Повторите попытку через некоторое время, возможно неисправности в сетях связи. "
                                       f"\nИспользуйте команду: /start")

        await asyncio.sleep(1.2)
        await bot.edit_message_text(text=f"Заявка передана на охрану с данными:\n{sms}", #Передаем как пользователь написал, а в остальных местах с реплейсом перевода строки
                                    chat_id=query.message.chat.id,
                                    message_id=query.message.message_id,
                                    reply_markup=builder2.as_markup())

        dt = str(usr_comp) + " ДЛЯ: " + str(sms_processed)
        print(dt)
        to_html(dt)
        root_logger.warning(f'Message in OHRANA. ID: {usr.id}, user: {usr.full_name}')
        root_logger.info(msg_text)
        ohrana_logger.info(f'От {usr_comp} Для: {sms_processed}')
    await state.clear() # сброс
    rotate_logs()




#Обработка кнопки Отмена, сброс
@dp.callback_query(F.data == "cancel")
async def cancel_data(query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await query.answer()
    await query.message.delete_reply_markup()
    await query.message.answer(f'Отменено.\nИспользуйте команду: /start')



async def can_send_message(sms_processed: str) -> bool:
    now = datetime.now()

    # Очистка старых записей
    for msg_text in list(sent_messages.keys()):
        sent_messages[msg_text] = [
            (uid, ts) for uid, ts in sent_messages[msg_text]
            if now - ts < TIME_WINDOW
        ]
        if not sent_messages[msg_text]:
            del sent_messages[msg_text]

    # Проверяем есть ли такое же сообщение в последние 30 минут
    if sms_processed in sent_messages:
        root_logger.info("Сообщение уже было отправлено"+sms_processed)
        return False  # Сообщение уже было отправлено

    # Если такого сообщения нет — добавляем его с текущим временем
    sent_messages.setdefault(sms_processed, []).append((None, now))  # ID пользователя не нужен здесь
    return True


async def reset_sent_messages():
    while True:
        now = datetime.now()
        next_reset_time = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        wait_time = (next_reset_time - now).total_seconds()

        await asyncio.sleep(wait_time)  # Ждем до следующего сброса

        global sent_messages
        sent_messages.clear()  # Сбрасываем словарь


@dp.callback_query(F.data == 'man_avto')
async def manual(query: types.CallbackQuery):
    await query.answer()
    await query.message.delete_reply_markup()
    await query.message.answer(text=manual_avto, reply_markup=builder.as_markup())

@dp.callback_query(F.data == 'man_pesh')
async def manual(query: types.CallbackQuery):
    await query.answer()
    await query.message.delete_reply_markup()
    await query.message.answer(text=manual_peshkom, reply_markup=builder.as_markup())


@dp.callback_query(F.data == 'admins')
async def for_adm(query: types.CallbackQuery):
    await query.message.answer('Выберите действие', reply_markup=adm_keys.as_markup())

#Ввод
@dp.callback_query(F.data == 'edit_bd')
async def cat_edit_bd(query: types.CallbackQuery, state: FSMContext):
    await query.message.answer('Введите номер элемента из БД для редактирования')
    await state.set_state(Form.edit_db_old)
    data = await state.get_data()
    print(data.get('edit_bd_old'))

@dp.message(Form.edit_db_old)
async def edit_bd(message: types.Message, state: FSMContext):
    load_bd()
    await state.update_data(edit_bd_old=message.text)
    print(f'Редактирование элемента БД: {message.text}')
    await message.answer(f'Выбран элемент:\n{id[int(message.text)]} {company[int(message.text)]}, '
                         f'')
    # data = await state.get_data()
    # a = data.get('edit_bd_old')
    await message.answer('Введите на что поменять, соблюдая разделитель ;')
    await state.set_state(Form.edit_db_new)

#Форма редактирования БД
@dp.message(Form.edit_db_new)
async def edit_bd(message: types.Message, state: FSMContext):
    load_bd()
    data = await state.get_data()
    a = int(data.get('edit_bd_old'))
    b = message.text
    company[a] = str(b)
    #await state.update_data(edit_bd_new=b)
    await message.answer(f'Обновлено: {id[a]} {company[a]}')
    save_bd()

@dp.callback_query(F.data == 'reg')
async def reg(query: types.CallbackQuery, state: FSMContext):
    await query.message.answer('Для вашего ID. Введите организацию')
    await state.set_state(Form.company_stat)

#кнопка База данных. из файла
@dp.callback_query(F.data == 'cat_bd')
async def catbd(query: types.CallbackQuery):
    with open('bd.txt', 'r', encoding='utf-8') as file:
        file_rd = file.read()
        # Разбиваем текст на блоки:
        chunk_size = 4096
        chunks = [file_rd[i:i + chunk_size] for i in range(0, len(file_rd), chunk_size)]
        # Отправляем каждую часть как отдельное сообщение
        for chunk in chunks:
            await query.message.answer(chunk)
            await asyncio.sleep(0.3)





#Кнопка поиска в БД
@dp.callback_query(F.data == 'find_bd')
async def amd_key_find(query: types.CallbackQuery, state: FSMContext):
    await query.message.answer(f'Поиск в БД. Ввести название компании или фамилию, или ID.')
    await state.set_state(Form.adm_find)

# Кнопка для удаления пользователя из группы
def get_delete_button(user_id: int):
    kb = InlineKeyboardBuilder()
    kb.add(types.InlineKeyboardButton(
        text=f'Удалить из группы пользователя {user_id}',
        callback_data=f'del_users_from_group_{user_id}'
    ))
    return kb.as_markup()


#обработка поиска в бд
@dp.message(Form.adm_find)
async def func_find(message: types.Message, state: FSMContext):
    await state.update_data(adm_keys=message.text)
    find = find_by_name(message.text)
    if find == -2:
        find = "Введите более точно, есть несколько совпадений в базе"
        await message.answer(find)
    elif find == -1:
        find = "Не найдено совпадений в базе"
        await message.answer(find)
    elif find > 0:
        user_info = f'Номер в базе: {str(find)}\n{id[find]} {company[find]}\n'
        await message.answer(f'{user_info}Вы хотите удалить этого пользователя из группы?',
                             reply_markup=get_delete_button(id[find]))
    else:
        await message.answer('Ошибка')


@dp.callback_query(F.data == 'del_bd')
async def func_del_bd(query: types.CallbackQuery, state: FSMContext):
    await query.message.answer('Введите номер элемента из базы данных')
    await state.set_state(Form.del_elm)

@dp.message(Form.del_elm)
async def del_elm(message: types.Message, state: FSMContext):
    load_bd()
    await state.update_data()
    elm = int(message.text)
    if (elm > len(id)) or (elm < 0):
        await message.answer(f'Некорректное значение')
    else:
        print(f'Удаляется из БД строка: {elm}')
        await message.answer(f'Удалена запись #{elm}\n'
                         f'{id[elm]} {company[elm]}\n'
                             f'Возможно необходимо перечитать базу данных. Используйте админское меню.')
        del_bd(elm)

#Реализация удаления пользователя из группы
@dp.callback_query(lambda c: c.data.startswith('del_users_from_group_'))
async def delete_user_handler(query: types.CallbackQuery):
    user_id = int(query.data.split('_')[-1])  # Извлечение user_id из callback_data
    try:
        await query.message.answer(f"Удалён пользователь с ID: {user_id}")
        await bot.ban_chat_member(CHANNEL, user_id)
        await bot.unban_chat_member(CHANNEL, user_id)
        root_logger.warning(f"Удалён пользователь с ID: {user_id}")
        print(f"Удалён пользователь с ID: {user_id}")
    except TelegramBadRequest as e:
        await query.message.answer(f'Ошибка при удалении пользователя из группы: {e}')
        print(e)

#tail logs, прочитать в бинарном режиме(потому что используется) лог и закодить в ютф-8.
# Может не выводить сообщение если произойдет разрыв одного символа в бинарном виде, в таком случае ошибка в лог
def tail(f, lines=20):
    total_lines_wanted = lines
    BLOCK_SIZE = 1024
    f.seek(0, 2)
    block_end_byte = f.tell()
    lines_to_go = total_lines_wanted
    block_number = -1
    blocks = []
    while lines_to_go > 0 and block_end_byte > 0:
        if (block_end_byte - BLOCK_SIZE > 0):
            f.seek(block_number*BLOCK_SIZE, 2)
            blocks.append(f.read(BLOCK_SIZE))
        else:
            f.seek(0,0)
            blocks.append(f.read(block_end_byte))
        lines_found = blocks[-1].count(b'\n')
        lines_to_go -= lines_found
        block_end_byte -= BLOCK_SIZE
        block_number -= 1
    all_read_text = b''.join(reversed(blocks))
    text_out = all_read_text.decode('utf-8')
    return text_out
    #return b'\n'.join(all_read_text.splitlines()[-total_lines_wanted:])


#Прочитать последние строки из файла(25 строк по умолчанию)
def tail_len(f, lines=25):
        read = f.readlines()
        full_length = len(read)
        log = (read[full_length - lines:])
        print(''.join(log))
        return str(''.join(log))

@dp.callback_query(F.data == 'cat_log')
async def cat_logs(query: types.CallbackQuery):
    with open('bot.log', 'rb') as f:
        catLOG = str(tail(f=f))
        await query.message.answer(catLOG)

#прочитать хвост KPP.log и отправить:
@dp.callback_query(F.data == 'cat_KPP')
async def cat_kpp(query: types.CallbackQuery):
    with open('KPP.log', 'r', encoding='utf-8') as file:
        catKPP = str(tail_len(f=file))
        await query.message.answer(catKPP)


#Прочитать phone.txt и отправить частями:
@dp.callback_query(F.data == 'phone')
async def cat_phone(query: types.CallbackQuery):
    with open('phone.txt', 'r', encoding='utf-8') as file:
        file_rd = file.read()
        # Разбиваем текст на блоки:
        chunk_size = 4096
        chunks = [file_rd[i:i + chunk_size] for i in range(0, len(file_rd), chunk_size)]
        # Отправляем каждую часть как отдельное сообщение
        for chunk in chunks:
            await query.message.answer(chunk)
            await asyncio.sleep(0.3)

@dp.callback_query(F.data == 'load_bd')
async def run_load_bd(query: types.CallbackQuery):
    print("Функция принудительной загрузки БД из файла")
    # Очистка массивов
    id.clear()
    company.clear()
    phone.clear()

    # Добавляем значения по умолчанию
    company.append("None")
    id.append("None")
    phone.append("None")

    load_bd()
    print(id, company)
    await query.message.answer('Очищаю кэш базы данных и вызываю функцию повторной загрузки из файла bd.txt в кэш')


@dp.message(F.text)
async def lovim_text(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer('Ошибка. Отправляйте данные согласно диалогу.\n'
                         'Используйте команду: /start')

# Запуск процесса поллинга новых апдейтов
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(bot_commands)
    # Запускаем задачу сброса словаря в отдельном потоке
    asyncio.create_task(reset_sent_messages())
    #поллинг
    await dp.start_polling(bot)


#Запуск
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.exception(e)
        print(e)
    # finally:
    #     dp.stop_polling(bot)
