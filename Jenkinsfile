pipeline {
    agent any
    
    // ---> CHANGE THIS TO YOUR DOCKER HUB USERNAME <---
    environment {
        DOCKER_IMAGE = 'YOUR_DOCKERHUB_USERNAME/smart-clinic:latest'
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                echo 'Building the Smart Clinic Docker Image...'
                sh "docker build -t ${DOCKER_IMAGE} ."
            }
        }

        stage('Security Scan (Trivy)') {
            steps {
                echo 'Running Trivy Vulnerability Scanner...'
                sh "trivy image --no-progress ${DOCKER_IMAGE}"
            }
        }

        stage('Push to Docker Hub') {
            steps {
                echo 'Pushing image to Docker Hub...'
                // Assumes you have configured Jenkins credentials named 'docker-hub-credentials'
                withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials', passwordVariable: 'DOCKER_PASS', usernameVariable: 'DOCKER_USER')]) {
                    sh "echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin"
                    sh "docker push ${DOCKER_IMAGE}"
                }
            }
        }

        stage('Deploy Infrastructure (Terraform)') {
            steps {
                echo 'Applying Terraform configuration...'
                sh 'terraform init'
                sh 'terraform apply -auto-approve'
            }
        }
    }
}