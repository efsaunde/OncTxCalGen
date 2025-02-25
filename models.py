from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Protocol(Base):
    __tablename__ = 'protocols'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    version = Column(String)
    publication_date = Column(String)
    description = Column(Text)
    cancer_type = Column(String)  # New field for cancer type
    subtype = Column(String)  # New field for subtype

    phases = relationship("Phase", back_populates="protocol", cascade="all, delete-orphan")


class Phase(Base):
    __tablename__ = 'phases'
    id = Column(Integer, primary_key=True)
    protocol_id = Column(Integer, ForeignKey('protocols.id'))
    phase_name = Column(String, nullable=False)
    cycle_count = Column(String)
    instructions = Column(Text)

    protocol = relationship("Protocol", back_populates="phases")
    cycles = relationship("Cycle", back_populates="phase", cascade="all, delete-orphan")


class Cycle(Base):
    __tablename__ = 'cycles'
    id = Column(Integer, primary_key=True)
    phase_id = Column(Integer, ForeignKey('phases.id'))
    cycle_name = Column(String)
    cycle_length = Column(String)
    instructions = Column(Text)

    phase = relationship("Phase", back_populates="cycles")
    treatments = relationship("Treatment", back_populates="cycle", cascade="all, delete-orphan")


class Treatment(Base):
    __tablename__ = 'treatments'
    id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, ForeignKey('cycles.id'))
    medication = Column(String)
    dose = Column(String)
    route = Column(String)
    days = Column(String)
    max_duration = Column(String)
    details = Column(Text)

    cycle = relationship("Cycle", back_populates="treatments")