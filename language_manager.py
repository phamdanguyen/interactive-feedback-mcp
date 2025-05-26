# Language Manager for Interactive Feedback MCP
# Handles loading and managing language configurations

import os
import json
import glob
from typing import Dict, Optional


class LanguageManager:
    """Class for managing multiple language configurations"""

    def __init__(self, default_language: str = "en"):
        self.current_language = default_language
        self.languages: Dict[str, Dict[str, str]] = {}
        self.available_languages: list[str] = []
        self._load_languages()

    def _load_languages(self):
        """Scan and load all available language configuration files"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        languages_dir = os.path.join(script_dir, "languages")

        if not os.path.exists(languages_dir):
            print(f"Warning: Languages directory {languages_dir} not found")
            return

        # Get language files
        json_files = glob.glob(os.path.join(languages_dir, "*.json"))

        for lang_file in json_files:
            # Get the language code from the file name
            lang_code = os.path.splitext(os.path.basename(lang_file))[0]

            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    lang_data = json.load(f)

                # Verify that the language file contains the necessary fields
                if 'name' not in lang_data:
                    print(f"Warning: Language file {lang_file} missing 'name' field")
                    continue

                self.languages[lang_code] = lang_data
                self.available_languages.append(lang_code)

            except FileNotFoundError:
                print(f"Warning: Language file {lang_file} not found")
            except json.JSONDecodeError as e:
                print(f"Warning: Error parsing language file {lang_file}: {e}")

        # Ensure there is a default language
        if self.current_language not in self.available_languages and self.available_languages:
            self.current_language = self.available_languages[0]
        elif not self.available_languages:
            print("Warning: No valid language files found")

    def set_language(self, language_code: str) -> bool:
        """Set the current language"""
        if language_code in self.languages:
            self.current_language = language_code
            return True
        return False

    def get_text(self, key: str, **kwargs) -> str:
        """Get the text for a given key, supporting formatting arguments"""
        if self.current_language not in self.languages:
            # If the current language is not available, fallback to English
            self.current_language = "en"

        text = self.languages.get(self.current_language, {}).get(key, key)

        # If the key is not found in the current language, try to get it from English
        if text == key and self.current_language != "en":
            text = self.languages.get("en", {}).get(key, key)

        # Apply formatting arguments
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                # If formatting fails, return the original text
                pass

        return text

    def get_current_language(self) -> str:
        """Get the current language code"""
        return self.current_language

    def get_available_languages(self) -> Dict[str, str]:
        """Retrieve the list of available languages and return the mapping between language codes and display names"""
        result = {}
        for lang_code in self.available_languages:
            if lang_code in self.languages and 'name' in self.languages[lang_code]:
                result[lang_code] = self.languages[lang_code]['name']
            else:
                result[lang_code] = lang_code
        return result

    def get_all_default_prompts(self) -> list[str]:
        """Get all default prompt variants for all languages"""
        default_prompts = []
        for lang_code in self.available_languages:
            if lang_code in self.languages and 'default_prompt' in self.languages[lang_code]:
                prompt = self.languages[lang_code]['default_prompt']
                if prompt not in default_prompts:
                    default_prompts.append(prompt)
        return default_prompts


_language_manager = None

def get_language_manager() -> LanguageManager:
    """Get a global language manager instance"""
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager()
    return _language_manager


def set_global_language(language_code: str) -> bool:
    """Set global language"""
    return get_language_manager().set_language(language_code)


def get_text(key: str, **kwargs) -> str:
    """Convenient function for obtaining text"""
    return get_language_manager().get_text(key, **kwargs)
