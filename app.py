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

    return render_template(
        'list_resources.html',
        selected_namespace=selected_namespace,
        selected_tab=selected_tab,
        resources=resource_list,
        namespaces=namespace_list  # Pass namespaces for the dropdown menu
    )


if __name__ == '__main__':
    app.run(debug=True)