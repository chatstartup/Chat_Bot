from krutrim_translator import Translator

class KrutrimTranslator:
    def __init__(self, src_lang="en", tgt_lang="hi"):
        """
        Initialize the translator with source and target languages.
        
        Args:
            src_lang (str): Source language code (default: "en" for English).
            tgt_lang (str): Target language code (default: "hi" for Hindi).
        """
        self.translator = Translator(src_lang=src_lang, tgt_lang=tgt_lang)

    def translate(self, text):
        """
        Translate text to the target language.
        
        Args:
            text (str): Text to translate.
        
        Returns:
            str: Translated text or original text if translation fails.
        """
        try:
            return self.translator.translate(text)
        except Exception as e:
            print(f"Translation error: {e}")
            return text  # Return original text if translation fails

# Example usage
if __name__ == "__main__":
    translator = KrutrimTranslator(tgt_lang="hi")  # Translate to Hindi
    translated_text = translator.translate("Hello, how are you?")
    print(translated_text)
