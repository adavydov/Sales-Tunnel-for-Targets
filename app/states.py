from aiogram.fsm.state import State, StatesGroup


class BotFlow(StatesGroup):
    awaiting_question = State()


class LeadFlow(StatesGroup):
    role = State()
    business_size = State()
    timeframe = State()
    motivation = State()


class ContactFlow(StatesGroup):
    waiting_contact_start = State()
    waiting_consent = State()
    waiting_contact_type = State()
    waiting_contact_value = State()