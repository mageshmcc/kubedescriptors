from manage_apiserver import ManageApiServer
from util import Utilities
from collections import defaultdict
import logging
import re
import os


class ManageYmlDescriptors(object):
    def __init__(self, kubehosts=None):
        self.microservice_dict = lambda: defaultdict(self.microservice_dict)
        self.microservice_install_dict = defaultdict(self.microservice_dict)
        self.kube_cluster = kubehosts if kubehosts else []
        self.kube_master = self.kube_cluster[0] if self.kube_cluster else 'localhost'
        self.kube_slaves = self.kube_cluster[1:] if self.kube_cluster else []
        self.kube_api_server = ManageApiServer()
        self.util = Utilities()
        logging.basicConfig(level=logging.INFO)
        self.m_logger = logging.getLogger(__name__)

    def get_all_yml_details_for_microservice_install(self, yml_location):
        '''
        This method get all the yml files in the list of location and gets the details like ymlfile full path,
        ymlfile install type and ymlfile namespace
        :param yml_location: ymlfile location, should be a dir
        :return: microservice_install_dict, dict with all the details
        '''
        yml_files = self.util.get_yaml_files_list(yml_location)
        for yml_file in yml_files:
            yml_descriptor = self.util.is_yaml_file_a_descriptor(yml_file)
            yml_install_type = 'kubectl' if yml_descriptor else 'kompose'
            yml_obj = self.util.get_yaml_dict_as_object(yml_file)
            namespace = '%s' % os.path.basename(os.path.dirname(yml_file))
            if 'kubectl' in yml_install_type and hasattr(yml_obj.metadata, 'namespace'):
                namespace = '%s' % yml_obj.metadata.namespace
            self.microservice_install_dict[yml_file]['INSTALL_YML_LIST'] = yml_file.split()
            self.microservice_install_dict[yml_file]['YML_INSTALL_TYPE'] = yml_install_type
            self.microservice_install_dict[yml_file]['YML_NAMESPACE'] = namespace
        self.m_logger.info('microservice_install_dict new : %s' % self.microservice_install_dict)
        return self.microservice_install_dict

    def get_all_yml_details_and_install_microservices(self, yml_location):
        '''
        This method get all the yml files in the list of location and gets the details like ymlfile full path,
        ymlfile install type and ymlfile namespace and install the ymlfile, if script_path is available for the
        yml_base_dir, script_path takes higher precedence
        :param yml_location: ymlfile location, should be a dir. For re installation scenarios,
                             yml_location has to be set as None
        :return: True, if all the ymlfile/s install is successful, else False
        '''
        install_fail = 0

        if yml_location and self.get_all_yml_details_for_microservice_install(yml_location):
            for yml_file, yml_file_details in self.microservice_install_dict.iteritems():
                if self.microservice_install(**yml_file_details):
                    self.m_logger.info('Install successful for %s' % yml_file)
                else:
                    install_fail += 1
                    self.m_logger.error('Install failed for %s' % yml_file)
            return True if not install_fail else False
        self.m_logger.error('yml_location : %s' % yml_location)
        self.m_logger.error('microservice_install_dict : %s' % self.microservice_install_dict)
        return False

    def get_all_yml_details_and_uninstall_microservices(self, yml_location):
        '''
        This method get all the yml files in the list of location and gets the details like ymlfile full path,
        ymlfile install type and ymlfile namespace and install the ymlfile
        :param yml_location: ymlfile location, should be a dir. For re installation scenarios,
                             yml_location has to be set as None
        :return: True, if all the ymlfile/s uninstall is successful, else False
        '''
        microservice_uninstall_dict = defaultdict(self.microservice_dict)
        install_fail = 0
        yml_files = self.util.get_yaml_files_list(yml_location)
        yml_uninstall_list = list(filter(lambda yml: self.util.is_yaml_file_a_descriptor(yml), yml_files))
        for yml_uninstall_file in yml_uninstall_list:
            namespace = '%s' % os.path.basename(os.path.dirname(yml_uninstall_file))
            microservice_uninstall_dict[yml_uninstall_file]['INSTALL_YML_LIST'] = yml_uninstall_file.split()
            microservice_uninstall_dict[yml_uninstall_file]['YML_NAMESPACE'] = namespace
        if microservice_uninstall_dict:
            for yml_file, yml_file_details in microservice_uninstall_dict.iteritems():
                if self.microservice_uninstall(**yml_file_details):
                    self.m_logger.info('Uninstall successful for %s' % yml_file)
                else:
                    install_fail += 1
                    self.m_logger.error('Uninstall failed for %s' % yml_file)
            return True if not install_fail else False
        return False

    def microservice_install(self, **kwargs):
        '''
        This function will install the pods/apps on the Kubernetes Cluster with the
        descriptors(using "kubectl create -f descriptor.yml") or kompose(using "kompose convert -f docker_compose.yml"
        :param INSTALL_YML_LIST: List of descriptor_install.yml files to be deployed, full path to be provided
                                     for each yml file
        :param YML_INSTALL_TYPE: Type of pod/app install, values: "kubectl", "yml_dir" or "kompose", default: "kubectl"
        :param YML_NAMESPACE: namespace for the INSTALL_YML_LIST to be installed
        :param LOCAL_HOST_INSTALL:"True" if yml_install is done on localhost, else "False"
        :return: "True" if all pods/apps gets installed successfully, else "False"
        '''
        kompose_descriptor_list = []
        failed_install_yml_list = kwargs['YML_INSTALL_FAIL_LIST'] if 'YML_INSTALL_FAIL_LIST' in kwargs else []
        fail_count = kwargs['YML_INSTALL_FAIL_COUNT'] if 'YML_INSTALL_FAIL_COUNT' in kwargs else 0
        install_yml_list = kwargs['INSTALL_YML_LIST']
        yml_install_type = kwargs['YML_INSTALL_TYPE'] if 'YML_INSTALL_TYPE' in kwargs else 'kubectl'
        yml_namespace = kwargs['YML_NAMESPACE'] if 'YML_NAMESPACE' in kwargs else 'default'
        local_host = kwargs['LOCAL_HOST_INSTALL'] if 'LOCAL_HOST_INSTALL' in kwargs else True
        yml_install_host = '%s' % self.kube_master
        yml_execute_cmd = 'kubectl create' if 'kubectl' in yml_install_type else 'sudo kompose convert'
        for install_yml in install_yml_list:
            yml_install_cmd = '%s -f %s' % (yml_execute_cmd, install_yml)
            if 'kompose' in yml_install_type:
                yml_install_cmd = '%s -f %s -o %s' % (yml_execute_cmd, install_yml, os.path.dirname(install_yml))
            if 'kubectl' in yml_install_type:
                namespace, namespace_status, namespace_output = self.kubectl_create_namespace(yml_namespace,
                                                                                              yml_install_host,
                                                                                              local_host)
                if namespace_status:
                    yml_install_cmd = '%s -f %s --namespace %s' % (yml_execute_cmd, install_yml, namespace)
                    self.m_logger.info('Namespace %s created' % namespace)
                    self.m_logger.info('Namespace %s create output : %s' % (namespace, namespace_output))
                else:
                    fail_count += 1
                    self.m_logger.error('Namespace %s creation failed with error %s' % (namespace,
                                                                                        namespace_output))
                    self.m_logger.error('%s descriptor will not be created due to Namespace creation failed' %
                                        install_yml)
                    continue
            yml_install_status, yml_install_output = self.util.execute_cmd(host_to_ssh=yml_install_host,
                                                                           cmd_to_execute=yml_install_cmd,
                                                                           local_host=local_host)
            if yml_install_status:
                self.m_logger.info('CMD %s PASSED FOR %s' % (yml_execute_cmd, install_yml))
                self.m_logger.info('CMD OUTPUT : %s' % yml_install_output)
                if 'kompose' in yml_install_type:
                    kompose_descriptor_list, fail_count = self.get_descriptors_from_kompose(yml_install_output,
                                                                                            kompose_descriptor_list,
                                                                                            fail_count)
                    if kompose_descriptor_list:
                        for yml_key, yml_value in self.microservice_install_dict.get(install_yml).iteritems():
                            if 'INSTALL_YML_LIST' in yml_key:
                                self.microservice_install_dict[install_yml][yml_key] = kompose_descriptor_list
                            if 'YML_INSTALL_TYPE' in yml_key:
                                self.microservice_install_dict[install_yml][yml_key] = 'kubectl'
                        self.m_logger.info('kompose_descriptor_yml_list all : %s' % kompose_descriptor_list)
                        self.m_logger.info('microservice_install_dict updated : %s' % self.microservice_install_dict)
                        return self.microservice_install(INSTALL_YML_LIST=kompose_descriptor_list,
                                                         YML_NAMESPACE=yml_namespace,
                                                         YML_INSTALL_FAIL_COUNT=fail_count,
                                                         YML_INSTALL_FAIL_LIST=failed_install_yml_list)
            else:
                fail_count += 1
                failed_install_yml_list.append(install_yml)
                self.m_logger.error('CMD %s FAILED FOR %s' % (yml_execute_cmd, install_yml))
                self.m_logger.error('CMD OUTPUT : %s' % yml_install_output)

        if not fail_count:
            self.m_logger.info('YML INSTALL PASSED FOR ALL THE YML_INSTALL FILES: %s' %
                               install_yml_list)
            return True

        self.m_logger.error('YML INSTALL FAILED FOR THE YML_INSTALL FILES: %s' %
                            failed_install_yml_list)
        return False

    def cleanup_installed_microservices(self):
        '''
        This method get all the yml details in the list of location and gets the details like ymlfile full path,
        ymlfile install type and ymlfile namespace and uninstall the ymlfile
        :return: True, if all the ymlfile/s install is successful, else False
        '''
        install_fail = 0
        for yml_file, yml_file_details in self.microservice_install_dict.iteritems():
            if self.microservice_uninstall(**yml_file_details):
                self.m_logger.info('Uninstall successful for %s' % yml_file)
            else:
                install_fail += 1
                self.m_logger.error('Uninstall failed for %s' % yml_file)
        return True if not install_fail else False

    def microservice_uninstall(self, **kwargs):
        '''
        This function will uninstall the pods/apps on the Kubernetes Cluster with the
        descriptors(using "kubectl delete -f descriptor.yml")
        :param YML_LIST: List of Descriptor YML File/s to be deleted
        :return: "True" if all Descriptors gets uninstalled successfully, else "False"
        '''
        fail_count, failed_yml_list = 0, []
        local_host = kwargs['LOCAL_HOST_INSTALL'] if 'LOCAL_HOST_INSTALL' in kwargs else True
        yml_file_list = kwargs['INSTALL_YML_LIST']
        namespace = kwargs['YML_NAMESPACE']
        for yml_file in yml_file_list:
            uninstall_cmd = 'kubectl delete -f %s --namespace %s' % (yml_file, namespace)
            uninstall_status, uninstall_output = self.util.execute_cmd(host_to_ssh='%s' % self.kube_master,
                                                                       cmd_to_execute=uninstall_cmd,
                                                                       local_host=local_host)
            if uninstall_status:
                self.m_logger.info('CMD %s PASSED' % uninstall_cmd)
                self.m_logger.info('CMD OUTPUT : %s' % uninstall_output)
            else:
                fail_count += 1
                failed_yml_list.append(yml_file)
                self.m_logger.error('CMD %s FAILED' % uninstall_cmd)
                self.m_logger.error('CMD OUTPUT : %s' % uninstall_output)

        if not fail_count:
            self.m_logger.info('UNINSTALL SUCCESSFUL FOR ALL THE YML FILES: %s' % yml_file_list)
            return True

        self.m_logger.error('UNINSTALL FAILED FOR THE YML FILES: %s' % failed_yml_list)
        return False

    def kubectl_create_namespace(self, namespace, kube_master, local_host):
        '''
        This method creates namespace using "kubectl create namespace <namespace>", if namespace does not exists
        :param namespace: namespace to be created
        :param kube_master: kube_master_ip, default: 'localhost'
        :param local_host: True if yml_install_host is 'localhost', else False
        :return: namespace_created, namespace_create_status, namespace_create_output
        '''
        namespace_status, namespace_output = True, 'Namespace %s is already available' % namespace
        if namespace not in self.kube_api_server.get_all_available_namespaces_names():
            namespace_create_cmd = 'kubectl create namespace %s' % namespace
            namespace_status, namespace_output = self.util.execute_cmd(host_to_ssh=kube_master,
                                                                       cmd_to_execute=namespace_create_cmd,
                                                                       local_host=local_host)
        return namespace, namespace_status, namespace_output

    def kubectl_create_namespace_for_all_descriptors_in_a_dir(self, yml_dir, yml_install_host, local_host, fail_count):
        '''
        This method creates namespaces for all descriptor in a given yml_dir, if the namespace does not exists
        :param yml_dir: full directory path of the descriptors
        :param yml_install_host: kube_master_ip, default: 'localhost'
        :param local_host: True if yml_install_host is 'localhost', else False
        :param fail_count: fail_count, gets incremented incase of failed scenarios
        :return: fail_count
        '''
        if os.path.isdir(yml_dir):
            for file in os.listdir(yml_dir):
                descriptor_yml_file = os.path.join(yml_dir, file)
                namespace, namespace_status, namespace_output = self.kubectl_create_namespace(descriptor_yml_file,
                                                                                              yml_install_host,
                                                                                              local_host)
                if namespace_status:
                    self.m_logger.info('Namespace %s created' % namespace)
                    self.m_logger.info('Namespace %s create output : %s' % (namespace, namespace_output))
                else:
                    fail_count += 1
                    self.m_logger.error('Namespace %s creation failed with error %s' % (namespace,
                                                                                        namespace_output))
        else:
            fail_count += 1
            self.m_logger.error('%s is not a directory' % yml_dir)
        return fail_count

    def get_descriptors_from_kompose(self, yml_install_output, kompose_descriptor_yml_list, fail_count):
        '''
        This method appends all the descriptor files to kompose_descriptor_yml_list, which were created using "kompose convert"
        :param yml_install_output: output of "kompose convert"
        :param kompose_descriptor_yml_list: kompose_descriptor_yml_list
        :param fail_count: fail_count, gets incremented incase of failed scenarios
        :return: kompose_descriptor_yml_list, fail_count
        '''
        for yml in yml_install_output:
            self.m_logger.info('KOMPOSE CONVERT OUTPUT : %s' % yml)
            yml_file_search = re.search('Kubernetes file \"(\S+\.yaml)\" created', '%s' % yml)
            if yml_file_search:
                yml_file = '%s' % yml_file_search.group(1)
                self.m_logger.info('yml_file_search : %s' % yml_file)
                if 'deployment' in yml_file_search.group(1):
                    kompose_descriptor_yml_list.insert(0, yml_file)
                else:
                    kompose_descriptor_yml_list.append(yml_file)
            else:
                fail_count += 1
                self.m_logger.error('Not able to find the descriptor file')
                self.m_logger.error('Faile/Ouput seen is : %s' % yml)
        return kompose_descriptor_yml_list, fail_count


