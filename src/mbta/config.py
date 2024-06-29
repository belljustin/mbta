import os

class Config:
    apikey: str

    def __init__(self) -> None:
        self.apikey = os.getenv("MBTA_APIKEY", default=None)
    
    def validate(self):
        if self.apikey is None:
            raise ValueError("apikey configuration is not set. Set with environment variable MBTA_APIKEY. Get a free key from the MBTA website https://api-v3.mbta.com/.")

config = Config()
config.validate()