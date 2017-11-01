# KubeDescriptors
Installing/Managing YML Descriptors/Docker-compose file on K8S Cluster

KubeDescriptors is a Python(2.7) wrapper, which auto magically install yml descriptors/docker-compose file/s as microservices on a Kubernetes Cluster using the combination of Kubernetes APIs and kubectl commands

## Usecase
Let us take a scenario, where we have huge platform with Multiple Microservices and each Microservices are handled by different teams in an organization.
If each team, provides their own list of YAML Files, which could Descriptors/docker-compose or combination of both, to be installed on the K8S Cluster.
Kubedescriptor can auto magically got thru all the YAML Files, find the type of the YML(Descriptors/docker-compose) and install them accordingly.
    
    * If YML file is a Descriptor, it is installed using "kubectl" command
    * If YML file is a docker-compose, it is converted to a descriptor and then installed using "kubectl" command
    * Example of YAML Files for a Platfrom;
       YML_FILE_LOCATION
       |
       |-Team1-|--Microservice_1--|-descriptor_yml_file_1
       |       |                  |-descriptor_yml_file_2
       |       |                  |:
       |       |                  |-descriptor_yml_file_N
       |       |
       |       |--Microservice_2--|-descriptor_yml_file_1
       |       |                  |-descriptor_yml_file_2
       |       |                  |:
       |       |                  |-descriptor_yml_file_N
       |       |                  |
       |       |                  |-docker_compose_yml_file_1
       |       |                  |-docker_compose_yml_file_2
       |       |                  |:
       |       |                  |-docker_compose_yml_file_N
       |       |:
       |       |:
       |       |--Microservice_N--|-docker_compose_yml_file_1
       |                          |-docker_compose_yml_file_2
       |                          |:
       |                          |-docker_compose_yml_file_N
       |:
       |:
       |-TeamN(with multiple Microservices))
       
## Prerequisites

1. Kubernetes Cluster Installed and Up and Running
2. kompose installed on the K8S Master
3. pip install kubernetes(Python Client for K8S) on the K8S Master
4. pip install bunch on the K8S Master
5. pip install yaml on the K8S Master
6. KubeDescriptors should be cloned/present on the K8S Master

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


            

