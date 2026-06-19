import hashlib
import math
import re


EMBEDDING_DIMENSION = 384


def generate_embedding(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSION

    words = re.findall(r"\w+", text.lower())

    if not words:
        return vector

    for word in words:
        digest = hashlib.md5(word.encode("utf-8")).hexdigest()

        index = int(digest[:8], 16) % EMBEDDING_DIMENSION
        sign = 1 if int(digest[8:10], 16) % 2 == 0 else -1

        vector[index] += sign

    norm = math.sqrt(sum(value * value for value in vector))

    if norm == 0:
        return vector

    return [value / norm for value in vector]