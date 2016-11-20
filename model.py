from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class Mqtt_input(Base):
    __tablename__ = 'mqtt_input'

    topic = Column(String, primary_key=True)
    topic_regexp = Column(String)
    message_regexp = Column(String)
    process_value = Column(String)
    process_time = Column(String)

    def __repr__(self):
        return "<Input(topic='%s', topic_regexp='%s', message_regexp='%s', process_value='%s', process_time='%s')>" % (
                             self.topic, self.topic_regexp, self.message_regexp, self.process_value, self.process_time)

class Rawid_sensorid(Base):
    __tablename__ = 'rawid_sensorid'

    rawid = Column(String, primary_key=True)
    sensorid = Column(Integer)

    def __repr__(self):
        return "<Rawid_sensorid(rawid='%s', sensorid='%s')>" % (self.rawid, self.sensorid)


