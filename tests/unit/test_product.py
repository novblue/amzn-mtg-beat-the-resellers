from unittest.mock import Mock, patch
from amazon_monitor.amazon.product import ProductChecker
from unittest.mock import Mock, patch

from amazon_monitor.amazon.product import ProductChecker


class TestProductChecker:
    def test_check_availability_direct_button_found(self, config, mock_driver):
        checker = ProductChecker(config)
        mock_button = Mock()

        # Mock the methods called by check_availability
        with patch.object(checker, 'simulate_human_browsing'):
            with patch.object(checker, '_navigate_to_product'):
                with patch.object(checker, '_check_direct_preorder_buttons', return_value=(True, mock_button, "direct")):
                    available, button, button_type = checker.check_availability(mock_driver)

        assert available is True
        assert button == mock_button
        assert button_type == "direct"

    def test_check_availability_buying_options_found(self, config, mock_driver):
        checker = ProductChecker(config)
        mock_button = Mock()

        # Mock the methods called by check_availability
        with patch.object(checker, 'simulate_human_browsing'):
            with patch.object(checker, '_navigate_to_product'):
                with patch.object(checker, '_check_direct_preorder_buttons', return_value=(False, None, None)):
                    with patch.object(checker, '_check_buying_options_buttons', return_value=(True, mock_button, "buying_options")):
                        available, button, button_type = checker.check_availability(mock_driver)

        assert available is True
        assert button == mock_button
        assert button_type == "buying_options"

    def test_check_availability_unavailable_message(self, config, mock_driver):
        checker = ProductChecker(config)

        # Mock the methods called by check_availability
        with patch.object(checker, 'simulate_human_browsing'):
            with patch.object(checker, '_navigate_to_product'):
                with patch.object(checker, '_check_direct_preorder_buttons', return_value=(False, None, None)):
                    with patch.object(checker, '_check_buying_options_buttons', return_value=(False, None, None)):
                        with patch.object(checker, '_check_unavailability_messages', return_value=True):
                            available, button, button_type = checker.check_availability(mock_driver)

        assert available is False
        assert button is None
        assert button_type is None

    def test_simulate_human_browsing(self, config, mock_driver):
        checker = ProductChecker(config)

        with patch.object(checker, '_simulate_referrer_visit'):
            with patch.object(checker, '_scroll_page'):
                with patch.object(checker, '_check_images'):
                    with patch.object(checker, '_scroll_back_to_top'):
                        checker.simulate_human_browsing(mock_driver)

                        # Verify human-like actions were called
                        checker._simulate_referrer_visit.assert_called_once()
                        checker._scroll_page.assert_called_once()
                        checker._check_images.assert_called_once()
                        checker._scroll_back_to_top.assert_called_once()

    def test_check_direct_preorder_buttons_found(self, config, mock_driver):
        checker = ProductChecker(config)
        mock_button = Mock()
        mock_driver.find_elements.return_value = [mock_button]

        available, button, button_type = checker._check_direct_preorder_buttons(mock_driver)

        assert available is True
        assert button == mock_button
        assert button_type == "direct"

    def test_check_direct_preorder_buttons_not_found(self, config, mock_driver):
        checker = ProductChecker(config)
        mock_driver.find_elements.return_value = []

        available, button, button_type = checker._check_direct_preorder_buttons(mock_driver)

        assert available is False
        assert button is None
        assert button_type is None

    def test_check_buying_options_buttons_found(self, config, mock_driver):
        checker = ProductChecker(config)
        mock_button = Mock()
        mock_driver.find_elements.return_value = [mock_button]

        available, button, button_type = checker._check_buying_options_buttons(mock_driver)

        assert available is True
        assert button == mock_button
        assert button_type == "buying_options"

    def test_check_unavailability_messages_found(self, config, mock_driver):
        checker = ProductChecker(config)
        mock_driver.page_source = "Currently unavailable - We don't know when this item will be back in stock."

        result = checker._check_unavailability_messages(mock_driver)

        assert result is True

    def test_check_unavailability_messages_not_found(self, config, mock_driver):
        checker = ProductChecker(config)
        mock_driver.page_source = "Add to Cart - In stock and ready to ship"

        result = checker._check_unavailability_messages(mock_driver)

        assert result is False

    def test_extract_product_name_from_url(self, config):
        # Update config with a URL that has a product name
        config.product_url = "https://www.amazon.com/Magic-Gathering-Product-Name/dp/B123456789"
        checker = ProductChecker(config)

        name = checker._extract_product_name_from_url()

        assert name == "Magic Gathering Product Name"

    def test_extract_product_name_fallback(self, config):
        # Use default URL without product name
        checker = ProductChecker(config)

        name = checker._extract_product_name_from_url()

        assert name == "new products"