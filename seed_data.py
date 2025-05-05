import os
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

from app import create_app, db
from app.models import User, Character, Ability, Item, Condition

import random
import string

def generate_item_code():
    def an(): return random.choice(string.ascii_uppercase)
    def nn(): return str(random.randint(0, 9))
    def ax(): return random.choice(string.ascii_uppercase + string.digits)

    return f"{an()}{nn()}{nn()}{ax()}{ax()}{ax()}{ax()}"


load_dotenv()
app = create_app()

with app.app_context():
    db.create_all()

    # Create users
    control_user = User(
        username="admin",
        email="control@redshift.local",
        password=generate_password_hash("password"),
        is_verified=True,
        role="Control"
    )
    player_user1 = User(
        username="Susan",
        email="sbigelow@redshift.local",
        password=generate_password_hash("password"),
        is_verified=True,
        role="Player"
    )
    player_user2 = User(
        username="Frank",
        email="bigfrankie@redshift.local",
        password=generate_password_hash("password"),
        is_verified=True,
        role="Player"
    )

    # Add characters
    char = Character(
        name="Riggs",
        position="Chief Engineer",
        affiliation="Mining Ship Octavia",
        status="Nominal",
        abilities=["Weldmaster", "Overclock"],
        items=["Plasma Torch"],
        conditions=[],
        user=player_user1
    )

    # Add abilities
    abilities = [
        Ability(name="Weldmaster", description="Can bypass most physical locks with welding gear."),
        Ability(name="Overclock", description="Once per game cycle, speed up a system at risk of overheating.")
    ]

    # Add conditions
    conditions = [
        Condition(name="Exhausted", effect="Disadvantage on physical tasks until rested."),
        Condition(name="Injured", effect="Cannot take physical actions without assistance.")
    ]

    # Add items
    items = [
        Item(name="Plasma Torch", description="Can cut through most bulkhead doors.", code=generate_item_code()),
        Item(name="Medkit", description="Removes 'Injured' condition on use.", code=generate_item_code()),
        Item(name="MiniFusion", description="portable fusion powerplant.", code=generate_item_code()),
        Item(name="Unknown Item", description="Bizarre object.", code=generate_item_code()),
        Item(name="Blooka", description="Removes 'Injured' condition on use.", code=generate_item_code())
    ]

    # Add everything to the session
    db.session.add(control_user)
    db.session.add(player_user1)
    db.session.add(player_user2)
    db.session.add(char)
    db.session.add_all(abilities + conditions + items)
    db.session.commit()

    print("Seed data created successfully.")
