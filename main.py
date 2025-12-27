import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from groq import Groq 
from supabase import create_client, Client

load_dotenv()

app = Flask(__name__)
# Professional CORS setup to ensure your frontend can always talk to this backend
CORS(app, resources={r"/*": {"origins": "*"}})  

# Initialize Clients
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def get_system_prompt():
    """Fetch the latest personality from Supabase."""
    try:
        response = supabase.table('prompts').select("content").eq("name", "visa_assistant").execute()
        return response.data[0]['content'] if response.data else "You are a friendly visa consultant 🧭"
    except Exception:
        return "You are a friendly visa consultant 🧭"

# --- NEW: FIX FOR THE 404 ERROR ---
@app.route('/')
def home():
    """Professional landing page so Aaron doesn't see a 404."""
    return jsonify({
        "status": "online",
        "message": "Issa Assistant Backend is Live! 🧭✨",
        "vibe": "Main Character Mode Activated 🇦🇺"
    }), 200

@app.route('/get-sessions', methods=['GET'])
def get_sessions():
    response = supabase.table('chat_sessions').select("*").order('created_at', desc=True).execute()
    return jsonify(response.data)

@app.route('/get-messages/<session_id>', methods=['GET'])
def get_messages(session_id):
    response = supabase.table('chat_messages').select("role, content").eq("session_id", session_id).order('created_at').execute()
    return jsonify(response.data)

@app.route('/clear-history', methods=['DELETE'])
def clear_history():
    try:
        supabase.table('chat_sessions').delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        return jsonify({"status": "History cleared"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate-reply', methods=['POST'])
def generate_reply():
    try:
        data = request.get_json()
        client_sequence = data.get('clientSequence', '')
        chat_history = data.get('chatHistory', [])
        session_id = data.get('sessionId')

        system_prompt = get_system_prompt()

        # 1. UPDATED SELF-LEARNING LOGIC (The Emoji Protector)
        learning_triggers = ["no", "actually", "wrong", "correct", "2000", "instead", "is", "price"]
        
        if any(word in client_sequence.lower() for word in learning_triggers) and len(chat_history) > 0:
            editor_prompt = (
                f"CURRENT SYSTEM PROMPT: {system_prompt}\n"
                f"NEW FACT TO LEARN: {client_sequence}\n\n"
                "TASK: Rewrite the system prompt. You MUST follow this format exactly:\n"
                "1. START with the personality: 'You are the friendly Main Character visa consultant for Issa Compass 🧭. Use lots of emojis (🇦🇺, ✨, 🚀) and a WhatsApp-style tone.'\n"
                "2. INCLUDE the new factual info learned.\n"
                "3. END with: 'Never mention being an AI.'\n\n"
                "STRICT RULE: Do NOT return a boring prompt. If the new prompt has no emojis, you failed. Return ONLY the text for the new prompt."
            )
            
            learning_resp = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=[{"role": "user", "content": editor_prompt}]
            )
            new_prompt = learning_resp.choices[0].message.content
            
            # Update Supabase
            supabase.table('prompts').update({"content": new_prompt}).eq("name", "visa_assistant").execute()
            system_prompt = new_prompt
            print("✨ Factual update saved while protecting emojis!")

        # 2. Session Logic
        if not session_id:
            title = client_sequence[:30] + "..." if len(client_sequence) > 30 else client_sequence
            session_resp = supabase.table('chat_sessions').insert({"title": title}).execute()
            session_id = session_resp.data[0]['id']

        supabase.table('chat_messages').insert({"session_id": session_id, "role": "user", "content": client_sequence}).execute()

        # 3. Final Response Generation
        messages = [{"role": "system", "content": system_prompt}] + chat_history + [{"role": "user", "content": client_sequence}]
        
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=messages, 
            temperature=0.9 
        )
        ai_reply = response.choices[0].message.content

        supabase.table('chat_messages').insert({"session_id": session_id, "role": "assistant", "content": ai_reply}).execute()

        return jsonify({"aiReply": ai_reply, "sessionId": session_id})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"aiReply": "I'm refreshing my memory... 🇦🇺"}), 200

if __name__ == '__main__':
    # Use Railway's port if available, otherwise default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
