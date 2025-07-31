# Amazon MTG Pre-order Monitor

A Python-based monitor for Amazon pre-orders with human-like behavior designed to help legitimate buyers secure Magic: The Gathering products against reseller bots.

## Features

- **Automated Pre-order Monitoring**: Continuously monitors product availability
- **Human-like Behavior**: Implements anti-detection measures to avoid bot detection
- **Secure Password Storage**: Uses encryption to protect Amazon credentials
- **Cookie Persistence**: Saves login sessions to avoid repeated authentication
- **Configurable Monitoring**: Customizable refresh intervals and behavior settings
- **Headless Operation**: Can run with or without browser UI

## Requirements

- Python 3.9+
- Chrome/Chromium browser
- ChromeDriver (automatically managed)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/amzn-mtg-beat-the-resellers.git
cd amzn-mtg-beat-the-resellers
```

2. Install the package:
```bash
pip install -e .
```

Or for development:
```bash
pip install -e ".[dev]"
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Encrypt your Amazon password:
```bash
amazon-encrypt-password
```

3. Update `.env` with your settings:
```env
AMAZON_EMAIL=your-email@example.com
AMAZON_PASSWORD_ENCRYPTED=your-encrypted-password
PRODUCT_URL=https://www.amazon.com/dp/B123456789
```

### Optional Settings

- `REFRESH_INTERVAL`: Check interval in seconds (default: 60)
- `HEADLESS`: Run without browser UI (default: false)
- `COOKIE_FILE`: Path to store cookies (default: amazon_cookies.json)

### Anti-Detection Features

- `ENABLE_ANTI_DETECTION`: Master switch for anti-bot measures
- `RANDOMIZE_USER_AGENT`: Use random browser user agents
- `RANDOMIZE_WINDOW_SIZE`: Vary browser window dimensions
- `RANDOM_DELAYS`: Add human-like delays between actions
- `STEALTH_MODE`: Enable all stealth features

## Usage

### Basic Usage

Run with environment configuration:
```bash
amazon-monitor
```

### Command Line Options

Override environment settings:
```bash
amazon-monitor --url https://www.amazon.com/dp/B123456789 --interval 30
```

Enable anti-detection features:
```bash
amazon-monitor --enable-anti-detection --random-delays --stealth-mode
```

Run in headless mode:
```bash
amazon-monitor --headless
```

### All Options

```
--email                  Amazon email address
--password-encrypted     Encrypted Amazon password
--url                    Product URL to monitor
--interval               Check interval in seconds
--headless               Run in headless mode
--cookie-file            Cookie file path
--enable-anti-detection  Enable anti-detection measures
--randomize-user-agent   Randomize user agent
--randomize-window-size  Randomize window size
--random-delays          Add random delays
--stealth-mode           Enable stealth mode
--verbose                Enable verbose logging
```

## Security

- Passwords are encrypted using Fernet encryption
- Credentials are never stored in plain text
- Cookies are saved locally to reduce login frequency
- All sensitive data is excluded from version control

## Development

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=amazon_monitor

# Specific test file
pytest tests/unit/test_monitor.py
```

### Code Quality

```bash
# Format code
black src tests

# Lint
flake8 src tests

# Type checking
mypy src

# Security scan
bandit -r src
```

### Pre-commit Hooks

Install pre-commit hooks:
```bash
pre-commit install
```

## Project Structure

```
amzn-mtg-beat-the-resellers/
├── src/
│   └── amazon_monitor/
│       ├── amazon/          # Amazon interaction modules
│       ├── cli/             # CLI tools
│       ├── config/          # Configuration management
│       ├── core/            # Core monitoring logic
│       ├── security/        # Encryption and security
│       └── utils/           # Utility functions
├── tests/
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── .env.example            # Example configuration
├── pyproject.toml          # Project configuration
└── requirements.txt        # Dependencies
```

## Troubleshooting

### Common Issues

1. **Login failures**: Clear cookies and re-authenticate
2. **Detection issues**: Enable anti-detection features
3. **ChromeDriver errors**: Update Chrome browser

### Logs

Check `amazon_monitor.log` for detailed debugging information.

## License

This project is for educational purposes only. Use responsibly and in accordance with Amazon's Terms of Service.

## Disclaimer

This tool is designed as a proof-of-concept project to help legitimate buyers compete with reseller bots. 

It should not be used for:
- Actual purchasing
- Bulk purchasing for resale
- Violating Amazon's Terms of Service
- Any illegal or unethical purposes

The authors are not responsible for any misuse of this software.