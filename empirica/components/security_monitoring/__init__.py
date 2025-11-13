#!/usr/bin/env python3
"""
🛡️ Security Monitoring Module
Real-time security monitoring and uncertainty-grounded analysis for AI systems
"""

from .security_monitoring import (
    SecurityThreat,
    SecurityMonitoringEngine
)

def create_security_monitor():
    """Create a Security Monitoring Engine instance"""
    return SecurityMonitoringEngine()

def activate_security_monitoring(monitoring_interval: int = 30) -> SecurityMonitoringEngine:
    """
    Activate security monitoring with real-time threat detection
    
    Args:
        monitoring_interval (int): Security check interval in seconds
        
    Returns:
        SecurityMonitoringEngine: Active security monitoring engine
    """
    print("🛡️ ACTIVATING SECURITY MONITORING")
    print("=" * 40)
    print("✅ Real-time threat detection")
    print("✅ System integrity validation") 
    print("✅ Resource usage monitoring")
    print("✅ Uncertainty-grounded analysis")
    
    monitor = SecurityMonitoringEngine(monitoring_interval)
    monitor.activate_monitoring()
    
    return monitor

__all__ = [
    'SecurityThreat',
    'SecurityMonitoringEngine',
    'create_security_monitor',
    'activate_security_monitoring'
]

__version__ = "1.0.0"
__component__ = "security_monitoring"
__purpose__ = "Real-time security monitoring and uncertainty-grounded analysis for AI systems"

print(f"🛡️ Security Monitoring Module ready for AI collaboration!")