ALPHABET = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'


def encode_base62(number):
    if number == 0:
        return '0'

    result = ''
    base = len(ALPHABET)
    while number > 0:
        number, remainder = divmod(number, base)
        result = ALPHABET[remainder] + result

    return result


def decode_base62(value):
    number = 0
    base = len(ALPHABET)

    for char in value:
        number = number * base + ALPHABET.index(char)

    return number
