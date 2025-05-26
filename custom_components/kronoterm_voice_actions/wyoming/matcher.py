import re
import difflib
from difflib import SequenceMatcher

number_words = {
    "eno": 1,
    "ena": 1,
    "dva": 2,
    "dve": 2,
    "tri": 3,
    "štiri": 4,
    "pet": 5,
    "šest": 6,
    "sedem": 7,
    "osem": 8,
    "devet": 9,
    "deset": 10,
    "enajst": 11,
    "dvanajst": 12,
    "trinajst": 13,
    "štirinajst": 14,
    "petnajst": 15,
    "šestnajst": 16,
    "sedemnajst": 17,
    "osemnajst": 18,
    "devetnajst": 19
}

compound_number_words = {
    "dvajset": 20,
    "trideset": 30,
    "štirideset": 40,
    "petdeset": 50,
    "šestdeset": 60,
    "sedemdeset": 70,
    "osemdeset": 80,
    "devetdeset": 90,
}

floating_point_words = {
    "celih",
    "cela",
}

digit_to_text = {
    "1": "ena",
    "1.0": "ena",
    "2": "dva",
    "2.0": "dva",
    "3": "tri",
    "3.0": "tri",
    "4": "štiri",
    "4.0": "štiri",
}


def find_last_number(text: str) -> str | None:
    matches = re.findall(r'\d+(?:\.\d+)?', text)
    if not matches:
        return None

    last = matches[-1]
    return last


def get_float(word: str) -> float | None:
    """
    Extracts a floating point number from the word.
    Returns None if no valid number is found.
    """
    try:
        return float(word)
    except ValueError:
        try:
            return float(word.replace(",", "."))
        except ValueError:
            return None


def is_float(word: str) -> bool:
    try:
        float(word)
        return True
    except ValueError:
        try:
            float(word.replace(",", "."))
        except ValueError:
            return False


def includes_temperature(text: str, ensured_similarity: float = 0.65) -> bool:
    """
    Checks if the text includes a temperature command.
    """
    if "°C" in text:
        return True

    words = text.lower().split()
    last_word = words[-1]
    match = get_similarity(last_word, "stopinj")
    return match >= ensured_similarity


def get_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def insert_dots_for_floats(words: list[str]) -> list[str]:
    for i in range(len(words)):
        word = words[i]
        match = difflib.get_close_matches(word, floating_point_words, n=1, cutoff=0.79)
        if match:
            words[i] = "."

    return words


def merge_floats(words: list[str]) -> list[str]:
    new_words = []
    i = 0
    while i < len(words):
        if i + 2 < len(words) and is_float(words[i]) and (words[i + 1] == "." or words[i + 1] == ",") and is_float(words[i + 2]):
            merged = f"{int(get_float(words[i]))}.{int(get_float(words[i + 2]))}"
            new_words.append(merged)
            i += 3
        else:
            new_words.append(words[i])
            i += 1

    return new_words


def merge_numbers(words: list[str]) -> list[str]:
    new_words = []
    i = 0
    while i < len(words):
        if i + 2 < len(words) and is_float(words[i]) and words[i + 1] == "in" and is_float(words[i + 2]):
            merged = str(get_float(words[i]) + get_float(words[i + 2]))
            new_words.append(merged)
            i += 3
        else:
            new_words.append(words[i])
            i += 1

    return new_words


def slovenian_word_to_number_strict(word) -> str | None:
    """Converts a Slovenian number word to its digit equivalent"""

    if get_float(word) is not None:
        return str(get_float(word))

    if word.isdigit():
        return str(get_float(word))

    word = word.translate(str.maketrans('', '', "!?"))
    if get_float(word) is not None:
        return str(get_float(word))

    if word.isdigit():
        return str(get_float(word))

    word = word.translate(str.maketrans('', '', ",."))
    if word.isdigit():
        return str(get_float(word))

    if word == "nič":
        return "0.0"

    if word in number_words.keys():
        return str(float(number_words[word]))
    if word in compound_number_words.keys():
        return str(float(compound_number_words[word]))

    for tens_word, tens_val in compound_number_words.items():
        if word.endswith(tens_word):
            prefix = word[: -(len("in" + tens_word))]
            if prefix in number_words:
                return str(float(number_words[prefix] + tens_val))

    return None


def slovenian_word_to_number(word) -> str | None:
    """Converts a Slovenian number word to its digit equivalent, allowing for slight typos."""

    word = word.translate(str.maketrans('', '', ",.!?"))
    if len(word) < 3:
        return None

    direct_similarity = 0.86
    match = difflib.get_close_matches(word, number_words.keys(), n=1, cutoff=direct_similarity)
    if match:
        return str(float(number_words[match[0]]))

    match = difflib.get_close_matches(word, compound_number_words.keys(), n=1, cutoff=direct_similarity)
    if match:
        return str(float(compound_number_words[match[0]]))

    compound_similarity = 0.7
    best_suff = (0.0, None, None)
    for tens_word in compound_number_words.keys():
        L = len(tens_word)
        for suffix_len in range(max(1, L - 2), L + 3):
            suffix = word[-suffix_len:]
            sim = get_similarity(suffix, tens_word)
            if sim >= compound_similarity and sim > best_suff[0]:
                best_suff = (sim, tens_word, suffix)

    sim, tens_word, suffix = best_suff
    if sim == 0:
        return None

    remainder = word[:-len(suffix)]
    best_pref = (0.0, None, None)
    for number_word in number_words.keys():
        L = len(number_word)
        for prefix_len in range(max(3, L - 2), L + 3):
            prefix = remainder[:prefix_len]
            sim = get_similarity(prefix, number_word)
            if sim >= compound_similarity and sim > best_pref[0]:
                best_pref = (sim, number_word, prefix)

    sim, number_word, prefix = best_pref
    if sim == 0:
        return None

    return str(float(number_words[number_word] + compound_number_words[tens_word]))


def replace_numbers_with_digits(text: str) -> str:
    """Replaces Slovenian number words in the text with their digit equivalents"""
    words = text.lower().split()
    new_words = []
    for word in words:
        number = slovenian_word_to_number_strict(word)
        if number is None:
            new_words.append(word)
        else:
            new_words.append(number)

    words = []
    for word in new_words:
        number = slovenian_word_to_number(word)
        if number is None:
            words.append(word)
        else:
            words.append(number)

    words = merge_numbers(words)
    words = insert_dots_for_floats(words)
    words = merge_floats(words)
    return ' '.join(words)


def insert_numbers_back(text: str) -> str:
    words = text.split()
    for i in range(len(words)):
        word = words[i]
        if word in digit_to_text.keys():
            words[i] = digit_to_text[word]

    return ' '.join(words)

def sanitize_text(text: str) -> str:
    text = text.replace("°C", "")
    if text.endswith("."):
        text = text[:-1]

    return text

def match_command(text: str, commands: list[str]) -> tuple[str, float | None]:
    temperature = None
    if includes_temperature(text):
        text = sanitize_text(text)
        text = replace_numbers_with_digits(text)
        temperature = find_last_number(text)
        if temperature is None:
            raise ValueError

        text = text.replace(temperature, "<temperature>")

    text = insert_numbers_back(text)
    print(f"Processed text: {text}")
    match = difflib.get_close_matches(text, commands, n=1, cutoff=0.65)
    if not match:
        raise ValueError

    match = match
    if temperature is None:
        return match[0], None

    return match[0], float(temperature)