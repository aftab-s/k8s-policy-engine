import os
import json
import subprocess
from flask import Flask, render_template, request, jsonify, redirect, url_for
from kubernetes import client, config

app = Flask(__name__)

# Load Kubernetes configuration from the default kubeconfig file
config.load_kube_config()

# Specifying the directories containing policies YAML files
JSPOLICY_DIRECTORY = "JsPolicy-YAML"
KYVERNO_DIRECTORY = "Kyverno-YAML"

@app.route('/', methods=['GET', 'POST'])
def index():
    # Create Kubernetes API client
    v1 = client.CoreV1Api()

    if request.method == 'POST':
        selected_engine = request.form.get('engine', 'kyverno')
        return redirect(url_for('list_resources', engine=selected_engine))

    # Get list of namespaces
    namespaces = v1.list_namespace()
    namespace_list = [ns.metadata.name for ns in namespaces.items]

    # Fetch jspolicy policies
    return render_template('index.html', namespaces=namespace_list)

@app.route('/list_resources', methods=['POST'])
def list_resources():
    # Create Kubernetes API client
    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    core_v1 = client.CoreV1Api()
    networking_v1 = client.NetworkingV1Api()
    argo_v1 = client.CustomObjectsApi()

    # Initializing engine to kyverno
    selected_engine = request.form.get('engine', 'kyverno')

    # Get selected namespace and tab from the form
    selected_namespace = request.form.get('namespace', 'default')
    selected_tab = request.form.get('tab', 'pods')

    # Get list of namespaces
    namespaces = v1.list_namespace()
    namespace_list = [ns.metadata.name for ns in namespaces.items]

    # if selected_engine == 'kyverno':
    #     policies_directory = KYVERNO_DIRECTORY
    # elif selected_engine == 'jspolicy':
    #     policies_directory = JSPOLICY_DIRECTORY
    # else:
    #     # Handle invalid selection
    #     policies_directory = None

    # Initialize resource list
    resource_list = []

    if selected_tab == 'pods':
        # Get list of pods in the selected namespace
        pods = v1.list_namespaced_pod(selected_namespace)

        # Extract relevant information about each pod
        for pod in pods.items:
            pod_info = {
                'name': pod.metadata.name,
                'status': pod.status.phase,
                'namespace': pod.metadata.namespace,
            }
            resource_list.append(pod_info)

    elif selected_tab == 'services':
        # Get list of services in the selected namespace
        services = v1.list_namespaced_service(selected_namespace)

        # Extract relevant information about each service
        for service in services.items:
            service_info = {
                'name': service.metadata.name,
                'type': service.spec.type,
                'namespace': service.metadata.namespace,
            }
            resource_list.append(service_info)

    elif selected_tab == 'deployments':
        # Get list of deployments in the selected namespace
        deployments = apps_v1.list_namespaced_deployment(selected_namespace)

        # Extract relevant information about each deployment
        for deployment in deployments.items:
            deployment_info = {
                'name': deployment.metadata.name,
                'replicas': deployment.spec.replicas,
                'namespace': deployment.metadata.namespace,
            }
            resource_list.append(deployment_info)

    elif selected_tab == 'configmaps':
        # Get list of ConfigMaps in the selected namespace
        configmaps = core_v1.list_namespaced_config_map(selected_namespace)

        # Extract relevant information about each ConfigMap
        for configmap in configmaps.items:
            configmap_info = {
                'name': configmap.metadata.name,
                'namespace': configmap.metadata.namespace,
            }
            resource_list.append(configmap_info)

    elif selected_tab == 'ingresses':
        # Get list of Ingresses in the selected namespace
        ingresses = networking_v1.list_namespaced_ingress(selected_namespace)

        # Extract relevant information about each Ingress
        for ingress in ingresses.items:
            ingress_info = {
                'name': ingress.metadata.name,
                'namespace': ingress.metadata.namespace,
            }
            resource_list.append(ingress_info)

    elif selected_tab == 'secrets':
        # Get list of Secrets in the selected namespace
        secrets = core_v1.list_namespaced_secret(selected_namespace)

        # Extract relevant information about each Secret
        for secret in secrets.items:
            secret_info = {
                'name': secret.metadata.name,
                'namespace': secret.metadata.namespace,
            }
            resource_list.append(secret_info)

    elif selected_tab == 'applications':
        # Get list of Applications using Argo CD API
        group = 'argoproj.io'
        version = 'v1alpha1'
        plural = 'applications'
        field_selector = f'metadata.namespace={selected_namespace}'
        applications = argo_v1.list_namespaced_custom_object(group, version, selected_namespace, plural, field_selector=field_selector)

        # Extract relevant information about each Application
        for application in applications['items']:
            application_info = {
                'name': application['metadata']['name'],
                'namespace': application['metadata']['namespace'],
            }
            resource_list.append(application_info)

    elif selected_tab == 'volumes':
        # Get list of PersistentVolumes in the cluster
        volumes = core_v1.list_persistent_volume()

        # Extract relevant information about each PersistentVolume
        for volume in volumes.items:
            volume_info = {
                'name': volume.metadata.name,
                'capacity': volume.spec.capacity,
                'namespace': volume.metadata.namespace,
            }
            resource_list.append(volume_info)

    return render_template(
        'list_resources.html',
        selected_namespace=selected_namespace,
        selected_tab=selected_tab,
        resources=resource_list,
        namespaces=namespace_list,
        selected_engine=selected_engine,
        jspolicy_policies=get_yaml_policy_names(JSPOLICY_DIRECTORY) if selected_engine == 'jspolicy' else None,
        kyverno_policies=get_yaml_policy_names(KYVERNO_DIRECTORY) if selected_engine == 'kyverno' else None
    )


def get_yaml_policy_names(directory):
    try:
        # Get list of files in the specified directory
        files = [f for f in os.listdir(directory) if f.endswith(".yaml")]

        # Extract policy names from file names
        policy_names = [os.path.splitext(os.path.basename(file))[0] for file in files]

        print(f"Fetched jspolicy policies from YAML files: {policy_names}")

        return policy_names

    except Exception as e:
        # Handle exceptions (e.g., directory not found, file read error)
        print(f"Error fetching jspolicy policies from YAML files: {str(e)}")
        return []
    

@app.route('/list_jspolicy_policies')
def list_jspolicy_policies():
    jspolicy_policies = get_yaml_policy_names(POLICIES_DIRECTORY)
    print(f"jspolicy policies passed to frontend: {jspolicy_policies}")
    return render_template('list_jspolicy_policies.html', jspolicy_policies=jspolicy_policies)

@app.route('/apply_policy', methods=['POST'])
def apply_policy():
    selected_policy = request.form.get('jspolicy_policy', 'default_policy')
     
    command = f"kubectl apply -f {POLICIES_DIRECTORY}/{selected_policy}.yaml"
    subprocess.run(command, shell=True, check=True)

    # Fetch jspolicy policy details after applying
    print(f"Fetched jspolicy policy details: {selected_policy}")
    
    applied_policies = get_applied_jspolicy_policies()

    return render_template('applied_policies.html', applied_policies=applied_policies)
    
@app.route('/applied_policies')
def applied_policies():
    # Fetch applied jspolicy policies (you need to implement this function)
    applied_policies = get_applied_jspolicy_policies()
    
    return render_template('applied_policies.html', applied_policies=applied_policies)

def get_applied_jspolicy_policies():
    try:
        # Run kubectl command to get applied jspolicy policies
        command = "kubectl get clusterpolicies -o=json"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)

        # Parse the JSON output
        applied_policies = json.loads(result.stdout)

        # Extract relevant information about each applied policy
        applied_policies_list = [{'cluster_name': policy['metadata'].get('clusterName', 'N/A'), 'name': policy['metadata']['name']} for policy in applied_policies.get('items', [])]

        print(f"Fetched applied jspolicy policies: {applied_policies_list}")

        return applied_policies_list

    except subprocess.CalledProcessError as e:
        # Handle exceptions (e.g., kubectl command failed)
        print(f"Error fetching applied jspolicy policies: {str(e)}")
        return []

@app.route('/delete_policy', methods=['POST'])
def delete_policy():
    
    selected_policy = request.form.get('jspolicy_policy', 'default_policy')

    # Fetch jspolicy policies
    
    command = f"kubectl delete -f {POLICIES_DIRECTORY}/{selected_policy}.yaml"
    subprocess.run(command, shell=True, check=True)

    # Fetch jspolicy policy details after applying
    print(f"Fetched jspolicy policy details: {selected_policy}")

    response = {
        "success": True,
        "message": "Policy deleted successfully",
        "redirect": url_for('applied_policies')
    }

    return jsonify(response)
    
def get_jspolicy_policies():
    try:
        # Create Kubernetes API client for Custom Resources (CR)
        custom_api = client.CustomObjectsApi()

        # Fetch jspolicy policies
        group = 'jspolicy.io'
        version = 'v1'
        plural = 'clusterpolicies'
        policies = custom_api.list_cluster_custom_object(group, version, plural)

        # Extract relevant information about each policy
        jspolicy_policies = [policy['metadata']['name'] for policy in policies.get('items', [])]
        print(f"Fetched jspolicy policies: {jspolicy_policies}")

        return jspolicy_policies

    except Exception as e:
        # Handle exceptions (e.g., jspolicy CRD not found, API server unreachable)
        print(f"Error fetching jspolicy policies: {str(e)}")
        return []

if __name__ == '__main__':
    app.run(debug=True)