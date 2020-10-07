import os
import json
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from utility.service_log import ServiceLog


class BaseJob(object):
    def __init__(self, k8s_config_path=None, docker_registry_host=None, image_config=None):
        if not k8s_config_path:
            config_path = os.path.join(os.environ['HOME'], '.kube/config')
        try:
            config.load_kube_config(config_path)
        except Exception:
            config.load_incluster_config()  # in kubernetes
        self.batch_client = client.BatchV1Api()
        self.core_client = client.CoreV1Api()

        self._image_name = image_config['IMAGE_NAME']
        self._image_tag = image_config['IMAGE_TAG']
        self._memory = image_config['MEMORY']

        self._docker_registry_host = docker_registry_host
        if self._docker_registry_host is not None:
            self._repository_name = self._docker_registry_host + '/' + self._image_name + ':' + self._image_tag
        else:
            self._repository_name = self._image_name + ':' + self._image_tag

    def create(self):
        raise NotImplementedError

    def run(self, namespace='default'):
        try:
            resp = self.batch_client.create_namespaced_job(
                namespace=namespace,
                body=self.job
            )
            return resp
        except Exception as e:
            print(e)
            raise Exception

    def list(self, namespace):
        pretty = 'pretty_example'
        limit = 56
        timeout_seconds = 56

        try:
            return self.batch_client.list_namespaced_job(
                namespace, pretty=pretty, limit=limit, timeout_seconds=timeout_seconds)
        except ApiException as e:
            print("Exception when calling BatchV1Api->list_namespaced_job: %s\n" % e)

    def logs(self, name, namespace):
        label_selector = 'job-name=' + name

        try:
            pods = self.core_client.list_namespaced_pod(namespace, label_selector=label_selector)
        except ApiException as e:
            print("Exception when calling CoreV1Api->list_namespaced_pod: %s\n" % e)
            return
        try:
            for pod in pods.items:
                pod_log = self.core_client.read_namespaced_pod_log(pod.metadata.name, namespace)
                ServiceLog.error('pod-name=' + pod.metadata.name, detail_msg=pod_log)
            if pods.items == []:
                pod_log = 'no logs'
                ServiceLog.error(label_selector, detail_msg='no logs')
            return pod_log
        except ApiException as e:
            print("Exception when calling CoreV1Api->read_namespaced_pod_log: %s\n" % e)

    def fetch(self, name, namespace):
        pretty = 'pretty_example'

        try:
            res = self.batch_client.read_namespaced_job(name, namespace, pretty=pretty)
            return {'is_succeeded': True, 'content': res.status}
        except client.rest.ApiException as e:
            return {'is_succeeded': False, 'content': json.loads(e.body)}
        except Exception as e:
            # FIXME: add logging
            raise e

    def delete(self, name, namespace):
        body = client.V1DeleteOptions()

        try:
            return self.batch_client.delete_namespaced_job(name=name, body=body, namespace=namespace)
        except client.rest.ApiException as e:
            print("Exception when calling BatchV1Api->delete_namespaced_job: %s\n" % e)
