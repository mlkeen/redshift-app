import os
from player_app.app import create_app

app = create_app()

if __name__ == "__main__":
    print("🔧 ENVIRONMENT:", dict(os.environ)) 
    
    port = int(os.environ.get("PORT", 5000))
    print("🚀 Flask app starting...")
    app.run(host="0.0.0.0", port=port)