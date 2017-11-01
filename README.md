# KubeDescriptors
Installing/Managing YML Descriptors/Docker-compose file on K8S Cluster

KubeDescriptors is a Python(2.7) wrapper to install yml descriptors/docker-compose file on a Kubernetes Cluster using the combination of Kubernetes APIs and kubectl commands

## Prerequisites

1. Kubernetes Cluster Installed and Up and Running
2. kompose installed on the K8S Master
3. pip install kubernetes(Python Client for K8S) on the K8S Master
4. pip install bunch on the K8S Master
5. KubeDescriptors should be cloned/present on the K8S Master

## Working of KubeDescriptors

1. Provide a yml_file_location of the YML Files to be installed on the K8S Cluster;
    * yml_file_location can have multiple dirs/files within it
    * yml_file_location should be present on the K8S Master
    * KubeDescriptors will go through the all the files using os.walk and get all the yml files to be installed on the K8S Cluster


2. yml_file_location can have a combination of yml descriptors or docker-compose file/s
    * KubeDescriptors have logic to find if the yml file is a descriptor or a docker-compose
    * If the yml file is a docker-compose, descriptor/s are generated using "kompose"
    * Once we have all descriptors, they are installed individually using "kubectl"
    * Logic to create the Namespace required for each descriptors is also taken care
    * Incase of docker-compose files, Namespaces are not present in the yml file/s and hence the descriptors generated using "kompose" will not have the Namespace details. In these scenario, the base directory name is taken as the Namespace name and all descriptors are installed within this Namespace
        * Example:
            -   If the yml_file_location is /home/some_name/yml_files/ 
            -   The docker-compose yml file is present inside /home/some_name/yml_files/xyz_dir/xyz-docker-compose.yml
            -   xyz-docker-compose.yml is converted into descriptor/s and installed in the Namespace "xyz_dir"
            
            
3. KubeDescriptors also provides the Status of the pods with basic details once the Descriptors are insatlled using the APIs from the APIServer, for more details, please see the examples

## Future of KubeDescriptors

1. KubeDescriptors will have logic to install/upgrade/manage Kubernetes Cluster on Bare Metals/VMs, using kubespray
2. Replace all/most of the "kubectl" commands with the APIs from the APIServer
3. Many More to come


            

