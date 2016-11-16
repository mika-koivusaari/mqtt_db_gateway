from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class Mqtt_input(Base):
    __tablename__ = 'mqtt_input'

    topic = Column(String, primary_key=True)
    topic_regexp = Column(String)
    message_regexp = Column(String)
    process = Column(String)

    def __repr__(self):
        return "<Input(topic='%s', topic_regexp='%s', message_regexp='%s', process='%s')>" % (
                             self.topic, self.topic.regexp, self.message_regexp, self.process)
