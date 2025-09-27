import os

try:
    from api.config import env
except ModuleNotFoundError:
    from config import env

from openai import OpenAI
from googletrans import Translator as GoogleTranslator


class Translator:
    def __init__(self, strategy='openai', **kwargs):
        """
        Initializes the main Translator class.
        
        Args:
            strategy (str): The translation strategy to use.
                            Options: 'openai', 'google'.
            **kwargs: Additional arguments for the chosen strategy's constructor.
        """
        if strategy == 'openai':
            self._translator_strategy = OpenAITranslator(**kwargs)
        elif strategy == 'google':
            self._translator_strategy = GoogleTranslatorStrategy()
        else:
            raise ValueError(f"Unknown translation strategy: {strategy}")

    def translate(self, text, from_lang, to_lang):
        """
        Translates text using the selected strategy.

        Args:
            text (str): The text to translate.
            from_lang (str): The source language code (e.g., 'sv' for Swedish).
            to_lang (str): The target language code (e.g., 'en' for English).

        Returns:
            str: The translated text or an error message.
        """
        return self._translator_strategy.translate(text, from_lang, to_lang)
    
class BaseTranslatorStrategy:
    """
    Base class for all translation strategies.
    All subclasses must implement the 'translate' method.
    """
    def translate(self, text, from_lang, to_lang):
        raise NotImplementedError("Subclasses must implement the translate method.")
    

class GoogleTranslatorStrategy(BaseTranslatorStrategy):
    """
    A translation strategy using the free googletrans library.
    """
    def __init__(self):
        self.translator = GoogleTranslator()

    def translate(self, text, from_lang, to_lang):
        try:
            translation = self.translator.translate(text, src=from_lang, dest=to_lang)
            return translation.text
        except Exception as e:
            return f"An error occurred with googletrans: {e}"
        
        


class OpenAITranslator(BaseTranslatorStrategy):
    """
    A translation strategy using the OpenAI API.
    """
    def __init__(self, api_key=None):
        if api_key is None:
            api_key = env.OPENAI_KEY
            if not api_key:
                raise ValueError("API key not provided and OPENAI_API_KEY environment variable is not set.")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini" # or another model

    def translate(self, text, from_lang, to_lang):
        mappings = {
                "sv" : "Swedish",
                "en" : "English"
        }
        from_lang = mappings.get(from_lang)
        to_lang = mappings.get(to_lang)
        prompt_messages = [
            {"role": "system", "content": f"You are a professional translator. Translate the following text from {from_lang} to {to_lang}."},
            {"role": "user", "content": f"Translate this: '{text}'"}
        ]
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=prompt_messages,
                temperature=0.2,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"An error occurred with OpenAI: {e}"
