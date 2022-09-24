
def is_time_allowed(time: str) -> bool:
    pattern = set(":0123456789")
    if set(time).difference(pattern):  # Если в строке есть что-то, помимо паттерна, вернется False
        return False
    try:
        hours, minutes = map(int, time.split(":"))
        if ((len(time) == 5 and 0 <= hours <= 23) or (len(time) == 4 and 0 <= hours <= 9)) and 0 <= minutes <= 59:
            return True
        else:
            return False
    except Exception:
        return False


def is_string_allowed(text: str) -> bool:
    pattern = set("0123456789")
    alp_en = "abcdefghijklmnopqrstuvwxyz"
    alp_ru = "абвгдеёзжийклмнопрстуфхцчшщъыьэюя"

    alp_en_set = set(alp_en)
    alp_en_up = set(alp_en.upper())
    alp_ru_set = set(alp_ru)
    alp_ru_up = set(alp_ru.upper())
    symbols = set(""""
    '/|\?!.,:()+=_-*&^%$#@; "<>«»„“
    """)
    pattern.update(alp_en_set, alp_en_up, alp_ru_set, alp_ru_up, symbols)
    # Если в строке есть что-то, помимо паттерна, вернется False
    return False if set(text).difference(pattern) else True


if __name__ == '__main__':

    def test_is_time_allowed():
        assert is_time_allowed("00:00")
        assert is_time_allowed("00:58")
        assert is_time_allowed("00:59")
        assert is_time_allowed("0:00")
        assert is_time_allowed("5:00")
        assert is_time_allowed("05:00")
        assert is_time_allowed("23:00")
        assert not is_time_allowed("00:60")
        assert not is_time_allowed("00:223")
        assert not is_time_allowed("00.00")
        assert not is_time_allowed("24:00")
        assert not is_time_allowed("111:00")

    def test_is_string_allowed():
        assert is_string_allowed("|\/dыDЫ30.?,")
        assert not is_string_allowed(">")

    test_is_time_allowed()
    test_is_string_allowed()
