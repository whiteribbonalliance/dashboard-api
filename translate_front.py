import json
import os
import shutil

from app import constants
from app.services.translations_cache import TranslationsCache
from app.services.translator import Translator

count_chars_only = False


def translate_front():
    """Apply translation on texts"""

    translations_cache = TranslationsCache()
    translations_cache.load()

    with open("front_translations/to_translate.json", "r", encoding="utf8") as file:
        texts: dict = json.loads(file.read())

    translator = Translator()

    # Translate text for every language
    for language in constants.TRANSLATION_LANGUAGES.keys():
        print(f"Translating texts to {language}...")

        translator.set_target_language(target_language=language)

        for text_id, text in texts.items():
            translator.extract_text(text)

        translator.translate_extracted_texts(count_chars_only=count_chars_only)

    if not count_chars_only:
        # Create languages dir
        languages_dir_path = "front_translations/languages"
        if not os.path.isdir(languages_dir_path):
            os.mkdir(languages_dir_path)
        else:
            shutil.rmtree(languages_dir_path)
            os.mkdir(languages_dir_path)

        # Save translations for each language
        latest_generated_keys_per_language = (
            translator.get_latest_generated_keys_per_language()
        )
        for language, keys in latest_generated_keys_per_language.items():
            language_dir_path = f"{languages_dir_path}/{language}"
            os.mkdir(language_dir_path)

            translations = {}
            for text_id, text in texts.items():
                key = f"{language}.{text}"
                if translations_cache.has(key):
                    translations[text_id] = translations_cache.get(key)

            with open(f"{language_dir_path}/translation.json", "w") as file:
                file.write(json.dumps(translations))

    # English
    if not count_chars_only:
        os.mkdir("front_translations/languages/en/")
        with open(f"front_translations/languages/en/translation.json", "w") as file:
            file.write(json.dumps(texts))

    # Print
    if count_chars_only:
        print(
            f"Total Characters count from texts that can be translated: {translator.get_translations_char_count()}"
        )
    else:
        print(
            f"Total Characters count from texts translated: {translator.get_translations_char_count()}"
        )


translate_front()
