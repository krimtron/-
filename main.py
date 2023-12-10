import aiogram
from aiogram import Bot, types
from aiogram import Dispatcher
from aiogram.filters.state import State, StatesGroup
import asyncio
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
import logging
import requests


API_TOKEN = 'YOUR_API_TOKEN'
OPENWEATHERMAP_API_KEY = 'YOUR_OPENWEATHERMAP_API_KEY'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

start_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Get Weather'))

class States(StatesGroup):
    START = State()
    LOCATION = State()
    RESULT = State()

@dp.message(Command("start", "help"))
async def send_welcome(message: types.Message):
    global correct_answers, incorrect_answers
    correct_answers = 0
    incorrect_answers = 0
    await message.reply("Привіт! Я готовий перевіряти твої знання математики. Готовий до першого питання? (введіть 'я готовий')")

@dp.message(Command("start"), state="*")
async def cmd_start(message: types.Message, state: FSMContext):
    await message.reply("Добро пожаловать в погодный бот! Введите /cancel в любое время, чтобы остановиться. вы хотите узнать погоду:", reply_markup=start_keyboard)
    await States.START.set()

@dp.message(state=States.START)
async def process_start(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user_id'] = message.from_user.id
    await message.reply("Пожалуйста, введите место, для которого вы хотите узнать погоду:")
    await States.LOCATION.set()

@dp.message(state=States.LOCATION)
async def process_location(message: types.Message, state: FSMContext):
    location = message.text
    try:
        weather_data = get_weather_data(location)
        temperature = weather_data['main']['temp'] - 273.15
        description = weather_data['weather'][0]['description']
        wind_speed = weather_data['wind']['speed']
        humidity = weather_data['main']['humidity']

        result_text = (
            f"Temperature: {temperature:.2f}°C\n"
            f"Weather: {description}\n"
            f"Wind Speed: {wind_speed} m/s\n"
            f"Humidity: {humidity}%"
        )

        await message.reply(result_text, reply_markup=ReplyKeyboardRemove())
        await States.RESULT.set()

    except Exception as e:
        logging.exception(f"Error getting weather data: {e}")
        await message.reply("К сожалению, при получении данных о погоде произошла ошибка. Пожалуйста, попробуйте еще раз.")

    await state.finish()

@dp.message(state=States.RESULT)
async def process_result(message: types.Message, state: FSMContext):
    await message.reply("Чем ты хочешь заняться дальше?", reply_markup=start_keyboard)
    await States.START.set()

def get_weather_data(location):
    api_url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={OPENWEATHERMAP_API_KEY}"
    response = requests.get(api_url)
    response.raise_for_status()
    return response.json()

if __name__ == '__main__':
    print("Starting bot...")
    asyncio.run(dp.start_polling())
