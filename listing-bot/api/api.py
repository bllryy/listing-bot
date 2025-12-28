from quart import Quart
from quart_cors import cors
import os

def create_api():

    class App(Quart):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.bot = None

    app = App(__name__)
    app = cors(app, allow_origin="*")

    METHODS = ["GET", "POST"]

    for METHOD in METHODS:
        for file in os.listdir(f"api/{METHOD}"):
            if file.endswith(".py"):
                
                route = __import__(f"api.{METHOD}.{file[:-3]}", fromlist=["route", "func"])
                endpoint = f"{METHOD}_{file[:-3]}"

                app.add_url_rule(route.route, endpoint, route.func, methods=[METHOD])
                print(f"Added route {route.route} with method {METHOD}.")
    
    return app