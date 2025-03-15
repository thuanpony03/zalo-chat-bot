import google.generativeai as genai
import os
genai.configure(api_key="AIzaSyCJUjn3E8bXcaA1w4FO9Rh_D1lANdhPnFY")
for model in genai.list_models():
    print(model.name)