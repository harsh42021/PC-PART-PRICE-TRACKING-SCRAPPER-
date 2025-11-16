PC-Part-Price-Tracker-Canada/
│
├─ backend/
│   ├─ app.py                  # Main Flask backend, APIs, Pushbullet notifications
│   ├─ scrapper.py             # Scraping logic + currency conversion
│   ├─ models.py               # SQLAlchemy models (Retailers, Builds, Parts, PriceHistory)
│   ├─ database.db             # SQLite DB (auto-created on first run)
│   └─ requirements.txt        # Python dependencies
│
├─ frontend/
│   ├─ public/
│   │   └─ index.html          # React HTML template
│   ├─ src/
│   │   ├─ index.js            # React entry point
│   │   ├─ App.js              # Main React app
│   │   ├─ api.js              # API helper functions (axios)
│   │   └─ components/
│   │       ├─ BuildTab.js             # Handles builds and parts
│   │       ├─ RetailerManager.js      # Manage active/inactive retailers
│   │       └─ NotificationSettings.js # Pushbullet integration UI
│   └─ package.json             # React project dependencies
│
├─ .gitignore                  # Ignore node_modules, __pycache__, DB, etc.
└─ README.md                   # Project description, deployment instructions, folder tree
