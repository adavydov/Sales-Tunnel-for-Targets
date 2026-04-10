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
    precise_clients = State()
    precise_contacts = State()
    precise_contact_name = State()
    precise_contact_email = State()
    precise_contact_phone = State()
    precise_contact_company = State()
    precise_margin = State()
    precise_standardization = State()
    precise_automation = State()
    precise_advisory = State()
    precise_growth = State()
    precise_mna = State()
    precise_wait_excel = State()


class MeetingBookingFlow(StatesGroup):
    waiting_email = State()
    waiting_date = State()
    waiting_custom_time = State()
