pipeline {
    agent any

    environment {
        IMAGE_NAME     = "genapp"
        CONTAINER_NAME = "generic-app"
        HOST_PORT      = "8000"
        CONTAINER_PORT = "8000"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build image') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} -t ${IMAGE_NAME}:latest ."
            }
        }

        stage('Restart container') {
            steps {
                sh """
                    docker rm -f ${CONTAINER_NAME} 2>/dev/null || true
                    docker run -d \
                        --name ${CONTAINER_NAME} \
                        --restart unless-stopped \
                        -p ${HOST_PORT}:${CONTAINER_PORT} \
                        ${IMAGE_NAME}:latest
                """
            }
        }
    }

    post {
        always {
            sh "docker image prune -f"
        }
        success {
            sh "docker ps --filter name=${CONTAINER_NAME}"
        }
    }
}