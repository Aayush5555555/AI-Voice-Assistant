# Import necessary libraries
import os  # For interacting with the operating system
from googlesearch import search  # For searching the internet
from groq import Groq  # For using the Groq API
from json import load, dump  # For loading and dumping JSON data
import datetime  # For getting the current date and time
from dotenv import dotenv_values  # For loading environment variables from a .env file
import speech_recognition as sr  # For speech recognition
import pyttsx3  # For text-to-speech

# Load environment variables from the .env file
env_vars = dotenv_values(".env")  # Load environment variables from the .env file
Username = env_vars.get("username")  # Get the username from the environment variables
Assistantname = env_vars.get("Assistantname")  # Get the assistant name from the environment variables
GroqAPIkey = env_vars.get("GroqAPIkey")  # Get the Groq API key from the environment variables

# Initialize the Groq client
client = Groq(api_key=GroqAPIkey)  # Initialize the Groq client with the API key

# Initialize recognizer and text-to-speech engine
recognizer = sr.Recognizer()  # Initialize the speech recognizer
tts_engine = pyttsx3.init()  # Initialize the text-to-speech engine

# Chatbot system prompt
System = (  # Define the chatbot system prompt
    f"Hello, I am {Username}. You are a very accurate and advanced AI Assistant named {Assistantname} "  # Greet the user and introduce the assistant
    "which has real-time up-to-date information from the internet.\n"  # Explain the assistant's capabilities
    "*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar.***\n"  # Provide instructions for the assistant's responses
    "*** Just answer the question from the provided data in a professional way. *** "  # Provide instructions for the assistant's responses
    f"I was built by {Username}."  # Provide information about the assistant's creator
)

# Predefined system messages
SystemChatBot = [  # Define a list of predefined system messages
    {"role": "system", "content": System},  # Add the chatbot system prompt to the list
    {"role": "system", "content": f"Hello, I am {Username}. You are a very accurate and advanced AI chatbot named {Assistantname} which also has real-time up-to-date information from the internet.\n*** Do not tell time until I ask, do not talk too much, just answer the question.***\n*** Reply in only English, even if the question is in Hindi.***\n*** Do not provide notes in the output, just answer the question and never mention your training data. ***"}  # Add another predefined system message
]

# Try to load existing chat log
try:  # Try to load the existing chat log
    with open(r"Data\ChatLog.json", "r") as f:  # Open the chat log file in read mode
        messages = load(f)  # Load the chat log data
except FileNotFoundError:  # If the file does not exist
    with open(r"Data\ChatLog.json", "w") as f:  # Open the chat log file in write mode
        dump([], f)  # Create an empty chat log
    messages = []  # Initialize an empty list for the chat log

# Google search function
def GoogleSearch(query):  # Define a function for searching the internet
    results = list(search(query, advanced=True, num_results=5, lang="hi-IN", safe="active"))  # Search the internet using the Google search API
    answer = f"The Search results for '{query}' are :\n[start]\n"  # Initialize the answer string
    for i in results:  # Loop through the search results
        answer += f"Title: {i.title}\nDescription: {i.description}\n\n"  # Add the title and description of each result to the answer string
    answer += "[end]"  # Add the end of the search results to the answer string
    return answer  # Return the answer string

# Removes extra blank lines
def AnswerModifier(Answer):  # Define a function for modifying the answer
    lines = Answer.split('\n')  # Split the answer into lines
    non_empty_lines = [line for line in lines if line.strip()]  # Remove empty lines
    modified_answer = '\n'.join(non_empty_lines)  # Join the non-empty lines back into a string
    return modified_answer  # Return the modified answer

# Add real-time date and time info
def Information():  # Define a function for getting 
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")
    data = (
        f"Please use this real-life information if needed,\n"
        f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
        f"Time: {hour} hours :{minute} minutes :{second} seconds.\n"
    )
    return data
    
# Core logic that handles user input, fetches data, and gets response from LLM
def RealtimeSearchEngine(query):
    global SystemChatBot, messages

    # Reload chat history from file
    try:
        with open(r"Data\ChatLog.json", "r") as f:
            messages = load(f)
    except FileNotFoundError:
        messages = []

    messages.append({"role": "user", "content": f"{query}"})  # Add user message to history

    # Perform Google search and inject result into system messages
    search_result = GoogleSearch(query)
    SystemChatBot.append({"role": "system", "content": search_result})

    # Inject real-world date/time info
    info = Information()

    # Call the Groq API with all contextual messages
    compilation = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=SystemChatBot + [{"role": "system", "content": info}] + messages,
        max_tokens=1024,
        temperature=0.7,
        top_p=1,
        stream=True,
        stop=None,
    )

    # Construct the answer as it streams from the API
    Answer = ""
    for chunk in compilation:
        if hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content:
            Answer += chunk.choices[0].delta.content

    Answer = Answer.strip().replace("</s", "")  # Clean the response
    messages.append({"role": "assistant", "content": Answer})  # Add to chat log

    # Save the updated chat log
    with open(r"Data\ChatLog.json", "w") as f:
        dump(messages, f, indent=4)

    # Remove the last Google result from system context (avoid stacking results)
    SystemChatBot.pop()

    return AnswerModifier(Answer=Answer)

# Function to convert text to speech and also print the assistant's response
def speak(text):
    print(f"\033[94mAssistant: {text}\033[0m")  # Print in blue
    tts_engine.say(text)  # Use TTS to say the text
    tts_engine.runAndWait()  # Wait until speech is done

# Function to capture voice input and convert it to text
def listen():
    with sr.Microphone() as source:
        print("\033[93mListening...\033[0m")  # Print in yellow
        recognizer.adjust_for_ambient_noise(source)  # Adjust for background noise
        audio = recognizer.listen(source)  # Listen to user input

        try:
            query = recognizer.recognize_google(audio)  # Convert speech to text
            print(f"\033[92mYou said: {query}\033[0m")  # Print in green
            return query
        except sr.UnknownValueError:
            print("Sorry, I could not understand your what you said,say again!")
            return ""
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return ""

# Main loop for voice assistant
# Listens continuously and responds unless the user says stop

def speech_loop():
    while True:
        spoken_query = listen()  # Get user's spoken input
        if spoken_query.lower() in ["exit", "quit", "stop"]:
            speak("Goodbye! sir ,have a nice day,")
            break  # Exit loop if user wants to stop
        if spoken_query.strip() == "":
            continue  # Skip empty input
        response = RealtimeSearchEngine(spoken_query)  # Generate AI response
        speak(response)  # Speak the response

# Entry point of the script
if __name__ == "__main__":
    speech_loop()  # Start the assistant
