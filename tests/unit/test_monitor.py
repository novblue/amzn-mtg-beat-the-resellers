from unittest.mock import Mock, patch

import pytest
from amazon_monitor.config.settings import Config
from amazon_monitor.core.monitor import PreorderMonitor


class TestPreorderMonitor:
    @pytest.fixture(autouse=True)
    def setup(self, encrypted_password, mock_browser_manager):
        """Set up test fixtures."""
        self.config = Config(
            email="test@example.com",
            password_encrypted=encrypted_password,
            product_url="https://www.amazon.com/dp/B123456789"
        )
        self.browser_manager = mock_browser_manager
        self.monitor = PreorderMonitor(self.config, self.browser_manager)

    def test_monitor_initialization(self, config, mock_browser_manager):
        monitor = PreorderMonitor(config, mock_browser_manager)

        assert monitor.config == config
        assert monitor.browser_manager == mock_browser_manager
        assert monitor.is_running is False

    def test_start_monitoring_success(self, config, mock_browser_manager):
        monitor = PreorderMonitor(config, mock_browser_manager)

        # Mock the monitoring loop to avoid infinite loop
        with patch.object(monitor, '_monitoring_loop', return_value=True) as mock_loop:
            monitor.start()

            # The monitor should have tried to run the loop
            mock_loop.assert_called_once()
            # After start() completes, is_running should be False (cleanup)
            assert monitor.is_running is False

    def test_stop_monitoring(self, config, mock_browser_manager):
        monitor = PreorderMonitor(config, mock_browser_manager)
        monitor.is_running = True

        monitor.stop()

        assert monitor.is_running is False
        # Verify browser cleanup was called
        mock_browser_manager.cleanup.assert_called_once()

    def test_monitoring_loop_finds_available_product(self, config, mock_browser_manager, mock_driver):
        monitor = PreorderMonitor(config, mock_browser_manager)
        mock_browser_manager.get_driver.return_value = mock_driver

        # Mock all the dependencies
        with patch.object(monitor, '_initialize_session', return_value=True):
            with patch.object(monitor, '_check_availability', return_value=True):
                with patch.object(monitor, '_attempt_purchase', return_value=True):
                    # Set is_running to False after first iteration to avoid infinite loop
                    monitor.is_running = True
                    def stop_after_first_check(*args):
                        monitor.is_running = False
                        return True

                    with patch.object(monitor, '_check_availability', side_effect=stop_after_first_check):
                        result = monitor._monitoring_loop()

                        assert result is True  # Successfully purchased

    def test_monitoring_loop_session_initialization_fails(self, config, mock_browser_manager, mock_driver):
        monitor = PreorderMonitor(config, mock_browser_manager)
        mock_browser_manager.get_driver.return_value = mock_driver

        with patch.object(monitor, '_initialize_session', return_value=False):
            result = monitor._monitoring_loop()

            assert result is False

    def test_initialize_session_with_valid_existing_session(self, encrypted_password):
        """Test session initialization with valid existing session."""
        # Create a real config instead of using the mocked one
        real_config = Config(
            email="test@example.com",
            password_encrypted=encrypted_password,
            product_url="https://www.amazon.com/dp/B123456789"
        )

        # Update the monitor to use the real config
        self.monitor.config = real_config
        self.monitor.auth.config = real_config  # Update auth config too

        mock_driver = Mock()

        # Mock both the quick session check and the full session validation
        with patch.object(self.monitor, '_quick_session_check', return_value=True):
            result = self.monitor._initialize_session(mock_driver)
            assert result is True


    def test_initialize_session_with_successful_login(self, config, mock_browser_manager, mock_driver):
        monitor = PreorderMonitor(config, mock_browser_manager)

        # Mock auth: invalid session but successful login
        with patch.object(monitor.auth, 'is_session_valid', return_value=False):
            with patch.object(monitor.auth, 'login', return_value=True):
                result = monitor._initialize_session(mock_driver)

                assert result is True

    def test_initialize_session_fails(self, config, mock_browser_manager, mock_driver):
        monitor = PreorderMonitor(config, mock_browser_manager)

        # Mock auth: invalid session and failed login
        with patch.object(monitor.auth, 'is_session_valid', return_value=False):
            with patch.object(monitor.auth, 'login', return_value=False):
                result = monitor._initialize_session(mock_driver)

                assert result is False

    def test_should_check_session_logic(self, config, mock_browser_manager):
        monitor = PreorderMonitor(config, mock_browser_manager)

        # Should not check session initially
        assert monitor._should_check_session() is False

        # Set counter high enough to trigger check
        monitor.session_check_counter = 10
        assert monitor._should_check_session() is True

        # Counter should reset after check
        assert monitor.session_check_counter == 0

    def test_should_do_random_browsing_logic(self, config, mock_browser_manager):
        monitor = PreorderMonitor(config, mock_browser_manager)

        # Should not browse initially
        assert monitor._should_do_random_browsing() is False

        # Set count to trigger browsing (mock random to be predictable)
        with patch('random.randint', return_value=1):
            monitor.check_count = 1
            assert monitor._should_do_random_browsing() is True

    def test_handle_random_browsing(self, config, mock_browser_manager, mock_driver):
        monitor = PreorderMonitor(config, mock_browser_manager)

        # Mock time.sleep to speed up test
        with patch('time.sleep'):
            with patch('random.choice', return_value="https://www.amazon.com/gp/bestsellers"):
                with patch('random.uniform', return_value=1.0):
                    with patch('random.randint', return_value=1):
                        monitor._handle_random_browsing(mock_driver)

                        # Verify driver was used
                        mock_driver.get.assert_called_with("https://www.amazon.com/gp/bestsellers")
                        mock_driver.execute_script.assert_called()

    def test_calculate_interval_with_randomization(self, config, mock_browser_manager):
        monitor = PreorderMonitor(config, mock_browser_manager)

        # Test with large interval (should add randomization)
        monitor.config.refresh_interval = 60
        with patch('random.randint', return_value=5):
            interval = monitor._calculate_interval()
            assert interval == 65  # 60 + 5

        # Test with small interval (no randomization)
        monitor.config.refresh_interval = 10
        interval = monitor._calculate_interval()
        assert interval == 10