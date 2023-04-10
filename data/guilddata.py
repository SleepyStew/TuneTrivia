guild_data = {}


def set_data(id, key, value):
    try:
        guild_data[id][key] = value
    except KeyError:
        guild_data[id] = {}
        guild_data[id][key] = value


def get_data(id, key):
    try:
        return guild_data[id][key]
    except KeyError:
        return None
