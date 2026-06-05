import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
print("KEY =", os.getenv("GEMINI_API_KEY"))

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-flash-lite-latest")

def generate_json(system_prompt, user_prompt):
    response = model.generate_content(
        f"{system_prompt}\n\n{user_prompt}"
    )
    return response.text