import os
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

load_dotenv()

API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = "https://hero-sms.com/stubs/handler_api.php"

# ===== Serveur HTTP pour Render =====

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>HeroSMS Bot is running!</h1>')
    
    def log_message(self, format, *args):
        return  # Silence les logs

def start_http_server():
    port = int(os.getenv('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    print(f"🌐 HTTP Server started on port {port}")
    server.serve_forever()

# ===== Fonctions HeroSMS =====

def get_balance():
    """Récupère le solde"""
    params = {"action": "getBalance", "api_key": API_KEY}
    response = requests.get(BASE_URL, params=params, timeout=10)
    return response.text.replace("ACCESS_BALANCE:", "")

def get_all_services(lang="en"):
    """Récupère TOUS les services disponibles"""
    params = {
        "action": "getServicesList",
        "lang": lang,
        "api_key": API_KEY
    }
    response = requests.get(BASE_URL, params=params, timeout=10)
    data = response.json()
    
    if data.get("status") == "success":
        return data.get("services", [])
    return []

def get_countries_for_service(service_code):
    """Récupère les pays disponibles pour un service"""
    params = {
        "action": "getTopCountriesByService",
        "service": service_code,
        "api_key": API_KEY
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        print(f"\n=== API Call: getTopCountriesByService ===")
        print(f"Service: {service_code}")
        print(f"HTTP Status: {response.status_code}")
        
        data = response.json()
        
        if isinstance(data, dict):
            countries_list = []
            for key in data.keys():
                value = data[key]
                if isinstance(value, dict) and "country" in value:
                    countries_list.append(value)
            
            if countries_list:
                print(f"✅ Trouvé {len(countries_list)} pays")
                return countries_list
            else:
                print(f"⚠️ Dictionnaire reçu mais pas de données pays valides")
                return []
        
        elif isinstance(data, list):
            print(f"✅ Format liste reçu avec {len(data)} éléments")
            if len(data) > 0 and isinstance(data[0], dict) and "country" in data[0]:
                return data
            elif len(data) > 0 and isinstance(data[0], dict):
                for key, value in data[0].items():
                    if isinstance(value, list):
                        return value
        
        print(f"❌ Format non reconnu: {type(data)}")
        return []
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return []

def get_countries():
    """Liste de tous les pays"""
    params = {"action": "getCountries", "api_key": API_KEY}
    response = requests.get(BASE_URL, params=params, timeout=10)
    return response.json()

def request_number(service, country):
    """Commander un numéro"""
    params = {
        "action": "getNumber",
        "service": service,
        "country": country,
        "api_key": API_KEY
    }
    response = requests.get(BASE_URL, params=params, timeout=10)
    return response.text

def get_sms_code(activation_id):
    """Récupérer le code SMS"""
    params = {
        "action": "getStatus",
        "id": activation_id,
        "api_key": API_KEY
    }
    response = requests.get(BASE_URL, params=params, timeout=10)
    return response.text

def cancel_activation(activation_id):
    """Annuler une activation"""
    params = {
        "action": "setStatus",
        "id": activation_id,
        "status": 8,
        "api_key": API_KEY
    }
    response = requests.get(BASE_URL, params=params, timeout=10)
    return response.text

def confirm_sms(activation_id):
    """Confirmer la réception du SMS"""
    params = {
        "action": "setStatus",
        "id": activation_id,
        "status": 6,
        "api_key": API_KEY
    }
    response = requests.get(BASE_URL, params=params, timeout=10)
    return response.text

def get_active_activations():
    """Récupérer les activations actives"""
    params = {
        "action": "getActiveActivations",
        "api_key": API_KEY
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        if isinstance(data, dict) and data.get("status") == "success":
            activations = data.get("activeActivations", [])
            if isinstance(activations, list):
                return activations
        
        return []
    except Exception as e:
        print(f"Erreur get_active_activations: {e}")
        return []

def get_history(limit=10):
    """Récupérer l'historique des activations"""
    import time
    params = {
        "action": "getHistory",
        "start": int(time.time()) - (7 * 24 * 3600),
        "end": int(time.time()),
        "offset": 0,
        "size": limit,
        "api_key": API_KEY
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        if isinstance(data, list):
            return data
        
        return []
    except Exception as e:
        print(f"Erreur get_history: {e}")
        return []

# ===== Commandes Telegram =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Message de bienvenue"""
    keyboard = [
        [InlineKeyboardButton("💰 Voir mon solde", callback_data="balance")],
        [InlineKeyboardButton("📱 Commander un numéro", callback_data="order")],
        [InlineKeyboardButton("📋 Mes activations", callback_data="activations")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎯 *Bot HeroSMS*\n\n"
        "Bienvenue ! Que veux-tu faire ?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def search_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recherche de service par mot-clé"""
    query_text = update.message.text.lower()
    
    all_services = get_all_services(lang="en")
    
    if not all_services:
        await update.message.reply_text("❌ Impossible de récupérer la liste des services.")
        return
    
    matching_services = [
        s for s in all_services 
        if query_text in s["name"].lower() or query_text in s["code"].lower()
    ]
    
    if not matching_services:
        await update.message.reply_text(
            f"❌ Aucun service trouvé pour `{query_text}`\n\n"
            "💡 Exemples : telegram, crypto, whatsapp, google",
            parse_mode="Markdown"
        )
        return
    
    matching_services = matching_services[:20]
    
    keyboard = [
        [InlineKeyboardButton(
            f"{s['name']} ({s['code']})", 
            callback_data=f"srv_{s['code']}"
        )]
        for s in matching_services
    ]
    keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="order")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🔍 *{len(matching_services)} service(s)*\n\nChoisis :",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les boutons"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "balance":
        balance = get_balance()
        keyboard = [[InlineKeyboardButton("🔙 Menu", callback_data="back_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"💰 *Solde :* {balance} USD",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    elif query.data == "order":
        await query.edit_message_text(
            "🔍 *Recherche de service*\n\n"
            "Tape le nom du service :\n"
            "• telegram\n"
            "• crypto\n"
            "• whatsapp\n"
            "• google",
            parse_mode="Markdown"
        )
    
    elif query.data == "back_menu":
        keyboard = [
            [InlineKeyboardButton("💰 Voir mon solde", callback_data="balance")],
            [InlineKeyboardButton("📱 Commander un numéro", callback_data="order")],
            [InlineKeyboardButton("📋 Mes activations", callback_data="activations")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🎯 *Bot HeroSMS*\n\nQue veux-tu faire ?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    elif query.data == "activations":
        active = get_active_activations()
        
        if not isinstance(active, list):
            print(f"ERREUR: active n'est pas une liste, c'est un {type(active)}")
            active = []
        
        if active:
            message = "📋 *Activations en cours*\n\n"
            keyboard = []
            
            for act in active[:5]:
                phone = act.get("phoneNumber", "N/A")
                service = act.get("serviceCode", "N/A")
                status = act.get("activationStatus", "0")
                act_id = act.get("activationId", "")
                
                status_text = {
                    "0": "⏳ En attente",
                    "1": "📨 SMS envoyé",
                    "3": "🔄 Redemandé",
                    "4": "✅ Code reçu",
                    "6": "✅ Complété",
                    "8": "❌ Annulé"
                }.get(status, f"Status {status}")
                
                message += f"• {service.upper()} - {phone}\n  {status_text}\n\n"
                
                if status in ["0", "1", "3"]:
                    keyboard.append([
                        InlineKeyboardButton(
                            f"🔄 Vérifier {service} ({phone[-4:]})",
                            callback_data=f"check_{act_id}"
                        )
                    ])
            
            keyboard.append([InlineKeyboardButton("📜 Voir historique", callback_data="history")])
            keyboard.append([InlineKeyboardButton("🔙 Menu", callback_data="back_menu")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            history = get_history(5)
            
            if history:
                message = "📜 *Historique (5 dernières)*\n\n"
                for h in history:
                    phone = h.get("phone", "N/A")
                    sms = h.get("sms") or "Pas de SMS"
                    cost = h.get("cost", 0)
                    status = h.get("status", "0")
                    
                    status_text = {
                        "4": "✅ Complété",
                        "6": "✅ Complété",
                        "8": "❌ Annulé"
                    }.get(status, f"Status {status}")
                    
                    if sms and len(sms) > 30:
                        sms_short = sms[:30] + "..."
                    else:
                        sms_short = sms
                    
                    message += f"• {phone}\n  {status_text} - ${cost}\n  {sms_short}\n\n"
                
                keyboard = [[InlineKeyboardButton("🔙 Menu", callback_data="back_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    message,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            else:
                keyboard = [[InlineKeyboardButton("🔙 Menu", callback_data="back_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "📋 Aucune activation trouvée",
                    reply_markup=reply_markup
                )
    
    elif query.data == "history":
        history = get_history(10)
        
        if history:
            message = "📜 *Historique (10 dernières)*\n\n"
            for h in history:
                phone = h.get("phone", "N/A")
                sms = h.get("sms") or "Pas de SMS"
                cost = h.get("cost", 0)
                status = h.get("status", "0")
                
                status_text = {
                    "4": "✅ Complété",
                    "6": "✅ Complété", 
                    "8": "❌ Annulé"
                }.get(status, f"Status {status}")
                
                if sms and len(sms) > 40:
                    sms_short = sms[:40] + "..."
                else:
                    sms_short = sms
                
                message += f"• {phone}\n  {status_text} - ${cost}\n  {sms_short}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("🔙 Activations", callback_data="activations")],
                [InlineKeyboardButton("🏠 Menu", callback_data="back_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 Menu", callback_data="back_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "📜 Aucun historique",
                reply_markup=reply_markup
            )
    
    elif query.data.startswith("srv_"):
        service_code = query.data.replace("srv_", "")
        context.user_data["service"] = service_code
        
        await query.edit_message_text("⏳ Recherche des pays...")
        
        countries_data = get_countries_for_service(service_code)
        
        if not countries_data:
            keyboard = [[InlineKeyboardButton("🔙 Retour", callback_data="order")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"❌ Pas de pays pour `{service_code}`",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
        
        all_countries = get_countries()
        country_dict = {c["id"]: c for c in all_countries}
        
        countries_data.sort(key=lambda x: x.get("count", 0), reverse=True)
        countries_data = countries_data[:15]
        
        keyboard = []
        for c_data in countries_data:
            country_id = c_data.get("country")
            country_info = country_dict.get(country_id)
            
            if country_info:
                name = country_info.get("eng", f"ID{country_id}")
                count = c_data.get("count", 0)
                price = c_data.get("price", 0)
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"{name} • {count} nums • ${price:.2f}",
                        callback_data=f"ctry_{country_id}"
                    )
                ])
        
        if not keyboard:
            keyboard = [[InlineKeyboardButton("🔙 Retour", callback_data="order")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"❌ Erreur affichage pays",
                reply_markup=reply_markup
            )
            return
        
        keyboard.append([InlineKeyboardButton("🔙 Retour", callback_data="order")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🌍 *Pays pour {service_code}*\n\nChoisis :",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    elif query.data.startswith("ctry_"):
        country_id = query.data.replace("ctry_", "")
        service = context.user_data.get("service")
        
        if not service:
            await query.edit_message_text("❌ Erreur. /start pour recommencer")
            return
        
        await query.edit_message_text(f"⏳ Commande...", parse_mode="Markdown")
        
        result = request_number(service, country_id)
        print(f"Résultat: {result}")
        
        if "ACCESS_NUMBER" in result:
            parts = result.split(":")
            activation_id = parts[1]
            phone_number = parts[2]
            
            context.user_data["activation_id"] = activation_id
            
            keyboard = [
                [InlineKeyboardButton("🔄 Vérifier SMS", callback_data=f"check_{activation_id}")],
                [InlineKeyboardButton("❌ Annuler", callback_data=f"cancel_{activation_id}")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ *Numéro reçu !*\n\n"
                f"📞 `{phone_number}`\n"
                f"🆔 `{activation_id}`\n\n"
                f"Utilise-le puis clique 'Vérifier SMS'",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        elif "NO_NUMBERS" in result:
            keyboard = [[InlineKeyboardButton("🔙 Réessayer", callback_data=f"srv_{service}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Plus de numéros disponibles",
                reply_markup=reply_markup
            )
        elif "NO_BALANCE" in result:
            keyboard = [[InlineKeyboardButton("💰 Solde", callback_data="balance")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Solde insuffisant",
                reply_markup=reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 Menu", callback_data="back_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"❌ Erreur : `{result}`",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    
    elif query.data.startswith("check_"):
        activation_id = query.data.split("_")[1]
        status = get_sms_code(activation_id)
        
        if "STATUS_OK" in status:
            code = status.replace("STATUS_OK:", "")
            await confirm_sms(activation_id)
            
            keyboard = [[InlineKeyboardButton("🔙 Menu", callback_data="back_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ *Code reçu !*\n\n🔢 `{code}`",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        elif "STATUS_WAIT_CODE" in status:
            await query.answer("⏳ Pas encore reçu", show_alert=True)
        else:
            keyboard = [
                [InlineKeyboardButton("🔄 Réessayer", callback_data=f"check_{activation_id}")],
                [InlineKeyboardButton("❌ Annuler", callback_data=f"cancel_{activation_id}")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"⚠️ Statut : `{status}`",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    
    elif query.data.startswith("cancel_"):
        activation_id = query.data.split("_")[1]
        result = cancel_activation(activation_id)
        
        keyboard = [[InlineKeyboardButton("🔙 Menu", callback_data="back_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if "ACCESS_CANCEL" in result:
            await query.edit_message_text(
                "✅ Annulé, argent remboursé",
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                f"⚠️ `{result}`",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

# ===== Main =====

if __name__ == "__main__":
    # Démarrer le serveur HTTP en arrière-plan
    http_thread = Thread(target=start_http_server, daemon=True)
    http_thread.start()
    
    # Démarrer le bot
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_service))
    
    print("🤖 Bot Telegram démarré !")
    app.run_polling()
