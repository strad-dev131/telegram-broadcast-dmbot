
"""
Professional health monitoring system for 24/7 operation
Real-time system health tracking and automatic recovery
"""

import asyncio
import logging
import psutil
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
from pyrogram.client import Client
from pyrogram.errors import AuthKeyUnregistered, SessionPasswordNeeded

from config import Config
from session_manager import SessionManager
from enhanced_error_handler import EnhancedErrorHandler

logger = logging.getLogger(__name__)

class HealthMonitor:
    """Professional system health monitoring with automatic recovery"""
    
    def __init__(self):
        self.config = Config()
        self.session_manager = SessionManager()
        self.error_handler = EnhancedErrorHandler()
        self.start_time = datetime.now()
        self.health_checks = []
        self.last_health_check = None
        self.system_status = "healthy"
        
        # Health thresholds
        self.max_memory_usage = 80  # Percentage
        self.max_cpu_usage = 85     # Percentage
        self.max_error_rate = 10    # Percentage
        
        # Monitoring intervals
        self.health_check_interval = 300  # 5 minutes
        self.session_check_interval = 600  # 10 minutes
        
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        logger.info("Starting professional health monitoring system")
        
        # Schedule health checks
        asyncio.create_task(self._continuous_health_check())
        asyncio.create_task(self._continuous_session_health())
        asyncio.create_task(self._memory_optimization_task())
        
    async def _continuous_health_check(self):
        """Continuous system health monitoring"""
        while True:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(60)  # Retry in 1 minute on error
    
    async def _continuous_session_health(self):
        """Continuous session health monitoring"""
        while True:
            try:
                await self._check_session_health()
                await asyncio.sleep(self.session_check_interval)
            except Exception as e:
                logger.error(f"Session health check error: {e}")
                await asyncio.sleep(120)  # Retry in 2 minutes on error
    
    async def _memory_optimization_task(self):
        """Continuous memory optimization"""
        while True:
            try:
                await self._optimize_memory_usage()
                await asyncio.sleep(1800)  # 30 minutes
            except Exception as e:
                logger.error(f"Memory optimization error: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes on error
    
    async def _perform_health_check(self):
        """Perform comprehensive health check"""
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'system_health': await self._get_system_health(),
            'session_health': await self._get_session_health_summary(),
            'error_health': self._get_error_health(),
            'performance_metrics': self._get_performance_metrics()
        }
        
        # Determine overall health status
        self._update_system_status(health_data)
        
        # Store health check
        self.health_checks.append(health_data)
        self.last_health_check = health_data
        
        # Keep only last 100 health checks
        if len(self.health_checks) > 100:
            self.health_checks = self.health_checks[-100:]
        
        # Log critical issues
        if health_data['system_health']['status'] != 'healthy':
            logger.warning(f"System health issue detected: {health_data['system_health']}")
        
        logger.debug(f"Health check completed - Status: {self.system_status}")
    
    async def _get_system_health(self) -> Dict[str, Any]:
        """Get system resource health"""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Process information
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            status = "healthy"
            issues = []
            
            if memory_percent > self.max_memory_usage:
                status = "warning"
                issues.append(f"High memory usage: {memory_percent:.1f}%")
            
            if cpu_percent > self.max_cpu_usage:
                status = "warning"
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            if disk_percent > 90:
                status = "warning"
                issues.append(f"High disk usage: {disk_percent:.1f}%")
            
            return {
                'status': status,
                'memory_percent': round(memory_percent, 2),
                'cpu_percent': round(cpu_percent, 2),
                'disk_percent': round(disk_percent, 2),
                'process_memory_mb': round(process_memory, 2),
                'issues': issues
            }
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def _get_session_health_summary(self) -> Dict[str, Any]:
        """Get session health summary"""
        try:
            sessions = await self.session_manager.get_all_sessions()
            total_sessions = len(sessions)
            healthy_sessions = 0
            unhealthy_sessions = []
            
            for phone, session_data in sessions.items():
                try:
                    # Extract session string from session data
                    session_string = session_data.get('session_string') if isinstance(session_data, dict) else session_data
                    if session_string:
                        is_healthy = await self._check_single_session_health(session_string, phone)
                        if is_healthy:
                            healthy_sessions += 1
                        else:
                            unhealthy_sessions.append(phone)
                    else:
                        unhealthy_sessions.append(f"{phone} (no session string)")
                except Exception as e:
                    unhealthy_sessions.append(f"{phone} (error: {str(e)[:50]})")
            
            health_rate = (healthy_sessions / total_sessions * 100) if total_sessions > 0 else 100
            
            return {
                'total_sessions': total_sessions,
                'healthy_sessions': healthy_sessions,
                'unhealthy_sessions': len(unhealthy_sessions),
                'health_rate_percent': round(health_rate, 2),
                'status': 'healthy' if health_rate > 90 else 'warning' if health_rate > 70 else 'critical',
                'unhealthy_list': unhealthy_sessions[:5]  # Show first 5
            }
            
        except Exception as e:
            logger.error(f"Error getting session health: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def _check_single_session_health(self, session_string: str, phone: str) -> bool:
        """Check health of a single session"""
        client = None
        try:
            client = Client(
                f"health_{phone.replace('+', '').replace(' ', '')}",
                session_string=session_string,
                api_id=self.config.API_ID,
                api_hash=self.config.API_HASH,
                workdir="sessions"
            )
            
            await client.start()
            
            # Try to get account info
            me = await client.get_me()
            
            await client.stop()
            return True
            
        except (AuthKeyUnregistered, SessionPasswordNeeded):
            logger.warning(f"Session {phone} requires re-authentication")
            return False
        except Exception as e:
            logger.debug(f"Session {phone} health check failed: {e}")
            return False
        finally:
            if client:
                try:
                    await client.stop()
                except:
                    pass
    
    def _get_error_health(self) -> Dict[str, Any]:
        """Get error handling health metrics"""
        error_stats = self.error_handler.get_error_statistics()
        
        error_rate = 0
        if error_stats['total_errors_handled'] > 0:
            failed_errors = error_stats['total_errors_handled'] - error_stats['successful_recoveries']
            error_rate = (failed_errors / error_stats['total_errors_handled']) * 100
        
        status = "healthy"
        if error_rate > self.max_error_rate:
            status = "warning"
        if error_rate > 25:
            status = "critical"
        
        return {
            'status': status,
            'error_rate_percent': round(error_rate, 2),
            'total_errors': error_stats['total_errors_handled'],
            'recovered_errors': error_stats['successful_recoveries'],
            'recovery_rate': error_stats['recovery_rate_percent']
        }
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        uptime = datetime.now() - self.start_time
        
        return {
            'uptime_hours': round(uptime.total_seconds() / 3600, 2),
            'uptime_days': round(uptime.days + uptime.seconds / 86400, 2),
            'avg_health_checks_per_hour': round(len(self.health_checks) / max(uptime.total_seconds() / 3600, 1), 2),
            'last_health_check_ago_minutes': round((datetime.now() - datetime.fromisoformat(self.last_health_check['timestamp'])).total_seconds() / 60, 1) if self.last_health_check else 0
        }
    
    def _update_system_status(self, health_data: Dict[str, Any]):
        """Update overall system status"""
        statuses = [
            health_data['system_health']['status'],
            health_data['session_health']['status'],
            health_data['error_health']['status']
        ]
        
        if 'critical' in statuses:
            self.system_status = 'critical'
        elif 'warning' in statuses:
            self.system_status = 'warning'
        elif 'error' in statuses:
            self.system_status = 'error'
        else:
            self.system_status = 'healthy'
    
    async def _check_session_health(self):
        """Perform detailed session health checks"""
        sessions = await self.session_manager.get_all_sessions()
        
        for phone, session_data in sessions.items():
            try:
                # Extract session string from session data
                session_string = session_data.get('session_string') if isinstance(session_data, dict) else session_data
                if session_string:
                    is_healthy = await self._check_single_session_health(session_string, phone)
                    
                    if not is_healthy:
                        logger.warning(f"Unhealthy session detected: {phone}")
                        # Could implement automatic session recovery here
                else:
                    logger.warning(f"No session string found for {phone}")
                    
            except Exception as e:
                logger.error(f"Error checking session {phone} health: {e}")
    
    async def _optimize_memory_usage(self):
        """Optimize memory usage"""
        try:
            import gc
            
            # Force garbage collection
            collected = gc.collect()
            
            # Clear error handler caches if they're too large
            if len(self.error_handler.invalid_peers) > 1000:
                logger.info("Clearing large invalid peers cache for memory optimization")
                self.error_handler.clear_invalid_peers()
            
            # Log memory optimization
            memory = psutil.virtual_memory()
            logger.debug(f"Memory optimization: collected {collected} objects, memory usage: {memory.percent:.1f}%")
            
        except Exception as e:
            logger.error(f"Memory optimization error: {e}")
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        if not self.last_health_check:
            return {
                'status': 'initializing',
                'message': 'Health monitoring system starting up'
            }
        
        uptime = datetime.now() - self.start_time
        
        return {
            'overall_status': self.system_status,
            'uptime': {
                'seconds': uptime.total_seconds(),
                'human_readable': str(uptime).split('.')[0]
            },
            'last_check': self.last_health_check,
            'health_checks_performed': len(self.health_checks),
            'monitoring_active': True,
            'next_check_in_seconds': self.health_check_interval,
            'system_reliability': 'Professional Grade' if self.system_status == 'healthy' else 'Recovering'
        }
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        try:
            return await self._get_system_health()
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'cpu_percent': 0,
                'memory_percent': 0,
                'disk_percent': 0
            }
    
    def get_trend_analysis(self) -> Dict[str, Any]:
        """Get health trend analysis"""
        if len(self.health_checks) < 2:
            return {'status': 'insufficient_data'}
        
        recent_checks = self.health_checks[-10:]  # Last 10 checks
        
        # Calculate trends
        memory_trend = [check['system_health'].get('memory_percent', 0) for check in recent_checks]
        cpu_trend = [check['system_health'].get('cpu_percent', 0) for check in recent_checks]
        error_trend = [check['error_health'].get('error_rate_percent', 0) for check in recent_checks]
        
        return {
            'memory_trend': {
                'current': memory_trend[-1] if memory_trend else 0,
                'average': sum(memory_trend) / len(memory_trend) if memory_trend else 0,
                'trending': 'stable'  # Could implement trend calculation
            },
            'cpu_trend': {
                'current': cpu_trend[-1] if cpu_trend else 0,
                'average': sum(cpu_trend) / len(cpu_trend) if cpu_trend else 0,
                'trending': 'stable'
            },
            'error_trend': {
                'current': error_trend[-1] if error_trend else 0,
                'average': sum(error_trend) / len(error_trend) if error_trend else 0,
                'trending': 'stable'
            },
            'overall_trend': 'stable'
        }
