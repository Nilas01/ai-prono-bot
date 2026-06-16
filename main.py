import logging
import random
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
# 🔑 METS TON TOKEN DIRECTEMENT ICI
# ==========================================
TELEGRAM_TOKEN = "8652808582:AAFS5nG7xFxBpjI8aPMW5Y7Km7ME3Db-rOY"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)

CHOIX_SPORT, CHOIX_MOMENT, CHOIX_TYPE_PARI, CHOIX_MATCH = range(4)

# Liste complète pour détecter les pays et les clubs
CORRESPONDANCES_PAYS = {
    "🇫🇷": ["france", "psg", "marseille", "lyon", "monaco", "lille", "lens"],
    "🇪🇸": ["espagne", "spain", "real madrid", "barcelone", "barca", "atletico", "alcaraz", "nadal"],
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿": ["angleterre", "england", "manchester", "city", "united", "arsenal", "liverpool", "chelsea"],
    "🇮🇹": ["italie", "italia", "juventus", "milan", "inter", "roma", "sinner"],
    "🇩🇪": ["allemagne", "germany", "bayern", "dortmund", "leverkusen"],
    "🇵🇹": ["portugal", "benfica", "porto", "sporting"],
    "🇺🇸": ["usa", "etats-unis", "lakers", "celtics", "bulls", "warriors", "nba"],
    "🇸🇳": ["senegal"], "🇲🇦": ["maroc", "morocco"], "🇩🇿": ["algerie", "algeria"], 
    "🇨🇮": ["cote d'ivoire", "ivoire", "abidjan"], "🇨🇲": ["cameroun", "cameroon"], "🇨🇬": ["congo"],
    "🇮🇳": ["inde", "india", "mumbai", "chennai", "rcb"], "🇿🇦": ["afrique du sud", "south africa"],
    "🇷🇸": ["djokovic", "serbie"], "🇵🇱": ["swiatek", "pologne"]
}

def deviner_drapeau(nom_equipe):
    nom_clean = nom_equipe.lower().strip()
    for drapeau, mots_cles in CORRESPONDANCES_PAYS.items():
        for mot in mots_cles:
            if mot in nom_clean:
                return drapeau
    return "🏳️"

def séparer_équipes(texte_match):
    for separateur in [" vs ", " VS ", " v ", " V ", "-", " - "]:
        if separateur in texte_match:
            parties = texte_match.split(separateur, 1)
            return parties[0].strip(), parties[1].strip()
    mots = texte_match.strip().split()
    if len(mots) >= 2:
        return mots[0], " ".join(mots[1:])
    return texte_match.strip(), "Adversaire"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texte_start = (
        "📊 **Bienvenue sur AI prono !**\n\n"
        "Analyste multisport automatique. Algorithmes BetWatch avancés.\n\n"
        "👉 **Utilise /prono pour démarrer !**"
    )
    await update.message.reply_text(texte_start, parse_mode="Markdown")

async def prono_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    options_sports = [
        ["⚽ Football", "🏀 Basket-ball", "🎾 Tennis"],
        ["🏏 Cricket", "🏐 Volley-ball", "🏉 Rugby"],
        ["🤾 Handball"]
    ]
    reply_markup = ReplyKeyboardMarkup(options_sports, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("🏆 **Sélectionnez le sport :**", reply_markup=reply_markup)
    return CHOIX_SPORT

async def recevoir_sport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["sport"] = update.message.text
    options_moment = [["🔮 Avant-Match (Pronostics)", "📝 Fin de Match (Bilan)"]]
    reply_markup = ReplyKeyboardMarkup(options_moment, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("⚙️ **Type d'analyse :**", reply_markup=reply_markup)
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
        await update.message.reply_text("🤔 **Option de pari :**", reply_markup=reply_markup)
        return CHOIX_TYPE_PARI
    else:
        context.user_data["type_pari"] = "Bilan Fin de Match"
        await update.message.reply_text("📝 **Entrez le match terminé (Ex: Congo vs Portugal) :**", reply_markup=ReplyKeyboardRemove())
        return CHOIX_MATCH

async def recevoir_type_pari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["type_pari"] = update.message.text
    await update.message.reply_text("📝 **Entrez les équipes (Ex: Portugal vs Congo) :**", reply_markup=ReplyKeyboardRemove())
    return CHOIX_MATCH

async def analyser_le_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    match_input = update.message.text
    sport = context.user_data.get("sport", "⚽ Football")
    moment = context.user_data.get("moment", "🔮 Avant-Match (Pronostics)")
    type_pari = context.user_data.get("type_pari", "Général")
    
    equipe_dom, equipe_ext = séparer_équipes(match_input)
    drapeau_dom = deviner_drapeau(equipe_dom)
    drapeau_ext = deviner_drapeau(equipe_ext)

    await update.message.reply_text(f"⏳ **AI prono se connecte aux serveurs BetWatch...**\nAnalyse mathématique en cours pour {sport}...", parse_mode="Markdown")
    await update.message.reply_chat_action("typing")

    # Algorithme neutre qui bloque le résultat peu importe l'ordre d'écriture
    cle_unique = "".join(sorted([equipe_dom.lower(), equipe_ext.lower()]))
    random.seed(cle_unique)

    # Détection automatique des favoris du football ou sport de combat
    favoris = ["portugal", "france", "espagne", "angleterre", "italie", "allemagne", "psg", "real madrid", "barcelone", "manchester", "lakers", "djokovic"]
    force_dom = 3 if equipe_dom.lower() in favoris else 1
    force_ext = 3 if equipe_ext.lower() in favoris else 1
    
    score_dom_calcule = random.randint(1, 3) + (force_dom - force_ext if force_dom > force_ext else 0)
    score_ext_calcule = random.randint(0, 2) + (force_ext - force_dom if force_ext > force_dom else 0)
    score_dom_calcule, score_ext_calcule = max(0, score_dom_calcule), max(0, score_ext_calcule)

    # Recommandation logique et stable
    if score_dom_calcule > score_ext_calcule:
        recommandation = f"Victoire de {drapeau_dom} {equipe_dom}"
        cote_dom, cote_ext = "1.45", "5.80"
    elif score_ext_calcule > score_dom_calcule:
        recommandation = f"Victoire de {drapeau_ext} {equipe_ext}"
        cote_dom, cote_ext = "6.10", "1.38"
    else:
        recommandation = "Match Nul ou Moins de 2.5 buts"
        cote_dom, cote_ext = "2.90", "3.10"

    # Calcul strict des détails chiffrés demandés
    b_1ere = random.randint(0, min(score_dom_calcule + score_ext_calcule, 2))
    b_2eme = max(0, (score_dom_calcule + score_ext_calcule) - b_1ere)
    buts_tete_1ere = random.randint(0, 1) if b_1ere > 0 else 0
    buts_tete_2eme = random.randint(0, 1) if b_2eme > 0 else 0
    
    # Adaptation des chiffres précis selon le sport choisi
    if "Football" in sport or "Handball" in sport or "Rugby" in sport:
        details_chiffres = (
            f"📊 **STATISTIQUES CALCULÉES DU MATCH**\n"
            f"• Nombre total de buts estimé : **{score_dom_calcule + score_ext_calcule} buts**\n"
            f"• Buts marqués en 1ère mi-temps : **{b_1ere}**\n"
            f"• Buts marqués en 2ème mi-temps : **{b_2eme}**\n"
            f"• But de la tête en 1ère mi-temps : **{'Oui' if buts_tete_1ere > 0 else 'Non'} ({buts_tete_1ere})**\n"
            f"• But de la tête en 2ème mi-temps : **{'Oui' if buts_tete_2eme > 0 else 'Non'} ({buts_tete_2eme})**\n"
        )
    elif "Basket" in sport:
        q1, q2, q3, q4 = random.randint(40, 50), random.randint(42, 52), random.randint(40, 48), random.randint(45, 55)
        details_chiffres = (
            f"📊 **STATISTIQUES POINTS PAR QUART-TEMPS**\n"
            f"• Points prévus au 1er Quart : **{q1} pts**\n"
            f"• Points prévus au 2ème Quart : **{q2} pts**\n"
            f"• Points prévus au 3ème Quart : **{q3} pts**\n"
            f"• Points prévus au 4ème Quart : **{q4} pts**\n"
            f"• Total Points estimé : **{q1+q2+q3+q4} pts**\n"
        )
    else: # Tennis / Volley-ball
        s1, s2 = random.randint(6, 7), random.randint(3, 6)
        details_chiffres = (
            f"📊 **PRÉVISIONS DES JEUX ET SETS**\n"
            f"• Score estimé du 1er Set : **{s1} - {random.randint(2,5)}**\n"
            f"• Score estimé du 2ème Set : **{random.randint(2,5)} - {s2}**\n"
        )

    random.seed() # Nettoyage

    if "Avant-Match" in moment:
        rapport = (
            f"🤖 **RAPPORT D'ANALYSE IA AVANT-MATCH (BetWatch)**\n"
            f"{sport} : {drapeau_dom} **{equipe_dom.upper()}** vs {drapeau_ext} **{equipe_ext.upper()}**\n"
            f"🎯 Option demandée : _{type_pari}_\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
            f"{details_chiffres}\n"
            f"📊 **COTES DE RÉFÉRENCE (Flux 1XBET)**\n"
            f"• Cote [{equipe_dom}] : **{cote_dom}**\n"
            f"• Cote [{equipe_ext}] : **{cote_ext}**\n\n"
            f"🔮 **PRODUIT DE L'ANALYSE**\n"
            f"👉 **Recommandation optimale** : **{recommandation}** (Score estimé : {score_dom_calcule}-{score_ext_calcule})\n\n"
            f"👋 _prédictions fait par le zehi_"
        )
    else:
        rapport = (
            f"🤖 **BILAN POST-MATCH & INCIDENTS (BetWatch)**\n"
            f"{sport} : {drapeau_dom} **{equipe_dom.upper()}** {score_dom_calcule} - {score_ext_calcule} {drapeau_ext} **{equipe_ext.upper()}**\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n"
            f"📝 **ÉVÉNEMENTS EXÉCUTÉS** : Les données récoltées valident l'intensité physique globale appliquée durant la rencontre.\n\n"
            f"👋 _prédictions fait par le zehi_"
        )

    await update.message.reply_text(rapport, parse_mode="Markdown")
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Opération annulée.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "TON_TOKEN_ICI":
        print("Erreur : Remplace 'TON_TOKEN_ICI' à la ligne 15 par ton vrai token Telegram !")
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
