# tests/optimization/test_code_optimization.py

"""
代码优化测试套件
Code Optimization Test Suite

验证代码优化后的功能完整性和性能改进
Verifies functional integrity and performance improvements after code optimization
"""

import os
import sys
import time
import unittest

# 添加源代码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

try:
    from interactive_feedback_server.core import (
        get_singleton_manager,
        get_stats_collector,
        get_config_loader,
        increment_stat,
        set_stat_gauge,
        register_config,
        load_config,
    )
    from interactive_feedback_server.utils.option_resolver import get_option_resolver
    from interactive_feedback_server.monitoring import get_metric_collector
    from interactive_feedback_server.error_handling import get_error_handler

    OPTIMIZATION_AVAILABLE = True
except ImportError as e:
    print(f"优化模块导入失败: {e}")
    OPTIMIZATION_AVAILABLE = False


@unittest.skipUnless(OPTIMIZATION_AVAILABLE, "优化模块不可用")
class TestSingletonManager(unittest.TestCase):
    """单例管理器测试"""

    def test_singleton_manager_functionality(self):
        """测试单例管理器功能"""
        manager = get_singleton_manager()

        # 测试注册和获取
        def test_factory():
            return "test_instance"

        manager.register_factory("test_singleton", test_factory)

        # 获取实例
        instance1 = manager.get_instance("test_singleton")
        instance2 = manager.get_instance("test_singleton")

        # 验证单例行为
        self.assertEqual(instance1, instance2)
        self.assertEqual(instance1, "test_instance")

        # 测试清除
        self.assertTrue(manager.clear_instance("test_singleton"))

        # 重新获取应该创建新实例
        instance3 = manager.get_instance("test_singleton")
        self.assertEqual(instance3, "test_instance")

    def test_global_instances_consistency(self):
        """测试全局实例一致性"""
        # 测试选项解析器
        resolver1 = get_option_resolver()
        resolver2 = get_option_resolver()
        self.assertIs(resolver1, resolver2)

        # 测试指标收集器
        collector1 = get_metric_collector()
        collector2 = get_metric_collector()
        self.assertIs(collector1, collector2)

        # 测试错误处理器
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        self.assertIs(handler1, handler2)


@unittest.skipUnless(OPTIMIZATION_AVAILABLE, "优化模块不可用")
class TestUnifiedStatsCollector(unittest.TestCase):
    """统一统计收集器测试"""

    def setUp(self):
        """测试前准备"""
        self.stats_collector = get_stats_collector()
        # 清除之前的统计
        self.stats_collector.reset_stats()

    def test_stats_collection(self):
        """测试统计收集"""
        # 测试计数器
        increment_stat("test_counter", 5, "test_category")
        self.assertEqual(self.stats_collector.get_counter("test_counter"), 5)

        # 测试仪表
        set_stat_gauge("test_gauge", 42.5, "test_category")
        self.assertEqual(self.stats_collector.get_gauge("test_gauge"), 42.5)

        # 测试直方图
        self.stats_collector.record_value("test_histogram", 10.0, "test_category")
        self.stats_collector.record_value("test_histogram", 20.0, "test_category")

        histogram_stats = self.stats_collector.get_histogram_stats("test_histogram")
        self.assertEqual(histogram_stats["count"], 2)
        self.assertEqual(histogram_stats["min"], 10.0)
        self.assertEqual(histogram_stats["max"], 20.0)

    def test_category_stats(self):
        """测试分类统计"""
        # 添加不同分类的统计
        increment_stat("counter1", 10, "category1")
        increment_stat("counter2", 20, "category2")

        # 获取分类统计
        category1_stats = self.stats_collector.get_category_stats("category1")
        category2_stats = self.stats_collector.get_category_stats("category2")

        self.assertEqual(category1_stats["count"], 1)
        self.assertEqual(category1_stats["total"], 10)
        self.assertEqual(category2_stats["count"], 1)
        self.assertEqual(category2_stats["total"], 20)

    def test_stats_export(self):
        """测试统计导出"""
        # 添加一些统计数据
        increment_stat("export_test", 100, "export_category")

        # 测试JSON导出
        json_export = self.stats_collector.export_stats("json")
        self.assertIsInstance(json_export, str)
        self.assertIn("export_test", json_export)

        # 测试CSV导出
        csv_export = self.stats_collector.export_stats("csv")
        self.assertIsInstance(csv_export, str)
        self.assertIn("timestamp,category,name,value,type", csv_export)


@unittest.skipUnless(OPTIMIZATION_AVAILABLE, "优化模块不可用")
class TestUnifiedConfigLoader(unittest.TestCase):
    """统一配置加载器测试"""

    def setUp(self):
        """测试前准备"""
        self.config_loader = get_config_loader()
        self.test_config_path = "test_config.json"

        # 清理测试文件
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)

    def test_config_registration_and_loading(self):
        """测试配置注册和加载"""
        # 注册配置
        default_config = {
            "setting1": "value1",
            "setting2": 42,
            "nested": {"key": "nested_value"},
        }

        register_config("test_config", self.test_config_path, default_config)

        # 加载配置（应该创建默认配置文件）
        config = load_config("test_config")

        self.assertEqual(config["setting1"], "value1")
        self.assertEqual(config["setting2"], 42)
        self.assertEqual(config["nested"]["key"], "nested_value")

        # 验证文件已创建
        self.assertTrue(os.path.exists(self.test_config_path))

    def test_config_value_operations(self):
        """测试配置值操作"""
        # 注册配置
        default_config = {"test_key": "test_value"}
        register_config("value_test", self.test_config_path, default_config)

        # 获取配置值
        value = self.config_loader.get_config_value("value_test", "test_key")
        self.assertEqual(value, "test_value")

        # 设置配置值
        success = self.config_loader.set_config_value(
            "value_test", "new_key", "new_value"
        )
        self.assertTrue(success)

        # 验证新值
        new_value = self.config_loader.get_config_value("value_test", "new_key")
        self.assertEqual(new_value, "new_value")

    def test_nested_config_keys(self):
        """测试嵌套配置键"""
        default_config = {"level1": {"level2": {"key": "nested_value"}}}

        register_config("nested_test", self.test_config_path, default_config)

        # 获取嵌套值
        value = self.config_loader.get_config_value("nested_test", "level1.level2.key")
        self.assertEqual(value, "nested_value")

        # 设置嵌套值
        success = self.config_loader.set_config_value(
            "nested_test", "level1.level2.new_key", "new_nested_value"
        )
        self.assertTrue(success)

        # 验证嵌套值
        new_value = self.config_loader.get_config_value(
            "nested_test", "level1.level2.new_key"
        )
        self.assertEqual(new_value, "new_nested_value")


@unittest.skipUnless(OPTIMIZATION_AVAILABLE, "优化模块不可用")
class TestOptimizedIntegration(unittest.TestCase):
    """优化后的集成测试"""

    def test_option_resolver_optimization(self):
        """测试选项解析器优化"""
        resolver = get_option_resolver()

        # 测试解析功能
        result = resolver.resolve_options("你觉得怎么样？", None, None, "zh_CN")
        self.assertIsInstance(result, list)

        # 测试统计收集
        stats = resolver.get_resolver_stats()
        self.assertIn("resolver_stats", stats)
        self.assertIn("version", stats)
        self.assertEqual(stats["version"], "V3.3-Optimized")

        # 验证统计数据
        self.assertGreater(stats["resolver_stats"]["total_resolutions"], 0)

    def test_performance_monitoring_integration(self):
        """测试性能监控集成"""
        from interactive_feedback_server.monitoring import get_monitoring_dashboard

        dashboard = get_monitoring_dashboard()

        # 测试实时指标
        metrics = dashboard.get_real_time_metrics()
        self.assertIn("timestamp", metrics)
        self.assertIn("cpu_percent", metrics)
        self.assertIn("memory_percent", metrics)

        # 测试性能摘要
        summary = dashboard.get_performance_summary()
        self.assertIn("overall_score", summary)
        self.assertIn("overall_level", summary)

    def test_error_handling_integration(self):
        """测试错误处理集成"""
        from interactive_feedback_server.error_handling import ValidationError

        handler = get_error_handler()

        # 创建测试错误
        error = ValidationError("测试验证错误", field="test_field")

        # 处理错误
        result = handler.handle_error(error)

        # 验证处理结果
        self.assertIsNotNone(result)

        # 检查统计
        stats = handler.get_error_statistics()
        self.assertGreater(stats["total_errors"], 0)


def run_optimization_tests():
    """运行优化测试"""
    print("=" * 60)
    print("代码优化测试套件 (Code Optimization Test Suite)")
    print("=" * 60)

    if not OPTIMIZATION_AVAILABLE:
        print("⚠️  优化模块不可用，跳过测试")
        return False

    # 创建测试套件
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestSingletonManager))
    suite.addTest(
        unittest.TestLoader().loadTestsFromTestCase(TestUnifiedStatsCollector)
    )
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestUnifiedConfigLoader))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestOptimizedIntegration))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 显示优化统计
    print("\n" + "=" * 60)
    print("代码优化统计信息 (Code Optimization Statistics)")
    print("=" * 60)

    try:
        # 单例管理器统计
        manager = get_singleton_manager()
        print(f"已注册单例: {manager.get_registered_names()}")
        print(f"活跃实例: {manager.get_active_instances()}")

        # 统计收集器统计
        stats_collector = get_stats_collector()
        all_stats = stats_collector.get_all_stats()
        print(
            f"统计收集器: {len(all_stats['counters'])} 计数器, {len(all_stats['gauges'])} 仪表"
        )

        # 配置加载器统计
        config_loader = get_config_loader()
        print(f"已注册配置: {config_loader.get_registered_configs()}")

    except Exception as e:
        print(f"获取优化统计失败: {e}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_optimization_tests()
    sys.exit(0 if success else 1)
