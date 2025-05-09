import os
from openpyxl import load_workbook
from app import create_app, db
from app.models import Item, Ability, Condition, Display, User
from werkzeug.security import generate_password_hash


app = create_app()

def get_cell(row, i):
    return str(row[i].value).strip() if row[i].value else ""

def populate_from_excel(filename):
    wb = load_workbook(filename)
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Items
        if 'Items' in wb.sheetnames:
            for row in list(wb['Items'].iter_rows(min_row=2)):
                db.session.add(Item(
                    name=get_cell(row, 0),
                    description=get_cell(row, 1),
                    code=get_cell(row, 2) or None
                ))

        # Abilities
        if 'Abilities' in wb.sheetnames:
            for row in list(wb['Abilities'].iter_rows(min_row=2)):
                db.session.add(Ability(
                    name=get_cell(row, 0),
                    description=get_cell(row, 1)
                ))

        # Conditions
        if 'Conditions' in wb.sheetnames:
            for row in list(wb['Conditions'].iter_rows(min_row=2)):
                db.session.add(Condition(
                    name=get_cell(row, 0),
                    effect=get_cell(row, 1)
                ))

        # Displays
        if 'Displays' in wb.sheetnames:
            for row in list(wb['Displays'].iter_rows(min_row=2)):
                db.session.add(Display(
                    name=get_cell(row, 0),
                    location=get_cell(row, 1),
                    message=get_cell(row, 2),
                    alert_level=get_cell(row, 3) or 'Nominal',
                    animation_mode=get_cell(row, 4) or 'pulse'
                ))

        # Users
        if 'Users' in wb.sheetnames:
            for row in list(wb['Users'].iter_rows(min_row=2)):
                username = get_cell(row, 0)
                email = get_cell(row, 1)
                raw_password = get_cell(row, 2)
                role = get_cell(row, 3) or 'Player'
                theme = get_cell(row, 4) or 'theme-green'

                if username and email and raw_password:
                    hashed_password = generate_password_hash(raw_password)
                    db.session.add(User(
                        username=username,
                        email=email,
                        password=hashed_password,
                        role=role,
                        theme=theme,
                        is_verified=True
                    ))


        db.session.commit()
        print("Seed data loaded successfully.")

if __name__ == '__main__':
    populate_from_excel('C:/Users/Matt/Documents/Redshift/seed_data.xlsx')
