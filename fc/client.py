# -*- coding: utf-8 -*-

import base64
import requests
import logging
import email
import io
import os
import json
from . import __version__
from . import auth
from . import util


class Client(object):
    def __init__(self, **kwargs):
        endpoint = kwargs.get('Endpoint', None)
        if not endpoint:
            raise ValueError('A valid Endpoint parameter must be specified to construct the Client object.')
        access_key_id = kwargs.get("AccessKeyID", None)
        if not access_key_id:
            raise ValueError('A valid AccessKeyID parameter must be specified to construct the Client object.')
        access_key_secret = kwargs.get('AccessKeySecret', None)
        if not access_key_secret:
            raise ValueError('A valid AccessKeySecret parameter must be specified to construct the Client object.')
        security_token = kwargs.get('SecurityToken', '')
        self.endpoint = Client._normalize_endpoint(endpoint)
        self.host = Client._get_host(endpoint)
        self.api_version = '2016-08-15'
        self.user_agent = 'aliyun-fc-python-sdk-v{0}'.format(__version__)
        self.auth = auth.Auth(access_key_id, access_key_secret, security_token)
        self.timeout = kwargs.get('Timeout', 60)

    @staticmethod
    def _normalize_endpoint(url):
        if not url.startswith('http://') and not url.startwith('https://'):
            return 'https://{0}'.format(url)
        return url.strip()

    @staticmethod
    def _get_host(endpoint):
        """ Extract host from endpoint. """
        if endpoint.startswith('http://'):
            return endpoint[7:].strip()

        if endpoint.startswith('https://'):
            return endpoint[8:].strip()

        return endpoint.strip()

    def _build_common_headers(self):
        headers = {
            'host': self.host,
            'date': email.utils.formatdate(usegmt=True),
            'content-type': 'application/json',
            'content-length': '0',
            'user-agent': self.user_agent,
        }
        return headers

    def _do_request(self, method, path, headers, params=None, body=None):
        url = '{0}{1}'.format(self.endpoint, path)
        logging.debug('Perform http request. Method: {0}. URL: {1}. Headers: {2}'.format(method, url, headers))
        r = requests.request(method, url, headers=headers, params=params, data=body, timeout=self.timeout)

        if r.status_code < 400:
            logging.debug(
                'Http status code: {0}. Method: {1}. URL: {2}. Headers: {3}'.format(
                    r.status_code, method, url, r.headers))
        elif 400 <= r.status_code < 500:
            errmsg = 'Client error: {0}. Message: {1}. Method: {2}. URL: {3}. Headers: {4}'.format(
                r.status_code, r.json(), method, url, r.headers)
            raise requests.HTTPError(errmsg, r)
        elif 500 <= r.status_code < 600:
            errmsg = 'Server error: {0}. Message: {1}. Method: {2}. URL: {3}. Headers: {4}'.format(
                r.status_code, r.json(), method, url, r.headers)
            raise requests.HTTPError(errmsg, r)

        return r

    def create_service(self, serviceName, description=None, logConfig=None, role=None, traceId=None):
        """
        Create a service.
        :param serviceName: name of the service.
        :param description: (optional, string), detail description of the service.
        :param logConfig: (optional, dict), log configuration.
        {
            'project': 'string',
            'logStore': 'string',
        }
        :param role: The Aliyun Resource Name (ARN) of the RAM role that FunctionCompute assumes when it executes
        your function to access any other Aliyun resources.
        For more information, see: https://help.aliyun.com/document_detail/52885.html
        :param traceId:(optional, string) a uuid to do the request tracing.
        :return: dict. For more information, see: https://help.aliyun.com/document_detail/52877.html#createservice
        {
            'createdTime': 'string',
            'description': 'string',
            'etag': 'string',
            'lastModifiedTime': 'string',
            'logConfig': {
                'project': 'string',
                'log_store': 'string',
            },
            'role': 'string',
            'serviceId': 'string',
            'serviceName': 'string',
        }
        """
        method = 'POST'
        path = '/{0}/services'.format(self.api_version)
        headers = self._build_common_headers()
        if traceId:
            headers['x-fc-trace-id'] = traceId

        # Sign the request and set the signature to headers.
        headers['authorization'] = self.auth.sign_request(method, path, headers)

        payload = {'serviceName': serviceName, 'description': description}
        if logConfig:
            payload['logConfig'] = logConfig
        if role:
            payload['role'] = role

        r = self._do_request(method, path, headers, body=bytes(json.dumps(payload)))
        dict = r.json()
        dict['etag'] = r.headers['etag']
        return dict

    def delete_service(self, serviceName, etag=None, traceId=None):
        """
        Delete the specified service.
        :param service_name: name of the service.
        :param etag: (optional, string) delete the service only when matched the given etag.
        :param trace_id: (optional, string) a uuid to do the request tracing.
        :return: None
        """
        method = 'DELETE'
        path = '/{0}/services/{1}'.format(self.api_version, serviceName)
        headers = self._build_common_headers()
        if etag:
            headers['if-match'] = etag
        if traceId:
            headers['x-fc-trace-id'] = traceId

        # Sign the request and set the signature to headers.
        headers['authorization'] = self.auth.sign_request(method, path, headers)

        self._do_request(method, path, headers)

    def update_service(self, serviceName, description=None, logConfig=None, role=None, etag=None, traceId=None):
        """
        Update the service attributes.
        :param serviceName: name of the service.
        :param description: (optional, string), detail description of the service.
        :param logConfig: (optional, dict), log configuration.
        {
            'project': 'string',
            'logStore': 'string',
        }
        :param role: The Aliyun Resource Name (ARN) of the RAM role that FunctionCompute assumes when it executes
        your function to access any other Aliyun resources.
        For more information, see: https://help.aliyun.com/document_detail/52885.html
        :param etag: (optional, string) delete the service only when matched the given etag.
        :param traceId:(optional, string) a uuid to do the request tracing.
        :return: dict. For more information, see: https://help.aliyun.com/document_detail/52877.html#createservice
        {
            'createdTime': 'string',
            'description': 'string',
            'etag': 'string',
            'lastModifiedTime': 'string',
            'logConfig': {
                'project': 'string',
                'log_store': 'string',
            },
            'role': 'string',
            'serviceId': 'string',
            'serviceName': 'string',
        }
        """
        method = 'PUT'
        path = '/{0}/services/{1}'.format(self.api_version, serviceName)
        headers = self._build_common_headers()
        if etag:
            headers['if-match'] = etag
        if traceId:
            headers['x-fc-trace-id'] = traceId

        # Sign the request and set the signature to headers.
        headers['authorization'] = self.auth.sign_request(method, path, headers)

        payload = {}
        if description:
            payload['description'] = description
        if logConfig:
            payload['logConfig'] = logConfig
        if role:
            payload['role'] = role

        r = self._do_request(method, path, headers, body=bytes(json.dumps(payload)))
        dict = r.json()
        dict['etag'] = r.headers['etag']
        return dict

    def get_service(self, serviceName, traceId=None):
        """
        Get the service configuration.
        :param serviceName: (string) name of the service.
        :param traceId: (optional, string) trace id of the request.
        :return: service configuration.
        :rtype: dict
        """
        method = 'GET'
        path = '/{0}/services/{1}'.format(self.api_version, serviceName)
        headers = self._build_common_headers()
        if traceId:
            headers['x-fc-trace-id'] = traceId

        # Sign the request and set the signature to headers.
        headers['authorization'] = self.auth.sign_request(method, path, headers)

        return self._do_request(method, path, headers).json()

    def list_services(self, limit=None, nextToken=None, prefix=None, startKey=None, traceId=None):
        """
        List the services in the current account.
        :param limit: (optional, integer) the total number of the returned services.
        :param nextToken: (optional, string) continue listing the service from the previous point.
        :param prefix: (optional, string) list the services with the given prefix.
        :param startKey: (optional, string) startKey is where you want to start listing from.
        :param traceId: (optional, string) trace id of the request.
        :return: dict, including all service information.
        {
            'services':
            [
                {
                    'createdTime': 'string',
                    'description': 'string',
                    'lastModifiedTime': 'string',
                    'logConfig': {
                        'project': 'string',
                        'log_store': 'string',
                    },
                    'role': 'string',
                    'serviceId': 'string',
                    'serviceName': 'string',
                    },
                    ...
            ],
            'nextToken': 'string'
        }
        """
        method = 'GET'
        path = '/{0}/services'.format(self.api_version)
        headers = self._build_common_headers()
        if traceId:
            headers['x-fc-trace-id'] = traceId

        # Sign the request and set the signature to headers.
        headers['authorization'] = self.auth.sign_request(method, path, headers)

        params = {}
        if limit:
            params['limit'] = limit
        if prefix:
            params['prefix'] = prefix
        if nextToken:
            params['nextToken'] = nextToken
        if startKey:
            params['startKey'] = startKey

        return self._do_request(method, path, headers, params=params).json()

    def create_function(
            self, serviceName, functionName, runtime, handler,
            codeZipFile=None, codeDir=None, codeOSSBucket=None, codeOSSObject=None,
            description=None, memorySize=256, timeout=60, traceId=None):
        """
        Create a function.
        :param serviceName: (required, string) the name of the service that the function belongs to.
        :param functionName: (required, string) the name of the function.
        :param runtime: (required, string) the runtime type. For example, nodejs4.4, python2.7 and etc.
        :param handler: (required, string) the entry point of the function.
        :param codeZipFile: (optional, string) the file path of the zipped code.
        :param codeDir: (optional, string) the directory of the code.
        :param codeOSSBucket: (optional, string) the oss bucket where the code located in.
        :param codeOSSObject: (optional, string) the zipped code stored as a OSS object.
        :param description: (optional, string) the readable description of the function.
        :param memorySize: (optional, integer) the memory size of the function, in MB.
        :param timeout: (optional, integer) the max execution time of the function, in second.
        :param traceId: (optional, string) a uuid to do the request tracing.
        :return: dict of the function attributes.
        {
            'codeChecksum': 'string',     // CRC64 checksum
            'codeSize': 1024,             // in byte
            'createdTime': 'string',
            'description': 'string',
            'functionId': 'string',
            'functionName': 'string',
            'handler': 'string',
            'lastModifiedTime': 'string',
            'memorySize': 512,            // in MB
            'runtime': 'string',
            'timeout': 60,                // in second
            'etag': 'string',
        }
        """
        method = 'POST'
        path = '/{0}/services/{1}/functions'.format(self.api_version, serviceName)
        headers = self._build_common_headers()
        if traceId:
            headers['x-fc-trace-id'] = traceId

        # Sign the request and set the signature to headers.
        headers['authorization'] = self.auth.sign_request(method, path, headers)

        payload = {'functionName': functionName, 'runtime': runtime, 'handler': handler}
        if codeZipFile:
            # codeZipFile has highest priority.
            file = open(codeZipFile, 'rb')
            data = file.read()
            encoded = base64.b64encode(data)
            payload['code'] = {'zipFile': encoded}
        elif codeDir:
            bytesIO = io.BytesIO()
            util.ZipDir(codeDir, bytesIO)
            encoded = base64.b64encode(bytesIO.getvalue())
            payload['code'] = {'zipFile': encoded}
        else:
            payload['code'] = {'ossBucketName': codeOSSBucket, 'ossObjectName': codeOSSObject}

        if description:
            payload['description'] = description

        if memorySize:
            payload['memorySize'] = memorySize

        if timeout:
            payload['timeout'] = timeout

        r = self._do_request(method, path, headers, body=bytes(json.dumps(payload)))
        dict = r.json()
        dict['etag'] = r.headers['etag']
        return dict

    def update_function(
            self, serviceName, functionName,
            codeZipFile=None, codeDir=None, codeOSSBucket=None, codeOSSObject=None,
            description=None, handler=None, memorySize=None, runtime=None, timeout=None,
            etag=None, traceId=None):
        """
        Update the function.
        :param serviceName: (required, string) the name of the service that the function belongs to.
        :param functionName: (required, string) the name of the function.
        :param runtime: (required, string) the runtime type. For example, nodejs4.4, python2.7 and etc.
        :param handler: (required, string) the entry point of the function.
        :param codeZipFile: (optional, string) the file path of the zipped code.
        :param codeDir: (optional, string) the directory of the code.
        :param codeOSSBucket: (optional, string) the oss bucket where the code located in.
        :param codeOSSObject: (optional, string) the zipped code stored as a OSS object.
        :param description: (optional, string) the readable description of the function.
        :param memorySize: (optional, integer) the memory size of the function, in MB.
        :param timeout: (optional, integer) the max execution time of the function, in second.
        :param etag: (optional, string) delete the service only when matched the given etag.
        :param traceId: (optional, string) a uuid to do the request tracing.        :return: dict of the function attributes.
        {
            'codeChecksum': 'string',     // CRC64 checksum
            'codeSize': 1024,             // in byte
            'createdTime': 'string',
            'description': 'string',
            'functionId': 'string',
            'functionName': 'string',
            'handler': 'string',
            'lastModifiedTime': 'string',
            'memorySize': 512,            // in MB
            'runtime': 'string',
            'timeout': 60,                // in second
            'etag': 'string',
        }
        """
        method = 'PUT'
        path = '/{0}/services/{1}/functions/{2}'.format(self.api_version, serviceName, functionName)
        headers = self._build_common_headers()
        if etag:
            headers['if-match'] = etag
        if traceId:
            headers['x-fc-trace-id'] = traceId

        # Sign the request and set the signature to headers.
        headers['authorization'] = self.auth.sign_request(method, path, headers)

        payload = {}
        if runtime:
            payload['runtime'] = runtime

        if handler:
            payload['handler'] = handler

        if codeZipFile:
            # codeZipFile has highest priority.
            file = open(codeZipFile, 'rb')
            data = file.read()
            encoded = base64.b64encode(data)
            payload['code'] = {'zipFile': encoded}
        elif codeDir:
            bytesIO = io.BytesIO()
            util.ZipDir(codeDir, bytesIO)
            encoded = base64.b64encode(bytesIO.getvalue())
            payload['code'] = {'zipFile': encoded}
        else:
            payload['code'] = {'ossBucketName': codeOSSBucket, 'ossObjectName': codeOSSObject}

        if description:
            payload['description'] = description

        if memorySize:
            payload['memorySize'] = memorySize

        if timeout:
            payload['timeout'] = timeout

        r = self._do_request(method, path, headers, body=bytes(json.dumps(payload)))
        dict = r.json()
        dict['etag'] = r.headers['etag']
        return dict

    def delete_function(self, serviceName, functionName, etag=None, traceId=None):
        """
        Delete the specified service.
        :param serviceName: name of the service.
        :param etag: (optional, string) delete the service only when matched the given etag.
        :param traceId: (optional, string) a uuid to do the request tracing.
        :return: None
        """
        method = 'DELETE'
        path = '/{0}/services/{1}'.format(self.api_version, serviceName)
        headers = self._build_common_headers()
        if etag:
            headers['if-match'] = etag
        if traceId:
            headers['x-fc-trace-id'] = traceId

        # Sign the request and set the signature to headers.
        headers['authorization'] = self.auth.sign_request(method, path, headers)

        self._do_request(method, path, headers)

    def invoke_function(self, service_name, function_name,
                        payload=None, invocation_type='Sync', log_type='None', trace_id=None):
        """
        Invoke the function.
        :param service_name: the name of the service.
        :param function_name: the name of the function.
        :param payload: (optional, bytes or seekable file-like object): the input of the function.
        :param invocation_type: (optional, string) 'Sync' or 'Async'.
        Invoke the function synchronously or asynchronously.
        :param log_type: (optional, string) 'None' or 'Tail'. When invoke a function synchronously,
        you can set the log type to 'Tail' to get the last 4KB base64-encoded function log.
        :param trace_id: (optional, string) a uuid to do the request tracing.
        :return a dict that contains following fields.
        {
        }
        """
        method = 'POST'
        path = '/{0}/services/{1}/functions/{2}/invocations'.format(self.api_version, service_name, function_name)
        headers = self._build_common_headers()
        headers['x-fc-invocation-type'] = invocation_type
        headers['x-fc-log-type'] = log_type
        headers['content-type'] = 'application/octet-stream'
        if isinstance(payload, file):
            payload.seek(0, os.SEEK_END)
            headers['content-length'] = payload.tell()
            payload.seek(0, os.SEEK_SET)
        elif isinstance(payload, bytes):
            headers['content-length'] = len(payload)
        if trace_id:
            headers['x-fc-trace-id'] = trace_id

        # Sign the request and set the signature to headers.
        headers['authorization'] = self.auth.sign_request(method, path, headers)

        return self._do_request(method, path, headers, body=payload)
