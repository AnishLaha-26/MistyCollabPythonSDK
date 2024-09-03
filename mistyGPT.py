import os
import sys
import time
import random
import threading
import websocket
import requests
from mistyPy.Robot import Robot
from mistyPy.Events import Events
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
import constants
import subprocess

# Initialize Misty with your robot's IP address
misty = Robot("10.106.11.9")
misty.set_default_volume(50)

# Set OpenAI API key
os.environ["OPENAI_API_KEY"] = constants.APIKEY
print("API key loaded")

# Initialize the embeddings
embeddings = OpenAIEmbeddings()

# Load your data
loader = TextLoader('data.txt')
print("data.txt is loaded")

# Read and prepare documents
documents = loader.load()

if documents:
    # Use FAISS as the persistent vector store
    vectorstore = FAISS.from_documents(documents, embeddings)
else:
    print("No documents found in the loader.")
    sys.exit(1)

def speech_captured(data):
    if data["message"]["step"] == "CompletedASR":
        user_input = data["message"]["text"]
        process_user_input(user_input)
        print(user_input)

def process_user_input(user_input):
    mistyOutput = vectorstore.similarity_search(user_input, llm=ChatOpenAI())
    
    # Command checks
    moveArms = "move my arms"
    moveHead = "move my head"
    moveForward = "go forward"
    moveBackward = "go backward"
    moveForGesture1 = "intelligence"
    lowerVolume = "lower my volume"
    higherVolume = "higher my volume"
    changeDisplay = "change my display"
    
    print(mistyOutput)
    misty.speak_and_listen(mistyOutput)
    
    if moveForGesture1 in mistyOutput:
        misty.move_arms(-70, 50, 40, 40)
        time.sleep(1)
        print("left arm moved")
        misty.move_arms(50, 50, 40, 40)
    elif moveArms in mistyOutput:
        misty.move_arms(-50, -50, 40, 40)
        time.sleep(2)
        misty.move_arms(50, 50, 40, 40)
        print("arms moved")
    elif moveHead in mistyOutput:
        misty.move_head(0, -25, 0, 100, None, None)
        time.sleep(2)
        misty.move_head(0, 25, 0, 100, None, None)
        time.sleep(2)
        misty.move_head(0, 0, 0, 100, None, None)
        print("head moved")
    elif moveForward in mistyOutput:
        misty.drive_time(5000, 1, 5000, 0)
        print("moving forward")
    elif moveBackward in mistyOutput:
        misty.drive_time(-5000, 1, 5000, 0)
        print("moving backward")
    elif lowerVolume in mistyOutput:
        misty.set_default_volume(50)
    elif higherVolume in mistyOutput:
        misty.set_default_volume(100)
    elif changeDisplay in mistyOutput:
        misty.display_image("e_JoyGoofy3.jpg")
        time.sleep(3)
        misty.display_image("e_EcstacyHilarious.jpg")
        time.sleep(3)
        misty.display_image("e_DefaultContent.jpg")

def recognized(data):
    print(data)  
    misty.speak("Yay, Hi " + data["message"]["label"], 1)
    misty.stop_face_recognition()
    time.sleep(2)
    misty.start_dialog()
    misty.speak_and_listen("How can I help you today", utteranceId="required-for-callback")

# If Misty is lifted she gets a bit touchy about that.
def touch_sensor(data):
    if data["message"]["sensorId"] == "cap" and data["message"]["isContacted"] == True:
        touched_sensor = data["message"]["sensorPosition"]
        print(touched_sensor)
        if touched_sensor == "Scruff":
            misty.play_audio("s_Rage.wav")
            misty.display_image("e_Anger.jpg")
            time.sleep(3)
           # Triggers face recognition event to initiate ChatGPT
        if touched_sensor == "HeadFront": 
            misty.move_head(-5, 0, 0, 85, None, None)
            misty.display_image("e_Joy2.jpg")
            misty.speak("Aha")
            time.sleep(1)
            misty.start_face_recognition()
            # Stops ChatGPT event
        if touched_sensor == "Chin":
            misty.move_head(0, -50, 0, 150, None, None)
            misty.play_audio("s_Love.wav")
            misty.display_image("e_Love.jpg")
            time.sleep(2)
            misty.display_image("e_DefaultContent.jpg")
            if misty.event_exists("dialog-action-event"):
                misty.unregister_event("dialog-action-event")

# WebSocket event handling class

class EventHandler:
    def on_open(self, ws, response=None):
        print("WebSocket connection opened.")

    def on_error(self, ws, error, response=None):
        print(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print(f"WebSocket closed with code: {close_status_code} and reason: {close_msg}")



def start_websocket_thread(url):
    handler = EventHandler()
    ws = websocket.WebSocketApp(
        url,
        on_open=handler.on_open,
        on_error=handler.on_error,
        on_close=handler.on_close
    )
    thread = threading.Thread(target=ws.run_forever, daemon=True)
    thread.start()


# Example WebSocket URL (replace with actual WebSocket service)
url_1 = "ws://10.106.11.9:PORT/websocket"

# Start WebSocket connection in a separate thread
start_websocket_thread(url_1)

# Rest of the code remains the same...


# Create a state that speaks and then listens
misty.create_state(
    name="InitialGreeting",
    speak="I am Misty, how are you?",
    listen=True,
    noMatchSpeech="Sorry, I didn't catch that. Could you please repeat?",
    repeatMaxCount=2,
    failoverState="FailoverState"
)

# Start the state machine with the state we just created
misty.register_event(event_name="touch-sensor",
                     event_type=Events.TouchSensor,
                     callback_function=touch_sensor,
                     keep_alive=True)

misty.register_event(event_name="dialog-action-event",
                     event_type=Events.DialogAction,
                     callback_function=speech_captured,
                     keep_alive=True)

misty.register_event(event_name='face_recognition_event', 
                     event_type=Events.FaceRecognition, 
                     callback_function=recognized, 
                     keep_alive=False)

# Example loop for Misty robot actions
x = 4
while (x > 3):
    misty.display_image("e_DefaultContent.jpg")
    misty.move_arms(30, 30, 40, 40)
    misty.move_head(0, 0, 0, 85, None, None)
    time.sleep(5)
    misty.display_image("e_ContentLeft.jpg")
    time.sleep(3)
    misty.move_arms(20, 10, 40, 40)
    time.sleep(2)
    misty.move_head(0, -10, 0, 60, None, None)
    time.sleep(5)
    misty.display_image("e_ContentRight.jpg")
    time.sleep(3)
    misty.move_head(0, 10, 0, 60, None, None)
    time.sleep(5)
    misty.move_arms(10, 20, 40, 40)

print("testing")
misty.keep_alive()
