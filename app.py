from flask import Flask, request, jsonify
import os
import requests
import re

app = Flask(__name__)

ID_INSTANCE = os.environ.get('GREEN_API_INSTANCE', '710722794392')
API_TOKEN = os.environ.get('GREEN_API_TOKEN')

# Наш каталог рыбы (цена за 1 кг)
FISH_CATALOG = {
    "камбала": 500,
    "горбуша": 650,
    "кета": 900,
    "нерка": 1200,
    "минтай": 300,
    "треска": 550,
    "семга": 1400
}

def send_whatsapp_message(chat_id, text):
    url = f"https://7107.api.greenapi.com/waInstance{ID_INSTANCE}/sendMessage/{API_TOKEN}"
    payload = {
        "chatId": chat_id,
        "message": text
    }
    requests.post(url, json=payload)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    
    try:
        if data and data.get('typeWebhook') == 'incomingMessageReceived':
            senderData = data.get('senderData', {})
            messageData = data.get('messageData', {})
            
            chatId = senderData.get('chatId')
            
            textMessage = ""
            if 'textMessageData' in messageData:
                textMessage = messageData['textMessageData'].get('textMessage', '').lower()
            
            print(f"Сообщение от {chatId}: {textMessage}")
            
            if chatId and textMessage:
                response_text = ""
                
                # 1. Если просят каталог / ассортимент
                if any(word in textMessage for word in ["каталог", "ассортимент", "что есть", "прайс", "рыба", "меню"]):
                    response_text = "🐟 *Свежий улов в наличии (цена за 1 кг):*\n\n"
                    for fish, price in FISH_CATALOG.items():
                        response_text += f"• {fish.capitalize()} — {price} руб./кг\n"
                    response_text += "\nНапишите, например: *«Хочу камбалу 2 кг»*, чтобы рассчитать заказ!"
                
                else:
                    # 2. Пытаемся найти рыбу и килограммы в сообщении
                    found_fish = None
                    for fish in FISH_CATALOG.keys():
                        if fish in textMessage:
                            found_fish = fish
                            break
                    
                    if found_fish:
                        # Ищем число перед или после слова 'кг' или просто цифру
                        numbers = re.findall(r'\d+', textMessage)
                        kg = float(numbers[0]) if numbers else 1.0 # Если цифру не указали, считаем за 1 кг
                        
                        price_per_kg = FISH_CATALOG[found_fish]
                        total_price = int(price_per_kg * kg)
                        
                        response_text = (
                            f"📦 Запрос: {found_fish.capitalize()} — {kg} кг.\n"
                            f"💰 Цена за 1 кг: {price_per_kg} руб.\n"
                            f"✅ *Итого к оплате:* *{total_price} руб.*\n\n"
                            f"Для оформления заказа напишите адрес доставки или свяжитесь с менеджером!"
                        )
                    else:
                        response_text = (
                            "Привет! 🎣 Я рыбный бот-помощник.\n"
                            "Напишите **«каталог»**, чтобы посмотреть наш ассортимент и цены, "
                            "или сразу укажите, какую рыбу и сколько килограммов хотите купить (например: *«камбала 2 кг»*)."
                        )
                
                send_whatsapp_message(chatId, response_text)
                
    except Exception as e:
        print("Ошибка при обработке вебхука:", e)
        
    return jsonify(status="success"), 200

@app.route('/ping', methods=['GET'])
def ping():
    return "I am alive!", 200

@app.route('/', methods=['GET'])
def index():
    return "WhatsApp Fish Bot is running!", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
