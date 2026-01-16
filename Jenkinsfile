pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'locust-app'
        REGISTRY = 'your-registry.com'
    }

    stages {
        stage('Checkout')
        stage('Build')
        stage('Test')
        stage('Deploy')
    }

    stage('Checkout') {
        steps {
            checkout scm
        }
    }

    stage('Build Docker Image') {
        steps {
            script {
                sh "docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} ."
                sh "docker tag ${DOCKER_IMAGE}:${BUILD_NUMBER} ${DOCKER_IMAGE}:latest"
            }
        }
    }

    stage('Test') {
        steps {
            script {
                sh "docker run --rm ${DOCKER_IMAGE}:${BUILD_NUMBER} streamlit version"
                sh "docker run --rm ${DOCKER_IMAGE}:${BUILD_NUMBER} python -m py_compile app/ui/main.py"
            }
        }
    }

    stage('Deploy') {
        when {
            branch 'main'
        }
        steps {
            script {
                sh "helm upgrade --install locust ./helm/locust --namespace loadtest --create-namespace"
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
