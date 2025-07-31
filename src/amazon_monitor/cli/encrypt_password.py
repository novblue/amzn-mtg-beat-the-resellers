import logging

import click
from amazon_monitor.security.encryption import Encryption

logger = logging.getLogger(__name__)

@click.command()
@click.option('--verify', is_flag=True, help='Verify decryption after encryption')
def encrypt_password(verify: bool):
    """
    CLI command to encrypt a password for Amazon Monitor.
    Stores the encryption key in the system keyring and outputs the encrypted password.
    """
    try:
        encryption = Encryption()
        encrypted = encryption.setup_encrypted_password()

        if verify:
            # Verify the encryption worked correctly
            decrypted = encryption.decrypt(encrypted)
            click.echo("\nVerification successful - password can be correctly decrypted.")

        click.echo("\nAdd this to your .env file:")
        click.echo("AMAZON_PASSWORD_ENCRYPTED=" + encrypted)

    except Exception as e:
        logger.error(f"Password encryption failed: {e}")
        click.echo("Error: Failed to encrypt password. Check logs for details.", err=True)
        raise click.Abort()

if __name__ == '__main__':
    encrypt_password()