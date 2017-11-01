from kubernetes import client as kube_client
from kubernetes import config as kube_config
from util import Utilities
from collections import defaultdict
import logging
import json


class ManageApiServer(object):
    def __init__(self, api_server='https://localhost', api_user='admin', api_pass='admin', kube_conf_file=None):
        self.kube_dict = lambda: defaultdict(self.kube_dict)
        self.kube_api_server = api_server
        self.kube_api_user = api_user
        self.kube_api_pass = api_pass
        self.kube_conf_file = kube_conf_file
        kube_client.configuration.host = self.kube_api_server
        kube_client.configuration.username = self.kube_api_user
        kube_client.configuration.password = self.kube_api_pass
        kube_config.load_kube_config(config_file=self.kube_conf_file)
        self.kube_api_client = kube_client.CoreV1Api()
        self.util = Utilities()
        logging.basicConfig(level=logging.INFO)
        self.m_logger = logging.getLogger(__name__)

    def get_all_pods_details_for_all_namespace(self, **kwargs):
        '''
        This method will do RESTApi calls to the Kubernetes APIServer and get all the deployed pod/s details
        :param kwargs: Dict with APIServer Details
        :return: api_output
        '''
        watch = kwargs['WATCH'] if 'WATCH' in kwargs else False
        pretty_output = kwargs['PRETTY'] if 'PRETTY' in kwargs else False
        all_pods = self.kube_api_client.list_pod_for_all_namespaces(pretty=pretty_output, watch=watch)
        return all_pods

    def get_all_pods_details_for_the_namespace(self, **kwargs):
        '''
        This method will do RESTApi calls to the Kubernetes APIServer and get all the deployed pod/s details
        for the given namespace
        :param kwargs: Dict with APIServer Details
        :return: api_output
        '''
        namespace = kwargs['NAMESPACE'] if 'NAMESPACE' in kwargs else 'default'
        watch = kwargs['WATCH'] if 'WATCH' in kwargs else False
        pretty_output = kwargs['PRETTY'] if 'PRETTY' in kwargs else False
        all_namespace_pods = self.kube_api_client.list_namespaced_pod(namespace=namespace, pretty=pretty_output,
                                                                      watch=watch)
        return all_namespace_pods

    def get_all_pods_details_for_kube_system_namespace(self):
        '''
        This method will do RESTApi calls to the Kubernetes APIServer and get all the deployed pod/s details
        for the "kube-system" namespace. "kube-system" is namespace where all kubernetes related pods reside
        :return: api_output
        '''
        return self.get_all_pods_details_for_the_namespace(NAMESPACE='kube-system')

    def get_all_nodes_details(self, **kwargs):
        '''
        This method will do RESTApi calls to the Kubernetes APIServer and get all the node/s details in the cluster
        :param kwargs: Dict with APIServer Details
        :return: api_output
        '''
        watch = kwargs['WATCH'] if 'WATCH' in kwargs else False
        pretty_output = kwargs['PRETTY'] if 'PRETTY' in kwargs else False
        all_nodes = self.kube_api_client.list_node(pretty=pretty_output, watch=watch)
        return all_nodes

    def get_details_of_the_node(self, **kwargs):
        '''
        This method gets all the output/details for all the nodes available in the cluster
        :param kwargs: kwargs key/value
        :return: node_dict with all the node details
        '''
        node_details_dict = defaultdict(self.kube_dict)
        node_output = self.get_all_nodes_details(**kwargs)
        for node in node_output.items:
            node_name = node.metadata.name
            node_details_dict[node_name]['node_name'] = node_name
            node_details_dict[node_name]['cluster_name'] = node.metadata.cluster_name
            node_details_dict[node_name]['namespace'] = node.metadata.namespace
            node_details_dict[node_name]['created_timestamp'] = node.metadata.creation_timestamp
            node_details_dict[node_name]['kubelet_version'] = node.status.node_info.kubelet_version
            node_details_dict[node_name]['os_image'] = node.status.node_info.os_image
            node_details_dict[node_name]['kernel_version'] = node.status.node_info.kernel_version
            node_role = 'Master' if 'node-role.kubernetes.io/master' in node.metadata.labels else 'Minion'
            node_details_dict[node_name]['node_role'] = node_role
            for address in node.status.addresses:
                node_details_dict[node_name][address.type] = address.address
            for condition in node.status.conditions:
                if 'Ready' in condition.type:
                    status = True if 'True' in condition.status else False
                    node_details_dict[node_name]['%s_%s' % (condition.type, 'State')] = status
                    node_details_dict[node_name]['%s_%s' % (condition.type, 'Message')] = condition.message
                    node_details_dict[node_name]['%s_%s' % (condition.type, 'Reason')] = condition.reason
                    node_details_dict[node_name]['%s_%s' % (condition.type,
                                                            'Latest_Heartbeat')] = condition.last_heartbeat_time
                    node_details_dict[node_name]['%s_%s' % (condition.type,
                                                            'Latest_Transition')] = condition.last_transition_time

        return node_details_dict

    def get_details_of_the_pod(self, **kwargs):
        '''
        This method gets all the output/details for all the pods available in a given NAMESPACE, if NAMESPACE is not
        provided in the kwargs, output/details for all the pods in all the namespaces is returned as pod_details_dict
        :param kwargs: kwargs key/value eg; POD_NAME, NAMESPACE
        :return: pod_details_dict with all the pod details
        '''
        pod_details_dict = defaultdict(self.kube_dict)
        all_ns_pods = True if 'NAMESPACE' not in kwargs else False
        pod_output = self.get_all_pods_details_for_all_namespace(**kwargs) if all_ns_pods \
                                    else self.get_all_pods_details_for_the_namespace(**kwargs)
        for pod in pod_output.items:
            pod_status, pod_message, pod_reason = [], [], []
            pod_name = pod.metadata.name
            pod_details_dict[pod_name]['pod_name'] = '%s' % pod_name
            pod_details_dict[pod_name]['namespace'] = '%s' % pod.metadata.namespace
            containers = ['%s' % container.name for container in pod.spec.containers]
            pod_details_dict[pod_name]['containers'] = containers
            pod_details_dict[pod_name]['node_name'] = '%s' % pod.spec.node_name
            pod_details_dict[pod_name]['pod_ip'] = '%s' % pod.status.pod_ip
            pod_details_dict[pod_name]['host_ip'] = '%s' % pod.status.host_ip
            status = '%s' % pod.status.phase
            message = '%s' % pod.status.message
            reason = '%s' % pod.status.reason
            if pod.status.container_statuses:
                for container_id in pod.status.container_statuses:
                    container_state = container_id.state.running
                    container_waiting = container_id.state.waiting
                    if not container_state and 'Running' in status:
                        pod_status.append('%s Not Running' % container_id.name)
                    container_message = container_waiting.message if container_waiting else None
                    pod_message.append(container_message) if container_message else pod_message
                    container_reason = container_waiting.reason if container_waiting else None
                    pod_reason.append(container_reason) if container_reason else pod_reason
            pod_details_dict[pod_name]['status'] = ' & '.join(pod_status) if pod_status else status
            pod_details_dict[pod_name]['status_message'] = ' & '.join(pod_message) if pod_message else message
            pod_details_dict[pod_name]['status_reason'] = ' & '.join(pod_reason) if pod_reason else reason

        return pod_details_dict

    def get_all_available_namespaces_details(self, **kwargs):
        '''
        This method will get all the namespaces available in the K8s Cluster
        :return: namespaces_api_output
        '''
        watch = kwargs['WATCH'] if 'WATCH' in kwargs else False
        pretty_output = kwargs['PRETTY'] if 'PRETTY' in kwargs else False
        all_namespaces = self.kube_api_client.list_namespace(pretty=pretty_output, watch=watch)
        return all_namespaces

    def get_all_available_namespaces_names(self, **kwargs):
        '''
        This method gives the list of names of the all the available namespaces in the K8s Cluster
        :param kwargs:
        :return: namespace_list
        '''
        namespaces_details = self.get_all_available_namespaces_details(**kwargs)
        return ['%s' % namespace.metadata.name for namespace in namespaces_details.items]

    def create_service(self, **kwargs):
        '''
        This method with create pod using the API
        :param kwargs: YML_LIST: List of YML Files
        :return: True or False
        '''
        service_create_fail = 0
        yml_list = kwargs['YML_LIST'] if 'YML_LIST' in kwargs else None
        namespace = kwargs['NAMESPACE'] if 'NAMESPACE' in kwargs else 'default'
        for yml in yml_list:
            yml_obj = self.util.get_yaml_dict_as_object(yml)
            namespace = yml_obj.metadata.namespace if hasattr(yml_obj.metadata, 'namespace') else yml_obj.metadata.name
            if namespace in self.get_all_available_namespaces_names():
                # TODO: create_namespace = self.kube_api_client.create_namespace(body='')
                # TODO: create_namespace if namespace is not available
                json_body = json.dumps(yml_obj, sort_keys=True, indent=2)
                service_create = self.kube_api_client.create_namespaced_service(namespace, json.loads(json_body))
                if service_create:
                    self.m_logger.info('Service Descriptor %s created' % service_create.metadata.name)
                else:
                    service_create_fail += 1
                    self.m_logger.error('Service Creation failed for the Descriptor : %s' % yml)
        return True if not service_create_fail else False


