pipeline {
    agent any

    environment {
        DOCKER_USER = 'usmanfarooq317'     // your DockerHub username
        IMAGE_NAME = 'api-analytics'       // repo name on DockerHub
        EC2_HOST = '54.89.241.89'          // your EC2 public IP
    }

    stages {

        stage('Checkout Code') {
    steps {
        git branch: 'main',
            credentialsId: 'github-token',
            url: 'https://github.com/usmanfarooq317/API-analytics.git'
    }
}


        stage('Build Docker Image') {
            steps {
                sh """
                    docker build -t ${DOCKER_USER}/${IMAGE_NAME}:latest .
                """
            }
        }

        stage('Login & Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'docker-hub-creds',
                    usernameVariable: 'DOCKER_USERNAME',
                    passwordVariable: 'DOCKER_PASSWORD'
                )]) {
                    sh """
                        echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
                        docker push ${DOCKER_USER}/${IMAGE_NAME}:latest
                    """
                }
            }
        }

        stage('Deploy to EC2') {
            steps {
                sshagent(['ec2-ssh-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} '
                            docker pull ${DOCKER_USER}/${IMAGE_NAME}:latest &&
                            docker stop api-analytics || true &&
                            docker rm api-analytics || true &&
                            docker run -d --name api-analytics -p 5000:5000 \
                                ${DOCKER_USER}/${IMAGE_NAME}:latest
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
