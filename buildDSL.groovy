pipeline {
    agent {
      label 'images'
    }

    options {
        skipStagesAfterUnstable()
    }

    stages {

        stage('Checkout Jenkins Job Generator') {
            steps {
                git branch: 'master',
                    url: 'https://github.com/lrusak/LibreELEC-jenkins-jobs'
            }
        }

        stage('Checkout LibreELEC') {
            steps {
                dir ('LibreELEC.tv') {
                  git branch: 'master',
                      url: 'https://github.com/LibreELEC/LibreELEC.tv'
                }
            }
        }

        stage('Run Jenkins Job Generator') {
            steps {
                sh 'rm -rf output'
                sh 'python3 jenkins-job-generator.py'
            }
        }

        stage('Build DSL') {
            steps {
              jobDsl targets: 'output/*.groovy',
                     removedJobAction: 'DELETE',
                     removedViewAction: 'DELETE',
                     failOnMissingPlugin: true
            }
        }
    }
}
