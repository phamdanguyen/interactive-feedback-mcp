# interactive_feedback_server/monitoring/dashboard.py

"""
监控仪表板 - V3.3 架构改进版本
Monitoring Dashboard - V3.3 Architecture Improvement Version

提供性能监控的可视化界面和实时数据展示。
Provides visualization interface and real-time data display for performance monitoring.
"""

import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from .performance_monitor import get_metric_collector
from .performance_analyzer import get_performance_analyzer, PerformanceLevel


class MonitoringDashboard:
    """
    监控仪表板
    Monitoring Dashboard

    提供性能数据的可视化和实时监控功能
    Provides visualization and real-time monitoring of performance data
    """

    def __init__(self):
        """初始化监控仪表板"""
        self.metric_collector = get_metric_collector()
        self.performance_analyzer = get_performance_analyzer()

        # 仪表板配置
        self.refresh_interval = 30  # 刷新间隔(秒)
        self.history_hours = 24  # 历史数据保留时间(小时)

    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        获取仪表板数据
        Get dashboard data

        Returns:
            Dict[str, Any]: 仪表板数据
        """
        current_time = time.time()

        # 收集当前系统指标
        current_snapshot = self.metric_collector.collect_system_metrics()

        # 获取性能分析报告
        performance_report = self.performance_analyzer.analyze_performance(10)

        # 获取指标摘要
        metrics_summary = self.metric_collector.get_all_metrics_summary()

        # 获取系统统计
        system_stats_5min = self.metric_collector.get_system_stats(5)
        system_stats_1hour = self.metric_collector.get_system_stats(60)

        return {
            "timestamp": current_time,
            "current_snapshot": self._snapshot_to_dict(current_snapshot),
            "performance_report": self._report_to_dict(performance_report),
            "metrics_summary": metrics_summary,
            "system_stats": {
                "5_minutes": system_stats_5min,
                "1_hour": system_stats_1hour,
            },
            "dashboard_config": {
                "refresh_interval": self.refresh_interval,
                "history_hours": self.history_hours,
            },
        }

    def get_real_time_metrics(self) -> Dict[str, Any]:
        """
        获取实时指标
        Get real-time metrics

        Returns:
            Dict[str, Any]: 实时指标数据
        """
        current_snapshot = self.metric_collector.collect_system_metrics()

        return {
            "timestamp": time.time(),
            "cpu_percent": current_snapshot.cpu_percent,
            "memory_percent": current_snapshot.memory_percent,
            "memory_used_mb": current_snapshot.memory_used_mb,
            "active_threads": current_snapshot.active_threads,
            "open_files": current_snapshot.open_files,
            "disk_io": {
                "read_mb": current_snapshot.disk_io_read_mb,
                "write_mb": current_snapshot.disk_io_write_mb,
            },
            "network_io": {
                "sent_mb": current_snapshot.network_sent_mb,
                "recv_mb": current_snapshot.network_recv_mb,
            },
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要
        Get performance summary

        Returns:
            Dict[str, Any]: 性能摘要
        """
        report = self.performance_analyzer.analyze_performance(10)

        return {
            "overall_score": report.overall_score,
            "overall_level": report.overall_level.value,
            "issues_count": len(report.issues),
            "critical_issues": len(
                [i for i in report.issues if i.severity == PerformanceLevel.CRITICAL]
            ),
            "recommendations_count": len(report.recommendations),
            "analysis_time": report.timestamp,
        }

    def get_alerts(self) -> List[Dict[str, Any]]:
        """
        获取告警信息
        Get alerts

        Returns:
            List[Dict[str, Any]]: 告警列表
        """
        report = self.performance_analyzer.analyze_performance(5)
        alerts = []

        for issue in report.issues:
            if issue.severity in [PerformanceLevel.CRITICAL, PerformanceLevel.POOR]:
                alerts.append(
                    {
                        "type": issue.issue_type.value,
                        "severity": issue.severity.value,
                        "description": issue.description,
                        "timestamp": issue.timestamp,
                        "recommendations": issue.recommendations[:3],  # 只显示前3个建议
                    }
                )

        return alerts

    def get_metrics_history(
        self, metric_name: str, hours: int = 1
    ) -> List[Dict[str, Any]]:
        """
        获取指标历史
        Get metrics history

        Args:
            metric_name: 指标名称
            hours: 历史时间范围(小时)

        Returns:
            List[Dict[str, Any]]: 指标历史数据
        """
        cutoff_time = time.time() - (hours * 3600)
        history = self.metric_collector.get_metric_history(metric_name)

        # 过滤时间范围
        filtered_history = [
            {"timestamp": metric.timestamp, "value": metric.value, "tags": metric.tags}
            for metric in history
            if metric.timestamp >= cutoff_time
        ]

        return filtered_history

    def get_system_overview(self) -> Dict[str, Any]:
        """
        获取系统概览
        Get system overview

        Returns:
            Dict[str, Any]: 系统概览数据
        """
        current_snapshot = self.metric_collector.collect_system_metrics()
        system_stats = self.metric_collector.get_system_stats(60)  # 1小时统计

        # 计算状态
        cpu_status = self._get_status_level(current_snapshot.cpu_percent, 70, 90)
        memory_status = self._get_status_level(current_snapshot.memory_percent, 80, 95)

        return {
            "system_health": {
                "cpu": {
                    "current": current_snapshot.cpu_percent,
                    "status": cpu_status,
                    "trend": self._calculate_trend("cpu", system_stats),
                },
                "memory": {
                    "current": current_snapshot.memory_percent,
                    "used_mb": current_snapshot.memory_used_mb,
                    "status": memory_status,
                    "trend": self._calculate_trend("memory", system_stats),
                },
                "processes": {
                    "threads": current_snapshot.active_threads,
                    "files": current_snapshot.open_files,
                },
            },
            "performance_score": self.get_performance_summary()["overall_score"],
            "uptime_info": self._get_uptime_info(),
            "last_updated": time.time(),
        }

    def _snapshot_to_dict(self, snapshot) -> Dict[str, Any]:
        """将性能快照转换为字典"""
        return {
            "timestamp": snapshot.timestamp,
            "cpu_percent": snapshot.cpu_percent,
            "memory_percent": snapshot.memory_percent,
            "memory_used_mb": snapshot.memory_used_mb,
            "disk_io_read_mb": snapshot.disk_io_read_mb,
            "disk_io_write_mb": snapshot.disk_io_write_mb,
            "network_sent_mb": snapshot.network_sent_mb,
            "network_recv_mb": snapshot.network_recv_mb,
            "active_threads": snapshot.active_threads,
            "open_files": snapshot.open_files,
        }

    def _report_to_dict(self, report) -> Dict[str, Any]:
        """将性能报告转换为字典"""
        return {
            "timestamp": report.timestamp,
            "overall_score": report.overall_score,
            "overall_level": report.overall_level.value,
            "issues": [
                {
                    "type": issue.issue_type.value,
                    "severity": issue.severity.value,
                    "description": issue.description,
                    "affected_metrics": issue.affected_metrics,
                    "recommendations": issue.recommendations,
                    "timestamp": issue.timestamp,
                }
                for issue in report.issues
            ],
            "recommendations": report.recommendations,
            "analysis_period_minutes": report.analysis_period_minutes,
        }

    def _get_status_level(
        self, value: float, warning_threshold: float, critical_threshold: float
    ) -> str:
        """获取状态等级"""
        if value >= critical_threshold:
            return "critical"
        elif value >= warning_threshold:
            return "warning"
        else:
            return "normal"

    def _calculate_trend(self, metric_type: str, system_stats: Dict[str, Any]) -> str:
        """计算趋势"""
        if not system_stats:
            return "unknown"

        # 简单的趋势计算
        if metric_type == "cpu":
            cpu_stats = system_stats.get("cpu", {})
            current = cpu_stats.get("current", 0)
            mean = cpu_stats.get("mean", 0)
        elif metric_type == "memory":
            memory_stats = system_stats.get("memory", {})
            current = memory_stats.get("current", 0)
            mean = memory_stats.get("mean", 0)
        else:
            return "unknown"

        if current > mean * 1.1:
            return "increasing"
        elif current < mean * 0.9:
            return "decreasing"
        else:
            return "stable"

    def _get_uptime_info(self) -> Dict[str, Any]:
        """获取运行时间信息"""
        try:
            import psutil

            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time

            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)

            return {
                "uptime_seconds": uptime_seconds,
                "uptime_formatted": f"{days}天 {hours}小时 {minutes}分钟",
                "boot_time": boot_time,
            }
        except Exception:
            return {"uptime_seconds": 0, "uptime_formatted": "未知", "boot_time": 0}

    def export_dashboard_data(self, format: str = "json") -> str:
        """
        导出仪表板数据
        Export dashboard data

        Args:
            format: 导出格式 ('json', 'csv')

        Returns:
            str: 导出的数据
        """
        data = self.get_dashboard_data()

        if format.lower() == "json":
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif format.lower() == "csv":
            # 简单的CSV导出（实际应用中可能需要更复杂的实现）
            lines = []
            lines.append("timestamp,metric,value")

            # 导出当前快照
            snapshot = data["current_snapshot"]
            timestamp = snapshot["timestamp"]
            for key, value in snapshot.items():
                if key != "timestamp" and isinstance(value, (int, float)):
                    lines.append(f"{timestamp},{key},{value}")

            return "\n".join(lines)
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    def get_dashboard_config(self) -> Dict[str, Any]:
        """
        获取仪表板配置
        Get dashboard configuration

        Returns:
            Dict[str, Any]: 配置信息
        """
        return {
            "refresh_interval": self.refresh_interval,
            "history_hours": self.history_hours,
            "supported_formats": ["json", "csv"],
            "available_metrics": list(
                self.metric_collector.get_all_metrics_summary().get("timers", {}).keys()
            ),
            "thresholds": self.performance_analyzer.thresholds,
        }


# 全局监控仪表板实例
_global_dashboard: Optional[MonitoringDashboard] = None


def get_monitoring_dashboard() -> MonitoringDashboard:
    """
    获取全局监控仪表板实例
    Get global monitoring dashboard instance

    Returns:
        MonitoringDashboard: 监控仪表板实例
    """
    global _global_dashboard
    if _global_dashboard is None:
        _global_dashboard = MonitoringDashboard()
    return _global_dashboard
