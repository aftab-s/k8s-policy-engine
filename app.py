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

@app.route('/pods', methods=['POST'])
def list_pods():
    # Create Kubernetes API client
    v1 = client.CoreV1Api()

    # Get selected namespace from the form
    selected_namespace = request.form.get('namespace', 'default')

    # Get list of pods in the selected namespace
    pods = v1.list_namespaced_pod(selected_namespace)

    # Extract relevant information about each pod
    pod_list = []
    for pod in pods.items:
        pod_info = {
            'name': pod.metadata.name,
            'status': pod.status.phase,
            'namespace': pod.metadata.namespace,
        }
        pod_list.append(pod_info)

    return render_template('list_pods.html', selected_namespace=selected_namespace, pods=pod_list)

if __name__ == '__main__':
    app.run(debug=True)