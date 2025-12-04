from hello import app, db, User, Ingredients
from werkzeug.security import generate_password_hash, check_password_hash

with app.app_context():
    db.drop_all()
    db.create_all()

    # Users
    Steven = User(username = "Steven10", password_hash=generate_password_hash("Steven123"))
    db.session.add(Steven)
    db.session.commit()

    Max = User(username = "Max10", password_hash=generate_password_hash("Max123"))
    db.session.add(Max)
    db.session.commit()

    Ian = User(username = "Ian10", password_hash=generate_password_hash("Ian123"))
    db.session.add(Ian)
    db.session.commit()

    Chris = User(username = "Chris10", password_hash=generate_password_hash("Chris123"))
    db.session.add(Chris)
    db.session.commit()


    # Ingredients
    

    # Veggies
    Carrot = Ingredients(name = "Carrot", category = "Vegetables")
    db.session.add(Carrot)
    db.session.commit()

    Onions = Ingredients(name = "Onions", category = "Vegetables")
    db.session.add(Onions)
    db.session.commit()

    Spinach = Ingredients(name = "Spinach", category = "Vegetables")
    db.session.add(Spinach)
    db.session.commit()

    Potato = Ingredients(name = "Potato", category = "Vegetables")
    db.session.add(Potato)
    db.session.commit()


    #  Meats
    Beef = Ingredients(name = "Beef", category = "Meats")
    db.session.add(Beef)
    db.session.commit()

    Chicken = Ingredients(name = "Chicken", category = "Meats")
    db.session.add(Chicken)
    db.session.commit()

    Pork = Ingredients(name = "Pork", category = "Meats")
    db.session.add(Pork)
    db.session.commit()

    Ham = Ingredients(name = "Ham", category = "Meats")
    db.session.add(Ham)
    db.session.commit()

    Turkey = Ingredients(name = "Turkey", category = "Meats")
    db.session.add(Turkey)
    db.session.commit()

    Bacon = Ingredients(name = "Bacon", category = "Meats")
    db.session.add(Bacon)
    db.session.commit()

    Lamb = Ingredients(name = "Lamb", category = "Meats")
    db.session.add(Lamb)
    db.session.commit()


    # Extra stuff idk lol

    Cheese = Ingredients(name = "Cheese", category = "Extra")
    db.session.add(Cheese)
    db.session.commit()

    Bread = Ingredients(name = "Bread", category = "Extra")
    db.session.add(Bread)
    db.session.commit()

    Tortilla = Ingredients(name = "Tortilla", category = "Extra")
    db.session.add(Tortilla)
    db.session.commit()

    ChowMein = Ingredients(name = "Chow Mein", category = "Extra")
    db.session.add(ChowMein)
    db.session.commit()










    
    
