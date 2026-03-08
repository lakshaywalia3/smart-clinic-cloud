pipeline {
    agent any

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                echo 'Building the Smart Clinic Docker Image...'
                sh 'docker build -t smart-clinic:latest .'
            }
        }

        stage('Security Scan (Trivy)') {
            steps {
                echo 'Running Trivy Vulnerability Scanner...'
                sh 'trivy image --no-progress smart-clinic:latest'
            }
        }

        stage('Push Image to Kubernetes') {
            steps {
                echo 'Transferring image from Docker to K3s...'
                // Docker save doesn't need sudo, but K3s import does
                sh 'docker save smart-clinic:latest | sudo k3s ctr images import -'
            }
        }

        stage('Deploy Infrastructure (Terraform)') {
            steps {
                echo 'Applying Terraform configuration...'
                sh 'terraform init'
                // -auto-approve means it won't wait for us to type "yes"
                sh 'terraform apply -auto-approve'
            }
        }
    }
}