from unittest.mock import Mock, patch
from amazon_monitor.amazon.checkout import CheckoutHandler
from unittest.mock import Mock, patch

from amazon_monitor.amazon.checkout import CheckoutHandler


class TestCheckoutHandler:
    def test_attempt_purchase_direct_success(self, config, mock_driver):
        handler = CheckoutHandler(config)
        mock_button = Mock()

        with patch.object(handler, '_handle_direct_purchase_flow', return_value=True):
            result = handler.attempt_purchase(mock_driver, mock_button, "direct")

            assert result is True

    def test_attempt_purchase_buying_options_success(self, config, mock_driver):
        handler = CheckoutHandler(config)
        mock_button = Mock()

        with patch.object(handler, '_handle_buying_options_flow', return_value=True):
            result = handler.attempt_purchase(mock_driver, mock_button, "buying_options")

            assert result is True

    def test_attempt_purchase_invalid_inputs(self, config, mock_driver):
        handler = CheckoutHandler(config)

        # Test with None button
        result = handler.attempt_purchase(mock_driver, None, "direct")
        assert result is False

        # Test with None button_type
        mock_button = Mock()
        result = handler.attempt_purchase(mock_driver, mock_button, None)
        assert result is False

    def test_handle_direct_purchase_flow_success(self, config, mock_driver):
        handler = CheckoutHandler(config)
        mock_button = Mock()
        mock_button.get_attribute.return_value = "test-button-id"

        with patch.object(handler, '_scroll_to_element'):
            with patch.object(handler, '_click_element'):
                with patch.object(handler, '_complete_checkout_process', return_value=True):
                    result = handler._handle_direct_purchase_flow(mock_driver, mock_button)

                    assert result is True

    def test_attempt_direct_checkout_success(self, config, mock_driver):
        handler = CheckoutHandler(config)
        mock_button = Mock()

        # Mock WebDriverWait to return a clickable button
        with patch('amazon_monitor.amazon.checkout.WebDriverWait') as mock_wait:
            mock_wait.return_value.until.return_value = mock_button
            with patch.object(handler, '_verify_order_success', return_value=True):
                with patch.object(handler, '_take_screenshot'):
                    result = handler._attempt_direct_checkout(mock_driver)

                    assert result is True
                    mock_button.click.assert_called_once()

    def test_attempt_direct_checkout_timeout(self, config, mock_driver):
        handler = CheckoutHandler(config)

        # Mock WebDriverWait to raise TimeoutException
        with patch('amazon_monitor.amazon.checkout.WebDriverWait') as mock_wait:
            from selenium.common.exceptions import TimeoutException
            mock_wait.return_value.until.side_effect = TimeoutException()

            result = handler._attempt_direct_checkout(mock_driver)

            assert result is False

    def test_is_in_cart_flow_true(self, config, mock_driver):
        handler = CheckoutHandler(config)
        mock_driver.current_url = "https://www.amazon.com/cart"
        mock_driver.page_source = "Shopping cart contents"

        result = handler._is_in_cart_flow(mock_driver)

        assert result is True

    def test_is_in_cart_flow_false(self, config, mock_driver):
        handler = CheckoutHandler(config)
        mock_driver.current_url = "https://www.amazon.com/product"
        mock_driver.page_source = "Product details"

        result = handler._is_in_cart_flow(mock_driver)

        assert result is False

    def test_verify_order_success_true(self, config, mock_driver):
        handler = CheckoutHandler(config)
        mock_driver.page_source = "Thank you! Your order has been placed."
        mock_driver.current_url = "https://www.amazon.com/confirmation"

        result = handler._verify_order_success(mock_driver)

        assert result is True

    def test_verify_order_success_false(self, config, mock_driver):
        handler = CheckoutHandler(config)
        mock_driver.page_source = "Product not available"
        mock_driver.current_url = "https://www.amazon.com/product"

        result = handler._verify_order_success(mock_driver)

        assert result is False

    def test_find_proceed_to_checkout_button_found(self, config, mock_driver):
        handler = CheckoutHandler(config)
        mock_button = Mock()
        mock_driver.find_elements.return_value = [mock_button]

        result = handler._find_proceed_to_checkout_button(mock_driver)

        assert result == mock_button

    def test_find_proceed_to_checkout_button_not_found(self, config, mock_driver):
        handler = CheckoutHandler(config)
        mock_driver.find_elements.return_value = []

        result = handler._find_proceed_to_checkout_button(mock_driver)

        assert result is None

    def test_get_element_identifier(self, config):
        handler = CheckoutHandler(config)
        mock_element = Mock()
        mock_element.get_attribute.side_effect = lambda attr: {
            "id": "test-id",
            "class": "test-class"
        }.get(attr)

        identifier = handler._get_element_identifier(mock_element)

        assert identifier == "ID: test-id"

    def test_click_element_regular_click_success(self, config, mock_driver):
        handler = CheckoutHandler(config)
        mock_element = Mock()

        handler._click_element(mock_driver, mock_element)

        mock_element.click.assert_called_once()

    def test_click_element_fallback_to_javascript(self, config, mock_driver):
        handler = CheckoutHandler(config)
        mock_element = Mock()
        mock_element.click.side_effect = Exception("Regular click failed")

        handler._click_element(mock_driver, mock_element)

        mock_element.click.assert_called_once()
        mock_driver.execute_script.assert_called_once()