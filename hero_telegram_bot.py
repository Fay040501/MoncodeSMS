import os
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

load_dotenv()

API_KEY = os.getenv("API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = "https://hero-sms.com/stubs/handler_api.php"

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
    """
    Récupère les pays disponibles pour un service
    
    Format de réponse RÉEL de l'API (différent de la doc):
    {
      "0": {"country": 48, "price": 0.25, "count": 12449},
      "1": {"country": 34, "price": 0.28, "count": 1902},
      ...
    }
    """
    params = {
        "action": "getTopCountriesByService",
        "service": service_code,
        "api_key": API_KEY
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        print(f"\n=== DEBUG getTopCountriesByService ===")
        print(f"Service: {service_code}")
        print(f"Status HTTP: {response.status_code}")
        
        data = response.json()
        print(f"Type de data: {type(data)}")
        
        # CAS 1: Dictionnaire avec clés numériques (format réel de l'API)
        if isinstance(data, dict):
            # Vérifier si ce sont des clés numériques
            keys = list(data.keys())
            if len(keys) > 0 and (keys[0].isdigit() if isinstance(keys[0], str) else isinstance(keys[0], int)):
                # Convertir le dict en liste
                countries_list = []
                for key in sorted(data.keys(), key=lambda x: int(x) if isinstance(x, str) else x):
                    country_data = data[key]
                    if isinstance(country_data, dict) and "country" in country_data:
                        countries_list.append(country_data)
                
                print(f"✅ Format détecté: Dict avec clés numériques ({len(countries_list)} pays)")
                return countries_list
            
            # Peut-être que c'est un dict avec le service comme clé
            if service_code in data and isinstance(data[service_code], list):
                print(f"✅ Format détecté: Service comme clé")
                return data[service_code]
        
        # CAS 2: Array direct (selon la doc, mais pas observé en pratique)
        elif isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict) and "country" in data[0]:
                print(f"✅ Format détecté: Array direct de pays ({len(data)} pays)")
                return data
            
            # Format alternatif: [{ "service_code": [...] }]
            elif len(data) > 0 and isinstance(data[0], dict):
                first_item = data[0]
                if service_code in first_item and isinstance(first_item[service_code], list):
                    print(f"✅ Format détecté: Service dans array")
                    return first_item[service_code]
                
                # Première liste trouvée
                for key, value in first_item.items():
                    if isinstance(value, list):
                        print(f"✅ Format détecté: Première clé '{key}'")
                        return value
        
        print(f"❌ Format non reconnu")
        return []
        
    except Exception as e:
        print(f"❌ ERREUR dans get_countries_for_service: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_countries():
    """Liste de tous les pays"""
    params = {"action": "getCountries", "api_key": API_KEY}
    response = requests.get(BASE_URL, params=params, timeout=10)
    return response.json()

def request_number(service, country, operator=None, max_price=None):
    """Commander un numéro"""
    params = {
        "action": "getNumber",
        "service": service,
        "country": country,
        "api_key": API_KEY
    }
    
    if operator:
        params["operator"] = operator
    if max_price:
        params["maxPrice"] = max_price
    
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
    
    # Récupérer tous les services
    all_services = get_all_services(lang="en")
    
    if not all_services:
        await update.message.reply_text(
            "❌ Impossible de récupérer la liste des services.\n"
            "Réessaye plus tard."
        )
        return
    
    # Filtrer selon la recherche
    matching_services = [
        s for s in all_services 
        if query_text in s["name"].lower() or query_text in s["code"].lower()
    ]
    
    if not matching_services:
        await update.message.reply_text(
            f"❌ Aucun service trouvé pour `{query_text}`\n\n"
            "💡 Exemples de recherche :\n"
            "• telegram\n"
            "• cryptonow\n"
            "• whatsapp\n"
            "• google\n"
            "• instagram",
            parse_mode="Markdown"
        )
        return
    
    # Limiter à 20 résultats
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
        f"🔍 *{len(matching_services)} service(s) trouvé(s)*\n\n"
        "Choisis celui que tu veux :",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les boutons"""
    query = update.callback_query
    await query.answer()
    
    # ===== SOLDE =====
    if query.data == "balance":
        balance = get_balance()
        keyboard = [[InlineKeyboardButton("🔙 Menu", callback_data="back_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"💰 *Ton solde :* {balance} USD",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # ===== COMMANDER UN NUMERO =====
    elif query.data == "order":
        await query.edit_message_text(
            "🔍 *Recherche de service*\n\n"
            "Tape le nom du service que tu veux :\n\n"
            "💡 Exemples :\n"
            "• `telegram`\n"
            "• `cryptonow`\n"
            "• `whatsapp`\n"
            "• `google`\n"
            "• `instagram`",
            parse_mode="Markdown"
        )
    
    # ===== RETOUR MENU =====
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
    
    # ===== SERVICE CHOISI =====
    elif query.data.startswith("srv_"):
        service_code = query.data.replace("srv_", "")
        context.user_data["service"] = service_code
        
        await query.edit_message_text("⏳ Recherche des pays disponibles...")
        
        # Récupérer les pays pour ce service
        countries_data = get_countries_for_service(service_code)
        
        if not countries_data:
            keyboard = [[InlineKeyboardButton("🔙 Nouvelle recherche", callback_data="order")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"❌ Aucun pays disponible pour `{service_code}`\n\n"
                "Ce service n'est peut-être pas disponible actuellement.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
        
        # Récupérer la liste complète des pays
        all_countries = get_countries()
        country_dict = {c["id"]: c for c in all_countries}
        
        # Trier par nombre de numéros disponibles
        countries_data.sort(key=lambda x: x.get("count", 0), reverse=True)
        
        # Limiter à 15 pays
        countries_data = countries_data[:15]
        
        keyboard = []
        for c_data in countries_data:
            country_id = c_data.get("country")
            country_info = country_dict.get(country_id)
            
            if country_info:
                country_name = country_info.get("eng", f"Country {country_id}")
                count = c_data.get("count", 0)
                price = c_data.get("price", 0)
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"{country_name} • {count} nums • ${price:.3f}",
                        callback_data=f"ctry_{country_id}"
                    )
                ])
        
        if not keyboard:
            keyboard = [[InlineKeyboardButton("🔙 Nouvelle recherche", callback_data="order")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"❌ Impossible d'afficher les pays pour `{service_code}`",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
        
        keyboard.append([InlineKeyboardButton("🔙 Nouvelle recherche", callback_data="order")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🌍 *Pays disponibles pour {service_code}*\n\n"
            "Choisis un pays :",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    # ===== PAYS CHOISI - COMMANDER =====
    elif query.data.startswith("ctry_"):
        country_id = query.data.replace("ctry_", "")
        service = context.user_data.get("service")
        
        if not service:
            await query.edit_message_text("❌ Erreur : service non trouvé. Recommence avec /start")
            return
        
        await query.edit_message_text(f"⏳ Commande en cours pour *{service}*...", parse_mode="Markdown")
        
        result = request_number(service, country_id)
        print(f"Résultat commande: {result}")
        
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
                f"✅ *Numéro reçu pour {service} !*\n\n"
                f"📞 Numéro : `{phone_number}`\n"
                f"🆔 ID : `{activation_id}`\n\n"
                f"📝 Utilise ce numéro pour t'inscrire\n"
                f"Puis clique sur 'Vérifier SMS'",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        elif "NO_NUMBERS" in result:
            keyboard = [[InlineKeyboardButton("🔙 Réessayer", callback_data=f"srv_{service}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"❌ *Plus de numéros disponibles*\n\n"
                f"Essaye un autre pays ou réessaye plus tard.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        elif "NO_BALANCE" in result:
            keyboard = [[InlineKeyboardButton("💰 Voir solde", callback_data="balance")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"❌ *Solde insuffisant*\n\n"
                f"Recharge ton compte HeroSMS.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 Menu", callback_data="back_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"❌ *Erreur lors de la commande*\n\n"
                f"Détails : `{result}`",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    
    # ===== VERIFIER SMS =====
    elif query.data.startswith("check_"):
        activation_id = query.data.split("_")[1]
        
        status = get_sms_code(activation_id)
        
        if "STATUS_OK" in status:
            code = status.replace("STATUS_OK:", "")
            await confirm_sms(activation_id)
            
            keyboard = [[InlineKeyboardButton("🔙 Menu", callback_data="back_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"✅ *Code reçu !*\n\n"
                f"🔢 Code : `{code}`\n\n"
                f"✔️ Activation terminée avec succès !",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        elif "STATUS_WAIT_CODE" in status:
            await query.answer("⏳ SMS pas encore reçu, réessaye dans quelques secondes", show_alert=True)
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
    
    # ===== ANNULER =====
    elif query.data.startswith("cancel_"):
        activation_id = query.data.split("_")[1]
        result = cancel_activation(activation_id)
        
        keyboard = [[InlineKeyboardButton("🔙 Menu", callback_data="back_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if "ACCESS_CANCEL" in result:
            await query.edit_message_text(
                f"✅ *Activation annulée*\n\nArgent remboursé sur ton compte.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                f"⚠️ Résultat : `{result}`",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

# ===== Lancement du bot =====

def main():
    """Point d'entrée"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_service))
    
    print("🤖 Bot HeroSMS démarré !")
    app.run_polling()

if __name__ == "__main__":
    main()
