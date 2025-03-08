from setuptools import setup, find_packages

setup(
    name="captain_tractors_chatbot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flask>=3.0.2",
        "groq>=0.18.0",
        "pinecone-client>=3.0.1",
        "pydantic>=2.5.3",
        "rich>=13.7.0",
        "markdown2>=2.4.12",
        "cachetools>=5.3.2",
        "tenacity>=8.2.3",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.5",
            "pytest-cov>=4.1.0",
            "black>=24.1.1",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
            "pre-commit>=3.6.0",
            "httpx>=0.26.0",
        ],
        "azure": [
            "azure-cognitiveservices-translation-text>=0.9.0",
        ],
    },
    python_requires=">=3.8",
)
