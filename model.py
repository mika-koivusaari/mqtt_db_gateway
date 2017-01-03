from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, DECIMAL

Base = declarative_base()


class MqttInput(Base):
    __tablename__ = 'mqtt_input'

    PROCESS_TYPE_EXPRESSION = 1
    PROCESS_TYPE_FORMAT = 2
    PROCESS_TYPE_EXEC = 3

    topic = Column(String, primary_key=True)
    topic_regexp = Column(String)
    message_regexp = Column(String)
    process_value = Column(String)
    process_value_type = Column(Integer)
    process_time = Column(String)
    process_time_type = Column(Integer)

    def __repr__(self):
        return "<Input(topic='%s', topic_regexp='%s', message_regexp='%s', process_value='%s', process_time='%s')>" % (
            self.topic, self.topic_regexp, self.message_regexp, self.process_value, self.process_time)


class RawidSensorid(Base):
    __tablename__ = 'rawid_sensorid'

    rawid = Column(String, primary_key=True)
    sensorid = Column(Integer)

    def __repr__(self):
        return "<RawidSensorid(rawid='%s', sensorid='%s')>" % (self.rawid, self.sensorid)


class Data(Base):
    __tablename__ = 'data'

    sensorid = Column(Integer, primary_key=True)
    time = Column(DateTime, primary_key=True)
    value = Column(DECIMAL)

    def __repr__(self):
        return "<Data(sensorid='%s', time='%s', value='%s')>" % (self.sensorid, self.time, self.value)

class DataText(Base):
    __tablename__ = 'datatext'

    sensorid = Column(Integer, primary_key=True)
    time = Column(DateTime, primary_key=True)
    text = Column(String)

    def __repr__(self):
        return "<DataText(sensorid='%s', time='%s', text='%s')>" % (self.sensorid, self.time, self.text)
