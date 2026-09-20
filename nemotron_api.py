import os # access environment variables for API keys.

from openai import OpenAI  # imports the OpenAI client used for Nvidia's API.
from dotenv import load_dotenv  # loads values from a local .env file.

load_dotenv()  # loads local environment variables before using them.


api_key = os.getenv("nemoapikey")  # reads the Nemotron API key from the environment.

client = OpenAI(  # creates the configured client for Nvidia's endpoint.
    base_url="https://integrate.api.nvidia.com/v1",  # sets the Nvidia API base URL.
    api_key=api_key,  # sends the API key with each request.
)

mdl = "nvidia/nemotron-3-super-120b-a12b"  # picks the model used for plant-related answers.


def getplant_info(plant_name):  # builds a detailed plant summary for a given plant name.
    prompt = f"""
    Provide a detailed description of the plant '{plant_name}'.

    Include:
    - Common name
    - Scientific name
    - Plant family
    - Native region
    - Plant type
    - Light requirements
    - Water requirements
    - Soil
    - Temperature
    - Humidity
    - Nutrient needs
    - Typical size
    - Growth pattern
    - Propagation
    - Toxicity to humans or pets
    - Common pests
    - Common problems
    - Interesting facts
    """  

    response = client.chat.completions.create(  # sends the prompt to the model.
        model=mdl,  # uses the selected Nemotron model.
        messages=[  # adds both system and user instructions.
            {
                "role": "system", # defines the assistant's behavior and context for plant information.
                "content": "You are a helpful assistant that provides detailed information about plants."  # Define the assistant's behavior.
            },
            {
                "role": "user", # provides the plant name and request a detailed description.
                "content": prompt  # passes the plant request into the model.
            },
        ],
        
        temperature=0.2,  # keeps answers focused and not too random.
        max_tokens = 1500, # limits the length of the response to avoid overly long outputs.
    )

    return response.choices[0].message.content  # returns the model-generated plant summary.




def askplant_question(plant_name, question):  # answers a specific question for a given plant.
    response = client.chat.completions.create( 
        model=mdl, 
        messages=[  # adds context and the actual user question.
            {
                "role": "system",
                "content": (
                    f"You are Photosynize, a plant education assistant. "  
                    f"The plant currently being discussed is {plant_name}. "  
                    f"Answer questions specifically in the context of this plant. "  
                    f"If something cannot be determined reliably, say so."  
                )
            },
            {
                "role": "user",
                "content": question  
            }
        ],
        temperature=0.4,
        max_tokens = 800,  
    )

    return response.choices[0].message.content  

