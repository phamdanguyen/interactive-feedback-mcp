# interactive_feedback_server/monitoring/performance_analyzer.py

"""
性能分析工具 - V3.3 架构改进版本
Performance Analyzer - V3.3 Architecture Improvement Version

提供性能数据分析、瓶颈识别和优化建议功能。
Provides performance data analysis, bottleneck identification and optimization recommendations.
"""

import time
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .performance_monitor import MetricCollector, PerformanceSnapshot, MetricData


class PerformanceLevel(Enum):
    """性能等级枚举"""

    EXCELLENT = "excellent"  # 优秀
    GOOD = "good"  # 良好
    FAIR = "fair"  # 一般
    POOR = "poor"  # 较差
    CRITICAL = "critical"  # 严重


class IssueType(Enum):
    """问题类型枚举"""

    HIGH_CPU = "high_cpu"  # 高CPU使用率
    HIGH_MEMORY = "high_memory"  # 高内存使用率
    SLOW_RESPONSE = "slow_response"  # 响应缓慢
    HIGH_ERROR_RATE = "high_error_rate"  # 高错误率
    RESOURCE_LEAK = "resource_leak"  # 资源泄漏
    PERFORMANCE_DEGRADATION = "perf_degradation"  # 性能下降


@dataclass
class PerformanceIssue:
    """
    性能问题
    Performance Issue
    """

    issue_type: IssueType  # 问题类型
    severity: PerformanceLevel  # 严重程度
    description: str  # 问题描述
    affected_metrics: List[str]  # 受影响的指标
    recommendations: List[str]  # 优化建议
    timestamp: float  # 发现时间
    details: Dict[str, Any]  # 详细信息


@dataclass
class PerformanceReport:
    """
    性能报告
    Performance Report
    """

    timestamp: float  # 报告时间
    overall_score: float  # 总体评分 (0-100)
    overall_level: PerformanceLevel  # 总体等级
    issues: List[PerformanceIssue]  # 发现的问题
    recommendations: List[str]  # 总体建议
    metrics_summary: Dict[str, Any]  # 指标摘要
    analysis_period_minutes: int  # 分析时间段


class PerformanceAnalyzer:
    """
    性能分析器
    Performance Analyzer

    分析性能数据，识别瓶颈并提供优化建议
    Analyzes performance data, identifies bottlenecks and provides optimization recommendations
    """

    def __init__(self, metric_collector: MetricCollector):
        """
        初始化性能分析器
        Initialize performance analyzer

        Args:
            metric_collector: 指标收集器
        """
        self.metric_collector = metric_collector

        # 性能阈值配置
        self.thresholds = {
            "cpu_warning": 70.0,  # CPU警告阈值
            "cpu_critical": 90.0,  # CPU严重阈值
            "memory_warning": 80.0,  # 内存警告阈值
            "memory_critical": 95.0,  # 内存严重阈值
            "response_warning": 1.0,  # 响应时间警告阈值(秒)
            "response_critical": 3.0,  # 响应时间严重阈值(秒)
            "error_rate_warning": 5.0,  # 错误率警告阈值(%)
            "error_rate_critical": 15.0,  # 错误率严重阈值(%)
        }

    def analyze_performance(
        self, analysis_period_minutes: int = 10
    ) -> PerformanceReport:
        """
        分析性能
        Analyze performance

        Args:
            analysis_period_minutes: 分析时间段(分钟)

        Returns:
            PerformanceReport: 性能报告
        """
        timestamp = time.time()
        issues = []

        # 分析系统指标
        system_issues = self._analyze_system_metrics(analysis_period_minutes)
        issues.extend(system_issues)

        # 分析响应时间
        response_issues = self._analyze_response_times(analysis_period_minutes)
        issues.extend(response_issues)

        # 分析错误率
        error_issues = self._analyze_error_rates(analysis_period_minutes)
        issues.extend(error_issues)

        # 分析资源使用趋势
        trend_issues = self._analyze_resource_trends(analysis_period_minutes)
        issues.extend(trend_issues)

        # 计算总体评分和等级
        overall_score, overall_level = self._calculate_overall_performance(issues)

        # 生成总体建议
        recommendations = self._generate_overall_recommendations(issues)

        # 获取指标摘要
        metrics_summary = self.metric_collector.get_all_metrics_summary()

        return PerformanceReport(
            timestamp=timestamp,
            overall_score=overall_score,
            overall_level=overall_level,
            issues=issues,
            recommendations=recommendations,
            metrics_summary=metrics_summary,
            analysis_period_minutes=analysis_period_minutes,
        )

    def _analyze_system_metrics(self, minutes: int) -> List[PerformanceIssue]:
        """分析系统指标"""
        issues = []
        system_stats = self.metric_collector.get_system_stats(minutes)

        if not system_stats:
            return issues

        # 分析CPU使用率
        cpu_stats = system_stats.get("cpu", {})
        cpu_mean = cpu_stats.get("mean", 0)
        cpu_max = cpu_stats.get("max", 0)

        if cpu_max >= self.thresholds["cpu_critical"]:
            issues.append(
                PerformanceIssue(
                    issue_type=IssueType.HIGH_CPU,
                    severity=PerformanceLevel.CRITICAL,
                    description=f"CPU使用率过高，峰值达到 {cpu_max:.1f}%",
                    affected_metrics=["cpu_percent"],
                    recommendations=[
                        "检查CPU密集型操作",
                        "优化算法复杂度",
                        "考虑异步处理",
                        "增加CPU资源",
                    ],
                    timestamp=time.time(),
                    details={"max_cpu": cpu_max, "mean_cpu": cpu_mean},
                )
            )
        elif cpu_mean >= self.thresholds["cpu_warning"]:
            issues.append(
                PerformanceIssue(
                    issue_type=IssueType.HIGH_CPU,
                    severity=PerformanceLevel.POOR,
                    description=f"CPU使用率较高，平均 {cpu_mean:.1f}%",
                    affected_metrics=["cpu_percent"],
                    recommendations=["监控CPU使用模式", "优化热点代码", "考虑负载均衡"],
                    timestamp=time.time(),
                    details={"max_cpu": cpu_max, "mean_cpu": cpu_mean},
                )
            )

        # 分析内存使用率
        memory_stats = system_stats.get("memory", {})
        memory_mean = memory_stats.get("mean", 0)
        memory_max = memory_stats.get("max", 0)

        if memory_max >= self.thresholds["memory_critical"]:
            issues.append(
                PerformanceIssue(
                    issue_type=IssueType.HIGH_MEMORY,
                    severity=PerformanceLevel.CRITICAL,
                    description=f"内存使用率过高，峰值达到 {memory_max:.1f}%",
                    affected_metrics=["memory_percent"],
                    recommendations=[
                        "检查内存泄漏",
                        "优化数据结构",
                        "清理无用对象",
                        "增加内存资源",
                    ],
                    timestamp=time.time(),
                    details={"max_memory": memory_max, "mean_memory": memory_mean},
                )
            )
        elif memory_mean >= self.thresholds["memory_warning"]:
            issues.append(
                PerformanceIssue(
                    issue_type=IssueType.HIGH_MEMORY,
                    severity=PerformanceLevel.POOR,
                    description=f"内存使用率较高，平均 {memory_mean:.1f}%",
                    affected_metrics=["memory_percent"],
                    recommendations=[
                        "监控内存使用模式",
                        "优化缓存策略",
                        "实施内存管理最佳实践",
                    ],
                    timestamp=time.time(),
                    details={"max_memory": memory_max, "mean_memory": memory_mean},
                )
            )

        return issues

    def _analyze_response_times(self, minutes: int) -> List[PerformanceIssue]:
        """分析响应时间"""
        issues = []

        # 获取所有计时器的统计信息
        metrics_summary = self.metric_collector.get_all_metrics_summary()
        timers = metrics_summary.get("timers", {})

        for timer_name, stats in timers.items():
            if not stats:
                continue

            mean_time = stats.get("mean", 0)
            p95_time = stats.get("p95", 0)
            p99_time = stats.get("p99", 0)

            if p99_time >= self.thresholds["response_critical"]:
                issues.append(
                    PerformanceIssue(
                        issue_type=IssueType.SLOW_RESPONSE,
                        severity=PerformanceLevel.CRITICAL,
                        description=f"{timer_name} 响应时间过慢，P99: {p99_time:.3f}s",
                        affected_metrics=[timer_name],
                        recommendations=[
                            "优化慢查询",
                            "添加缓存",
                            "异步处理",
                            "数据库索引优化",
                        ],
                        timestamp=time.time(),
                        details=stats,
                    )
                )
            elif mean_time >= self.thresholds["response_warning"]:
                issues.append(
                    PerformanceIssue(
                        issue_type=IssueType.SLOW_RESPONSE,
                        severity=PerformanceLevel.POOR,
                        description=f"{timer_name} 响应时间较慢，平均: {mean_time:.3f}s",
                        affected_metrics=[timer_name],
                        recommendations=["性能分析和优化", "代码重构", "算法优化"],
                        timestamp=time.time(),
                        details=stats,
                    )
                )

        return issues

    def _analyze_error_rates(self, minutes: int) -> List[PerformanceIssue]:
        """分析错误率 - V4.0 简化版本"""
        # 简化实现：暂时返回空列表，避免未实现的复杂逻辑
        return []

    def _analyze_resource_trends(self, minutes: int) -> List[PerformanceIssue]:
        """分析资源使用趋势 - V4.0 简化版本"""
        # 简化实现：暂时返回空列表，避免未实现的复杂逻辑
        return []

    def _calculate_overall_performance(
        self, issues: List[PerformanceIssue]
    ) -> Tuple[float, PerformanceLevel]:
        """
        计算总体性能评分和等级
        Calculate overall performance score and level

        Args:
            issues: 性能问题列表

        Returns:
            Tuple[float, PerformanceLevel]: 评分和等级
        """
        if not issues:
            return 100.0, PerformanceLevel.EXCELLENT

        # 根据问题严重程度计算扣分
        score = 100.0
        severity_penalties = {
            PerformanceLevel.CRITICAL: 30,
            PerformanceLevel.POOR: 15,
            PerformanceLevel.FAIR: 8,
            PerformanceLevel.GOOD: 3,
        }

        for issue in issues:
            penalty = severity_penalties.get(issue.severity, 0)
            score -= penalty

        score = max(0.0, score)

        # 确定等级
        if score >= 90:
            level = PerformanceLevel.EXCELLENT
        elif score >= 75:
            level = PerformanceLevel.GOOD
        elif score >= 60:
            level = PerformanceLevel.FAIR
        elif score >= 40:
            level = PerformanceLevel.POOR
        else:
            level = PerformanceLevel.CRITICAL

        return score, level

    def _generate_overall_recommendations(
        self, issues: List[PerformanceIssue]
    ) -> List[str]:
        """
        生成总体优化建议
        Generate overall optimization recommendations

        Args:
            issues: 性能问题列表

        Returns:
            List[str]: 建议列表
        """
        if not issues:
            return ["系统性能良好，继续保持监控"]

        recommendations = []

        # 按问题类型分组
        issue_types = {}
        for issue in issues:
            if issue.issue_type not in issue_types:
                issue_types[issue.issue_type] = []
            issue_types[issue.issue_type].append(issue)

        # 根据问题类型生成建议
        if IssueType.HIGH_CPU in issue_types:
            recommendations.append("优先解决CPU使用率问题，考虑代码优化和资源扩容")

        if IssueType.HIGH_MEMORY in issue_types:
            recommendations.append("检查内存使用模式，排查可能的内存泄漏")

        if IssueType.SLOW_RESPONSE in issue_types:
            recommendations.append("优化响应时间，重点关注慢查询和算法效率")

        # 严重问题的紧急建议
        critical_issues = [i for i in issues if i.severity == PerformanceLevel.CRITICAL]
        if critical_issues:
            recommendations.insert(0, "发现严重性能问题，建议立即处理")

        return recommendations

    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取性能趋势
        Get performance trends

        Args:
            hours: 分析时间范围(小时)

        Returns:
            Dict[str, Any]: 趋势数据
        """
        # 这里可以实现更复杂的趋势分析
        # 例如：性能指标的时间序列分析、预测等

        return {
            "analysis_period_hours": hours,
            "trend_analysis": "Not implemented yet",
            "predictions": "Not implemented yet",
        }


# 全局性能分析器实例
_global_performance_analyzer: Optional[PerformanceAnalyzer] = None


def get_performance_analyzer() -> PerformanceAnalyzer:
    """
    获取全局性能分析器实例
    Get global performance analyzer instance

    Returns:
        PerformanceAnalyzer: 性能分析器实例
    """
    global _global_performance_analyzer
    if _global_performance_analyzer is None:
        from .performance_monitor import get_metric_collector

        collector = get_metric_collector()
        _global_performance_analyzer = PerformanceAnalyzer(collector)
    return _global_performance_analyzer
