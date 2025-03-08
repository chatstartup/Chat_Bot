from config.settings import get_settings

settings = get_settings()

# Make these variables available for backward compatibility
GROQ_API_KEY = settings.GROQ_API_KEY
GROQ_MODEL = settings.GROQ_MODEL