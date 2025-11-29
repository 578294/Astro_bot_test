"""
Данный файл представляет Tg-бота Astro_bot, который выдает гороскоп на каждый день.
"""

import random
import time
import json
import requests
import telebot
from loguru import logger
from datetime import datetime, timedelta

from config import TOKEN, PROXYAPI_KEY, PROXYAPI_BASE_URL

# Настройка логирования
logger.add(
    "debug.log",
    format="{time} - {level}: {message}",
    level="ERROR",
    rotation="1 week",
    compression="zip",
)

bot = telebot.TeleBot(TOKEN)

# user_data - словарь для хранения пользовательских данных
user_data = {}

# Данные знаков зодиака с датами
ZODIAC_SIGNS = {
    'aries': {
        'name': 'Овен',
        'emoji': '♈',
        'dates': '21 марта - 19 апреля',
        'element': 'Огонь',
        'planet': 'Марс'
    },
    'taurus': {
        'name': 'Телец',
        'emoji': '♉',
        'dates': '20 апреля - 20 мая',
        'element': 'Земля',
        'planet': 'Венера'
    },
    'gemini': {
        'name': 'Близнецы',
        'emoji': '♊',
        'dates': '21 мая - 20 июня',
        'element': 'Воздух',
        'planet': 'Меркурий'
    },
    'cancer': {
        'name': 'Рак',
        'emoji': '♋',
        'dates': '21 июня - 22 июля',
        'element': 'Вода',
        'planet': 'Луна'
    },
    'leo': {
        'name': 'Лев',
        'emoji': '♌',
        'dates': '23 июля - 22 августа',
        'element': 'Огонь',
        'planet': 'Солнце'
    },
    'virgo': {
        'name': 'Дева',
        'emoji': '♍',
        'dates': '23 августа - 22 сентября',
        'element': 'Земля',
        'planet': 'Меркурий'
    },
    'libra': {
        'name': 'Весы',
        'emoji': '♎',
        'dates': '23 сентября - 22 октября',
        'element': 'Воздух',
        'planet': 'Венера'
    },
    'scorpio': {
        'name': 'Скорпион',
        'emoji': '♏',
        'dates': '23 октября - 21 ноября',
        'element': 'Вода',
        'planet': 'Плутон'
    },
    'sagittarius': {
        'name': 'Стрелец',
        'emoji': '♐',
        'dates': '22 ноября - 21 декабря',
        'element': 'Огонь',
        'planet': 'Юпитер'
    },
    'capricorn': {
        'name': 'Козерог',
        'emoji': '♑',
        'dates': '22 декабря - 19 января',
        'element': 'Земля',
        'planet': 'Сатурн'
    },
    'aquarius': {
        'name': 'Водолей',
        'emoji': '♒',
        'dates': '20 января - 18 февраля',
        'element': 'Воздух',
        'planet': 'Уран'
    },
    'pisces': {
        'name': 'Рыбы',
        'emoji': '♓',
        'dates': '19 февраля - 20 марта',
        'element': 'Вода',
        'planet': 'Нептун'
    }
}

class GPT5HoroscopeService:
    def __init__(self):
        self.api_key = PROXYAPI_KEY
        self.base_url = PROXYAPI_BASE_URL
        self.model = "gpt-5-chat-latest"

    def get_horoscope(self, zodiac_sign, period, gender):
        """Получение гороскопа через PROXY API с учетом пола"""
        try:
            if not self.api_key:
                logger.error("PROXYAPI_KEY not configured")
                return self._get_fallback_horoscope(zodiac_sign, period, gender)

            zodiac_data = ZODIAC_SIGNS.get(zodiac_sign)
            if not zodiac_data:
                return self._get_fallback_horoscope(zodiac_sign, period, gender)

            prompt = self._build_horoscope_prompt(zodiac_data, period, gender)

            return self._make_api_request(prompt, zodiac_data, period, gender)

        except Exception as e:
            logger.error(f"Horoscope generation failed: {str(e)}")
            return self._get_fallback_horoscope(zodiac_sign, period, gender)

    def get_compatibility(self, sign1, gender1, sign2, gender2):
        """Получение совместимости через PROXY API"""
        try:
            if not self.api_key:
                logger.error("PROXYAPI_KEY not configured")
                return self._get_fallback_compatibility(sign1, gender1, sign2, gender2)

            zodiac_data1 = ZODIAC_SIGNS.get(sign1)
            zodiac_data2 = ZODIAC_SIGNS.get(sign2)

            if not zodiac_data1 or not zodiac_data2:
                return self._get_fallback_compatibility(sign1, gender1, sign2, gender2)

            prompt = self._build_compatibility_prompt(zodiac_data1, gender1, zodiac_data2, gender2)

            return self._make_api_request(prompt, zodiac_data1, 'compatibility', zodiac_data2, gender1, gender2)

        except Exception as e:
            logger.error(f"Compatibility generation failed: {str(e)}")
            return self._get_fallback_compatibility(sign1, gender1, sign2, gender2)

    def _build_horoscope_prompt(self, zodiac_data, period, gender):
        """Создание промпта для гороскопа с учетом пола"""
        period_names = {
            'today': 'сегодня',
            'tomorrow': 'завтра',
            'week': 'на этой неделе',
            'month': 'в этом месяце',
            'year': 'в этом году'
        }

        period_name = period_names.get(period, 'сегодня')
        current_date = datetime.now().strftime("%d.%m.%Y")

        gender_text = "мужчины" if gender == 'мужчина' else "женщины"

        prompt = f"""
    СОСТАВЬ ПОДРОБНЫЙ ПЕРСОНАЛИЗИРОВАННЫЙ ГОРОСКОП ДЛЯ {gender_text.upper()} ЗНАКА {zodiac_data['name']} {zodiac_data['emoji']}
    НА ПЕРИОД: {period_name} ({self._get_period_dates(period)})

    ТЕКУЩАЯ ДАТА: {current_date}

    ИНФОРМАЦИЯ О ЗНАКЕ:
    - Стихия: {zodiac_data['element']}
    - Правящая планета: {zodiac_data['planet']}
    - Период действия: {zodiac_data['dates']}
    - Пол: {gender}

    СТРУКТУРА ГОРОСКОПА:

    <b>🌟 ОБЩИЙ ПРОГНОЗ ДЛЯ {gender_text.upper()}</b>
    Опиши общую энергетику периода с учетом гендерных особенностей

    <b>💖 ЛИЧНАЯ ЖИЗНЬ И ОТНОШЕНИЯ</b>
    Расскажи о романтических и семейных отношениях, учитывая что это {gender_text}

    <b>💼 КАРЬЕРА И ФИНАНСЫ</b>
    Опиши профессиональные и финансовые перспективы для {gender_text}

    <b>🌿 ЗДОРОВЬЕ И САМОЧУВСТВИЕ</b>
    Дай рекомендации по здоровью с учетом особенностей {gender_text}

    <b>📚 ЛИЧНОСТНЫЙ РОСТ</b>
    Расскажи о возможностях для развития личности {gender_text}

    <b>🎯 ПРАКТИЧЕСКИЕ РЕКОМЕНДАЦИИ</b>
    Дай конкретные советы для {gender_text} знака {zodiac_data['name']}

    Требования:
    - Используй HTML теги <b> для выделения заголовков
    - Не используй звездочки * и другие markdown символы
    - Будь конкретным и практичным
    - Сохраняй позитивный тон
    - Учитывай характеристики знака {zodiac_data['name']} и пол {gender}
    - Учитывай гендерные особенности в рекомендациях
    """

        return prompt

    def _build_compatibility_prompt(self, zodiac_data1, gender1, zodiac_data2, gender2):
        """Создание промпта для совместимости"""
        prompt = f"""
    ПРОАНАЛИЗИРУЙ СОВМЕСТИМОСТЬ В ОТНОШЕНИЯХ МЕЖДУ:

    {gender1.capitalize()} {zodiac_data1['name']} {zodiac_data1['emoji']}
    и
    {gender2.capitalize()} {zodiac_data2['name']} {zodiac_data2['emoji']}

    ИНФОРМАЦИЯ О ЗНАКАХ:
    {gender1.capitalize()} {zodiac_data1['name']}:
    - Стихия: {zodiac_data1['element']}
    - Правящая планета: {zodiac_data1['planet']}
    - Основные черты: {self._get_zodiac_traits(zodiac_data1['name'])}
    - Пол: {gender1}

    {gender2.capitalize()} {zodiac_data2['name']}:
    - Стихия: {zodiac_data2['element']}
    - Правящая планета: {zodiac_data2['planet']}
    - Основные черты: {self._get_zodiac_traits(zodiac_data2['name'])}
    - Пол: {gender2}

    СТРУКТУРА АНАЛИЗА СОВМЕСТИМОСТИ:

    <b>💫 ОБЩАЯ СОВМЕСТИМОСТЬ</b>
    Оцени общую совместимость в процентах и дай общее описание с учетом гендерных особенностей

    <b>❤️ РОМАНТИЧЕСКАЯ СОВМЕСТИМОСТЬ</b>
    Проанализируй химию, страсть и романтические аспекты для {gender1} и {gender2}

    <b>🤝 ЭМОЦИОНАЛЬНАЯ СОВМЕСТИМОСТЬ</b>
    Опиши эмоциональную связь и понимание друг друга с учетом пола

    <b>💼 ПРАКТИЧЕСКАЯ СОВМЕСТИМОСТЬ</b>
    Проанализируй бытовые вопросы и совместные цели для этой пары

    <b>🌟 СИЛЬНЫЕ СТОРОНЫ СОЮЗА</b>
    Перечисли основные преимущества этого сочетания с учетом гендерной динамики

    <b>⚠️ ВОЗМОЖНЫЕ СЛОЖНОСТИ</b>
    Укажи потенциальные проблемы и разногласия, которые могут возникнуть между {gender1} и {gender2}

    <b>💡 РЕКОМЕНДАЦИИ ДЛЯ ПАРЫ</b>
    Дай практические советы для гармоничных отношений между {gender1} {zodiac_data1['name']} и {gender2} {zodiac_data2['name']}

    Требования:
    - Используй HTML теги <b> для выделения заголовков
    - Не используй звездочки * и другие markdown символы
    - Будь объективным и честным
    - Учитывай гендерные особенности обоих партнеров
    - Дай конкретные примеры и рекомендации
    - Сохраняй профессиональный тон
    - Учитывай комбинацию полов в анализе
    """

        return prompt

    def _get_zodiac_traits(self, zodiac_name):
        """Получить характерные черты знака"""
        traits = {
            'Овен': 'энергичный, инициативный, прямолинейный',
            'Телец': 'надежный, терпеливый, практичный',
            'Близнецы': 'общительный, любознательный, адаптивный',
            'Рак': 'заботливый, интуитивный, эмоциональный',
            'Лев': 'щедрый, творческий, уверенный',
            'Дева': 'аналитичный, внимательный, практичный',
            'Весы': 'гармоничный, дипломатичный, эстетичный',
            'Скорпион': 'страстный, проницательный, решительный',
            'Стрелец': 'оптимистичный, авантюрный, философский',
            'Козерог': 'амбициозный, дисциплинированный, ответственный',
            'Водолей': 'инновационный, гуманитарный, независимый',
            'Рыбы': 'сочувствующий, творческий, интуитивный'
        }
        return traits.get(zodiac_name, '')

    def _make_api_request(self, prompt, zodiac_data1, period, zodiac_data2=None, gender1=None, gender2=None):
        """Общий метод для API запросов"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()

            if period == 'compatibility':
                return {
                    'success': True,
                    'compatibility': content,
                    'zodiac1_name': zodiac_data1['name'],
                    'zodiac1_emoji': zodiac_data1['emoji'],
                    'zodiac2_name': zodiac_data2['name'],
                    'zodiac2_emoji': zodiac_data2['emoji'],
                    'gender1': gender1,
                    'gender2': gender2
                }
            else:
                return {
                    'success': True,
                    'horoscope': content,
                    'period_dates': self._get_period_dates(period),
                    'zodiac_name': zodiac_data1['name'],
                    'zodiac_emoji': zodiac_data1['emoji'],
                    'gender': gender1
                }
        else:
            logger.error(f"API request failed: {response.status_code}")
            if period == 'compatibility':
                return self._get_fallback_compatibility(
                    zodiac_data1['name'].lower(), gender1,
                    zodiac_data2['name'].lower(), gender2
                )
            else:
                return self._get_fallback_horoscope(zodiac_data1['name'].lower(), period, gender1)

    def _get_system_prompt(self):
        """Системный промпт"""
        return """
Ты - профессиональный астролог с большим опытом. 
Составляй точные, полезные и мотивирующие гороскопы и анализы совместимости.
Будь конкретным в рекомендациях и учитывай особенности каждого знака зодиака и гендерные особенности.
Всегда следуй указанной структуре.
Используй современные астрологические методики.
"""

    def _get_period_dates(self, period):
        """Генерация дат для периодов"""
        today = datetime.now()
        months_ru = [
            'январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
            'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь'
        ]

        if period == 'today':
            return f"{today.day} {months_ru[today.month-1]}"
        elif period == 'tomorrow':
            tomorrow = today + timedelta(days=1)
            return f"{tomorrow.day} {months_ru[tomorrow.month-1]}"
        elif period == 'week':
            return "неделя"
        elif period == 'month':
            return f"{months_ru[today.month-1]}"
        elif period == 'year':
            return f"{today.year}"
        else:
            return ""

    def _get_fallback_horoscope(self, zodiac_sign, period, gender):
        """Резервный гороскоп на случай ошибки"""
        zodiac_data = ZODIAC_SIGNS.get(zodiac_sign, {
            'name': 'Неизвестный знак',
            'emoji': '✨',
            'element': '',
            'planet': ''
        })

        gender_text = "мужчины" if gender == 'мужчина' else "женщины"

        fallback_text = f"""<b>🌟 ОБЩИЙ ПРОГНОЗ ДЛЯ {gender_text.upper()}</b>
    Для {gender_text} знака {zodiac_data['name']} этот период обещает интересные возможности для роста и развития.

    <b>💖 ЛИЧНАЯ ЖИЗНЬ И ОТНОШЕНИЯ</b>
    Время укреплять существующие связи и открываться новым знакомствам.

    <b>💼 КАРЬЕРА И ФИНАНСЫ</b>
    Благоприятный период для профессиональных достижений и финансового планирования.

    <b>🌿 ЗДОРОВЬЕ И САМОЧУВСТВИЕ</b>
    Обратите внимание на баланс между работой и отдыхом.

    <b>📚 ЛИЧНОСТНЫЙ РОСТ</b>
    Идеальное время для обучения и саморазвития.

    <b>🎯 ПРАКТИЧЕСКИЕ РЕКОМЕНДАЦИИ</b>
    Составьте план действий и следуйте своей интуиции."""

        return {
            'success': True,
            'horoscope': fallback_text,
            'period_dates': self._get_period_dates(period),
            'zodiac_name': zodiac_data['name'],
            'zodiac_emoji': zodiac_data['emoji'],
            'gender': gender
        }

    def _get_fallback_compatibility(self, sign1, gender1, sign2, gender2):
        """Резервный анализ совместимости на случай ошибки"""
        zodiac_data1 = ZODIAC_SIGNS.get(sign1, {'name': 'Неизвестный', 'emoji': '✨'})
        zodiac_data2 = ZODIAC_SIGNS.get(sign2, {'name': 'Неизвестный', 'emoji': '✨'})

        fallback_text = f"""<b>💫 ОБЩАЯ СОВМЕСТИМОСТЬ</b>
    Совместимость {gender1} {zodiac_data1['name']} и {gender2} {zodiac_data2['name']}: 75%

    <b>❤️ РОМАНТИЧЕСКАЯ СОВМЕСТИМОСТЬ</b>
    Пара обладает хорошей химией и взаимным притяжением.

    <b>🤝 ЭМОЦИОНАЛЬНАЯ СОВМЕСТИМОСТЬ</b>
    Эмоциональная связь требует работы, но возможна глубокая привязанность.

    <b>💼 ПРАКТИЧЕСКАЯ СОВМЕСТИМОСТЬ</b>
    В бытовых вопросах могут возникать разногласия, но они решаемы.

    <b>🌟 СИЛЬНЫЕ СТОРОНЫ СОЮЗА</b>
    Взаимное уважение
    Общие интересы
    Способность поддерживать друг друга

    <b>⚠️ ВОЗМОЖНЫЕ СЛОЖНОСТИ</b>
    Разный подход к решению проблем
    Эмоциональные различия

    <b>💡 РЕКОМЕНДАЦИИ ДЛЯ ПАРЫ</b>
    Учитесь слушать и слышать друг друга
    Находите компромиссы в спорных ситуациях
    Цените различия как возможность для роста"""

        return {
            'success': True,
            'compatibility': fallback_text,
            'zodiac1_name': zodiac_data1['name'],
            'zodiac1_emoji': zodiac_data1['emoji'],
            'zodiac2_name': zodiac_data2['name'],
            'zodiac2_emoji': zodiac_data2['emoji'],
            'gender1': gender1,
            'gender2': gender2
        }

    def get_name_meaning(self, name):
        """Получение значения имени через PROXY API"""
        try:
            if not self.api_key:
                logger.error("PROXYAPI_KEY not configured")
                return self._get_fallback_name_meaning(name)

            prompt = self._build_name_meaning_prompt(name)
            return self._make_name_api_request(prompt, name)

        except Exception as e:
            logger.error(f"Name meaning generation failed: {str(e)}")
            return self._get_fallback_name_meaning(name)

    def _build_name_meaning_prompt(self, name):
        """Создание промпта для анализа имени"""
        prompt = f"""
    ПРОАНАЛИЗИРУЙ ЗНАЧЕНИЕ И ХАРАКТЕРИСТИКИ ИМЕНИ: {name.upper()}
    
    СТРУКТУРА АНАЛИЗА:
    
    <b>📛 ПРОИСХОЖДЕНИЕ И ЗНАЧЕНИЕ</b>
    Расскажи о происхождении имени, его этимологии и буквальном переводе
    
    <b>🌟 ОСНОВНЫЕ ЧЕРТЫ ХАРАКТЕРА</b>
    Опиши типичные характеристики личности, связанные с этим именем
    
    <b>💫 ЭНЕРГЕТИКА И ВИБРАЦИЯ</b>
    Проанализируй энергетику имени и его влияние на судьбу
    
    <b>❤️ ЛИЧНАЯ ЖИЗНЬ И ОТНОШЕНИЯ</b>
    Опиши особенности в отношениях и совместимость
    
    <b>💼 ПРОФЕССИОНАЛЬНЫЕ СКЛОННОСТИ</b>
    Укажи подходящие профессии и карьерные пути
    
    <b>🌿 СИЛЬНЫЕ И СЛАБЫЕ СТОРОНЫ</b>
    Перечисли достоинства и возможные challenges
    
    <b>🎯 СОВЕТЫ ДЛЯ ОБЛАДАТЕЛЕЙ ИМЕНИ</b>
    Дай практические рекомендации для личностного роста
    
    Требования:
    - Используй HTML теги <b> для выделения заголовков
    - Не используй звездочки * и другие markdown символы
    - Будь объективным и точным
    - Учитывай различные версии происхождения имени
    - Сохраняй позитивный и мотивирующий тон
    - Дай конкретные примеры и рекомендации
    """

        return prompt

    def _make_name_api_request(self, prompt, name):
        """API запрос для анализа имени"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self._get_system_prompt_for_names()},
                {"role": "user", "content": prompt}
            ],
        }

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()

            return {
                'success': True,
                'name_meaning': content,
                'name': name
            }
        else:
            logger.error(f"Name API request failed: {response.status_code}")
            return self._get_fallback_name_meaning(name)

    def _get_system_prompt_for_names(self):
        """Системный промпт для анализа имен"""
        return """
    Ты - эксперт по ономастике и анализу имен с большим опытом.
    Анализируй имена профессионально, учитывая:
    - Этимологию и происхождение
    - Исторический контекст
    - Культурные особенности
    - Психологические характеристики
    - Нумерологические аспекты
    
    Будь точным в фактах, но также учитывай современные интерпретации.
    Всегда следуй указанной структуре анализа.
    """

    def _get_fallback_name_meaning(self, name):
        """Резервный анализ имени на случай ошибки"""
        fallback_text = f"""<b>📛 ПРОИСХОЖДЕНИЕ И ЗНАЧЕНИЕ</b>
    Имя {name} имеет богатую историю и глубокое значение.
    
    <b>🌟 ОСНОВНЫЕ ЧЕРТЫ ХАРАКТЕРА</b>
    Обладатели имени {name} обычно отличаются целеустремленностью и коммуникабельностью.
    
    <b>💫 ЭНЕРГЕТИКА И ВИБРАЦИЯ</b>
    Имя несет позитивную энергию и способствует успеху в начинаниях.
    
    <b>❤️ ЛИЧНАЯ ЖИЗНЬ И ОТНОШЕНИЯ</b>
    В отношениях ценят искренность и доверие, стремятся к гармонии.
    
    <b>💼 ПРОФЕССИОНАЛЬНЫЕ СКЛОННОСТИ</b>
    Подходят профессии, связанные с общением, творчеством и руководством.
    
    <b>🌿 СИЛЬНЫЕ И СЛАБЫЕ СТОРОНЫ</b>
    Сильные стороны: лидерские качества, адаптивность
    Возможные сложности: излишняя эмоциональность
    
    <b>🎯 СОВЕТЫ ДЛЯ ОБЛАДАТЕЛЕЙ ИМЕНИ</b>
    Развивайте терпение и умение слушать других.
    Используйте свои коммуникативные навыки для построения карьеры."""

        return {
            'success': True,
            'name_meaning': fallback_text,
            'name': name
        }

# Создаем экземпляр сервиса
horoscope_service = GPT5HoroscopeService()

# Создаем клавиатуры
def get_main_menu_keyboard():
    """Главное меню выбора функции"""
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ['🔮 Получить гороскоп', '💑 Проверить совместимость', '📜 Знаки зодиака', '📛 Значение имени', 'ℹ️ Помощь']
    keyboard.row(buttons[0], buttons[1])
    keyboard.row(buttons[2], buttons[3])
    keyboard.row(buttons[4])
    return keyboard

def get_name_input_keyboard():
    """Клавиатура для ввода имени"""
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('🔙 Назад')
    return keyboard

def get_gender_keyboard():
    """Клавиатура выбора пола (упрощенная версия)"""
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = ['👨 Мужчина', '👩 Женщина', '🔙 Назад']
    keyboard.row(buttons[0], buttons[1])
    keyboard.row(buttons[2])
    return keyboard

def get_zodiac_keyboard():
    """Клавиатура с знаками зодиака"""
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)

    buttons = []
    for sign_id, sign_data in ZODIAC_SIGNS.items():
        btn_text = f"{sign_data['emoji']} {sign_data['name']}"
        buttons.append(btn_text)

    for i in range(0, len(buttons), 3):
        keyboard.row(*buttons[i:i+3])

    keyboard.row('🔙 Назад')
    return keyboard

def get_period_keyboard():
    """Клавиатура с периодами"""
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    today = datetime.now()
    months_ru = [
        'январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
        'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь'
    ]

    today_text = f"Сегодня ({today.day} {months_ru[today.month-1]})"
    tomorrow = today + timedelta(days=1)
    tomorrow_text = f"Завтра ({tomorrow.day} {months_ru[tomorrow.month-1]})"
    week_text = "Неделя"
    month_text = f"Месяц ({months_ru[today.month-1]})"
    year_text = f"Год ({today.year})"

    buttons = [today_text, tomorrow_text, week_text, month_text, year_text, '🔙 Назад']

    for i in range(0, len(buttons), 2):
        keyboard.row(*buttons[i:i+2])

    return keyboard

@bot.message_handler(commands=['start'])
@logger.catch
def welcome(message: telebot.types.Message) -> None:
    """Приветственное сообщение"""
    chat_id = message.chat.id
    user_name = message.from_user.first_name

    welcome_text = f"""
Привет, {user_name}! 👋

Я AstroBot - твой личный астрологический помощник! 
Я помогу в создании персонального гороскопа и анализа совместимости.

✨ <b>Выбери что тебя интересует:</b>"""

    bot.send_message(chat_id, welcome_text,
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text == '🔮 Получить гороскоп')
@logger.catch
def horoscope_start(message: telebot.types.Message) -> None:
    """Начало получения гороскопа"""
    chat_id = message.chat.id
    user_data[chat_id] = {'mode': 'horoscope', 'step': 'gender'}

    bot.send_message(chat_id, "👤 <b>Для персонализированного гороскопа выбери свой пол:</b>",
                    reply_markup=get_gender_keyboard(),
                    parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text == '💑 Проверить совместимость')
@logger.catch
def compatibility_start(message: telebot.types.Message) -> None:
    """Начало проверки совместимости"""
    chat_id = message.chat.id
    user_data[chat_id] = {'mode': 'compatibility', 'step': 'first_gender'}

    bot.send_message(chat_id, "👤 <b>Выбери свой пол:</b>",
                    reply_markup=get_gender_keyboard(),
                    parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text == '📛 Значение имени')
@logger.catch
def name_meaning_start(message: telebot.types.Message) -> None:
    """Начало получения значения имени"""
    chat_id = message.chat.id
    user_data[chat_id] = {'mode': 'name_meaning', 'step': 'input_name'}

    bot.send_message(chat_id,
                     "📛 <b>Введите имя для анализа:</b>\n\n<i>Я расскажу о его происхождении, значении и характеристиках личности.</i>",
                     reply_markup=get_name_input_keyboard(),
                     parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text in ['👨 Мужчина', '👩 Женщина'])
@logger.catch
def handle_gender_selection(message: telebot.types.Message) -> None:
    """Обработчик выбора пола"""
    chat_id = message.chat.id

    if chat_id not in user_data:
        bot.send_message(chat_id, "Пожалуйста, начните с выбора функции из главного меню.")
        return

    gender = 'мужчина' if message.text == '👨 Мужчина' else 'женщина'
    mode = user_data[chat_id]['mode']
    step = user_data[chat_id]['step']

    if mode == 'horoscope' and step == 'gender':
        user_data[chat_id].update({
            'gender': gender,
            'step': 'zodiac'
        })
        bot.send_message(chat_id, f"✨ <b>Отлично! Теперь выбери свой знак зодиака:</b>",
                        reply_markup=get_zodiac_keyboard(),
                        parse_mode='HTML')

    elif mode == 'compatibility':
        if step == 'first_gender':
            # Автоматически определяем противоположный пол для партнера
            partner_gender = 'женщина' if gender == 'мужчина' else 'мужчина'

            user_data[chat_id].update({
                'first_gender': gender,
                'second_gender': partner_gender,  # Автоматически устанавливаем противоположный пол
                'step': 'first_zodiac'
            })

            bot.send_message(chat_id, f"✨ <b>Теперь выбери свой знак зодиака:</b>",
                            reply_markup=get_zodiac_keyboard(),
                            parse_mode='HTML')

@bot.message_handler(func=lambda message: any(sign_data['name'] in message.text for sign_data in ZODIAC_SIGNS.values()))
@logger.catch
def handle_zodiac_selection(message: telebot.types.Message) -> None:
    """Обработчик выбора знака зодиака"""
    chat_id = message.chat.id
    zodiac_text = message.text

    # Находим выбранный знак зодиака
    selected_sign = None
    for sign_id, sign_data in ZODIAC_SIGNS.items():
        if sign_data['name'] in zodiac_text:
            selected_sign = sign_id
            break

    # Ранняя проверка и возврат если знак не найден
    if not selected_sign:
        bot.send_message(chat_id, "Пожалуйста, выбери знак зодиака из списка.")
        return

    if chat_id not in user_data:
        bot.send_message(chat_id, "Пожалуйста, начните с выбора функции из главного меню.")
        return

    mode = user_data[chat_id]['mode']
    step = user_data[chat_id]['step']

    if mode == 'horoscope' and step == 'zodiac':
        user_data[chat_id].update({
            'zodiac_sign': selected_sign,
            'step': 'period'
        })
        zodiac_data = ZODIAC_SIGNS[selected_sign]

        response_text = f"""
✅ <b>Выбран знак: {zodiac_data['emoji']} {zodiac_data['name']}</b>
👤 Пол: {user_data[chat_id]['gender']}
📅 Период: {zodiac_data['dates']}
🌌 Стихия: {zodiac_data['element']}
🪐 Планета: {zodiac_data['planet']}

<b>Теперь выбери период для гороскопа:</b>"""

        bot.send_message(chat_id, response_text,
                        reply_markup=get_period_keyboard(),
                        parse_mode='HTML')

    elif mode == 'compatibility':
        if step == 'first_zodiac':
            user_data[chat_id].update({
                'first_sign': selected_sign,
                'step': 'second_zodiac'
            })

            gender_text = "партнерши" if user_data[chat_id]['second_gender'] == 'женщина' else "партнера"
            bot.send_message(chat_id, f"✨ <b>Теперь выбери знак зодиака {gender_text}:</b>",
                            reply_markup=get_zodiac_keyboard(),
                            parse_mode='HTML')

        elif step == 'second_zodiac':
            user_data[chat_id].update({
                'second_sign': selected_sign
            })

            # Все данные собраны - генерируем совместимость
            first_sign = user_data[chat_id]['first_sign']
            first_gender = user_data[chat_id]['first_gender']
            second_sign = user_data[chat_id]['second_sign']
            second_gender = user_data[chat_id]['second_gender']

            zodiac1 = ZODIAC_SIGNS[first_sign]
            zodiac2 = ZODIAC_SIGNS[second_sign]

            loading_msg = bot.send_message(chat_id, "💞 <i>Анализирую совместимость ... Это займет несколько секунд.</i>",
                                          parse_mode='HTML')

            result = horoscope_service.get_compatibility(first_sign, first_gender, second_sign, second_gender)

            bot.delete_message(chat_id, loading_msg.message_id)

            if result['success']:
                response = f"""
💑 <b>СОВМЕСТИМОСТЬ</b> 💑

👤 {first_gender.capitalize()} {zodiac1['emoji']} <b>{zodiac1['name']}</b>
💞 
👤 {second_gender.capitalize()} {zodiac2['emoji']} <b>{zodiac2['name']}</b>

{result['compatibility']}

✨ <i>Пусть ваши отношения будут гармоничными!</i>"""

                bot.send_message(chat_id, response,
                                reply_markup=get_main_menu_keyboard(),
                                parse_mode='HTML')
            else:
                bot.send_message(chat_id,
                                "❌ Извините, произошла ошибка при анализе совместимости. Попробуйте позже.",
                                reply_markup=get_main_menu_keyboard())

def split_long_message(text, max_length=4000):
    """Разделяет длинное сообщение на части"""
    if len(text) <= max_length:
        return [text]

    parts = []
    while text:
        if len(text) <= max_length:
            parts.append(text)
            break

        # Находим последний перенос строки в пределах лимита
        split_pos = text.rfind('\n', 0, max_length)
        if split_pos == -1:
            # Если нет переносов, разбиваем по предложениям
            split_pos = text.rfind('. ', 0, max_length)
            if split_pos == -1:
                # Если нет точек, просто обрезаем
                split_pos = max_length

        parts.append(text[:split_pos + 1])
        text = text[split_pos + 1:]

    return parts

@bot.message_handler(func=lambda message: any(period in message.text for period in [
    'Сегодня (', 'Завтра (', 'Неделя', 'Месяц (', 'Год ('
]))
@logger.catch
def handle_period_selection(message: telebot.types.Message) -> None:
    """Обработчик выбора периода для гороскопа"""
    chat_id = message.chat.id

    if chat_id not in user_data or 'zodiac_sign' not in user_data[chat_id]:
        bot.send_message(chat_id, "Пожалуйста, сначала выбери свой знак зодиака.",
                        reply_markup=get_zodiac_keyboard())
        return

    zodiac_sign = user_data[chat_id]['zodiac_sign']
    gender = user_data[chat_id]['gender']
    period_text = message.text

    # Определяем период по тексту кнопки
    if period_text.startswith('Сегодня'):
        period = 'today'
    elif period_text.startswith('Завтра'):
        period = 'tomorrow'
    elif period_text == 'Неделя':
        period = 'week'
    elif period_text.startswith('Месяц'):
        period = 'month'
    elif period_text.startswith('Год'):
        period = 'year'
    else:
        bot.send_message(chat_id, "Пожалуйста, выбери период из списка.")
        return

    # Отправляем сообщение о загрузке
    loading_msg = bot.send_message(chat_id, "🔮 <i>Составляю ваш персональный гороскоп... Это займет несколько секунд.</i>",
                                  parse_mode='HTML')

    # Получаем гороскоп
    result = horoscope_service.get_horoscope(zodiac_sign, period, gender)

    # Удаляем сообщение о загрузке
    bot.delete_message(chat_id, loading_msg.message_id)

    if result['success']:
        zodiac_data = ZODIAC_SIGNS[zodiac_sign]

        # Форматируем период для отображения
        period_display = {
            'today': 'Сегодня',
            'tomorrow': 'Завтра',
            'week': 'Неделя',
            'month': 'Месяц',
            'year': 'Год'
        }.get(period, period)

        gender_text = "мужчины" if gender == 'мужчина' else "женщины"

        header = f"""
{zodiac_data['emoji']} <b>ПЕРСОНАЛИЗИРОВАННЫЙ ГОРОСКОП ДЛЯ {gender_text.upper()}</b> {zodiac_data['emoji']}
📅 <b>Период:</b> {period_display} ({result['period_dates']})
👤 <b>Знак:</b> {zodiac_data['name']} | <b>Пол:</b> {gender}

"""

        footer = "\n\n✨ <i>Пусть звезды благоволят вам!</i>"

        # Формируем полное сообщение
        full_message = header + result['horoscope'] + footer

        # Разделяем длинные сообщения
        message_parts = split_long_message(full_message)

        # Отправляем первую часть с клавиатурой, остальные - без
        for i, part in enumerate(message_parts):
            if i == 0:
                # Первая часть с клавиатурой
                bot.send_message(chat_id, part,
                                reply_markup=get_main_menu_keyboard(),
                                parse_mode='HTML')
            else:
                # Последующие части без клавиатуры
                bot.send_message(chat_id, part,
                                parse_mode='HTML')
    else:
        bot.send_message(chat_id,
                        "❌ Извините, произошла ошибка при генерации гороскопа. Попробуйте позже.",
                        reply_markup=get_main_menu_keyboard())

@bot.message_handler(func=lambda message: message.text == '📜 Знаки зодиака')
@logger.catch
def zodiacs_command(message: telebot.types.Message) -> None:
    """Список знаков зодиака с датами"""
    zodiacs_text = "<b>Знаки зодиака и их периоды:</b>\n\n"

    for sign_id, sign_data in ZODIAC_SIGNS.items():
        zodiacs_text += f"{sign_data['emoji']} <b>{sign_data['name']}</b>\n"
        zodiacs_text += f"   📅 {sign_data['dates']}\n"
        zodiacs_text += f"   🌌 {sign_data['element']} | 🪐 {sign_data['planet']}\n\n"

    bot.send_message(message.chat.id, zodiacs_text,
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode='HTML')

# ВАЖНО: Упрощенный обработчик для ввода имени - должен быть перед общим обработчиком
@bot.message_handler(func=lambda message:
                    user_data.get(message.chat.id, {}).get('mode') == 'name_meaning')
@logger.catch
def handle_name_input(message: telebot.types.Message) -> None:
    """Обработчик ввода имени"""
    chat_id = message.chat.id

    # Проверяем, что это не команда "Назад"
    if message.text == '🔙 Назад':
        back_command(message)
        return

    # Проверяем, что пользователь находится на шаге ввода имени
    if user_data.get(chat_id, {}).get('step') != 'input_name':
        return

    name = message.text.strip()

    # Проверяем валидность имени
    if not name or len(name) < 2:
        bot.send_message(chat_id, "❌ Пожалуйста, введите корректное имя (минимум 2 символа).",
                        reply_markup=get_name_input_keyboard())
        return

    if len(name) > 50:
        bot.send_message(chat_id, "❌ Имя слишком длинное. Пожалуйста, введите имя до 50 символов.",
                        reply_markup=get_name_input_keyboard())
        return

    # Отправляем сообщение о загрузке
    loading_msg = bot.send_message(chat_id, f"📛 <i>Анализирую имя '{name}'... Это займет несколько секунд.</i>",
                                   parse_mode='HTML')

    # Получаем значение имени
    result = horoscope_service.get_name_meaning(name)

    # Удаляем сообщение о загрузке
    bot.delete_message(chat_id, loading_msg.message_id)

    if result['success']:
        header = f"📛 <b>ЗНАЧЕНИЕ ИМЕНИ: {name.upper()}</b>\n\n"
        full_message = header + result['name_meaning']

        # Разделяем длинные сообщения
        message_parts = split_long_message(full_message)

        # Отправляем части сообщения
        for i, part in enumerate(message_parts):
            if i == len(message_parts) - 1:
                # Последняя часть с клавиатурой
                bot.send_message(chat_id, part,
                                 reply_markup=get_main_menu_keyboard(),
                                 parse_mode='HTML')
            else:
                # Промежуточные части без клавиатуры
                bot.send_message(chat_id, part,
                                 parse_mode='HTML')

        # Очищаем данные пользователя после успешного завершения
        if chat_id in user_data:
            del user_data[chat_id]
    else:
        bot.send_message(chat_id,
                         "❌ Извините, произошла ошибка при анализе имени. Попробуйте позже.",
                         reply_markup=get_main_menu_keyboard())

def send_help_message(chat_id):
    """Общая функция для отправки справки"""
    help_text = """
🤖 <b>AstroBot - Помощник по гороскопам</b>

<b>Доступные функции:</b>
🔮 <b>Получить гороскоп</b> - персонализированные ежедневные прогнозы с учетом пола
💑 <b>Проверить совместимость</b> - анализ отношений между двумя знаками с учетом гендерных особенностей
📜 <b>Знаки зодиака</b> - информация о всех знаках
📛 <b>Значение имени</b> - анализ происхождения и характеристик имени

<b>✨ Особенности:</b>
• Анализ открытых источников
• Учет гендерных особенностей в прогнозах
• Профессиональные астрологические анализы
• Персонализированные рекомендации
• Глубокий анализ имен

<b>Как пользоваться:</b>
1. Выбери нужную функцию
2. Для гороскопа и совместимости укажи пол
3. Для анализа имени - просто введи его
4. Получи детальный анализ!

<b>Команды:</b>
/start - Главное меню
/help - Эта справка
"""
    bot.send_message(chat_id, help_text,
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode='HTML')

@bot.message_handler(commands=['help'])
@logger.catch
def help_command(message: telebot.types.Message) -> None:
    """Обработчик команды /help"""
    send_help_message(message.chat.id)

@bot.message_handler(func=lambda message: message.text == 'ℹ️ Помощь')
@logger.catch
def help_button(message: telebot.types.Message) -> None:
    """Обработчик кнопки помощи"""
    send_help_message(message.chat.id)

@bot.message_handler(func=lambda message: message.text == '🔙 Назад')
@logger.catch
def back_command(message: telebot.types.Message) -> None:
    """Возврат в главное меню"""
    chat_id = message.chat.id
    if chat_id in user_data:
        del user_data[chat_id]

    bot.send_message(chat_id, "🔙 <b>Возвращаемся в главное меню</b>",
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode='HTML')

@bot.message_handler(func=lambda message: True)
@logger.catch
def handle_other_messages(message: telebot.types.Message) -> None:
    """Обработчик всех остальных сообщений"""
    chat_id = message.chat.id
    bot.send_message(chat_id,
                    "Я понимаю только команды и кнопки. Используй /start чтобы начать!",
                    reply_markup=get_main_menu_keyboard())

if __name__ == "__main__":
    print("Бот Astro_bot запущен с обновленной логикой и использованием GPT-5!")
    bot.infinity_polling()