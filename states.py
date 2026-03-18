from aiogram.dispatcher.filters.state import State, StatesGroup


class LoginState(StatesGroup):
    waiting_login = State()
    waiting_password = State()


class AdminProductState(StatesGroup):
    waiting_product_name = State()
    waiting_product_price = State()

    waiting_edit_product_name = State()
    waiting_edit_product_price = State()


class AdminAgentState(StatesGroup):
    waiting_agent_full_name = State()
    waiting_agent_login = State()
    waiting_agent_password = State()


class AdminStockState(StatesGroup):
    waiting_stock_qty = State()


class AgentSaleState(StatesGroup):
    waiting_shop_name = State()
    waiting_sale_qty = State()
    waiting_location = State()