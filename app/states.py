from aiogram.fsm.state import State, StatesGroup


class OnboardingFlow(StatesGroup):
    company = State()
    website = State()


class ToolConsentFlow(StatesGroup):
    waiting = State()
