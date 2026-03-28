from aiogram.fsm.state import State, StatesGroup


class BotFlow(StatesGroup):
    awaiting_question = State()


class OnboardingFlow(StatesGroup):
    company = State()
    wants_extra = State()
    contact_name = State()
    contact_phone = State()
    contact_email = State()
    contact_position = State()
    contact_position_custom = State()
    waiting_consent = State()


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