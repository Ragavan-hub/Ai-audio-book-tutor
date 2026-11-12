from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    gemini_api_key:str=""
    gemini_model:str="gemini-3.8-flash"
    ai_provider:str="gemini"
    ollama_base_url:str="http://localhost:11434"
    ollama_model:str="llama3.1"
    frontend_origin: str = "https://ai-audio-book-tutor.vercel.app"
    data_dir:str="./data"
    max_upload_mb:int=30
    model_config=SettingsConfigDict(env_file=".env",extra="ignore",case_sensitive=False)
settings=Settings()
