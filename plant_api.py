import os 
import requests  # Make HTTP requests

from dotenv import load_dotenv  # Load variables from .env

load_dotenv()  
api_key = os.getenv("plantapikey")  


def identify_plant(uploaded_image):
    """Send an image to PlantNet and return the JSON identification result."""
    url = "https://my-api.plantnet.org/v2/identify/all"  # PlantNet identification endpoint

    params = {  # parameters included in the reques to PlantNet API
        "api-key": api_key,
        "nb-results": 3,
        "lang": "en",
    }

    files = {
        "images": (
            uploaded_image.name,
            uploaded_image.getvalue(),
            uploaded_image.type,
        )
    }

    

    response = requests.post(url, params=params, files=files)  # sends the image to PlantNet.
    response.raise_for_status()  # stops if the API request fails.

    print("STATUS CODE:", response.status_code) #Had the Agent implemented a print statement to log the status code of the response for debugging purposes.
    print("RESPONSE:", response.text)                     

    return response.json()  # returns the plant identification result.

