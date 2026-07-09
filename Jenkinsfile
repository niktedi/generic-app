pipeline {
    agent any

    stages {
        stage('Hello') {
            steps {
                echo 'Пайплайн работает'
                sh 'uname -a'
            }
        }
        stage('Build') {
            steps {
                sh 'echo собираем...'
            }
        }
        stage('Test') {
            steps {
                sh 'echo тестируем...'
            }
        }
    }
}