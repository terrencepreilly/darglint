import random
import string


def random_string(min_length: int = 1,
                  max_length: int = 20
                  ) -> str:
    ret = ''
    for i in range(random.randint(min_length, max_length)):
        ret += random.choice(string.ascii_letters)
    return ret
