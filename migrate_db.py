from app import app, db

def migrate_database():
    with app.app_context():
        # Add the payment amount column
        db.engine.execute('ALTER TABLE booking ADD COLUMN payment_amount FLOAT')
        db.session.commit()

if __name__ == '__main__':
    migrate_database()
    print("Database migration completed successfully!")
