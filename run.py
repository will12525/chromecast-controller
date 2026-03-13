import argparse
from app import create_app

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the application.")
    parser.add_argument("--production", action="store_true", help="Run the app in production mode.")
    args = parser.parse_args()

    port = 5000 if args.production else 5001

    # setup_db()
    print("--------------------Running Main--------------------")
    app = create_app()
    app.run(debug=False, host="0.0.0.0", port=port)
