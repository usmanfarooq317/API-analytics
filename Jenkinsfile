pipeline {
    agent any

    environment {
        DOCKER_USER = 'usmanfarooq317'     
        IMAGE_NAME = 'api-analytics'       
        EC2_HOST = '54.89.241.89'          
        IMAGE_TAG = 'latest'                // can extend to dynamic version later
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
                script {
                    // Check if image exists locally
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
                    script {
                        // Login
                        sh "echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin"

                        // Check if image exists on Docker Hub
                        def existsOnHub = sh(
                            script: "curl -s -u $DOCKER_USERNAME:$DOCKER_PASSWORD https://hub.docker.com/v2/repositories/${DOCKER_USER}/${IMAGE_NAME}/tags/${IMAGE_TAG}/ | jq -r '.name'",
                            returnStdout: true
                        ).trim()

                        if (existsOnHub == IMAGE_TAG) {
                            echo "⚡ Docker image exists on Docker Hub. It will be replaced."
                        } else {
                            echo "🆕 Docker image does not exist on Docker Hub. Creating new."
                        }

                        // Push image
                        sh "docker push ${DOCKER_USER}/${IMAGE_NAME}:${IMAGE_TAG}"
                    }
                }
            }
        }

        stage('Deploy to EC2') {
            steps {
                sshagent(['ec2-ssh-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ubuntu@${EC2_HOST} '
                            docker pull ${DOCKER_USER}/${IMAGE_NAME}:${IMAGE_TAG} &&
                            docker stop api-analytics || true &&
                            docker rm api-analytics || true &&
                            docker run -d --name api-analytics -p 5000:5000 \
                                ${DOCKER_USER}/${IMAGE_NAME}:${IMAGE_TAG}
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
