user_states = {}
user_data = {}


def set_state(user_id, state):
    user_states[user_id] = state


def get_state(user_id):
    return user_states.get(user_id)


def clear_state(user_id):
    user_states.pop(user_id, None)
    user_data.pop(user_id, None)


def update_data(user_id, **kwargs):
    data = user_data.setdefault(user_id, {})
    data.update(kwargs)


def get_data(user_id):
    return user_data.get(user_id, {})