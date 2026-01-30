# 🚀 Guide Complet : Déployer ton Bot sur GitHub et Render

## 📋 Table des matières
1. [Préparer les fichiers](#étape-1-préparer-les-fichiers)
2. [Créer un repo GitHub](#étape-2-créer-un-repo-github)
3. [Upload le code sur GitHub](#étape-3-upload-le-code-sur-github)
4. [Déployer sur Render](#étape-4-déployer-sur-render)

---

## Étape 1 : Préparer les fichiers

### ✅ Fichiers nécessaires (déjà créés) :

```
hero-sms-bot/
├── hero_telegram_bot.py    # Le code principal du bot
├── requirements.txt         # Les dépendances Python
├── .env.example            # Exemple de configuration
├── .gitignore              # Fichiers à ne pas uploader
└── README.md               # Documentation
```

**IMPORTANT** : Ne mets JAMAIS ton fichier `.env` (avec tes vraies clés) sur GitHub !

---

## Étape 2 : Créer un repo GitHub

### 📝 Instructions :

1. **Va sur GitHub** : https://github.com
2. **Connecte-toi** (ou crée un compte si tu n'en as pas)
3. **Clique sur le "+"** en haut à droite → "New repository"
4. **Configure ton repo** :
   - Repository name : `hero-sms-bot`
   - Description : `Bot Telegram pour HeroSMS`
   - Visibilité : **Private** (recommandé) ou Public
   - ✅ Coche "Add a README file"
   - ✅ Coche "Add .gitignore" → Choisis "Python"
5. **Clique sur "Create repository"**

---

## Étape 3 : Upload le code sur GitHub

### Option A : Via l'interface web (FACILE) ✅

1. **Sur ton nouveau repo**, clique sur "Add file" → "Upload files"
2. **Glisse-dépose** ces fichiers :
   - `hero_telegram_bot.py`
   - `requirements.txt`
   - `.env.example`
3. **Écris un message** : "Initial commit - Bot HeroSMS"
4. **Clique sur "Commit changes"**

✅ **C'est fait !** Ton code est maintenant sur GitHub.

---

### Option B : Via Git en ligne de commande (AVANCÉ)

Si tu veux utiliser Git :

```bash
# 1. Initialiser Git dans ton dossier
cd "C:\Users\hp\Documents\INSSEDS\MASTER 2 ET CERTIFICATION\Projet\Test_Google_Gen"
git init

# 2. Ajouter tes fichiers
git add hero_telegram_bot.py requirements.txt .env.example .gitignore README.md

# 3. Faire ton premier commit
git commit -m "Initial commit - Bot HeroSMS"

# 4. Lier à GitHub (remplace TON_USERNAME et TON_REPO)
git remote add origin https://github.com/TON_USERNAME/hero-sms-bot.git

# 5. Pousser le code
git branch -M main
git push -u origin main
```

---

## Étape 4 : Déployer sur Render

### 📝 Instructions détaillées :

### 4.1 Créer un compte Render

1. **Va sur** https://render.com
2. **Clique sur "Get Started"**
3. **Connecte-toi avec GitHub** (recommandé)
   - Autorise Render à accéder à tes repos

---

### 4.2 Créer un nouveau Web Service

1. **Sur le dashboard Render**, clique sur "New +" → "Web Service"
2. **Connecte ton repo GitHub** :
   - Si c'est la première fois : clique sur "Connect GitHub"
   - Cherche ton repo `hero-sms-bot`
   - Clique sur "Connect"

---

### 4.3 Configurer le service

**Remplis les champs suivants** :

| Champ | Valeur |
|-------|--------|
| **Name** | `hero-sms-bot` |
| **Region** | `Frankfurt (EU Central)` ou le plus proche |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python hero_telegram_bot.py` |
| **Instance Type** | **Free** ✅ |

---

### 4.4 Ajouter les variables d'environnement

**CRUCIAL** : Scroll vers le bas jusqu'à "Environment Variables"

**Clique sur "Add Environment Variable"** et ajoute :

| Key | Value |
|-----|-------|
| `API_KEY` | `ta_vraie_cle_herosms` |
| `BOT_TOKEN` | `ton_vrai_token_telegram` |

⚠️ **IMPORTANT** : Entre tes VRAIES clés ici, pas les exemples !

---

### 4.5 Déployer !

1. **Scroll tout en bas**
2. **Clique sur "Create Web Service"**
3. **Attends 2-3 minutes** ⏳

Tu verras les logs de déploiement. Cherche ces lignes :

```
==> Installing dependencies from requirements.txt
==> Starting service with 'python hero_telegram_bot.py'
🤖 Bot HeroSMS démarré !
```

✅ **Si tu vois ça, c'est bon !** Ton bot tourne 24/7 !

---

## 🎉 Vérification

1. **Ouvre Telegram**
2. **Cherche ton bot** (le nom que tu as donné à BotFather)
3. **Envoie** `/start`
4. **Le bot devrait répondre !** 🎯

---

## ⚠️ Problèmes courants

### Le bot ne répond pas

**Vérifie** :
1. Les variables d'environnement sont bien configurées
2. Le service est "Live" (vert) sur Render
3. Pas d'erreurs dans les logs

### Erreur "Conflict: terminated by other getUpdates"

**Solution** : Arrête ton bot local sur ton PC
```bash
Ctrl + C  # dans le terminal où tourne le bot
```

### Le service s'arrête après quelques minutes

C'est normal sur le plan gratuit ! Render met le service en veille après 15 minutes d'inactivité. Il redémarre automatiquement quand quelqu'un utilise le bot.

---

## 🔄 Mettre à jour le bot

Si tu modifies ton code :

**Via GitHub web** :
1. Va sur ton repo
2. Clique sur le fichier à modifier
3. Clique sur le crayon ✏️
4. Modifie le code
5. "Commit changes"
6. Render redéploie automatiquement ! ✅

**Via Git** :
```bash
git add .
git commit -m "Description des changements"
git push
```

Render détecte le push et redéploie automatiquement !

---

## 💡 Conseils

✅ **Ne partage JAMAIS** tes clés API ou tokens
✅ **Utilise toujours** `.gitignore` pour `.env`
✅ **Teste en local** avant de push sur GitHub
✅ **Vérifie les logs** sur Render si problème

---

## 🆘 Besoin d'aide ?

Si tu es bloqué à une étape, copie-colle l'erreur exacte et je t'aide ! 😊
