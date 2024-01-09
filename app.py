from flask import Flask, render_template, request
from kubernetes import client, config

app = Flask(__name__)

# Load Kubernetes configuration from default kubeconfig file
config.load_kube_config()

@app.route('/')
def index():
    # Create Kubernetes API client
    v1 = client.CoreV1Api()

    try:
        # Get list of namespaces
        namespaces = v1.list_namespace()
        namespace_list = [ns.metadata.name for ns in namespaces.items]
        print("Namespace List:", namespace_list)  # Add this line for debugging
    except Exception as e:
        print("Error fetching namespaces:", str(e))  # Add this line for debugging
        namespace_list = []

    return render_template('index.html', namespaces=namespace_list)

@app.route('/resources', methods=['POST'])
def list_resources():
    # Create Kubernetes API client
    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()  # Use AppsV1Api instead of ExtensionsV1beta1Api

    # Get selected namespace and tab from the form
    selected_namespace = request.form.get('namespace', 'default')
    selected_tab = request.form.get('tab', 'pods')

    # Initialize variables for resource list and title
    resource_list = []
    title = f"{selected_tab.capitalize()} in {selected_namespace}"

    if selected_tab == 'pods':
        # Get list of pods in the selected namespace
        pods = v1.list_namespaced_pod(selected_namespace)

        # Extract relevant information about each pod
        resource_list = [{'name': pod.metadata.name, 'status': pod.status.phase, 'namespace': pod.metadata.namespace} for pod in pods.items]
    elif selected_tab == 'services':
        # Get list of services in the selected namespace
        services = v1.list_namespaced_service(selected_namespace)

        # Extract relevant information about each service
        resource_list = [{'name': svc.metadata.name, 'type': svc.spec.type, 'namespace': svc.metadata.namespace} for svc in services.items]
    elif selected_tab == 'deployments':
        # Get list of deployments in the selected namespace using AppsV1Api
        deployments = apps_v1.list_namespaced_deployment(selected_namespace)

        # Extract relevant information about each deployment
        resource_list = [{'name': dep.metadata.name, 'replicas': dep.status.replicas, 'namespace': dep.metadata.namespace} for dep in deployments.items]

    return render_template('list_resources.html', title=title, selected_namespace=selected_namespace, selected_tab=selected_tab, resources=resource_list)

if __name__ == '__main__':
    app.run(debug=True)
