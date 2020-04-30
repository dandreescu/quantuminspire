Module credentials
==================

.. automodule:: quantuminspire.credentials

The following functions use a resource file to store credentials information
for the user. The default location of this resource file is
:file:`.quantuminspire/qirc` in the user's home directory.
This default location is indicated with `DEFAULT_QIRC_FILE` in the following function signatures.

.. autofunction:: load_account(filename: str = DEFAULT_QIRC_FILE) -> Optional[str]
.. autofunction:: read_account(filename: str = DEFAULT_QIRC_FILE) -> Optional[str]
.. autofunction:: store_account(token: str, filename: str = DEFAULT_QIRC_FILE, overwrite: bool = False) -> None
.. autofunction:: delete_account(token: str, filename: str = DEFAULT_QIRC_FILE) -> None
.. autofunction:: save_account(token: str, filename: str = DEFAULT_QIRC_FILE) -> None
.. autofunction:: enable_account
.. autofunction:: get_token_authentication
.. autofunction:: get_basic_authentication
