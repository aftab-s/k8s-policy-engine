from flask import Flask, render_template, request
from kubernetes import client, config

app = Flask(__name__)

# Load Kubernetes configuration from default kubeconfig file
config.load_kube_config()

@app.route('/')
def index():
    # Create Kubernetes API client
    v1 = client.CoreV1Api()

    # Get list of namespaces
    namespaces = v1.list_namespace()
    namespace_list = [ns.metadata.name for ns in namespaces.items]

    return render_template('index.html', namespaces=namespace_list)

@app.route('/list_resources', methods=['POST'])
def list_resources():
    # Create Kubernetes API client
    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    core_v1 = client.CoreV1Api()
    networking_v1 = client.NetworkingV1Api()  # Use NetworkingV1Api instead of NetworkingV1beta1Api
    argo_v1 = client.CustomObjectsApi()

    # Get selected namespace and tab from the form
    selected_namespace = request.form.get('namespace', 'default')
    selected_tab = request.form.get('tab', 'pods')

    # Get list of namespaces
    namespaces = v1.list_namespace()
    namespace_list = [ns.metadata.name for ns in namespaces.items]

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
        namespaces=namespace_list  # Pass namespaces for the dropdown menu
    )


if __name__ == '__main__':
    app.run(debug=True)
