import hashlib
from src.database.db import get_session, User

class UserModel:
    @staticmethod
    def create(username, password):
        """Create a new user"""
        session = get_session()
        try:
            # Check if user already exists
            existing_user = session.query(User).filter_by(username=username).first()
            if existing_user:
                return False
                
            # Create password hash
            password_hash = hashlib.md5(password.encode()).hexdigest()
            
            # Create new user
            user = User(username=username, password_hash=password_hash)
            session.add(user)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error creating user: {e}")
            return False
        finally:
            session.close()

    @staticmethod
    def validate(username, password):
        """Validate user credentials"""
        session = get_session()
        try:
            # Get password hash from database
            user = session.query(User).filter_by(username=username).first()
            
            # Compare hashes
            if user:
                password_hash = hashlib.md5(password.encode()).hexdigest()
                return user.password_hash == password_hash
                
            return False
        except Exception as e:
            print(f"Error validating user: {e}")
            return False
        finally:
            session.close()
    
    @staticmethod
    def update_password(username, new_password):
        """Update user password"""
        session = get_session()
        try:
            # Get user
            user = session.query(User).filter_by(username=username).first()
            if not user:
                return False
                
            # Create password hash and update user
            new_hash = hashlib.md5(new_password.encode()).hexdigest()
            user.password_hash = new_hash
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error updating password: {e}")
            return False
        finally:
            session.close()
    
    @staticmethod
    def get_id(username):
        """Get user ID from username"""
        session = get_session()
        try:
            user = session.query(User).filter_by(username=username).first()
            return user.id if user else None
        except Exception as e:
            print(f"Error getting user ID: {e}")
            return None
        finally:
            session.close()
            return None
