# tests/architecture/test_error_handling.py

"""
错误处理系统测试套件
Error Handling System Test Suite

测试分级错误处理、自动恢复和系统稳定性功能
Tests hierarchical error handling, automatic recovery and system stability functionality
"""

import os
import sys
import time
import unittest
from unittest.mock import patch, MagicMock

# 添加源代码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

try:
    from interactive_feedback_server.error_handling import (
        ErrorLevel,
        ErrorCategory,
        RecoveryStrategy,
        ErrorContext,
        ErrorInfo,
        SystemError,
        ValidationError,
        ConfigurationError,
        PluginError,
        ErrorHandler,
        RecoveryManager,
        RecoveryTask,
        RecoveryStatus,
        get_error_handler,
        get_recovery_manager,
        create_error_context,
        create_system_error,
    )

    ERROR_HANDLING_AVAILABLE = True
except ImportError as e:
    print(f"错误处理模块导入失败: {e}")
    ERROR_HANDLING_AVAILABLE = False


@unittest.skipUnless(ERROR_HANDLING_AVAILABLE, "错误处理模块不可用")
class TestErrorTypes(unittest.TestCase):
    """错误类型测试"""

    def test_error_context_creation(self):
        """测试错误上下文创建"""
        context = create_error_context(
            component="test_component",
            operation="test_operation",
            user_id="user123",
            test_data="test_value",
        )

        self.assertEqual(context.component, "test_component")
        self.assertEqual(context.operation, "test_operation")
        self.assertEqual(context.user_id, "user123")
        self.assertEqual(context.additional_data["test_data"], "test_value")
        self.assertIsInstance(context.timestamp, float)

    def test_system_error_creation(self):
        """测试系统错误创建"""
        context = create_error_context("test", "test")
        error = create_system_error(
            level=ErrorLevel.ERROR,
            category=ErrorCategory.VALIDATION,
            message="测试错误",
            description="这是一个测试错误",
            context=context,
            recovery_strategy=RecoveryStrategy.RETRY,
        )

        self.assertIsInstance(error, SystemError)
        self.assertEqual(error.error_info.level, ErrorLevel.ERROR)
        self.assertEqual(error.error_info.category, ErrorCategory.VALIDATION)
        self.assertEqual(error.error_info.message, "测试错误")
        self.assertEqual(error.error_info.recovery_strategy, RecoveryStrategy.RETRY)

    def test_validation_error(self):
        """测试验证错误"""
        error = ValidationError("字段验证失败", field="email", value="invalid_email")

        self.assertIsInstance(error, SystemError)
        self.assertEqual(error.error_info.level, ErrorLevel.WARNING)
        self.assertEqual(error.error_info.category, ErrorCategory.VALIDATION)
        self.assertIn("字段验证失败", error.error_info.message)

    def test_configuration_error(self):
        """测试配置错误"""
        error = ConfigurationError("配置文件缺失", config_key="database.url")

        self.assertIsInstance(error, SystemError)
        self.assertEqual(error.error_info.level, ErrorLevel.ERROR)
        self.assertEqual(error.error_info.category, ErrorCategory.CONFIGURATION)
        self.assertEqual(error.error_info.recovery_strategy, RecoveryStrategy.FALLBACK)

    def test_plugin_error(self):
        """测试插件错误"""
        error = PluginError("插件加载失败", plugin_name="test_plugin")

        self.assertIsInstance(error, SystemError)
        self.assertEqual(error.error_info.level, ErrorLevel.ERROR)
        self.assertEqual(error.error_info.category, ErrorCategory.PLUGIN)
        self.assertEqual(
            error.error_info.recovery_strategy, RecoveryStrategy.GRACEFUL_DEGRADATION
        )


@unittest.skipUnless(ERROR_HANDLING_AVAILABLE, "错误处理模块不可用")
class TestErrorHandler(unittest.TestCase):
    """错误处理器测试"""

    def setUp(self):
        """测试前准备"""
        self.handler = ErrorHandler(max_error_history=100)

    def test_error_handler_initialization(self):
        """测试错误处理器初始化"""
        self.assertIsInstance(self.handler._recovery_handlers, dict)
        self.assertIn(RecoveryStrategy.RETRY, self.handler._recovery_handlers)
        self.assertIn(RecoveryStrategy.FALLBACK, self.handler._recovery_handlers)

    def test_handle_system_error(self):
        """测试处理系统错误"""
        context = create_error_context("test", "test")
        error = create_system_error(
            level=ErrorLevel.WARNING,
            category=ErrorCategory.VALIDATION,
            message="测试错误",
            context=context,
            recovery_strategy=RecoveryStrategy.FALLBACK,
        )

        result = self.handler.handle_error(error)

        # 验证错误已记录
        stats = self.handler.get_error_statistics()
        self.assertEqual(stats["total_errors"], 1)
        self.assertEqual(stats["errors_by_level"]["warning"], 1)
        self.assertEqual(stats["errors_by_category"]["validation"], 1)

        # 验证恢复策略已执行
        self.assertIsNotNone(result)
        self.assertEqual(result["action"], "fallback")

    def test_handle_regular_exception(self):
        """测试处理普通异常"""
        context = create_error_context("test", "test")
        exception = ValueError("测试异常")

        result = self.handler.handle_error(exception, context)

        # 验证异常已转换为SystemError并处理
        stats = self.handler.get_error_statistics()
        self.assertEqual(stats["total_errors"], 1)

    def test_retry_strategy(self):
        """测试重试策略"""
        context = create_error_context("test", "test")
        error = create_system_error(
            level=ErrorLevel.ERROR,
            category=ErrorCategory.EXTERNAL_SERVICE,
            message="服务不可用",
            context=context,
            recovery_strategy=RecoveryStrategy.RETRY,
            max_retries=2,
        )

        # 第一次重试
        result1 = self.handler.handle_error(error)
        self.assertEqual(result1["action"], "retry")
        self.assertEqual(result1["attempt"], 1)

        # 第二次重试
        result2 = self.handler.handle_error(error)
        self.assertEqual(result2["action"], "retry")
        self.assertEqual(result2["attempt"], 2)

        # 超过最大重试次数
        result3 = self.handler.handle_error(error)
        self.assertIsNone(result3)

    def test_circuit_breaker_strategy(self):
        """测试熔断器策略"""
        context = create_error_context("test_service", "test")

        # 连续失败触发熔断器
        for i in range(6):  # 超过默认阈值5
            error = create_system_error(
                level=ErrorLevel.ERROR,
                category=ErrorCategory.EXTERNAL_SERVICE,
                message=f"服务失败 {i}",
                context=context,
                recovery_strategy=RecoveryStrategy.CIRCUIT_BREAKER,
            )
            result = self.handler.handle_error(error)

        # 验证熔断器已打开
        self.assertTrue(self.handler.is_circuit_breaker_open("test_service"))

    def test_error_statistics(self):
        """测试错误统计"""
        # 添加不同类型的错误
        errors = [
            ValidationError("验证错误1"),
            ConfigurationError("配置错误1"),
            PluginError("插件错误1"),
        ]

        for error in errors:
            self.handler.handle_error(error)

        stats = self.handler.get_error_statistics()

        self.assertEqual(stats["total_errors"], 3)
        self.assertEqual(stats["errors_by_category"]["validation"], 1)
        self.assertEqual(stats["errors_by_category"]["configuration"], 1)
        self.assertEqual(stats["errors_by_category"]["plugin"], 1)

    def test_recent_errors(self):
        """测试获取最近错误"""
        # 添加一些错误
        for i in range(5):
            error = ValidationError(f"错误 {i}")
            self.handler.handle_error(error)

        recent_errors = self.handler.get_recent_errors(3)
        self.assertEqual(len(recent_errors), 3)

        # 验证是最近的错误
        self.assertIn("错误 4", recent_errors[-1].error_info.message)


@unittest.skipUnless(ERROR_HANDLING_AVAILABLE, "错误处理模块不可用")
class TestRecoveryManager(unittest.TestCase):
    """恢复管理器测试"""

    def setUp(self):
        """测试前准备"""
        self.recovery_manager = RecoveryManager()
        # 停止自动恢复以便测试
        self.recovery_manager.set_auto_recovery(False)

    def test_recovery_manager_initialization(self):
        """测试恢复管理器初始化"""
        self.assertIsInstance(self.recovery_manager._recovery_tasks, dict)
        self.assertIsInstance(self.recovery_manager._task_queue, list)

    def test_register_recovery_function(self):
        """测试注册恢复函数"""

        def test_recovery():
            return "恢复成功"

        task_id = self.recovery_manager.register_recovery_function(
            component="test_component",
            operation="test_operation",
            recovery_function=test_recovery,
            priority=5,
            max_attempts=3,
        )

        self.assertIsNotNone(task_id)
        self.assertIn(task_id, self.recovery_manager._recovery_tasks)

        task = self.recovery_manager._recovery_tasks[task_id]
        self.assertEqual(task.component, "test_component")
        self.assertEqual(task.operation, "test_operation")
        self.assertEqual(task.priority, 5)
        self.assertEqual(task.max_attempts, 3)

    def test_execute_recovery_task(self):
        """测试执行恢复任务"""

        def test_recovery():
            return "恢复成功"

        task_id = self.recovery_manager.register_recovery_function(
            component="test", operation="test", recovery_function=test_recovery
        )

        # 执行恢复任务
        success = self.recovery_manager.execute_recovery(task_id)
        self.assertTrue(success)

        # 等待任务完成
        time.sleep(0.1)

        # 检查任务状态
        task = self.recovery_manager.get_recovery_status(task_id)
        self.assertEqual(task.status, RecoveryStatus.SUCCESS)
        self.assertEqual(task.result, "恢复成功")

    def test_recovery_task_failure(self):
        """测试恢复任务失败"""

        def failing_recovery():
            raise Exception("恢复失败")

        task_id = self.recovery_manager.register_recovery_function(
            component="test",
            operation="test",
            recovery_function=failing_recovery,
            max_attempts=1,
        )

        # 执行恢复任务
        success = self.recovery_manager.execute_recovery(task_id)
        self.assertTrue(success)

        # 等待任务完成
        time.sleep(0.1)

        # 检查任务状态
        task = self.recovery_manager.get_recovery_status(task_id)
        self.assertEqual(task.status, RecoveryStatus.FAILED)
        self.assertIsNotNone(task.error_message)

    def test_health_check_registration(self):
        """测试健康检查注册"""

        def test_health_check():
            return True

        self.recovery_manager.register_health_check("test_component", test_health_check)

        health_status = self.recovery_manager.get_system_health()
        self.assertIn("test_component", health_status["component_status"])
        self.assertTrue(health_status["component_status"]["test_component"])

    def test_recovery_statistics(self):
        """测试恢复统计"""

        def test_recovery():
            return "成功"

        # 注册并执行一个恢复任务
        task_id = self.recovery_manager.register_recovery_function(
            component="test", operation="test", recovery_function=test_recovery
        )

        self.recovery_manager.execute_recovery(task_id)
        time.sleep(0.1)  # 等待完成

        stats = self.recovery_manager.get_recovery_statistics()

        self.assertEqual(stats["total_tasks"], 1)
        self.assertEqual(stats["successful_recoveries"], 1)
        self.assertGreater(stats["success_rate_percent"], 0)


@unittest.skipUnless(ERROR_HANDLING_AVAILABLE, "错误处理模块不可用")
class TestErrorHandlingIntegration(unittest.TestCase):
    """错误处理集成测试"""

    def test_global_instances(self):
        """测试全局实例"""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        self.assertIs(handler1, handler2)

        manager1 = get_recovery_manager()
        manager2 = get_recovery_manager()
        self.assertIs(manager1, manager2)

    def test_option_resolver_error_handling_integration(self):
        """测试选项解析器错误处理集成"""
        try:
            from interactive_feedback_server.utils.option_resolver import (
                get_option_resolver,
            )

            resolver = get_option_resolver()

            # 检查错误处理是否已集成
            self.assertTrue(hasattr(resolver, "_error_handling_enabled"))

            # 测试错误处理
            result = resolver.resolve_options("测试文本", None, None, "zh_CN")
            self.assertIsInstance(result, list)

        except ImportError:
            self.skipTest("选项解析器不可用")


def run_error_handling_tests():
    """运行错误处理测试"""
    print("=" * 60)
    print("错误处理系统测试套件 (Error Handling System Test Suite)")
    print("=" * 60)

    if not ERROR_HANDLING_AVAILABLE:
        print("⚠️  错误处理模块不可用，跳过测试")
        return False

    # 创建测试套件
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestErrorTypes))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestErrorHandler))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestRecoveryManager))
    suite.addTest(
        unittest.TestLoader().loadTestsFromTestCase(TestErrorHandlingIntegration)
    )

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 显示错误处理统计
    print("\n" + "=" * 60)
    print("错误处理系统统计信息 (Error Handling System Statistics)")
    print("=" * 60)

    try:
        handler = get_error_handler()
        error_stats = handler.get_error_statistics()
        print(f"错误处理器统计: {error_stats}")

        manager = get_recovery_manager()
        recovery_stats = manager.get_recovery_statistics()
        print(f"恢复管理器统计: {recovery_stats}")

        health_status = manager.get_system_health()
        print(f"系统健康状态: {health_status}")

    except Exception as e:
        print(f"获取错误处理统计失败: {e}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_error_handling_tests()
    sys.exit(0 if success else 1)
