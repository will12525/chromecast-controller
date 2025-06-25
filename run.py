from app import create_app

if __name__ == "__main__":
    # setup_db()
    print("--------------------Running Main--------------------")
    app = create_app()
    app.run(debug=False, host="0.0.0.0", port=5000)
