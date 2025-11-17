
from arms.pipeline.jenkins.objects.Stage import Stage
from arms.pipeline.jenkins.objects.credentials.SecretFile import SecretFile
from service_comunications.connectors import get_file_from_connector
from utils import File
from arms.arm import get_arm

def get_kubernetes_deploy(infrastructure_type, infrastructure_id):
    deployment = get_arm("infrastructure", infrastructure_type, infrastructure_id)
    # service.pipeline.install_jenkins_plugin("Kubernetes Continuous Deploy Plugin")
    deploy = Stage("Deploy")
    ###testing mode
    kubeconfig = get_file_from_connector(deployment.connector_id, "kubeconfig")
    ###end
    deploy.credentials.append(SecretFile(File("kubeconfig", kubeconfig["file_content"]), "kubeconfig"))
    step = f"""withKubeConfig([credentialsId: 'kubeconfig']) {{
					powershell '''
						kubectl create namespace {deployment.namespace}
                        $yamlFiles = Get-ChildItem -Path 'infrastructure/' -Filter "*.yaml" -Recurse
                        foreach ($yamlFile in $yamlFiles) {{
                            (Get-Content $yamlFile.FullName) -replace '&lt;version&gt;', $env:BUILD_NUMBER | Set-Content $yamlFile.FullName
                            Write-Host "Applying: $yamlFile"
                            kubectl apply -f $yamlFile.FullName --namespace {deployment.namespace}
                        }}
					'''
				    }}"""
    deploy.steps.append(step)
    return deploy