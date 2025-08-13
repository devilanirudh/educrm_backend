"""
Transportation management database models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, Time, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base


class BusRoute(Base):
    """Bus routes for school transportation"""
    __tablename__ = "bus_routes"
    
    id = Column(Integer, primary_key=True, index=True)
    route_name = Column(String(100), nullable=False, unique=True)
    route_number = Column(String(20), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Route details
    start_location = Column(String(200), nullable=False)
    end_location = Column(String(200), nullable=False)
    total_distance_km = Column(Float, nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)
    
    # Schedule
    morning_start_time = Column(Time, nullable=True)
    morning_end_time = Column(Time, nullable=True)
    evening_start_time = Column(Time, nullable=True)
    evening_end_time = Column(Time, nullable=True)
    
    # Capacity and pricing
    max_capacity = Column(Integer, nullable=False, default=50)
    current_occupancy = Column(Integer, nullable=False, default=0)
    monthly_fee = Column(Float, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    stops = relationship("BusStop", back_populates="route", cascade="all, delete-orphan")
    buses = relationship("Bus", back_populates="route")
    students = relationship("Student", foreign_keys="Student.bus_route_id", back_populates="bus_route")
    tracking_logs = relationship("BusTracking", back_populates="route", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BusRoute(id={self.id}, name='{self.route_name}', number='{self.route_number}')>"


class BusStop(Base):
    """Bus stops along routes"""
    __tablename__ = "bus_stops"
    
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("bus_routes.id"), nullable=False)
    stop_name = Column(String(100), nullable=False)
    address = Column(Text, nullable=True)
    
    # Location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    landmark = Column(String(200), nullable=True)
    
    # Schedule
    morning_arrival_time = Column(Time, nullable=True)
    morning_departure_time = Column(Time, nullable=True)
    evening_arrival_time = Column(Time, nullable=True)
    evening_departure_time = Column(Time, nullable=True)
    
    # Stop details
    stop_order = Column(Integer, nullable=False)  # Order in the route
    distance_from_previous_km = Column(Float, nullable=True)
    is_pickup_point = Column(Boolean, default=True, nullable=False)
    is_drop_point = Column(Boolean, default=True, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    route = relationship("BusRoute", back_populates="stops")
    pickup_assignments = relationship("StudentBusStop", foreign_keys="StudentBusStop.pickup_stop_id", cascade="all, delete-orphan")
    drop_assignments = relationship("StudentBusStop", foreign_keys="StudentBusStop.drop_stop_id", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BusStop(id={self.id}, name='{self.stop_name}', route_id={self.route_id})>"


class Bus(Base):
    """School buses"""
    __tablename__ = "buses"
    
    id = Column(Integer, primary_key=True, index=True)
    bus_number = Column(String(20), nullable=False, unique=True)
    registration_number = Column(String(50), nullable=False, unique=True)
    route_id = Column(Integer, ForeignKey("bus_routes.id"), nullable=True)
    
    # Bus details
    make = Column(String(50), nullable=True)
    model = Column(String(50), nullable=True)
    year = Column(Integer, nullable=True)
    color = Column(String(30), nullable=True)
    seating_capacity = Column(Integer, nullable=False)
    
    # Insurance and documents
    insurance_number = Column(String(100), nullable=True)
    insurance_expiry = Column(Date, nullable=True)
    fitness_certificate_expiry = Column(Date, nullable=True)
    pollution_certificate_expiry = Column(Date, nullable=True)
    
    # Maintenance
    last_service_date = Column(Date, nullable=True)
    next_service_date = Column(Date, nullable=True)
    last_service_odometer = Column(Integer, nullable=True)
    current_odometer = Column(Integer, nullable=True)
    
    # GPS tracking
    gps_device_id = Column(String(100), nullable=True)
    has_gps = Column(Boolean, default=False, nullable=False)
    
    # Status
    status = Column(String(20), nullable=False, default="active")  # active, maintenance, retired
    is_available = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    route = relationship("BusRoute", back_populates="buses")
    drivers = relationship("Driver", back_populates="assigned_bus")
    tracking_logs = relationship("BusTracking", back_populates="bus", cascade="all, delete-orphan")
    maintenance_records = relationship("BusMaintenanceRecord", back_populates="bus", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Bus(id={self.id}, number='{self.bus_number}', registration='{self.registration_number}')>"


class Driver(Base):
    """Bus drivers"""
    __tablename__ = "drivers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    employee_id = Column(String(50), unique=True, nullable=False)
    assigned_bus_id = Column(Integer, ForeignKey("buses.id"), nullable=True)
    
    # License information
    license_number = Column(String(50), nullable=False)
    license_type = Column(String(20), nullable=False)  # commercial, heavy_vehicle, etc.
    license_expiry = Column(Date, nullable=False)
    
    # Experience and training
    years_experience = Column(Integer, nullable=True)
    hire_date = Column(Date, nullable=False)
    last_training_date = Column(Date, nullable=True)
    next_training_due = Column(Date, nullable=True)
    
    # Emergency contact
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    
    # Medical fitness
    medical_certificate_expiry = Column(Date, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    assigned_bus = relationship("Bus", back_populates="drivers")
    driving_logs = relationship("DrivingLog", back_populates="driver", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Driver(id={self.id}, employee_id='{self.employee_id}', license='{self.license_number}')>"


class StudentBusStop(Base):
    """Student assignments to bus stops"""
    __tablename__ = "student_bus_stops"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    pickup_stop_id = Column(Integer, ForeignKey("bus_stops.id"), nullable=False)
    drop_stop_id = Column(Integer, ForeignKey("bus_stops.id"), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    student = relationship("Student")
    pickup_stop = relationship("BusStop", foreign_keys=[pickup_stop_id])
    drop_stop = relationship("BusStop", foreign_keys=[drop_stop_id])
    
    def __repr__(self):
        return f"<StudentBusStop(student_id={self.student_id}, pickup_stop_id={self.pickup_stop_id})>"


class BusTracking(Base):
    """Real-time bus tracking logs"""
    __tablename__ = "bus_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=False)
    route_id = Column(Integer, ForeignKey("bus_routes.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    
    # Location data
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed_kmh = Column(Float, nullable=True)
    heading = Column(Float, nullable=True)  # Direction in degrees
    
    # Trip information
    trip_type = Column(String(20), nullable=False)  # morning, evening
    trip_status = Column(String(20), nullable=False)  # started, in_progress, completed, delayed
    
    # Timing
    timestamp = Column(DateTime(timezone=True), nullable=False)
    estimated_arrival = Column(DateTime(timezone=True), nullable=True)
    
    # Additional data
    fuel_level = Column(Float, nullable=True)
    engine_status = Column(String(20), nullable=True)  # running, stopped, idle
    passenger_count = Column(Integer, nullable=True)
    
    # Alerts
    alert_type = Column(String(50), nullable=True)  # speeding, route_deviation, breakdown, etc.
    alert_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    bus = relationship("Bus", back_populates="tracking_logs")
    route = relationship("BusRoute", back_populates="tracking_logs")
    driver = relationship("Driver")
    
    def __repr__(self):
        return f"<BusTracking(id={self.id}, bus_id={self.bus_id}, lat={self.latitude}, lng={self.longitude})>"


class DrivingLog(Base):
    """Driver daily logs and performance tracking"""
    __tablename__ = "driving_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=False)
    date = Column(Date, nullable=False)
    
    # Trip details
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    start_odometer = Column(Integer, nullable=True)
    end_odometer = Column(Integer, nullable=True)
    total_distance_km = Column(Float, nullable=True)
    
    # Performance metrics
    fuel_consumed_liters = Column(Float, nullable=True)
    average_speed_kmh = Column(Float, nullable=True)
    max_speed_kmh = Column(Float, nullable=True)
    harsh_braking_count = Column(Integer, default=0, nullable=False)
    harsh_acceleration_count = Column(Integer, default=0, nullable=False)
    
    # Trip type and routes
    trip_type = Column(String(20), nullable=False)  # morning, evening, special
    routes_covered = Column(Text, nullable=True)  # JSON list of route IDs
    
    # Issues and incidents
    incidents = Column(Text, nullable=True)
    vehicle_issues = Column(Text, nullable=True)
    passenger_issues = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="completed")  # in_progress, completed, cancelled
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    driver = relationship("Driver", back_populates="driving_logs")
    bus = relationship("Bus")
    
    def __repr__(self):
        return f"<DrivingLog(id={self.id}, driver_id={self.driver_id}, date={self.date})>"


class BusMaintenanceRecord(Base):
    """Bus maintenance and service records"""
    __tablename__ = "bus_maintenance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=False)
    
    # Maintenance details
    maintenance_type = Column(String(50), nullable=False)  # routine, repair, inspection, etc.
    description = Column(Text, nullable=False)
    service_date = Column(Date, nullable=False)
    next_service_due = Column(Date, nullable=True)
    
    # Service provider
    service_provider = Column(String(200), nullable=True)
    mechanic_name = Column(String(100), nullable=True)
    
    # Cost and parts
    labor_cost = Column(Float, nullable=True)
    parts_cost = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    parts_replaced = Column(Text, nullable=True)  # JSON list of parts
    
    # Vehicle condition
    odometer_reading = Column(Integer, nullable=True)
    condition_before = Column(String(50), nullable=True)  # excellent, good, fair, poor
    condition_after = Column(String(50), nullable=True)
    
    # Documentation
    invoice_number = Column(String(100), nullable=True)
    receipt_path = Column(String(500), nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="completed")  # scheduled, in_progress, completed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    bus = relationship("Bus", back_populates="maintenance_records")
    
    def __repr__(self):
        return f"<BusMaintenanceRecord(id={self.id}, bus_id={self.bus_id}, type='{self.maintenance_type}')>"


class TransportAlert(Base):
    """Transportation alerts and notifications"""
    __tablename__ = "transport_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), nullable=False)  # delay, breakdown, route_change, cancellation
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Affected entities
    route_ids = Column(Text, nullable=True)  # JSON list of affected route IDs
    bus_ids = Column(Text, nullable=True)  # JSON list of affected bus IDs
    stop_ids = Column(Text, nullable=True)  # JSON list of affected stop IDs
    
    # Timing
    alert_date = Column(Date, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    severity = Column(String(20), nullable=False, default="medium")  # low, medium, high, critical
    is_active = Column(Boolean, default=True, nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False)
    
    # Created by
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    creator = relationship("User")
    
    def __repr__(self):
        return f"<TransportAlert(id={self.id}, type='{self.alert_type}', severity='{self.severity}')>"
