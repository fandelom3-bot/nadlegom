import streamlit as st
from datetime import datetime
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ------------------------
# CONFIGURATION ADMIN
# ------------------------
IDENTIFIANT_ADMIN = "admin"
MDP_ADMIN = "admin123"
NOM_PUBLIC_ADMIN = "nadlego_"

FICHIER_USERS = "users.txt"
FICHIER_NEWS = "om_news.json"
DOSSIER_IMAGES = "images"

SMTP_EMAIL = "nadlegomarseille@gmail.com"
SMTP_PASSWORD = "MOT_DE_PASSE_APP"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

if not os.path.exists(DOSSIER_IMAGES):
    os.makedirs(DOSSIER_IMAGES)

# ------------------------
# CSS pour feed OM stylé
# ------------------------
st.markdown("""
<style>
body {
    background-color: #003399;
    color: white;
}
.card {
    background-color: #ffffff;
    color: #003399;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 20px;
}
.stButton>button {
    background-color: #003399;
    color: white;
    font-weight: bold;
    border-radius: 5px;
}
.stTextInput>div>div>input, .stTextArea>div>div>textarea {
    background-color: white;
    color: #003399;
    border-radius: 5px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------
# Vérifier / créer compte admin
# ------------------------
def verifier_admin():
    if not os.path.exists(FICHIER_USERS):
        with open(FICHIER_USERS, "w", encoding="utf-8") as f:
            f.write(f"{IDENTIFIANT_ADMIN}:{MDP_ADMIN}:admin:{NOM_PUBLIC_ADMIN}:{SMTP_EMAIL}\n")
    else:
        with open(FICHIER_USERS, "r", encoding="utf-8") as f:
            lignes = f.readlines()
        admin_present = any(l.split(":")[0] == IDENTIFIANT_ADMIN for l in lignes)
        if not admin_present:
            with open(FICHIER_USERS, "a", encoding="utf-8") as f:
                f.write(f"{IDENTIFIANT_ADMIN}:{MDP_ADMIN}:admin:{NOM_PUBLIC_ADMIN}:{SMTP_EMAIL}\n")
verifier_admin()

# ------------------------
# Utilisateurs
# ------------------------
def lire_users():
    users = {}
    if not os.path.exists(FICHIER_USERS):
        return users
    with open(FICHIER_USERS, "r", encoding="utf-8") as f:
        for ligne in f:
            parts = ligne.strip().split(":")
            if len(parts) != 5:
                continue
            identifiant, mdp, role, nom_public, mail = parts
            users[identifiant] = {"mdp": mdp, "role": role, "public": nom_public, "mail": mail}
    return users

# ------------------------
# News JSON
# ------------------------
def lire_news():
    if not os.path.exists(FICHIER_NEWS):
        return []
    with open(FICHIER_NEWS, "r", encoding="utf-8") as f:
        return json.load(f)

def ecrire_news(news):
    with open(FICHIER_NEWS, "w", encoding="utf-8") as f:
        json.dump(news, f, indent=4)

# ------------------------
# Emails
# ------------------------
def envoyer_email(titre, texte):
    users = lire_users()
    for u in users.values():
        if u["role"] != "admin" and u["mail"]:
            try:
                msg = MIMEMultipart()
                msg['From'] = SMTP_EMAIL
                msg['To'] = u["mail"]
                msg['Subject'] = f"NOUVELLE NEWS OM : {titre}"
                body = f"{texte}\n\nPour suivre le blog OM, connectez-vous !"
                msg.attach(MIMEText(body, 'plain'))
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                server.starttls()
                server.login(SMTP_EMAIL, SMTP_PASSWORD)
                server.send_message(msg)
                server.quit()
            except Exception as e:
                print("Erreur email :", e)

# ------------------------
# Session
# ------------------------
if 'login_ok' not in st.session_state:
    st.session_state['login_ok'] = False
if 'user' not in st.session_state:
    st.session_state['user'] = None

# ------------------------
# Interface principale
# ------------------------
st.title("⚽ Feed Mini OM ⚽")
choix = st.radio("Connexion ou Inscription ?", ["Connexion", "Inscription"])
users = lire_users()
news = lire_news()

# ------------------------
# Inscription
# ------------------------
if choix == "Inscription":
    st.subheader("Créer un compte")
    new_user = st.text_input("Nom d'utilisateur")
    new_pass = st.text_input("Mot de passe", type="password")
    new_nom_public = st.text_input("Nom public visible")
    new_mail = st.text_input("Email pour recevoir les news")
    if st.button("Créer le compte"):
        if new_user in users:
            st.warning("Nom déjà utilisé !")
        else:
            with open(FICHIER_USERS, "a", encoding="utf-8") as f:
                f.write(f"{new_user}:{new_pass}:user:{new_nom_public}:{new_mail}\n")
            st.success("Compte créé ✅ ! Tu peux maintenant te connecter.")

# ------------------------
# Connexion
# ------------------------
if choix == "Connexion":
    st.subheader("Se connecter")
    login = st.text_input("Nom d'utilisateur", key="login")
    mdp = st.text_input("Mot de passe", type="password", key="mdp")
    if st.button("Se connecter"):
        if login in users and users[login]["mdp"] == mdp:
            st.session_state['login_ok'] = True
            st.session_state['user'] = users[login]
        else:
            st.warning("Identifiants incorrects !")

# ------------------------
# Après connexion
# ------------------------
if st.session_state['login_ok']:
    user = st.session_state['user']
    role = user["role"]
    st.success(f"Connecté en tant que {user['public']} ({role}) ✅")

    # ------------------------
    # Admin ajoute news
    # ------------------------
    if role == "admin":
        st.subheader("Ajouter une news")
        titre = st.text_input("Titre de la news", key="titre")
        texte = st.text_area("Texte de la news", key="texte")
        image = st.file_uploader("Ajouter une image (facultatif)", type=["png","jpg","jpeg"], key="img")
        if st.button("Publier la news"):
            date = datetime.now().strftime("%d/%m/%Y %H:%M")
            chemin_image = ""
            if image:
                chemin_image = os.path.join(DOSSIER_IMAGES, image.name)
                with open(chemin_image, "wb") as f:
                    f.write(image.getbuffer())
            nouvelle_news = {
                "date": date,
                "titre": titre,
                "texte": texte,
                "image": chemin_image,
                "auteur": user['public'],
                "likes": [],
                "commentaires": []
            }
            news.append(nouvelle_news)
            ecrire_news(news)
            envoyer_email(titre, texte)
            st.success("News publiée et emails envoyés ✅")

        # Supprimer une news
        st.subheader("Supprimer une news")
        for i, n in enumerate(news):
            st.markdown(f"**{n['titre']}** ({n['date']}) - par {n['auteur']}")
            if st.button(f"Supprimer #{i}", key=f"sup_{i}"):
                news.pop(i)
                ecrire_news(news)
                st.experimental_rerun()  # OK pour forcer refresh

    # ------------------------
    # Affichage feed
    # ------------------------
    st.subheader("Feed OM")
    for idx, n in reversed(list(enumerate(news))):
        st.markdown(f"<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"**{n['date']}**")
        st.markdown(f"**Titre :** {n['titre']}")
        st.markdown(f"{n['texte']}")
        if n["image"] and os.path.exists(n["image"]):
            st.image(n["image"], use_container_width=True)
        st.markdown(f"✍️ Publié par : **{n['auteur']}**")

        # Likes
        if 'likes' not in st.session_state:
            st.session_state['likes'] = {}
        if user['public'] not in n['likes']:
            if st.button(f"❤️ {len(n['likes'])} Likes", key=f"like_{idx}"):
                n['likes'].append(user['public'])
                ecrire_news(news)
        else:
            st.markdown(f"❤️ {len(n['likes'])} Likes")

        # Commentaires
        cmt_text = st.text_input("Commenter...", key=f"cmt_{idx}")
        if st.button("Envoyer", key=f"btn_cmt_{idx}"):
            if cmt_text.strip() != "":
                n['commentaires'].append({"user": user['public'], "texte": cmt_text})
                ecrire_news(news)

        # Affichage commentaires
        if n['commentaires']:
            st.markdown("💬 Commentaires :")
            for c in n['commentaires']:
                st.markdown(f"- **{c['user']}** : {c['texte']}")
        st.markdown("</div>", unsafe_allow_html=True)
