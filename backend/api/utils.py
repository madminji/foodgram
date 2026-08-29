ALPHABET = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'


def encode_base62(number):
    if number == 0:
        return '0'

    result = ''

    while number > 0:
        number, remainder = divmod(number, 62)
        result = ALPHABET[remainder] + result

    return result


def decode_base62(value):
    number = 0

    for char in value:
        number = number * 62 + ALPHABET.index(char)

    return number
