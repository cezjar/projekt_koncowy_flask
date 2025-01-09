from app import app

def main():
    with app.app_context():
        app.run(debug=True, port=5000)


if __name__ == "__main__":
    main()
