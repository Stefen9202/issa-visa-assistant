import requests
import json

# The URL where your Flask server is running locally
URL = "http://127.0.0.1:5000/generate-reply"

def test_visa_bot():
    # This is a fake message as if it came from a customer
    payload = {
        "clientSequence": "Hi, I want to move to Australia. Can you help me with the visa?",
        "chatHistory": [
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hey there! How can I help you today? 😊"}
        ]
    }

    print("🚀 Sending message to your AI Assistant...")
    
    try:
        # Send the POST request to your Flask app
        response = requests.post(URL, json=payload)
        
        # Check if it was successful
        if response.status_code == 200:
            result = response.json()
            print("\n✅ AI RESPONSE:")
            print("-" * 30)
            print(result.get("aiReply"))
            print("-" * 30)
        else:
            print(f"❌ Error: Server returned status code {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Connection Error: Is your app.py running? \nDetail: {e}")

if __name__ == "__main__":
    test_visa_bot()