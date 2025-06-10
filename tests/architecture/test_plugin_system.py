# tests/architecture/test_plugin_system.py

"""
插件系统测试套件
Plugin System Test Suite

测试插件化架构的功能和性能
Tests functionality and performance of plugin architecture
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# 添加源代码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from interactive_feedback_server.plugins import (
    PluginManager,
    get_plugin_manager,
    PluginInterface,
    BasePlugin,
    PluginMetadata,
    PluginType,
    PluginStatus,
    PluginContext,
)
from interactive_feedback_server.utils.option_resolver import get_option_resolver


class TestPluginInterface(unittest.TestCase):
    """插件接口测试"""

    def setUp(self):
        """测试前准备"""
        self.metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="测试插件",
            author="Test Author",
            plugin_type=PluginType.INTEGRATION,
            dependencies=[],
        )

    def test_plugin_metadata(self):
        """测试插件元数据"""
        self.assertEqual(self.metadata.name, "test_plugin")
        self.assertEqual(self.metadata.version, "1.0.0")
        self.assertEqual(self.metadata.plugin_type, PluginType.INTEGRATION)
        self.assertIsInstance(self.metadata.dependencies, list)
        self.assertIsInstance(self.metadata.permissions, list)

    def test_base_plugin_lifecycle(self):
        """测试基础插件生命周期"""
        plugin = BasePlugin(self.metadata)

        # 初始状态
        self.assertEqual(plugin.get_status(), PluginStatus.UNLOADED)
        self.assertFalse(plugin.is_initialized())
        self.assertFalse(plugin.is_active())

        # 初始化
        context = PluginContext(system_version="3.3.0", config={})
        self.assertTrue(plugin.initialize(context))
        self.assertEqual(plugin.get_status(), PluginStatus.LOADED)
        self.assertTrue(plugin.is_initialized())

        # 激活
        self.assertTrue(plugin.activate())
        self.assertEqual(plugin.get_status(), PluginStatus.ACTIVE)
        self.assertTrue(plugin.is_active())

        # 停用
        self.assertTrue(plugin.deactivate())
        self.assertEqual(plugin.get_status(), PluginStatus.INACTIVE)
        self.assertFalse(plugin.is_active())

        # 清理
        self.assertTrue(plugin.cleanup())
        self.assertEqual(plugin.get_status(), PluginStatus.UNLOADED)
        self.assertFalse(plugin.is_initialized())

    def test_plugin_stats(self):
        """测试插件统计"""
        plugin = BasePlugin(self.metadata)

        stats = plugin.get_stats()
        self.assertIn("name", stats)
        self.assertIn("version", stats)
        self.assertIn("type", stats)
        self.assertIn("status", stats)
        self.assertEqual(stats["name"], "test_plugin")
        self.assertEqual(stats["version"], "1.0.0")


class TestPluginManager(unittest.TestCase):
    """插件管理器测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_manager = PluginManager(
            plugin_dirs=[self.temp_dir], system_version="3.3.0"
        )

    def tearDown(self):
        """测试后清理"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_plugin_manager_initialization(self):
        """测试插件管理器初始化"""
        self.assertIsInstance(self.plugin_manager.plugin_dirs, list)
        self.assertIn(self.temp_dir, self.plugin_manager.plugin_dirs)
        self.assertEqual(self.plugin_manager.system_version, "3.3.0")

    def test_add_plugin_directory(self):
        """测试添加插件目录"""
        new_dir = tempfile.mkdtemp()
        try:
            self.assertTrue(self.plugin_manager.add_plugin_directory(new_dir))
            self.assertIn(new_dir, self.plugin_manager.plugin_dirs)
        finally:
            import shutil

            shutil.rmtree(new_dir, ignore_errors=True)

    def test_discover_plugins(self):
        """测试插件发现"""
        # 创建测试插件文件
        test_plugin_content = """
from interactive_feedback_server.plugins import BasePlugin, PluginMetadata, PluginType

class TestPlugin(BasePlugin):
    def __init__(self, metadata):
        super().__init__(metadata)
"""

        test_plugin_path = Path(self.temp_dir) / "test_plugin.py"
        with open(test_plugin_path, "w", encoding="utf-8") as f:
            f.write(test_plugin_content)

        # 发现插件
        discovered = self.plugin_manager.discover_plugins()
        self.assertIsInstance(discovered, list)

    def test_plugin_lifecycle_management(self):
        """测试插件生命周期管理"""
        # 创建简单的测试插件
        test_plugin_content = """
from interactive_feedback_server.plugins import BasePlugin, PluginMetadata, PluginType

class SimpleTestPlugin(BasePlugin):
    def __init__(self, metadata):
        super().__init__(metadata)

def create_plugin():
    metadata = PluginMetadata(
        name="simple_test",
        version="1.0.0",
        description="简单测试插件",
        author="Test",
        plugin_type=PluginType.INTEGRATION,
        dependencies=[]
    )
    return SimpleTestPlugin(metadata)
"""

        test_plugin_path = Path(self.temp_dir) / "simple_test_plugin.py"
        with open(test_plugin_path, "w", encoding="utf-8") as f:
            f.write(test_plugin_content)

        # 加载插件
        plugin_name = "simple_test_plugin"
        self.assertTrue(
            self.plugin_manager.load_plugin(str(test_plugin_path), plugin_name)
        )

        # 检查插件是否已加载
        plugin = self.plugin_manager.get_plugin(plugin_name)
        self.assertIsNotNone(plugin)

        # 激活插件
        self.assertTrue(self.plugin_manager.activate_plugin(plugin_name))

        # 检查活跃插件
        active_plugins = self.plugin_manager.get_active_plugins()
        self.assertTrue(len(active_plugins) > 0)

        # 停用插件
        self.assertTrue(self.plugin_manager.deactivate_plugin(plugin_name))

        # 卸载插件
        self.assertTrue(self.plugin_manager.unload_plugin(plugin_name))

        # 检查插件是否已卸载
        plugin = self.plugin_manager.get_plugin(plugin_name)
        self.assertIsNone(plugin)

    def test_get_plugins_by_type(self):
        """测试按类型获取插件"""
        plugins = self.plugin_manager.get_plugins_by_type(PluginType.OPTION_STRATEGY)
        self.assertIsInstance(plugins, list)

    def test_manager_stats(self):
        """测试管理器统计"""
        stats = self.plugin_manager.get_manager_stats()

        self.assertIn("manager_stats", stats)
        self.assertIn("plugin_directories", stats)
        self.assertIn("system_version", stats)
        self.assertIn("plugins", stats)

        self.assertEqual(stats["system_version"], "3.3.0")


class TestPluginIntegration(unittest.TestCase):
    """插件集成测试"""

    def test_global_plugin_manager(self):
        """测试全局插件管理器"""
        manager1 = get_plugin_manager()
        manager2 = get_plugin_manager()

        # 应该返回同一个实例
        self.assertIs(manager1, manager2)
        self.assertIsInstance(manager1, PluginManager)

    def test_option_resolver_plugin_integration(self):
        """测试选项解析器插件集成"""
        resolver = get_option_resolver()

        # 检查插件集成是否启用
        stats = resolver.get_resolver_stats()
        self.assertIn("plugin_integration_enabled", stats)

        # 检查插件统计
        if stats["plugin_integration_enabled"]:
            self.assertIn("plugin_stats", stats)

    def test_plugin_loading_through_resolver(self):
        """测试通过解析器加载插件"""
        resolver = get_option_resolver()

        # 获取已加载的插件
        loaded_plugins = resolver.get_loaded_plugins()
        self.assertIsInstance(loaded_plugins, list)


class TestBuiltinPlugins(unittest.TestCase):
    """内置插件测试"""

    def test_enhanced_ai_strategy_plugin_import(self):
        """测试增强AI策略插件导入"""
        try:
            from interactive_feedback_server.plugins.builtin.enhanced_ai_strategy_plugin import (
                EnhancedAIStrategy,
                EnhancedAIStrategyPlugin,
                create_plugin,
            )

            # 测试插件创建
            plugin = create_plugin()
            self.assertIsInstance(plugin, EnhancedAIStrategyPlugin)
            self.assertEqual(plugin.metadata.name, "enhanced_ai_strategy")

        except ImportError as e:
            self.skipTest(f"内置插件导入失败: {e}")

    def test_enhanced_ai_strategy_functionality(self):
        """测试增强AI策略功能"""
        try:
            from interactive_feedback_server.plugins.builtin.enhanced_ai_strategy_plugin import (
                EnhancedAIStrategy,
            )
            from interactive_feedback_server.utils.option_strategy import OptionContext

            # 创建策略实例
            strategy = EnhancedAIStrategy()

            # 测试策略基本属性
            self.assertEqual(strategy.name, "enhanced_ai_options")
            self.assertEqual(strategy.priority, 0)

            # 测试策略适用性
            context = OptionContext(
                text="你觉得怎么样？", ai_options=["很好", "不错", "需要改进"]
            )
            self.assertTrue(strategy.is_applicable(context))

            # 测试选项解析
            result = strategy.parse_options(context)
            self.assertIsNotNone(result)
            self.assertIsInstance(result.options, list)
            self.assertTrue(len(result.options) > 0)

        except ImportError as e:
            self.skipTest(f"增强AI策略导入失败: {e}")


def run_plugin_system_tests():
    """运行插件系统测试"""
    print("=" * 60)
    print("插件系统测试套件 (Plugin System Test Suite)")
    print("=" * 60)

    # 创建测试套件
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestPluginInterface))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestPluginManager))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestPluginIntegration))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestBuiltinPlugins))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 显示插件统计
    print("\n" + "=" * 60)
    print("插件系统统计信息 (Plugin System Statistics)")
    print("=" * 60)

    try:
        from interactive_feedback_server.utils.option_resolver import (
            get_option_resolver,
        )

        resolver = get_option_resolver()
        stats = resolver.get_resolver_stats()

        if stats.get("plugin_integration_enabled"):
            plugin_stats = stats.get("plugin_stats", {})
            print(f"插件系统状态: 已启用")
            print(f"插件统计: {plugin_stats}")
        else:
            print(f"插件系统状态: 未启用")

    except Exception as e:
        print(f"获取插件统计失败: {e}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_plugin_system_tests()
    sys.exit(0 if success else 1)
