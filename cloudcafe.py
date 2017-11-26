from app import create_app, sio

app = create_app(debug=True)

if __name__ == '__main__':
    sio.run(app, host="0.0.0.0", port=80)
