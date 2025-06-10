# tests/architecture/test_monitoring_system.py

"""
监控系统测试套件
Monitoring System Test Suite

测试性能监控、分析和仪表板功能
Tests performance monitoring, analysis and dashboard functionality
"""

import os
import sys
import time
import unittest
from unittest.mock import patch, MagicMock

# 添加源代码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

try:
    from interactive_feedback_server.monitoring import (
        MetricCollector,
        PerformanceTimer,
        MetricType,
        MetricData,
        PerformanceAnalyzer,
        PerformanceLevel,
        IssueType,
        MonitoringDashboard,
        get_metric_collector,
        get_performance_analyzer,
        get_monitoring_dashboard,
    )

    MONITORING_AVAILABLE = True
except ImportError as e:
    print(f"监控模块导入失败: {e}")
    MONITORING_AVAILABLE = False


@unittest.skipUnless(MONITORING_AVAILABLE, "监控模块不可用")
class TestMetricCollector(unittest.TestCase):
    """指标收集器测试"""

    def setUp(self):
        """测试前准备"""
        self.collector = MetricCollector(max_history=100)

    def test_counter_operations(self):
        """测试计数器操作"""
        # 增加计数器
        self.collector.increment_counter("test_counter", 1.0)
        self.collector.increment_counter("test_counter", 2.0)

        # 检查计数器值
        self.assertEqual(self.collector._counters["test_counter"], 3.0)

        # 检查指标历史
        history = self.collector.get_metric_history("test_counter")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[-1].value, 3.0)
        self.assertEqual(history[-1].metric_type, MetricType.COUNTER)

    def test_gauge_operations(self):
        """测试仪表操作"""
        # 设置仪表值
        self.collector.set_gauge("test_gauge", 42.5)
        self.collector.set_gauge("test_gauge", 55.0)

        # 检查仪表值
        self.assertEqual(self.collector._gauges["test_gauge"], 55.0)

        # 检查指标历史
        history = self.collector.get_metric_history("test_gauge")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[-1].value, 55.0)
        self.assertEqual(history[-1].metric_type, MetricType.GAUGE)

    def test_timer_operations(self):
        """测试计时器操作"""
        # 记录计时器
        self.collector.record_timer("test_timer", 0.1)
        self.collector.record_timer("test_timer", 0.2)
        self.collector.record_timer("test_timer", 0.15)

        # 检查计时器统计
        stats = self.collector.get_timer_stats("test_timer")
        self.assertEqual(stats["count"], 3)
        self.assertEqual(stats["min"], 0.1)
        self.assertEqual(stats["max"], 0.2)
        self.assertAlmostEqual(stats["mean"], 0.15, places=2)

    def test_performance_timer_context(self):
        """测试性能计时器上下文管理器"""
        with PerformanceTimer(self.collector, "context_timer"):
            time.sleep(0.01)  # 模拟一些工作

        # 检查计时器是否记录了时间
        stats = self.collector.get_timer_stats("context_timer")
        self.assertEqual(stats["count"], 1)
        self.assertGreater(stats["min"], 0.005)  # 至少5ms

    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    @patch("psutil.Process")
    def test_system_metrics_collection(self, mock_process, mock_memory, mock_cpu):
        """测试系统指标收集"""
        # 模拟系统数据
        mock_cpu.return_value = 45.5
        mock_memory.return_value = MagicMock(percent=60.0, used=8589934592)  # 8GB
        mock_process_instance = MagicMock()
        mock_process_instance.num_threads.return_value = 10
        mock_process_instance.open_files.return_value = []
        mock_process.return_value = mock_process_instance

        # 收集系统指标
        snapshot = self.collector.collect_system_metrics()

        # 验证快照数据
        self.assertEqual(snapshot.cpu_percent, 45.5)
        self.assertEqual(snapshot.memory_percent, 60.0)
        self.assertEqual(snapshot.active_threads, 10)
        self.assertIsInstance(snapshot.timestamp, float)

    def test_metrics_summary(self):
        """测试指标摘要"""
        # 添加一些测试数据
        self.collector.increment_counter("requests", 100)
        self.collector.set_gauge("active_users", 25)
        self.collector.record_timer("response_time", 0.5)

        # 获取摘要
        summary = self.collector.get_all_metrics_summary()

        # 验证摘要内容
        self.assertIn("counters", summary)
        self.assertIn("gauges", summary)
        self.assertIn("timers", summary)
        self.assertEqual(summary["counters"]["requests"], 100)
        self.assertEqual(summary["gauges"]["active_users"], 25)
        self.assertIn("response_time", summary["timers"])


@unittest.skipUnless(MONITORING_AVAILABLE, "监控模块不可用")
class TestPerformanceAnalyzer(unittest.TestCase):
    """性能分析器测试"""

    def setUp(self):
        """测试前准备"""
        self.collector = MetricCollector()
        self.analyzer = PerformanceAnalyzer(self.collector)

    def test_analyzer_initialization(self):
        """测试分析器初始化"""
        self.assertIsInstance(self.analyzer.thresholds, dict)
        self.assertIn("cpu_warning", self.analyzer.thresholds)
        self.assertIn("memory_warning", self.analyzer.thresholds)

    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    @patch("psutil.Process")
    def test_performance_analysis(self, mock_process, mock_memory, mock_cpu):
        """测试性能分析"""
        # 模拟高CPU使用率
        mock_cpu.return_value = 95.0  # 超过严重阈值
        mock_memory.return_value = MagicMock(percent=50.0, used=4294967296)
        mock_process_instance = MagicMock()
        mock_process_instance.num_threads.return_value = 5
        mock_process_instance.open_files.return_value = []
        mock_process.return_value = mock_process_instance

        # 收集一些系统指标
        self.collector.collect_system_metrics()

        # 执行性能分析
        report = self.analyzer.analyze_performance(1)

        # 验证报告
        self.assertIsInstance(report.overall_score, float)
        self.assertIsInstance(report.overall_level, PerformanceLevel)
        self.assertIsInstance(report.issues, list)

        # 应该检测到高CPU问题
        cpu_issues = [i for i in report.issues if i.issue_type == IssueType.HIGH_CPU]
        self.assertTrue(len(cpu_issues) > 0)
        self.assertEqual(cpu_issues[0].severity, PerformanceLevel.CRITICAL)

    def test_response_time_analysis(self):
        """测试响应时间分析"""
        # 添加一些慢响应时间
        self.collector.record_timer("slow_operation", 5.0)  # 超过严重阈值
        self.collector.record_timer("slow_operation", 4.5)

        # 执行分析
        report = self.analyzer.analyze_performance(1)

        # 应该检测到慢响应问题
        slow_issues = [
            i for i in report.issues if i.issue_type == IssueType.SLOW_RESPONSE
        ]
        self.assertTrue(len(slow_issues) > 0)

    def test_overall_score_calculation(self):
        """测试总体评分计算"""
        # 测试无问题情况
        issues = []
        score, level = self.analyzer._calculate_overall_performance(issues)
        self.assertEqual(score, 100.0)
        self.assertEqual(level, PerformanceLevel.EXCELLENT)

        # 测试有严重问题情况
        from interactive_feedback_server.monitoring.performance_analyzer import (
            PerformanceIssue,
        )

        critical_issue = PerformanceIssue(
            issue_type=IssueType.HIGH_CPU,
            severity=PerformanceLevel.CRITICAL,
            description="测试严重问题",
            affected_metrics=[],
            recommendations=[],
            timestamp=time.time(),
            details={},
        )

        score, level = self.analyzer._calculate_overall_performance([critical_issue])
        self.assertLess(score, 100.0)
        self.assertNotEqual(level, PerformanceLevel.EXCELLENT)


@unittest.skipUnless(MONITORING_AVAILABLE, "监控模块不可用")
class TestMonitoringDashboard(unittest.TestCase):
    """监控仪表板测试"""

    def setUp(self):
        """测试前准备"""
        self.dashboard = MonitoringDashboard()

    def test_dashboard_initialization(self):
        """测试仪表板初始化"""
        self.assertIsNotNone(self.dashboard.metric_collector)
        self.assertIsNotNone(self.dashboard.performance_analyzer)
        self.assertIsInstance(self.dashboard.refresh_interval, int)

    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    @patch("psutil.Process")
    def test_real_time_metrics(self, mock_process, mock_memory, mock_cpu):
        """测试实时指标获取"""
        # 模拟系统数据
        mock_cpu.return_value = 30.0
        mock_memory.return_value = MagicMock(percent=40.0, used=4294967296)
        mock_process_instance = MagicMock()
        mock_process_instance.num_threads.return_value = 8
        mock_process_instance.open_files.return_value = []
        mock_process.return_value = mock_process_instance

        # 获取实时指标
        metrics = self.dashboard.get_real_time_metrics()

        # 验证指标数据
        self.assertIn("timestamp", metrics)
        self.assertIn("cpu_percent", metrics)
        self.assertIn("memory_percent", metrics)
        self.assertEqual(metrics["cpu_percent"], 30.0)
        self.assertEqual(metrics["memory_percent"], 40.0)

    def test_performance_summary(self):
        """测试性能摘要"""
        summary = self.dashboard.get_performance_summary()

        # 验证摘要内容
        self.assertIn("overall_score", summary)
        self.assertIn("overall_level", summary)
        self.assertIn("issues_count", summary)
        self.assertIn("analysis_time", summary)

    def test_dashboard_data_export(self):
        """测试仪表板数据导出"""
        # 测试JSON导出
        json_data = self.dashboard.export_dashboard_data("json")
        self.assertIsInstance(json_data, str)

        # 测试CSV导出
        csv_data = self.dashboard.export_dashboard_data("csv")
        self.assertIsInstance(csv_data, str)
        self.assertIn("timestamp,metric,value", csv_data)

        # 测试不支持的格式
        with self.assertRaises(ValueError):
            self.dashboard.export_dashboard_data("xml")

    def test_dashboard_config(self):
        """测试仪表板配置"""
        config = self.dashboard.get_dashboard_config()

        # 验证配置内容
        self.assertIn("refresh_interval", config)
        self.assertIn("history_hours", config)
        self.assertIn("supported_formats", config)
        self.assertIn("available_metrics", config)


@unittest.skipUnless(MONITORING_AVAILABLE, "监控模块不可用")
class TestMonitoringIntegration(unittest.TestCase):
    """监控系统集成测试"""

    def test_global_instances(self):
        """测试全局实例"""
        collector1 = get_metric_collector()
        collector2 = get_metric_collector()
        self.assertIs(collector1, collector2)

        analyzer1 = get_performance_analyzer()
        analyzer2 = get_performance_analyzer()
        self.assertIs(analyzer1, analyzer2)

        dashboard1 = get_monitoring_dashboard()
        dashboard2 = get_monitoring_dashboard()
        self.assertIs(dashboard1, dashboard2)

    def test_option_resolver_monitoring_integration(self):
        """测试选项解析器监控集成"""
        try:
            from interactive_feedback_server.utils.option_resolver import (
                get_option_resolver,
            )

            resolver = get_option_resolver()

            # 检查监控是否已集成
            self.assertTrue(hasattr(resolver, "_monitoring_enabled"))

            # 执行一些解析操作以生成监控数据
            result = resolver.resolve_options("测试文本", None, None, "zh_CN")
            self.assertIsInstance(result, list)

            # 检查是否有监控数据
            if hasattr(resolver, "metric_collector"):
                summary = resolver.metric_collector.get_all_metrics_summary()
                self.assertIsInstance(summary, dict)

        except ImportError:
            self.skipTest("选项解析器不可用")


def run_monitoring_tests():
    """运行监控系统测试"""
    print("=" * 60)
    print("监控系统测试套件 (Monitoring System Test Suite)")
    print("=" * 60)

    if not MONITORING_AVAILABLE:
        print("⚠️  监控模块不可用，跳过测试")
        return False

    # 创建测试套件
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestMetricCollector))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestPerformanceAnalyzer))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestMonitoringDashboard))
    suite.addTest(
        unittest.TestLoader().loadTestsFromTestCase(TestMonitoringIntegration)
    )

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 显示监控统计
    print("\n" + "=" * 60)
    print("监控系统统计信息 (Monitoring System Statistics)")
    print("=" * 60)

    try:
        collector = get_metric_collector()
        summary = collector.get_all_metrics_summary()
        print(f"指标收集器统计: {summary}")

        dashboard = get_monitoring_dashboard()
        config = dashboard.get_dashboard_config()
        print(f"仪表板配置: {config}")

    except Exception as e:
        print(f"获取监控统计失败: {e}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_monitoring_tests()
    sys.exit(0 if success else 1)
