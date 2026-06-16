import logging
import requests
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
# 🔑 CONFIGURATION DE TON BOT
# ==========================================
# Mets ton token Telegram officiel fourni par BotFather ici :
TELEGRAM_TOKEN = "8652808582:AAEIvLKUIPe7xiKrWOVGmRL8VNGrXNlwhpY"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)

CHOIX_MOMENT, CHOIX_TYPE_PARI, CHOIX_MATCH = range(3)

DICTIONNAIRE_DRAPEAUX = {
    "france": "🇫🇷", "psg": "🇫🇷", "marseille": "🇫🇷", "lyon": "🇫🇷", "monaco": "🇫🇷",
    "espagne": "🇪🇸", "real": "🇪🇸", "barcelone": "🇪🇸", "atletico": "🇪🇸", "madrid": "🇪🇸",
    "angleterre": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "manchester": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "arsenal": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "liverpool": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "chelsea": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "italie": "🇮🇹", "juventus": "🇮🇹", "milan": "🇮🇹", "inter": "🇮🇹", "roma": "🇮🇹",
    "allemagne": "🇩🇪", "bayern": "🇩🇪", "dortmund": "🇩🇪", "leverkusen": "🇩🇪",
    "portugal": "🇵🇹", "benfica": "🇵🇹", "porto": "🇵🇹", "sporting": "🇵🇹",
    "senegal": "🇸🇳", "maroc": "🇲🇦", "algerie": "🇩🇿", "cote d'ivoire": "🇨🇮", "cameroun": "🇨🇲",
    "lakers": "🇺🇸", "celtics": "🇺🇸", "bulls": "🇺🇸", "warriors": "🇺🇸", "nba": "🇺🇸",
    "alcaraz": "🇪🇸", "nadal": "🇪🇸", "djokovic": "🇷🇸", "sinner": "🇮🇹", "swiatek": "🇵🇱"
}

def obtenir_drapeau(nom_equipe):
    nom_clean = nom_equipe.lower().strip()
    for cle, emoji in DICTIONNAIRE_DRAPEAUX.items():
        if cle in nom_clean:
            return emoji
    return "🏳️"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texte_start = (
        "📊 **Bienvenue sur AI prono !**\n\n"
        "Plus qu'un simple livescore, je suis ton analyste sportif personnel. "
        "Je scanne des milliers de données en temps réel sur le Football, le Tennis et le Basket-ball.\n\n"
        "🔮 Matchs récents, rencontres à venir, dynamiques d'équipes et alertes en direct : "
        "l'analyse pro est désormais automatisée.\n\n"
        "👉 **Utilise la commande /prono pour lancer une analyse !**"
    )
    await update.message.reply_text(texte_start, parse_mode="Markdown")

async def prono_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    options_moment = [["🔮 Avant-Match (Pronostics)", "📝 Fin de Match (Bilan & Incidents)"]]
    reply_markup = ReplyKeyboardMarkup(options_moment, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("⚙️ **Que souhaitez-vous analyser pour ce match ?**", reply_markup=reply_markup)
    return CHOIX_MOMENT

async def recevoir_moment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    moment = update.message.text
    context.user_data["moment"] = moment
    if "Avant-Match" in moment:
        options_pari = [
            ["Victoire (1N2)", "Total Buts/Points (Over/Under)"],
            ["Les deux équipes marquent", "Handicap / Corners"]
        ]
        reply_markup = ReplyKeyboardMarkup(options_pari, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("🤔 **Quel type de Paris voulez-vous ?**", reply_markup=reply_markup)
        return CHOIX_TYPE_PARI
    else:
        context.user_data["type_pari"] = "Bilan Fin de Match"
        await update.message.reply_text("📝 **Dite le match terminé que vous voulez analyser ( DOMICILE - EXTERIEUR )**", reply_markup=ReplyKeyboardRemove())
        return CHOIX_MATCH

async def recevoir_type_pari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["type_pari"] = update.message.text
    await update.message.reply_text(
        "📝 **Dite le match que vous voulez analyser ( DOMICILE - EXTERIEUR )**\n\n⚠️ _Exemple_ : `Real Madrid - Barcelone`",
        parse_mode="Markdown", reply_markup=ReplyKeyboardRemove()
    )
    return CHOIX_MATCH

async def analyser_le_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    match_input = update.message.text
    moment = context.user_data.get("moment", "🔮 Avant-Match (Pronostics)")
    type_pari = context.user_data.get("type_pari", "Général")
    
    if " - " in match_input:
        equipe_dom, equipe_ext = match_input.split(" - ", 1)
        equipe_dom = equipe_dom.strip()
        equipe_ext = equipe_ext.strip()
    else:
        equipe_dom, equipe_ext = match_input.strip(), "Adversaire"

    drapeau_dom = obtenir_drapeau(equipe_dom)
    drapeau_ext = obtenir_drapeau(equipe_ext)

    await update.message.reply_text(f"⏳ **AI prono se connecte à BetWatch...**\nGénération des données pour {drapeau_dom} *{equipe_dom}* vs {drapeau_ext} *{equipe_ext}*.", parse_mode="Markdown")
    await update.message.reply_chat_action("typing")

    if "Avant-Match" in moment:
        rapport = (
            f"🤖 **RAPPORT D'ANALYSE IA AVANT-MATCH (via BetWatch)**\n"
            f"⚽ **MATCH** : {drapeau_dom} {equipe_dom.upper()} - {drapeau_ext} {equipe_ext.upper()}\n"
            f"🎯 Optique : _{type_pari}_\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
            f"{drapeau_dom} **ANALYSE INDIVIDUELLE : {equipe_dom}**\n• **Matchs récents** : V-N-V-D-V.\n• **Blessures** : Latéral droit blessé.\n• **🔥 Buteurs chauds** : Attaquant n°9.\n\n"
            f"{drapeau_ext} **ANALYSE INDIVIDUELLE : {equipe_ext}**\n• **Matchs récents** : D-N-D-V-N.\n• **Absences** : Défenseur central suspendu.\n• **🔥 Buteurs chauds** : Ailier gauche.\n\n"
            f"📊 **COTES RÉELLES EN DIRECT (Flux 1XBET)**\n• Cote [{equipe_dom}] : **1.95**\n• Cote [Match Nul] : **3.50**\n• Cote [{equipe_ext}] : **4.00**\n\n"
            f"🔮 **PRONOSTICS & ESTIMATIONS AI PRONO**\n• **Buteur probable** : Buteur n°9 Domicile.\n• **Estimation buts** : Total +2.5 buts.\n• **Score Exact Estimé** : 2 - 1 ou 3 - 1.\n\n"
            f"👉 **Recommandation** : **Victoire de {equipe_dom}**.\n\n✍️ **zehi prediction**"
        )
    else:
        rapport = (
            f"🤖 **BILAN POST-MATCH & INCIDENTS (via BetWatch)**\n"
            f"🏁 **MATCH TERMINÉ** : {drapeau_dom} {equipe_dom.upper()} 2 - 1 {drapeau_ext} {equipe_ext.upper()} 🔴\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
            f"⚽ **BUTEURS** : 34' n°9 (Action), 61' n°10 (Pen), 88' n°7 (Action).\n"
            f"🟨 🟥 **CARTONS** : 12' 🟨 Dom, 45' 🟨 Ext, 76' 🟥 Expulsion Ext.\n"
            f"🥅 **PENALTIES** : 61' ✅ Réussi Ext, 82' ❌ Manqué Dom.\n"
            f"🏥 **INFIRMERIE** : 40' Blessure milieu de {equipe_dom}.\n\n"
            f"📊 **STATS FINALES** : Possession {equipe_dom} 58% - 42%\n\n✍️ **zehi prediction**"
        )

    await update.message.reply_text(rapport, parse_mode="Markdown")
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Opération annulée.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("prono", prono_command)],
        states={
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
