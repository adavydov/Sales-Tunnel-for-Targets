from aiogram.fsm.state import State, StatesGroup


class OnboardingFlow(StatesGroup):
    company = State()
    website = State()


class ToolConsentFlow(StatesGroup):
    waiting = State()


class SimulateFlow(StatesGroup):
    mode_select = State()
    express_revenue = State()
    express_accountants = State()
    express_salary = State()
