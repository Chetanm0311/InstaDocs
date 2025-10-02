import base64
import os
from openai import OpenAI

from io import BytesIO
import json
import base64
# from dotenv import load_dotenv
class Gemini:
    def __init__(self):
        # load_dotenv(override=True)  
        self.api_key = os.getenv('GOOGLE_API_KEY',"")
        self.client = OpenAI(
            api_key=self.api_key ,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        self.model="gemini-2.5-flash"

    def chat(self, messages, tools=[]):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            # tools=tools,
            # tool_choice="auto",
            response_format={"type": "json_object"}
        )
        result = response.choices[0].message.content
        return json.loads(result)
    
# g = Gemini()
# print(g.chat([{"role": "system", "content": "You are a helpful assistant."},{"role": "user", "content": "Write a short poem about the sea."}]))
