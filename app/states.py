from aiogram.fsm.state import State, StatesGroup


class LeadFlow(StatesGroup):
    choosing_track = State()
    role = State()
    business_size = State()
    timeframe = State()
    motivation = State()