from app.handlers.max.state import get_state, set_state, clear_state, update_data, get_data

class Context:

    def __init__(self, session, chat_type, chat_id, user_id, user_name, text, send):
        self.session = session
        self.chat_type = chat_type
        self.chat_id = chat_id
        self.user_id = user_id
        self.user_name = user_name
        self.text = text
        self.send = send


    # ===== FSM-like интерфейс =====
    @property
    def state(self):
        return get_state(self.user_id)

    def set_state(self, state):
        set_state(self.user_id, state)

    def clear_state(self):
        clear_state(self.user_id)

    def update_data(self, **kwargs):
        update_data(self.user_id, **kwargs)

    def get_data(self):
        return get_data(self.user_id)