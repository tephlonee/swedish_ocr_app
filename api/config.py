from pydantic_settings import BaseSettings


class Environment(BaseSettings):
    
    OPENAI_KEY : str
    
    
env = Environment()