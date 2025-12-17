from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    """用户表"""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, user
    password = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<User {self.name}>'

class NetworkInterface(db.Model):
    """网络接口表"""
    __tablename__ = 'network_interfaces'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    ip_address = db.Column(db.String(45))
    mac_address = db.Column(db.String(17))
    status = db.Column(db.String(20))  # up, down
    is_monitored = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<NetworkInterface {self.name}>'

class TrafficStats(db.Model):
    """流量统计表"""
    __tablename__ = 'traffic_stats'
    id = db.Column(db.Integer, primary_key=True)
    interface_id = db.Column(db.Integer, db.ForeignKey('network_interfaces.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    total_packets = db.Column(db.BigInteger, default=0)
    total_bytes = db.Column(db.BigInteger, default=0)
    tcp_packets = db.Column(db.BigInteger, default=0)
    udp_packets = db.Column(db.BigInteger, default=0)
    icmp_packets = db.Column(db.BigInteger, default=0)
    other_packets = db.Column(db.BigInteger, default=0)
    
    interface = db.relationship('NetworkInterface', backref='stats')
    
    def __repr__(self):
        return f'<TrafficStats {self.timestamp}>'

class Alert(db.Model):
    """告警表"""
    __tablename__ = 'alerts'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    alert_type = db.Column(db.String(50), nullable=False)  # high_traffic, suspicious_port
    description = db.Column(db.Text)
    source_ip = db.Column(db.String(45), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, resolved
    resolved_at = db.Column(db.DateTime)
    dst_ip = db.Column(db.String(45))
    src_port = db.Column(db.Integer)
    dst_port = db.Column(db.Integer)
    protocol = db.Column(db.String(20))
    severity = db.Column(db.String(20), default='info')
    category = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<Alert {self.alert_type}>'

class Packet(db.Model):
    """数据包详情表"""
    __tablename__ = 'packets'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    src_ip = db.Column(db.String(45), nullable=False, index=True)
    dst_ip = db.Column(db.String(45), nullable=False, index=True)
    protocol = db.Column(db.String(20), nullable=False, index=True)
    length = db.Column(db.Integer, nullable=False)
    src_port = db.Column(db.Integer)
    dst_port = db.Column(db.Integer)
    flags = db.Column(db.String(20))
    ttl = db.Column(db.Integer)
    src_mac = db.Column(db.String(32))
    dst_mac = db.Column(db.String(32))
    
    def __repr__(self):
        return f'<Packet {self.src_ip} -> {self.dst_ip}>' 