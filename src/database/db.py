import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from dotenv import load_dotenv
import pandas as pd
import hashlib
from datetime import datetime

load_dotenv()

# Database connection settings
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_NAME = os.getenv("DB_NAME", "stockapp")
DB_USER = os.getenv("DB_USER", "stockuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "stockpassword")
DB_PORT = os.getenv("DB_PORT", "5432")

# Create engine
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# Create base model
Base = declarative_base()

# Define models
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")

class Portfolio(Base):
    __tablename__ = 'portfolio'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    ticker = Column(String(20), nullable=False)
    shares = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    purchase_date = Column(Date, nullable=False)
    
    user = relationship("User", back_populates="portfolios")
    
    __table_args__ = (UniqueConstraint('user_id', 'ticker', name='_user_ticker_uc'),)

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    ticker = Column(String(20), nullable=False)
    order_type = Column(String(10), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())
    status = Column(String(20), default='pending')
    
    user = relationship("User", back_populates="orders")

# Create session
Session = scoped_session(sessionmaker(bind=engine))

def init_db():
    """Initialize database and create tables"""
    try:
        Base.metadata.create_all(engine)
        print("Database initialized successfully")
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

def get_session():
    """Get a new database session"""
    return Session()

def release_connection(conn):
    """Release a connection back to the pool"""
    if connection_pool is not None:
        connection_pool.putconn(conn)

def migrate_data_from_csv():
    """Migrate data from CSV files to database"""
    import pandas as pd
    import os
    from datetime import datetime
    
    session = get_session()
    
    try:
        # Migrate users
        if os.path.exists("users.csv"):
            users_df = pd.read_csv("users.csv")
            for _, row in users_df.iterrows():
                # Check if user already exists
                existing_user = session.query(User).filter_by(username=row['username']).first()
                if existing_user:
                    continue
                    
                # Create new user
                user = User(username=row['username'], password_hash=row['password_hash'])
                session.add(user)
            
            session.commit()
        
        # Migrate portfolios
        # First find all portfolio CSV files
        portfolio_files = [f for f in os.listdir() if f.startswith("portfolio_") and f.endswith(".csv")]
        
        for file in portfolio_files:
            # Extract username from filename
            username = file.replace("portfolio_", "").replace(".csv", "")
            
            # Get user
            user = session.query(User).filter_by(username=username).first()
            if not user:
                continue
                
            # Read portfolio data
            try:
                portfolio_df = pd.read_csv(file)
                for _, row in portfolio_df.iterrows():
                    if 'Ticker' in row and pd.notna(row['Ticker']):
                        # Check if this holding already exists
                        existing = session.query(Portfolio).filter_by(
                            user_id=user.id, ticker=row['Ticker']
                        ).first()
                        
                        if existing:
                            continue
                            
                        # Parse purchase date
                        purchase_date = datetime.now()
                        if 'Kaufdatum' in row and pd.notna(row['Kaufdatum']):
                            try:
                                purchase_date = datetime.strptime(row['Kaufdatum'], '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                try:
                                    purchase_date = datetime.strptime(row['Kaufdatum'], '%Y-%m-%d')
                                except ValueError:
                                    pass
                        
                        # Create portfolio entry
                        portfolio_entry = Portfolio(
                            user_id=user.id,
                            ticker=row['Ticker'],
                            shares=float(row['Anteile']) if pd.notna(row['Anteile']) else 0.0,
                            entry_price=float(row['Einstiegspreis']) if pd.notna(row['Einstiegspreis']) else 0.0,
                            purchase_date=purchase_date
                        )
                        session.add(portfolio_entry)
            except Exception as e:
                print(f"Error migrating portfolio {file}: {e}")
                
        # Migrate orders
        if os.path.exists("orders.csv"):
            try:
                orders_df = pd.read_csv("orders.csv")
                for _, row in orders_df.iterrows():
                    if 'username' in row and pd.notna(row['username']):
                        # Get user
                        user = session.query(User).filter_by(username=row['username']).first()
                        if not user:
                            continue
                            
                        # Parse created_at
                        created_at = datetime.now()
                        if 'created_at' in row and pd.notna(row['created_at']):
                            try:
                                created_at = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                pass
                                
                        # Create order
                        order = Order(
                            user_id=user.id,
                            ticker=row['ticker'],
                            order_type=row['order_type'],
                            price=float(row['price']),
                            quantity=float(row['quantity']),
                            created_at=created_at,
                            status=row.get('status', 'completed')
                        )
                        session.add(order)
            except Exception as e:
                print(f"Error migrating orders: {e}")
                
        session.commit()
        print("Data migration completed successfully")
        return True
    except Exception as e:
        session.rollback()
        print(f"Error during data migration: {e}")
        return False
    finally:
        session.close()
        users_df = pd.read_csv("users.csv")
        with get_connection() as conn:
            with conn.cursor() as cur:
                for _, row in users_df.iterrows():
                    cur.execute(
                        "INSERT INTO users (username, password_hash) VALUES (%s, %s) ON CONFLICT (username) DO NOTHING",
                        (row['username'], row['password_hash'])
                    )
                conn.commit()
    
    # Migrate portfolios
    csv_files = [f for f in os.listdir('.') if f.startswith('portfolio_') and f.endswith('.csv')]
    
    for file in csv_files:
        username = file.replace('portfolio_', '').replace('.csv', '')
        
        # Get user ID
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                result = cur.fetchone()
                
                if not result:
                    continue
                
                user_id = result[0]
                
                # Import portfolio
                portfolio_df = pd.read_csv(file, parse_dates=["Kaufdatum"])
                
                for _, row in portfolio_df.iterrows():
                    cur.execute(
                        """
                        INSERT INTO portfolio (user_id, ticker, shares, entry_price, purchase_date) 
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (user_id, ticker) DO UPDATE SET
                            shares = EXCLUDED.shares,
                            entry_price = EXCLUDED.entry_price,
                            purchase_date = EXCLUDED.purchase_date
                        """,
                        (user_id, row['Ticker'], row['Anteile'], row['Einstiegspreis'], row['Kaufdatum'])
                    )
                
                conn.commit()
    
    # Migrate orders
    if os.path.exists("orders.csv"):
        orders_df = pd.read_csv("orders.csv")
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                for _, row in orders_df.iterrows():
                    # Get user ID
                    cur.execute("SELECT id FROM users WHERE username = %s", (row['username'],))
                    result = cur.fetchone()
                    
                    if not result:
                        continue
                    
                    user_id = result[0]
                    
                    cur.execute(
                        """
                        INSERT INTO orders 
                        (user_id, ticker, order_type, price, quantity, created_at, status) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            user_id, row['ticker'], row['order_type'], 
                            row['price'], row['quantity'], row['created_at'], row['status']
                        )
                    )
                
                conn.commit()
