"""
Background monitoring and alerting scheduler for the MODA crypto trading system.
Provides automated threshold checking and system health monitoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import time


class MonitoringScheduler:
    """Background scheduler for automated system monitoring and alerting."""
    
    def __init__(self):
        self.running = False
        self.tasks = []
        self.check_interval = 300  # 5 minutes default
        self.logger = logging.getLogger(__name__)
    
    async def start_monitoring(self):
        """Start the background monitoring loop."""
        if self.running:
            self.logger.warning("Monitoring scheduler already running")
            return
        
        self.running = True
        self.logger.info("Starting background monitoring scheduler")
        
        # Start monitoring tasks
        self.tasks = [
            asyncio.create_task(self._threshold_monitoring_loop()),
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._performance_monitoring_loop())
        ]
        
        try:
            await asyncio.gather(*self.tasks)
        except Exception as e:
            self.logger.error(f"Monitoring scheduler error: {e}")
        finally:
            self.running = False
    
    async def stop_monitoring(self):
        """Stop the background monitoring."""
        self.logger.info("Stopping background monitoring scheduler")
        self.running = False
        
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete cancellation
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks = []
    
    async def _threshold_monitoring_loop(self):
        """Continuously monitor system thresholds and create alerts."""
        self.logger.info("Starting threshold monitoring loop")
        
        while self.running:
            try:
                from ..firestore_client import check_system_thresholds
                
                alerts_created = check_system_thresholds()
                
                if alerts_created:
                    self.logger.warning(f"Threshold monitoring created {len(alerts_created)} alerts")
                    for alert in alerts_created:
                        self.logger.warning(f"Alert: {alert['type']} - {alert.get('service', 'system')}")
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in threshold monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def _health_check_loop(self):
        """Continuously monitor system health."""
        self.logger.info("Starting health check monitoring loop")
        
        while self.running:
            try:
                from ..firestore_client import get_system_health, create_system_alert
                
                health = get_system_health()
                system_status = health.get("status", "unknown")
                
                # Create alerts for degraded systems
                if system_status == "degraded":
                    create_system_alert(
                        alert_type="system_degraded",
                        message="System health is degraded",
                        severity="warning",
                        metadata={"health_data": health}
                    )
                elif system_status == "error":
                    create_system_alert(
                        alert_type="system_error",
                        message="System health check failed",
                        severity="error",
                        metadata={"health_data": health}
                    )
                
                # Monitor individual services
                services = health.get("services", {})
                for service_name, service_data in services.items():
                    service_status = service_data.get("status", "unknown")
                    
                    if service_status == "error":
                        create_system_alert(
                            alert_type="service_error",
                            message=f"Service {service_name} is in error state",
                            severity="error",
                            metadata={"service": service_name, "service_data": service_data}
                        )
                
                # Wait for next health check
                await asyncio.sleep(self.check_interval * 2)  # Health checks every 10 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(60)
    
    async def _performance_monitoring_loop(self):
        """Monitor system performance metrics."""
        self.logger.info("Starting performance monitoring loop")
        
        while self.running:
            try:
                from ..firestore_client import get_performance_metrics, create_system_alert
                
                performance = get_performance_metrics()
                
                # Check for performance issues
                for service_name, metrics in performance.items():
                    avg_duration = metrics.get("avg_duration", 0)
                    error_rate = metrics.get("error_rate", 0)
                    
                    # Alert on high average duration (over 30 seconds)
                    if avg_duration > 30:
                        create_system_alert(
                            alert_type="high_latency",
                            message=f"Service {service_name} has high average duration: {avg_duration:.1f}s",
                            severity="warning",
                            metadata={"service": service_name, "avg_duration": avg_duration}
                        )
                    
                    # Alert on high error rate (over 20%)
                    if error_rate > 0.2:
                        create_system_alert(
                            alert_type="high_error_rate",
                            message=f"Service {service_name} has high error rate: {error_rate:.1%}",
                            severity="error",
                            metadata={"service": service_name, "error_rate": error_rate}
                        )
                
                # Wait for next performance check
                await asyncio.sleep(self.check_interval * 3)  # Performance checks every 15 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in performance monitoring loop: {e}")
                await asyncio.sleep(60)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status."""
        return {
            "running": self.running,
            "active_tasks": len([task for task in self.tasks if not task.done()]),
            "check_interval_seconds": self.check_interval,
            "uptime": datetime.utcnow().isoformat() if self.running else None
        }


# Global scheduler instance
monitoring_scheduler = MonitoringScheduler()


async def start_background_monitoring():
    """Start the background monitoring scheduler."""
    global monitoring_scheduler
    
    if not monitoring_scheduler.running:
        # Start monitoring in background
        asyncio.create_task(monitoring_scheduler.start_monitoring())
        return True
    return False


async def stop_background_monitoring():
    """Stop the background monitoring scheduler."""
    global monitoring_scheduler
    
    if monitoring_scheduler.running:
        await monitoring_scheduler.stop_monitoring()
        return True
    return False


def get_monitoring_status() -> Dict[str, Any]:
    """Get current monitoring scheduler status."""
    global monitoring_scheduler
    return monitoring_scheduler.get_status()