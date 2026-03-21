from aiogram.fsm.state import State, StatesGroup


class BotFlow(StatesGroup):
    awaiting_question = State()


class LeadFlow(StatesGroup):
    role = State()
    business_size = State()
    timeframe = State()
    motivation = State()