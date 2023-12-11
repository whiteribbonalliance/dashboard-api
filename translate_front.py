"""
MIT License

Copyright (c) 2023 White Ribbon Alliance. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import json
import os
import shutil

from app import helpers
from app.services.translations_cache import TranslationsCache
from app.services.translator import Translator
from app.types import CloudService

count_chars_only = False


def translate_front(cloud_service: CloudService):
    """Apply translation on texts"""

    if cloud_service == "google":
        name = "Google"
    elif cloud_service == "azure":
        name = "Azure"
    else:
        name = ""

    translations_cache = TranslationsCache()
    translations_cache.load()

    with open("front_translations/to_translate.json", "r", encoding="utf8") as file:
        texts: dict = json.loads(file.read())

    # Translate text for every language
    translator = Translator(cloud_service=cloud_service)
    for language in helpers.get_translation_languages(
        cloud_service=cloud_service
    ).keys():
        print(f"{name} - Translating texts to {language}...")

        translator.change_target_language(target_language=language)

        for text_id, text in texts.items():
            translator.extract_text(text=text, add_key_to_latest_generated_keys=True)

        translator.translate_extracted_texts(
            count_chars_only=count_chars_only, add_key_to_latest_generated_keys=True
        )

    if not count_chars_only:
        # Create languages dir
        languages_dir_path = "front_translations/languages"
        if not os.path.isdir(languages_dir_path):
            os.mkdir(languages_dir_path)
        else:
            shutil.rmtree(languages_dir_path)
            os.mkdir(languages_dir_path)

        # Save translations for each language
        latest_generated_keys = translator.get_latest_generated_keys()
        for language, keys in latest_generated_keys.items():
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


translate_front(cloud_service="google")

# Values already translated by Google will not be translated again
# Azure has languages that Google does not
translate_front(cloud_service="azure")
