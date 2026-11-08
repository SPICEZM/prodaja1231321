from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# Читаем переменные окружения, которые мы настроили на Render
ID_INSTANCE = os.environ.get('GREEN_API_INSTANCE', '710722794392')
API_TOKEN = os.environ.get('GREEN_API_TOKEN')

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Получены данные от вебхука:", data)
    
    try:
        # Проверяем, что это входящее текстовое сообщение
        if data and data.get('typeWebhook') == 'incomingMessageReceived':
            senderData = data.get('senderData', {})
            messageData = data.get('messageData', {})
            
            chatId = senderData.get('chatId') # Кто написал (номер)
            
            # Проверяем текст сообщения
            textMessage = ""
            if 'textMessageData' in messageData:
                textMessage = messageData['textMessageData'].get('textMessage', '')
            
            print(f"Сообщение от {chatId}: {textMessage}")
            
            # Логика ответа бота
            if textMessage:
                response_text = f"Привет! Я бот-помощник. Ты написал: «{textMessage}»"
                
                # Отправляем ответ через Green API
                url = f"https://7107.api.greenapi.com/waInstance{ID_INSTANCE}/sendMessage/{API_TOKEN}"
                payload = {
                    "chatId": chatId,
                    "message": response_text
                }
                requests.post(url, json=payload)
                
    except Exception as e:
        print("Ошибка при обработке вебхука:", e)
        
    return jsonify(status="success"), 200

@app.route('/ping', methods=['GET'])
def ping():
    return "I am alive!", 200

@app.route('/', methods=['GET'])
def index():
    return "WhatsApp Bot is running!", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
