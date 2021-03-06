# Final Project

`Python v3.9.6`

To install required packages  
`pip install -r requirements.txt`  

To run flask server  
`python main.py`

--------

### Root Folder Schema

```bash
│   db.sqlite3
│   main.py
│   README.md
│   requirements.txt
│   
├───application
│   │   database.py
│   │   error.py
│   │   
│   ├───models
│   │   │   deck.py
│   │   │   response_mode.py
│   │   │   user_mode.py
│   │           
│   └───routes
│       │   auth.py
│       │   card.py
│       │   deck.py
│       │   profile.py
│       │   review.py
│       
├───static
│   ├───css
│   │       add_card.css
│   │       base.css
│   │       card.css
│   │       deck.css
│   │       login.css
│   │       profile.css
│   │       review.css
│   │       
│   ├───js
│   │       login.js
│   │       
│   └───media
│               
└───templates
    │   Base.html
    │   
    ├───Dashboard
    │       Profile.html
    │       
    ├───Deck
    │       Add_Card.html
    │       Card.html
    │       Deck.html
    │       
    ├───Review
    │       Review.html
    │       
    └───Security
            login_user.html
```