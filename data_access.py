from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from models import User, Session, Message, Feedback
from password import generate_salt,hash_password,check_password

uri = 'sqlite:///C:/ChatBots/test/test.db'
    

class DataAccess:
    def __init__(self, connection_uri=uri):
        self.engine = create_engine(connection_uri, echo=True)
        self.db_Session = sessionmaker(bind=self.engine)
        self.db_session = self.db_Session()

    # Session
    def add_new_session(self,session_serial, username):

        existing_user = self.db_session.query(User).filter_by(userName=username).first()

        if existing_user:
            # Action 1: Create new session
            new_session = Session(serial=session_serial, startAt=datetime.utcnow(), endAt=None, totalCost=0.0, uId=existing_user.uId)
            # Action 2: Add to the database
            self.db_session.add(new_session)
            self.db_session.commit()
            print(f"New session '{session_serial}' added successfully.")
            return new_session.sId
        else:
            print(f"User {username} Not Found")


    def set_total_cost(self,session_id):
        existing_session = self.db_session.query(Session).filter_by(sId=session_id).first()
        if existing_session:
            print("Session Exist -------------------------")
            messages = self.db_session.query(Message).filter_by(sessionId=existing_session.sId).all()
            if messages:
                print("messages Exist -------------------------")

                total_cost = float(0)
                # print(f"total cost before{total_cost} -------------------------")
                total_cost = sum(float(message.cost) for message in messages)
                # print(f"total cost after{total_cost} -------------------------")
                existing_session.totalCost = float(total_cost)
                self.db_session.commit()
                print(f"Total cost for session '{session_id}' is {existing_session.totalCost}.")
                return total_cost
            else:
                print(f"No messages found for session '{session_id}'.")
        else:
            print(f"Session '{session_id}' not found.")  
        
    # def delete_session(self,session_serial):
    #     existing_session = self.db_session.query(Session).filter_by(serial=session_serial).first()
    #     if existing_session:
    #         self.db_session.delete(existing_session)
    #         self.db_session.commit()
    #         print(f"Session '{session_serial}' deleted.")  

    #     else:
    #         print(f"Session '{session_serial}' not found.")  
 






    def end_session(self,session_id):
        # Action 1: Set end time
        existing_session = self.db_session.query(Session).filter_by(sId=session_id).first()

        if existing_session:
            if(existing_session.totalCost > 0):
                existing_session.endAt = datetime.utcnow()
                self.db_session.commit()
                print(f"Session '{session_id}' ended successfully.")
                return existing_session.endAt
            else:
                self.db_session.delete(existing_session)
                self.db_session.commit()
                print(f"Session '{session_id}' deleted.")            

        else:
            print(f"Session '{session_id}' not found.")            


    # Message
    def add_new_message(self,question, answer, resources, cost, session_id):
        # Action 1: Create new message
        existing_session = self.db_session.query(Session).filter_by(sId=session_id).first()

        if existing_session:
            new_message = Message(
                question=question,
                answer=answer,
                resources=resources,
                cost=cost,
                sendAt=datetime.utcnow(),
                sId=existing_session.sId
            )

            # Action 2: Add to the database
            self.db_session.add(new_message)
            self.db_session.commit()
            print(f"New message added successfully to session '{session_id}'.")
            return new_message.mId
        else:
            print(f"Session '{session_id}' not found.")
            return 
        
    def add_feedback(self,description, message_id):
        # Action 1: Create new message
        existing_message = self.db_session.query(Message).filter_by(mId=message_id).first()

        if existing_message:
            new_feedback = Feedback(
                description=description,
                sendAt=datetime.utcnow(),
                mId=existing_message.mId
            )

            # Action 2: Add to the database
            self.db_session.add(new_feedback)
            self.db_session.commit()
            print(f"New feedback added successfully to message '{message_id}'.")
            return True
        else:
            print(f"Message '{message_id}' not found.")
            return False






    # User
    def register_user(self,username, password)-> int:
        # Action 1: Check if the username already exists
        existing_user = self.db_session.query(User).filter_by(userName=username).first()

        if existing_user:
            print(f"Username '{username}' already exists. Please choose a different username.")
            return 0

        # Action 2: Check password length and contain a number
        if len(password) < 8 or not any(char.isdigit() for char in password):
            print("Password must be at least 8 characters long and contain at least one number.")
            return 0

        # Action 3: Generate salt
        salt = generate_salt()

        # Action 4: Hash password using salt
        hashed_password = hash_password(password,salt)

        # Action 5: Add the new user to the database
        new_user = User(
            userName=username,
            salt=salt,
            hashedPassword=hashed_password,
            balance=1,
            usage=0.0,
            previousUsage=0.0,
            requestCount=0,
            requestDate=None
        )

        self.db_session.add(new_user)
        self.db_session.commit()
        print(f"User '{username}' registered successfully.")
        return new_user.uId

    def login_user(self,username, password):
        # Action 1: Check if the username exists
        user = self.db_session.query(User).filter_by(userName=username).first()

        if not user:
            print(f"Username '{username}' not found. Please check your username.")
            return

        # Action 2: Hash the password using the stored salt
        password__status = check_password(password,user)

        # Action 3: Compare the hashed passwords
        if password__status:
            print(f"Login successful for user '{username}'.")
            return user
        else:
            print("Incorrect password. Please check your password.")
            return


    def check_user_balance(self,username)-> bool:
        # Action 1: Get user
        existing_user = self.db_session.query(User).filter_by(userName=username).first()

        if existing_user:
            # Action 2: Check if balance > usage
            if existing_user.balance > existing_user.usage:
                print(f"User '{existing_user.userName}' has a balance greater than their usage.")
                return True
            else:
                print(f"User '{existing_user.userName}' does not have sufficient balance.")
                return False
        else:
            print(f"User Name '{username}' not found.")
            return False



    def increment_user_usage(self,username, increment_amount)-> bool:
        if(increment_amount <= 0):
            print(f"increment amount can't be negative")
            return False
        # Action 1: Get user
        existing_user = self.db_session.query(User).filter_by(userName=username).first()

        if existing_user:
            # Action 2: Add amount to usage
            print("---"*10)
            print(existing_user.usage + increment_amount)
            existing_user.usage += increment_amount
            self.db_session.commit()
            print(f"Usage for '{existing_user.userName}' incremented by {increment_amount} and now {existing_user.usage}.")
            return True

        else:
            print(f"User Name '{username}' not found.")
            return False


    
        

    def request_quota(self,username)-> bool:
        # Action 1: Check balance with usage
        existing_user = self.db_session.query(User).filter_by(userName=username).first()

        if existing_user:
            if existing_user.balance <= existing_user.usage:
                if existing_user.requestDate == None:
                    # Action 2: Set request date and increment request count
                    existing_user.requestDate = datetime.utcnow()
                    existing_user.requestCount += 1
                    self.db_session.commit()
                    print(f"Quota requested successfully for user '{existing_user.userName}'.")
                    return f"Quota requested successfully for user '{existing_user.userName}'."
                else:
                    print(f"User '{existing_user.userName}' already requested quota.")
                    return f"User '{existing_user.userName}'  already requested  quota. Contact with R&D if it urgent"
            else:
                print(f"User '{existing_user.userName}' does not have sufficient balance to request quota.")
                return f"User '{existing_user.userName}' does not have sufficient balance to request quota."
        else:
            print(f"User Name '{username}' not found.")
            return f"User Name '{username}' not found."


    def reset_usage(self,user_id)-> bool:
        # Action 1: Get user
        existing_user = self.db_session.query(User).filter_by(uId=user_id).first()

        
        if existing_user:

            if(self.check_user_balance(user_id)):
            # Action 2: Add amount of usage to previous usage
                existing_user.previousUsage += existing_user.usage
                
                # Action 3: Set usage to 0
                existing_user.usage = 0.0
                
                # Action 4: Set request date to none
                existing_user.requestDate = None
                
                self.db_session.commit()
                print(f"Usage reset successfully for user '{existing_user.userName}'.")
                return True
        
        print(f"User with ID '{user_id}' not found.")
        return False

