# tests/architecture/test_configurable_rules.py

"""
可配置规则引擎测试套件
Configurable Rule Engine Test Suite

测试可配置规则引擎的功能和性能
Tests functionality and performance of configurable rule engine
"""

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

# 添加源代码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from interactive_feedback_server.utils.configurable_rule_engine import (
    ConfigurableRuleEngine,
    get_configurable_rule_engine,
    extract_options_configurable,
)
from interactive_feedback_server.utils.rule_engine import (
    extract_options_from_text,
    reload_configurable_rules,
    add_custom_rule_pattern,
    get_rule_engine_performance_stats,
)


class TestConfigurableRuleEngine(unittest.TestCase):
    """可配置规则引擎基础功能测试"""

    def setUp(self):
        """测试前准备"""
        # 创建临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_rules.json"

        # 测试配置
        self.test_config = {
            "version": "1.0",
            "languages": {
                "zh_CN": {
                    "patterns": {
                        "test_question": {
                            "triggers": ["测试", "问题"],
                            "options": ["是的", "不是", "不确定"],
                            "priority": 1,
                            "enabled": True,
                        },
                        "test_action": {
                            "triggers": ["执行", "运行"],
                            "options": ["开始", "取消", "暂停"],
                            "priority": 2,
                            "enabled": True,
                        },
                    }
                },
                "en_US": {
                    "patterns": {
                        "test_question": {
                            "triggers": ["test", "question"],
                            "options": ["Yes", "No", "Maybe"],
                            "priority": 1,
                            "enabled": True,
                        }
                    }
                },
            },
            "global_settings": {
                "max_options": 3,
                "case_sensitive": False,
                "cache_enabled": True,
                "hot_reload": True,
            },
        }

        # 保存测试配置
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.test_config, f, ensure_ascii=False, indent=2)

        # 创建测试引擎
        self.engine = ConfigurableRuleEngine(str(self.config_path))

    def tearDown(self):
        """测试后清理"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_rules(self):
        """测试规则加载"""
        self.assertTrue(self.engine.load_rules())
        self.assertIn("languages", self.engine.rules)
        self.assertIn("zh_CN", self.engine.rules["languages"])
        self.assertIn("en_US", self.engine.rules["languages"])

    def test_extract_options_chinese(self):
        """测试中文选项提取"""
        # 测试问题场景
        result = self.engine.extract_options("这是一个测试问题", "zh_CN")
        self.assertEqual(result, ["是的", "不是", "不确定"])

        # 测试动作场景
        result = self.engine.extract_options("请执行这个操作", "zh_CN")
        self.assertEqual(result, ["开始", "取消", "暂停"])

        # 测试无匹配
        result = self.engine.extract_options("普通文本", "zh_CN")
        self.assertEqual(result, [])

    def test_extract_options_english(self):
        """测试英文选项提取"""
        result = self.engine.extract_options("This is a test question", "en_US")
        self.assertEqual(result, ["Yes", "No", "Maybe"])

        # 测试无匹配
        result = self.engine.extract_options("normal text", "en_US")
        self.assertEqual(result, [])

    def test_priority_matching(self):
        """测试优先级匹配"""
        # 同时包含多个触发器，应该返回优先级最高的
        result = self.engine.extract_options("测试执行问题", "zh_CN")
        self.assertEqual(result, ["是的", "不是", "不确定"])  # 优先级1的问题场景

    def test_add_custom_pattern(self):
        """测试添加自定义模式"""
        custom_pattern = {
            "triggers": ["自定义", "测试"],
            "options": ["选项1", "选项2"],
            "priority": 5,
            "enabled": True,
        }

        success = self.engine.add_custom_pattern("zh_CN", "custom_test", custom_pattern)
        self.assertTrue(success)

        # 测试自定义模式
        result = self.engine.extract_options("这是自定义测试", "zh_CN")
        self.assertEqual(result, ["选项1", "选项2"])

    def test_remove_pattern(self):
        """测试移除模式"""
        # 先添加一个模式
        custom_pattern = {
            "triggers": ["临时"],
            "options": ["临时选项"],
            "priority": 10,
            "enabled": True,
        }
        self.engine.add_custom_pattern("zh_CN", "temp_pattern", custom_pattern)

        # 验证模式存在
        result = self.engine.extract_options("临时测试", "zh_CN")
        self.assertEqual(result, ["临时选项"])

        # 移除模式
        success = self.engine.remove_pattern("zh_CN", "temp_pattern")
        self.assertTrue(success)

        # 验证模式已移除
        result = self.engine.extract_options("临时测试", "zh_CN")
        self.assertEqual(result, [])

    def test_hot_reload(self):
        """测试热重载功能"""
        # 修改配置文件
        modified_config = self.test_config.copy()
        modified_config["languages"]["zh_CN"]["patterns"]["new_pattern"] = {
            "triggers": ["新模式"],
            "options": ["新选项"],
            "priority": 1,
            "enabled": True,
        }

        # 保存修改后的配置
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(modified_config, f, ensure_ascii=False, indent=2)

        # 等待文件修改时间更新
        time.sleep(0.1)

        # 测试热重载
        result = self.engine.extract_options("新模式测试", "zh_CN")
        self.assertEqual(result, ["新选项"])

    def test_cache_functionality(self):
        """测试缓存功能"""
        # 第一次调用
        result1 = self.engine.extract_options("测试问题", "zh_CN")
        stats1 = self.engine.get_stats()

        # 第二次调用相同文本
        result2 = self.engine.extract_options("测试问题", "zh_CN")
        stats2 = self.engine.get_stats()

        # 结果应该相同
        self.assertEqual(result1, result2)

        # 缓存命中次数应该增加
        self.assertGreater(stats2["cache_hit_count"], stats1["cache_hit_count"])

    def test_get_stats(self):
        """测试统计信息"""
        # 执行一些操作
        self.engine.extract_options("测试", "zh_CN")
        self.engine.extract_options("问题", "zh_CN")

        stats = self.engine.get_stats()

        # 验证统计信息
        self.assertIn("load_count", stats)
        self.assertIn("match_count", stats)
        self.assertIn("cache_hit_count", stats)
        self.assertIn("available_languages", stats)
        self.assertGreater(stats["match_count"], 0)


class TestRuleEngineIntegration(unittest.TestCase):
    """规则引擎集成测试"""

    def test_extract_options_with_configurable(self):
        """测试使用可配置引擎的选项提取"""
        # 测试中文
        result = extract_options_from_text(
            "你觉得怎么样？", "zh_CN", use_configurable=True
        )
        self.assertIsInstance(result, list)

        # 测试英文
        result = extract_options_from_text(
            "What do you think?", "en_US", use_configurable=True
        )
        self.assertIsInstance(result, list)

    def test_extract_options_fallback(self):
        """测试回退到传统方法"""
        # 禁用可配置引擎
        result = extract_options_from_text(
            "你觉得怎么样？", "zh_CN", use_configurable=False
        )
        self.assertIsInstance(result, list)

    def test_add_custom_rule_pattern_function(self):
        """测试添加自定义规则模式函数"""
        success = add_custom_rule_pattern(
            language="zh_CN",
            name="test_custom",
            triggers=["自定义触发"],
            options=["自定义选项1", "自定义选项2"],
            priority=5,
        )
        self.assertIsInstance(success, bool)

    def test_reload_configurable_rules_function(self):
        """测试重新加载规则函数"""
        success = reload_configurable_rules()
        self.assertIsInstance(success, bool)

    def test_performance_stats_integration(self):
        """测试性能统计集成"""
        stats = get_rule_engine_performance_stats()

        self.assertIn("configurable_engine", stats)
        self.assertIn("version", stats)
        self.assertEqual(stats["version"], "V3.3-Architecture")


class TestGlobalFunctions(unittest.TestCase):
    """全局函数测试"""

    def test_get_configurable_rule_engine(self):
        """测试获取全局引擎"""
        engine = get_configurable_rule_engine()
        self.assertIsInstance(engine, ConfigurableRuleEngine)

        # 多次调用应该返回同一个实例
        engine2 = get_configurable_rule_engine()
        self.assertIs(engine, engine2)

    def test_extract_options_configurable_function(self):
        """测试全局选项提取函数"""
        result = extract_options_configurable("你好吗？", "zh_CN")
        self.assertIsInstance(result, list)


class TestErrorHandling(unittest.TestCase):
    """错误处理测试"""

    def test_invalid_config_file(self):
        """测试无效配置文件"""
        # 创建无效的配置文件
        temp_dir = tempfile.mkdtemp()
        invalid_config_path = Path(temp_dir) / "invalid.json"

        with open(invalid_config_path, "w") as f:
            f.write("invalid json content")

        try:
            engine = ConfigurableRuleEngine(str(invalid_config_path))
            # 应该回退到默认配置
            self.assertIn("languages", engine.rules)
        finally:
            import shutil

            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_missing_config_file(self):
        """测试缺失配置文件"""
        engine = ConfigurableRuleEngine("nonexistent/path/rules.json")
        # 应该使用默认配置
        self.assertIn("languages", engine.rules)

    def test_invalid_pattern_addition(self):
        """测试无效模式添加"""
        engine = get_configurable_rule_engine()

        # 缺少必需字段的模式
        invalid_pattern = {
            "triggers": ["test"]
            # 缺少 options 和 priority
        }

        success = engine.add_custom_pattern("zh_CN", "invalid", invalid_pattern)
        self.assertFalse(success)


def run_configurable_rules_tests():
    """运行可配置规则测试"""
    print("=" * 60)
    print("可配置规则引擎测试套件 (Configurable Rule Engine Test Suite)")
    print("=" * 60)

    # 创建测试套件
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTest(
        unittest.TestLoader().loadTestsFromTestCase(TestConfigurableRuleEngine)
    )
    suite.addTest(
        unittest.TestLoader().loadTestsFromTestCase(TestRuleEngineIntegration)
    )
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestGlobalFunctions))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestErrorHandling))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 显示性能统计
    print("\n" + "=" * 60)
    print("可配置规则引擎统计信息 (Configurable Rule Engine Statistics)")
    print("=" * 60)

    try:
        stats = get_rule_engine_performance_stats()
        print(f"规则引擎统计: {stats}")
    except Exception as e:
        print(f"获取统计信息失败: {e}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_configurable_rules_tests()
    sys.exit(0 if success else 1)
