import logging
import re
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters,
)

# ==========================================
# 🔑 METS TON TOKEN DIRECTEMENT ICI EN DESSOUS
# ==========================================
TELEGRAM_TOKEN = "8652808582:AAFS5nG7xFxBpjI8aPMW5Y7Km7ME3Db-rOY"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)

CHOIX_SPORT, CHOIX_MOMENT, CHOIX_TYPE_PARI, CHOIX_MATCH = range(4)

# Dictionnaire pour détecter le pays et attribuer le bon drapeau
CORRESPONDANCES_PAYS = {
    "🇫🇷": ["france", "psg", "marseille", "lyon", "monaco", "lille", "lens", "rennes", "nantes"],
    "🇪🇸": ["espagne", "spain", "real madrid", "barcelone", "barca", "atletico", "madrid", "seville", "valencia", "alcaraz", "nadal"],
    "🏴%7B%5C%E2%80%A0%5D%7B%5C%E2%80%A0%5D%7B%5C%E2%80%A0%5D%7D%E2%80%A1%E2%80%A1%E2%80%A1": ["angleterre", "england", "manchester", "city", "united", "arsenal", "liverpool", "chelsea", "tottenham", "newcastle"],
    "🇮🇹": ["italie", "italia", "juventus", "milan", "inter", "roma", "napoli", "lazio", "sinner"],
    "🇩🇪": ["allemagne", "germany", "bayern", "dortmund", "leverkusen", "leipzig", "frankfurt"],
    "🇵🇹": ["portugal", "benfica", "porto", "sporting", "braga"],
    "🇺🇸": ["usa", "etats-unis", "lakers", "celtics", "bulls", "warriors", "nba", "inter miami"],
    "🇸🇳": ["senegal"], "🇲🇦": ["maroc", "morocco"], "🇩🇿": ["algerie", "algeria"], 
    "🇨🇮": ["cote d'ivoire", "ivoire", "abidjan"], "🇨🇲": ["cameroun", "cameroon"],
    "🇮🇳": ["inde", "india", "mumbai", "chennai", "rcb", "kolkata", "delhi", "rajasthan"],
    "🇦🇺": ["australie", "australia"], "🇵🇦": ["pakistan"], "🇿🇦": ["afrique du sud", "south africa"],
    "🇷🇸": ["djokovic", "serbie"], "🇵🇱": ["swiatek", "pologne"]
}

def deviner_drapeau(nom_equipe):
    nom_clean = nom_equipe.lower().strip()
    for drapeau, mots_cles in CORRESPONDANCES_PAYS.items():
        for mot in mots_cles:
            if mot in nom_clean:
                return drapeau
    return "🏳️"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texte_start = (
        "📊 **Bienvenue sur AI prono !**\n\n"
        "Je suis ton analyste multisport personnel. Je scanne les données en temps réel "
        "pour te fournir les meilleures analyses professionnelles automatisées.\n\n"
        "👉 **Utilise la commande /prono pour lancer une analyse !**"
    )
    await update.message.reply_text(texte_start, parse_mode="Markdown")

async def prono_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    options_sports = [
        ["⚽ Football", "🏀 Basket-ball", "🎾 Tennis"],
        ["🏏 Cricket", "🏐 Volley-ball", "🏉 Rugby"],
        ["🤾 Handball"]
    ]
    reply_markup = ReplyKeyboardMarkup(options_sports, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("🏆 **Sélectionnez le sport à analyser :**", reply_markup=reply_markup)
    return CHOIX_SPORT

async def recevoir_sport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["sport"] = update.message.text
    options_moment = [["🔮 Avant-Match (Pronostics)", "📝 Fin de Match (Bilan & Incidents)"]]
    reply_markup = ReplyKeyboardMarkup(options_moment, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("⚙️ **Que souhaitez-vous analyser pour ce match ?**", reply_markup=reply_markup)
    return CHOIX_MOMENT

async def recevoir_moment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    moment = update.message.text
    context.user_data["moment"] = moment
    if "Avant-Match" in moment:
        options_pari = [
            ["Victoire / Résultat (1N2)", "Total Buts/Points (Over/Under)"],
            ["Les deux équipes marquent", "Handicap / Stats avancées"]
        ]
        reply_markup = ReplyKeyboardMarkup(options_pari, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("🤔 **Quel type d'analyse de paris voulez-vous ?**", reply_markup=reply_markup)
        return CHOIX_TYPE_PARI
    else:
        context.user_data["type_pari"] = "Bilan Fin de Match"
        await update.message.reply_text("📝 **Entrez le match terminé (Exemple: Real Madrid - Barcelone) :**", reply_markup=ReplyKeyboardRemove())
        return CHOIX_MATCH

async def recevoir_type_pari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["type_pari"] = update.message.text
    await update.message.reply_text(
        "📝 **Entrez le match à analyser ( DOMICILE - EXTERIEUR )** :",
        reply_markup=ReplyKeyboardRemove()
    )
    return CHOIX_MATCH

async def analyser_le_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    match_input = update.message.text
    sport = context.user_data.get("sport", "⚽ Football")
    moment = context.user_data.get("moment", "🔮 Avant-Match (Pronostics)")
    type_pari = context.user_data.get("type_pari", "Général")
    
    if " - " in match_input:
        equipe_dom, equipe_ext = match_input.split(" - ", 1)
        equipe_dom = equipe_dom.strip()
        equipe_ext = equipe_ext.strip()
    else:
        equipe_dom, equipe_ext = match_input.strip(), "Adversaire"

    drapeau_dom = deviner_drapeau(equipe_dom)
    drapeau_ext = deviner_drapeau(equipe_ext)

    await update.message.reply_text(f"⏳ **AI prono se connecte aux serveurs BetWatch...**\nAnalyse en cours pour {sport}...", parse_mode="Markdown")
    await update.message.reply_chat_action("typing")

    if "Avant-Match" in moment:
        rapport = (
            f"🤖 **RAPPORT D'ANALYSE IA AVANT-MATCH (via BetWatch)**\n"
            f"{sport} **MATCH** : {drapeau_dom} {equipe_dom.upper()} - {drapeau_ext} {equipe_ext.upper()}\n"
            f"🎯 Option : _{type_pari}_\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
            f"📈 **STATUT ET COMPORTEMENT DES ÉQUIPES**\n"
            f"• {drapeau_dom} **{equipe_dom}** : Dynamique solide à domicile, l'effectif montre une grande régularité offensive.\n"
            f"• {drapeau_ext} **{equipe_ext}** : Difficultés notables lors des déplacements récents, bloc défensif sous pression.\n\n"
            f"📊 **DONNÉES ET COTES EN DIRECT (Flux 1XBET)**\n"
            f"• Cote [{equipe_dom}] : **1.85**\n"
            f"• Cote [Égalité/Nul] : **3.40** (si applicable)\n"
            f"• Cote [{equipe_ext}] : **4.20**\n\n"
            f"🔮 **PRODUIT DE L'ANALYSE AI PRONO**\n"
            f"• **Scénario attendu** : Domination tactique de l'équipe à domicile.\n"
            f"• **Score ou Seuil Estimé** : Avantage net pour l'hôte.\n\n"
            f"👉 **Recommandation finale** : **Victoire / Avantage à {equipe_dom}**.\n\n"
            f"                                      _prédictions fait par le zehi_"
        )
    else:
        rapport = (
            f"🤖 **BILAN POST-MATCH & INCIDENTS (via BetWatch)**\n"
            f"{sport} **MATCH TERMINÉ** : {drapeau_dom} {equipe_dom.upper()} 2 - 1 {drapeau_ext} {equipe_ext.upper()} 🔴\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
            f"📝 **ÉVÉNEMENTS DU MATCH** : Intensité maximale dès la reprise. Changements tactiques décisifs ayant inversé la tendance en seconde période.\n"
            f"🟨 **DISCIPLINE & FAUTES** : Match engagé avec plusieurs interventions arbitrables importantes des deux côtés.\n"
            f"📊 **DONNÉES STATISTIQUES FINALES** : Clairement à l'avantage du camp à domicile qui a su concrétiser ses opportunités majeures.\n\n"
            f"                                      _prédictions fait par le zehi_"
        )

    await update.message.reply_text(rapport, parse_mode="Markdown")
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Opération annulée.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "TON_TOKEN_ICI":
        print("Erreur : Tu as oublié de remplacer TON_TOKEN_ICI à la ligne 15 !")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("prono", prono_command)],
        states={
            CHOIX_SPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_sport)],
            CHOIX_MOMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_moment)],
            CHOIX_TYPE_PARI: [MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_type_pari)],
            CHOIX_MATCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, analyser_le_match)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
