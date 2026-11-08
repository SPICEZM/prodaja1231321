from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Главный эндпоинт, куда будут приходить сообщения (вебхуки от WhatsApp-шлюза)
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data:
        print("Получены данные:", data)
        # Здесь будет логика обработки сообщений (команды, меню, сбор текста)
        
    return jsonify(status="success"), 200

# Эндпоинт для пинга, чтобы бесплатный сервер на Render не засыпал
@app.route('/ping', methods=['GET'])
def ping():
    return "I am alive!", 200

@app.route('/', methods=['GET'])
def index():
    DOCKER_RUNNING = os.environ.get('RENDER', False)
    return "WhatsApp Bot is running!", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
