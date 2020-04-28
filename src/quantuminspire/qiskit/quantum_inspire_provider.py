# Quantum Inspire SDK
#
# Copyright 2018 QuTech Delft
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from copy import copy
from typing import List, Optional, Any

import coreapi
from qiskit.providers import BaseProvider

from quantuminspire.api import QuantumInspireAPI
from quantuminspire.credentials import get_token_authentication, get_basic_authentication
from quantuminspire.exceptions import ApiError
from quantuminspire.qiskit.backend_qx import QuantumInspireBackend

QI_URL = 'https://api.quantum-inspire.com'


class QuantumInspireProvider(BaseProvider):  # type: ignore
    """ Provides a backend and an api for a single Quantum Inspire account. """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._backends: List[QuantumInspireBackend] = []
        self._api: Optional[QuantumInspireAPI] = None

    def __str__(self) -> str:
        return 'QI'

    def backends(self, name: Optional[str] = None, **kwargs: Any) -> List[QuantumInspireBackend]:
        """ Provides a list of backends.

        :param name: Name of the requested backend.
        :param kwargs: Used for filtering, not implemented.

        :return:
            List of backends that meet the filter requirements.
        """
        if self._api is None:
            raise ApiError('Authentication details have not been set.')

        available_backends = self._api.get_backend_types()
        if name is not None:
            available_backends = list(filter(lambda b: b['name'] == name, available_backends))
        backends = []
        for backend in available_backends:
            if backend['is_allowed']:
                config = copy(QuantumInspireBackend.DEFAULT_CONFIGURATION)
                config.backend_name = backend['name']
                backends.append(QuantumInspireBackend(self._api, provider=self, configuration=config))

        return backends

    def set_authentication_details(self, email: str, password: str, qi_url: str = QI_URL) -> None:
        """Set a single authentication for Quantum Inspire.

        .. deprecated:: 0.5.0
           Replaced with method :meth:`~.set_basic_authentication`


        :param email: A valid email address.
        :param password: Password for the account.
        :param qi_url: URL that points to quantum-inspire api. Default value: 'https://api.quantum-inspire.com'.

        """
        self.set_basic_authentication(email, password, qi_url)

    def set_basic_authentication(self, email: str, password: str, qi_url: str = QI_URL) -> None:
        """Set up basic authentication for Quantum Inspire.

        :param email: A valid email address.
        :param password: Password for the account.
        :param qi_url: URL that points to quantum-inspire api. Default value: 'https://api.quantum-inspire.com'.
        """
        authentication = get_basic_authentication(email, password)
        self.set_authentication(authentication, qi_url)

    def set_token_authentication(self, token: str, qi_url: str = QI_URL) -> None:
        """
        Set up token authentication for Quantum Inspire.

        :param token: A valid token.
        :param qi_url: URL that points to quantum-inspire api. Default value: 'https://api.quantum-inspire.com'.
        """
        authentication = get_token_authentication(token)
        self.set_authentication(authentication, qi_url)

    def set_authentication(self, authentication: Optional[coreapi.auth.AuthBase] = None,
                           qi_url: str = QI_URL) -> None:
        """
        Initializes the API and sets the authentication for Quantum Inspire.

        :param authentication: The authentication, can be one of the following coreapi authentications:

            * ``BasicAuthentication(email, password)``, HTTP authentication with valid email/password.
            * ``TokenAuthentication(token, scheme="token")``, token authentication with a valid API-token.

            When authentication is ``None``, the api will try to load a token from the default resource.

        :param qi_url: URL that points to quantum-inspire api. Default value: 'https://api.quantum-inspire.com'.
        """
        self._api = QuantumInspireAPI(qi_url, authentication)
