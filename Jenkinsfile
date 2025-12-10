
pipeline {
    agent any

    environment {
        DOCKER_USER = 'usmanfarooq317'
        IMAGE_NAME = 'api-analytics'
        IMAGE_TAG = 'latest'                // Can extend to dynamic version later
        EC2_HOST = '54.89.241.89'
    }

    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main',
                    credentialsId: 'github-token',
                    url: 'https://github.com/usmanfarooq317/API-analytics.git'
            }
        }

        stage('Docker Login') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'docker-hub-creds',
                    usernameVariable: 'DOCKER_USERNAME',
                    passwordVariable: 'DOCKER_PASSWORD'
                )]) {
                    sh """
                        echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
                    """
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    def imageExists = sh(
                        script: "docker images -q ${DOCKER_USER}/${IMAGE_NAME}:${IMAGE_TAG}",
                        returnStdout: true
                    ).trim()

                    if (imageExists) {
                        echo "⚡ Docker image exists locally. Rebuilding..."
                        sh "docker rmi -f ${DOCKER_USER}/${IMAGE_NAME}:${IMAGE_TAG} || true"
                    } else {
                        echo "🆕 Docker image does not exist locally. Building new..."
                    }

                    sh "docker build -t ${DOCKER_USER}/${IMAGE_NAME}:${IMAGE_TAG} ."
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'docker-hub-creds',
                    usernameVariable: 'DOCKER_USERNAME',
                    passwordVariable: 'DOCKER_PASSWORD'
                )]) {
                    sh "docker push ${DOCKER_USER}/${IMAGE_NAME}:${IMAGE_TAG}"
                }
            }
        }

        stage('Deploy to EC2') {
            steps {
                sshagent(['ec2-ssh-key']) {
                    sh """
                    ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} '
                        # Stop and remove container if exists
                        docker rm -f api-analytics 2>/dev/null || true

                        # Kill any process using port 5000
                        fuser -k 5000/tcp || true

                        # Pull latest image
                        docker pull ${DOCKER_USER}/${IMAGE_NAME}:${IMAGE_TAG}

                        # Run new container
                        docker run -d --name api-analytics -p 5000:5000 ${DOCKER_USER}/${IMAGE_NAME}:${IMAGE_TAG}
                    '
                    """
                }
            }
        }
    }

    post {
        success {
            echo "🚀 Deployment Successful!"
        }
        failure {
            echo "❌ Deployment Failed!"
        }
    }
}
