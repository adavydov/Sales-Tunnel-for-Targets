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
    precise_revenue = State()
    precise_accountants = State()
    precise_salary = State()
    precise_clients = State()
    precise_margin = State()
    precise_ops_share = State()
    precise_complex_cases = State()
    precise_standardization = State()
    precise_automation = State()
    precise_advisory = State()
    precise_wait_excel = State()


class MeetingBookingFlow(StatesGroup):
    waiting_email = State()
    waiting_date = State()
    waiting_custom_time = State()
