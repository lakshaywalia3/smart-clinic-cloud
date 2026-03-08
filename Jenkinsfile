pipeline {
    agent any // This tells Jenkins to run on your home server

    stages {
        stage('Checkout Code') {
            steps {
                // This automatically pulls the latest code from GitHub
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                // We use 'sh' to run Linux terminal commands
                echo 'Building the Smart Clinic Docker Image...'
                sh 'docker build -t smart-clinic:latest .'
            }
        }

        stage('Security Scan (Trivy)') {
            steps {
                echo 'Running Trivy Vulnerability Scanner...'
                // We scan the image we just built. 
                sh 'trivy image --no-progress smart-clinic:latest'
            }
        }
    }
}