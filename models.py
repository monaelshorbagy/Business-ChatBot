from sqlalchemy import create_engine, ForeignKey, Column,Numeric, String, Integer, DECIMAL, DateTime,FLOAT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
Base = declarative_base()

db_uri  = 'sqlite:///C:/Users/mona.elshorbagy/Documents/business-chatbot/Business-Chatbot/test.db'

class User(Base): 
    __tablename__ ="users"
    uId = Column("uId",Integer,primary_key=True,autoincrement=True)
    userName = Column("userName",String(length=255),unique=True,nullable=False)
    salt = Column("salt",String)
    hashedPassword = Column("hashedPassword",String)
    balance = Column("balance",FLOAT)
    usage = Column("usage",FLOAT)
    previousUsage  = Column("previousUsage",FLOAT)
    requestDate = Column("requestDate", DateTime,nullable=True)
    requestCount = Column("requestCount", Integer)
    sessions = relationship("Session", back_populates="user")

    def __init__(self, userName, salt, hashedPassword, balance= 1.0, usage= 0,previousUsage = 0,requestCount = 0,requestDate = None ):
        self.userName = userName
        self.salt = salt
        self.hashedPassword = hashedPassword
        self.balance = balance
        self.usage = usage
        self.previousUsage = previousUsage
        self.requestCount = requestCount
        self.requestDate = requestDate 

    def __repr__(self):
        return f"<User(uId={self.uId}, userName={self.userName}, balance={self.balance}, usage={self.usage}, requestDate={self.requestDate}, requestCount={self.requestCount})>"




class Session(Base):
    __tablename__ ="sessions"
    sId = Column("sId",Integer,primary_key=True,autoincrement=True)
    serial = Column("serial",String(length=255),nullable=False)
    startAt = Column("startAt",DateTime)
    endAt = Column("endAt",DateTime,nullable=True)
    totalCost = Column("totalCost",FLOAT)
    userId = Column(Integer,ForeignKey("users.uId"))
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session")

    def __init__(self, serial, startAt,uId,endAt = None,totalCost=0 ):
        self.serial = serial
        self.startAt = startAt
        self.endAt = endAt
        self.totalCost = totalCost
        self.userId = uId

    def __repr__(self):
        return f"<Session(sId={self.sId}, serial={self.serial}, startAt={self.startAt}, endAt={self.endAt}, totalCost={self.totalCost}, user={self.user.userName})>"


class Message(Base):
    __tablename__ ="messages"
    mId = Column("mId",Integer,primary_key=True,autoincrement=True)
    question  = Column("question",String)
    answer  = Column("answer",String)
    resources  = Column("resources",String)
    sendAt = Column("sendAt",DateTime)
    cost = Column("cost",FLOAT)
    sessionId = Column(Integer,ForeignKey("sessions.sId"))
    session = relationship("Session", back_populates="messages")
    feedback = relationship("Feedback", uselist=False, back_populates="message")


    def __init__(self, question, answer, resources, cost, sId,sendAt = datetime.utcnow()):
        self.question = question
        self.answer = answer
        self.resources = resources
        self.sendAt = sendAt
        self.cost = cost
        self.sessionId = sId

def __repr__(self):
        return f"<Message(mId={self.mId}, Question={self.question}, Answer={self.answer}, resources={self.resources}, sendAt={self.sendAt}, cost={self.cost}, sessionId={self.sessionId} )>"


class Feedback(Base):
    __tablename__ ="feedback"
    fId = Column("fId",Integer,primary_key=True,autoincrement=True)
    description  = Column("description",String)
    sendAt = Column("sendAt",DateTime)
    messageId = Column(Integer,ForeignKey("messages.mId"))
    message = relationship("Message", back_populates="feedback")

    def __init__(self, description, mId,sendAt = datetime.utcnow()):
        self.description = description
        self.sendAt = sendAt
        self.messageId = mId

def __repr__(self):
        return f"<Message(fId={self.fId}, Description={self.description}, sendAt={self.sendAt}, messageId={self.messageId} )>"


engine = create_engine(db_uri, echo=True)
Base.metadata.create_all(bind= engine)