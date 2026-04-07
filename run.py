import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # We pull the port from an environment variable, defaulting to 5001
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=False, host="0.0.0.0", port=port)
