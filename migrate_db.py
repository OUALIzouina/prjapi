from app import app, db

def migrate_database():
    with app.app_context():
        # Add provider payment columns
        db.engine.execute('ALTER TABLE booking ADD COLUMN provider_payment FLOAT')
        db.engine.execute('ALTER TABLE booking ADD COLUMN provider_payment_status VARCHAR(20) DEFAULT "pending"')
        db.engine.execute('ALTER TABLE booking ADD COLUMN platform_fee_percentage FLOAT DEFAULT 20')
        db.session.commit()

if __name__ == '__main__':
    migrate_database()
    print("Database migration completed successfully!")
