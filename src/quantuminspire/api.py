""" Quantum Inspire SDK

Copyright 2018 QuTech Delft

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging
import time
import uuid
from collections import OrderedDict
from urllib.parse import urljoin

import coreapi
from quantuminspire.exceptions import ApiError


class QuantumInspireAPI:

    def __init__(self, base_uri, authentication, project_name=None,
                 logger=logging, coreapi_client_class=coreapi.Client):
        """ Python interface to the Quantum Inspire API For documentation see:
                https://dev.quantum-inspire.com/api
                https://dev.quantum-inspire.com/api/docs/#jobs-create

        Args:
            base_uri (str): The url of the Quantum Inspire api.
            authentication (BasicAuthentication): The basic HTTP authentication.
            project_name (str or None): The used project for execution jobs.
                                        Project will not deleted when a name is given.
            logger (Logger): The logging module instance.
        """
        self.__client = coreapi_client_class(auth=authentication)
        self.project_name = project_name
        self.base_uri = base_uri
        self.__logger = logger
        try:
            self._load_schema()
        except Exception as ex:
            raise ApiError('Could not connect to {}'.format(base_uri)) from ex

    def _get(self, uri_path):
        """ Makes a request to get request with a client instance.

        Args:
            uri_path (str): The URL where to request the data.

        Returns:
            OrderedDict: The resulting data from the request.
        """
        return self.__client.get(uri_path)

    def _action(self, action, params=None):
        """ Requests for interaction with the Quantum Inspire API.

        Args:
            action (list): A list with strings indexing into the link.
            params (dict): Some links may accept a set of parameters with names as keys.

        Returns:
            OrderedDict: The resulting data form the request.
        """
        return self.__client.action(self.document, action, params=params)

    def _load_schema(self):
        """ Loads the schema with metadata that explains how the api-data is structured."""
        self.document = self._get(urljoin(self.base_uri, 'schema/'))

    def list_backend_types(self):
        """ Prints the backend types with the name and number of qubits."""
        backends = self.get_backend_types()
        [print('Backend: {name} (qubits {number_of_qubits})'.format(**backend)) for backend in backends]

    def get_backend_types(self):
        """ Gets the backend types with properties.

        Returns:
            OrderedDict: The type of backends with the properties.
        """
        return self._action(['backendtypes', 'list'])

    def get_default_backend_type(self):
        """ Gets the default backend type.

        Returns:
            OrderedDict: The default backend type.
        """
        return self._action(['backendtypes', 'default', 'list'])

    def get_backend_type_by_id(self, backend_id):
        """ Gets the properties of a backend type.

        Args:
            backend_id (int): The backend identification number.

        Returns:
            OrderedDict: The properties of the backend type.
        """
        return self._action(['backendtypes', 'read'], params={'id': backend_id})

    def get_backend_type_by_name(self, backend_name):
        """ Gets the properties of the first backend type, given the backend name.

        Args:
            backend_name (str): The backend name.

        Raises:
            ApiError: if the backend name does not exists.

        Returns:
            OrderedDict: The properties of the backend type.
        """
        backend = next((backend for backend in self.get_backend_types()
                        if backend['name'] == backend_name), None)
        if backend is None:
            raise ApiError('Backend with name {} does not exist!'.format(backend_name))
        return backend

    def get_backend_type(self, identifier=None):
        """ Gets the properties of the backend type, given the identifier. If no identifier is given,
            the default backend type will be returned. With an identifier of type string or int,
            the backend type will be searched by name or number respectively.

        Args:
            identifier (None, int or str): The backend type identifier.

        Raises:
            ApiError: if the backend name does not exists.
            ValueError: if the identifier is not of the correct type.

        Returns:
            OrderedDict: The properties of the backend type.
        """
        if identifier is None:
            return self.get_default_backend_type()
        elif isinstance(identifier, int):
            return self.get_backend_type_by_id(identifier)
        elif isinstance(identifier, str):
            return self.get_backend_type_by_name(identifier)
        else:
            raise ValueError('Identifier should be of type int, str or None!')

    #  projects  #

    def list_projects(self):
        """ Prints the prjoects with the name and backend type."""
        projects = self.get_projects()
        [print('Project: {name} (backend type {backend_type})'.format(**project)) for project in projects]

    def get_projects(self):
        """ Gets the projects with its properties; backend type, default number of shots, etc.

        Returns:
            OrderedDict: The projects with properties.
        """
        return self._action(['projects', 'list'])

    def get_project(self, project_id):
        """ Gets the properties of a project.

        Args:
            project_id (int): The project identification number.

        Returns:
            OrderedDict: The properties of the project.
        """
        return self._action(['projects', 'read'], params={'id': project_id})

    def _create_project(self, name, default_number_of_shots, backend):
        """ Creates a new project for executing QASM code.

        Args:
            name (str): The name for the project.
            default_number_of_shots (int): The default number of executions before collecting the results.
            backend (OrderedDict): The properties of the backend.

        Returns:
            OrderedDict: The properties of the new project.
        """
        payload = {
            'name': name,
            'default_number_of_shots': default_number_of_shots,
            'backend_type': backend['url'],
        }
        return self._action(['projects', 'create'], params=payload)

    def _delete_project(self, project_id):
        """ Deletes a project together with all its assets, jobs and results.

        Args:
            project_id (str): The project identification number.
        """
        payload = {
            'id': project_id
        }
        self._action(['projects', 'delete'], params=payload)

    #  jobs  #

    def list_jobs(self):
        """ Prints the jobs with the name, identification number and status."""
        jobs = self.get_jobs()
        [print('Job: name {name}, id {id}, status {status}'.format(**job)) for job in jobs]

    def get_jobs(self):
        """ Gets the jobs with its properties; name, status, backend, results, etc.

        Returns:
            OrderedDict: The projects with properties.
        """
        return self._action(['jobs', 'list'])

    def get_job(self, job_id):
        """ Gets the properties of a job.

        Args:
            job_id (int): The job identification number.

        Returns:
            OrderedDict: The properties of the job.
        """
        return self._action(['jobs', 'read'], params={'id': job_id})

    def _create_job(self, name, asset, project, number_of_shots, full_state_projection=True):
        """ Creates a new job for executing QASM code.

        Args:
            name (str): The name for the project.
            asset (OrderedDict):  The asset with the QASM code.
            project (OrderedDict): The project with backend.
            number_of_shots (int): The number of executions before returning the result.
            full_state_projection (bool): Used for optimizing simulations. For more information see:
                                          https://www.quantum-inspire.com/kbase/optimization-of-simulations/

        Returns:
            OrderedDict: The properties of the new project.
        """
        payload = {
            'status': 'NEW',
            'name': name,
            'input': asset['url'],
            'backend_type': project['backend_type'],
            'number_of_shots': number_of_shots,
            'full_state_projection': full_state_projection,
        }
        return self._action(['jobs', 'create'], params=payload)

    #  results  #

    def list_results(self):
        """ Prints the results of the users with the identification number and creation date."""
        results = self.get_results()
        [print('Result: id {id} (date {created_at})'.format(**result)) for result in results]

    def get_results(self):
        """ Gets the results with its properties; histogram, run time, creation date, etc.

        Returns:
            OrderedDict: The results with properties.
        """
        return self._action(['results', 'list'])

    def get_result(self, result_id):
        """ Gets the histogram results of the executed QASM code.

        Args:
            result_id (str): The result identification number.

        Returns:
            OrderedDict: The result with the execution properties.
        """
        return self._action(['results', 'read'], params={'id': result_id})

    #  assets  #

    def list_assets(self):
        """ Prints the assets of the users with the name, identification number and project identification number."""
        assets = self.get_assets()
        [print('Asset: name {name}, id {id}, (project_id {project_id})'.format(**asset)) for asset in assets]

    def get_assets(self):
        """ Gets the assets with its properties; qasm content, name, etc.

        Returns:
            OrderedDict: The results with properties.
        """
        return self._action(['assets', 'list'])

    def get_asset(self, asset_id):
        """ Gets the properties of an asset.

        Args:
            asset_id (int): The asset identification number.

        Returns:
            OrderedDict: The properties of the asset.
        """
        return self._action(['assets', 'read'], params={'id': asset_id})

    def _create_asset(self, name, project, content):
        """ Creates a new asset the the QASM code content.

        Args:
            name (str): The name of the new asset
            project (OrderedDict): The project to which the asset corresponds to.
            content (str): The QASM code content.

        Returns:
            OrderedDict: The properties of the asset.
        """
        payload = {
            'name': name,
            'contentType': 'application/qasm',
            'project': project['url'],
            'content': content,
        }
        return self._action(['assets', 'create'], params=payload)

    #  other  #

    def _wait_for_completed_job(self, job_id, collect_max_tries, sec_retry_delay=0.5):
        """ Holds the process and requests the job status untill completed or when
            the maximum number of tries has been reached.

        Args:
            job_id (int): The job identification number.
            collect_max_tries (int): The maximum number of request tries.
            sec_retry_delay (float): The time delay in between requests in seconds.

        Returns:
            Boolean: True if the job result could be collected else false.
        """
        tries = 0
        while tries < collect_max_tries:
            tries += 1
            time.sleep(sec_retry_delay)
            job = self.get_job(job_id)
            status_message = '(id {}, iteration {})'.format(job['id'], tries)
            if job['status'] == 'COMPLETE':
                self.__logger.info('Got result: %s', status_message)
                return True
            self.__logger.info('Waiting for result: %s', status_message)
        self.__logger.error('Failed getting result: %s', status_message)
        return False

    def execute_qasm(self, qasm, number_of_shots=256, backend_type=None,
                     collect_tries=300, default_number_of_shots=256, identifier=None):
        """ Creates the project, asset and job with the given qasm code and returns
            the execution result.

        Args:
            qasm (str): The qasm code as string object.
            backend_type (OrderedDict, int, str or None): The backend_type on to execute the algorithm.
            number_of_shots (int): Execution times of the algorithm before collecting the results.
            collect_tries (int): The number of times the results should be collected before returning.
            default_number_of_shots (int): The default used number of shots for the project.
            identifier (str or None): The identifier of the project, asset and job.

        Returns:
            OrderedDict: The results of the executed qasm if succesfull else an empty dictionary if
                         the results could not be collected.
        """
        if not isinstance(backend_type, OrderedDict):
            backend_type = self.get_backend_type(backend_type)

        project = None
        delete_project_afterwards = True
        if identifier is None:
            identifier = uuid.uuid1()

        if self.project_name is not None:
            delete_project_afterwards = False
            project = next((project for project in self.get_projects()
                            if project['name'] == self.project_name), None)

        if project is None:
            project_name = self.project_name if self.project_name else 'qi-sdk-project-{}'.format(identifier)
            project = self._create_project(project_name, default_number_of_shots, backend_type)
        try:
            asset_name = 'qi-sdk-asset-{}'.format(identifier)
            asset = self._create_asset(asset_name, project, qasm)

            job_name = 'qi-sdk-job-{}'.format(identifier)
            initial_job = self._create_job(job_name, asset, project, number_of_shots)

            job_identifier = initial_job['id']
            result_uri = initial_job['results']
            self.__logger.info('submitting qasm code to quantum inspire %s', job_name)
            has_results = self._wait_for_completed_job(job_identifier, collect_tries)
            return self._get(result_uri) if has_results else {}

        finally:
            if delete_project_afterwards:
                project_identifier = project['id']
                self._delete_project(project_identifier)
