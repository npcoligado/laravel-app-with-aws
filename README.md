# Deploying Laravel on ECS Fargate with an ALB

## Managing the infrastructure
Required AWS resources are deployed via **CDK**.

Prerequisites:
- Python 3.13 (option to manage via `pyenv`)
- `uv` (install via `pip install uv`)
- AWS CDK (install via `npm install -g aws-cdk)
- AWS credentials setup

### Deploying the resources
1. Change directory to `infra`: `cd infra`.
2. If not yet done, create a virtual environment: `uv venv .venv`.
3. Activate virtual environment: `.\.venv\Scripts\activate`.
4. If not yet done, install dependencies: `uv sync`.
5. Set environment variables: `STAGE`. Set either in .env or command line.
6. Configure AWS credentials.
7. Deploy ECR: `cdk deploy laravel-$STAGE-ecr`.
8. Build image and upload to ECR. Follow steps [here](#how-to-build-and-deploy-the-image).
9. Deploy remaining stacks: `cdk deploy --all`.

### Destroying the resources
1. Activate virtual environment: `.\.venv\Scripts\activate`.
2. Set environment variables: `STAGE`. Set either in .env or command line.
3. Configure AWS credentials.
4. Destroy stacks: `cdk destroy --all`.


## How to build and deploy the image
1. Configure AWS credentials.
2. Set environment variables: `AWS_ACCOUNT_ID`, `AWS_REGION`, `STAGE`, `IMAGE_TAG`. Set either in .env or command line.
3. Run deploy script: `bash docker/deploy.sh`.


## Application DNS

Sample ALB DNS: laravel-dev-alb-874188047.ap-southeast-2.elb.amazonaws.com

```
curl laravel-dev-alb-874188047.ap-southeast-2.elb.amazonaws.com
```

### Getting DNS via AWS Console
1. Login to AWS Console.
2. Search for `EC2`.
3. In the side navigation, select Load Balancers under Load Balancing.
4. Select the load balancer with name laravel-{STAGE}-alb.

### Getting DNS via AWS CLI
```
aws elbv2 describe-load-balancers --names laravel-%STAGE%-alb --query "LoadBalancers[0].DNSName" --output text
```

### Health check
**NOTE**: The PHP application deployed in ECS cannot be accessed properly so health check via route `/healthz` is expected to fail at the moment.

### Via browser
Visit http://laravel-dev-alb-874188047.ap-southeast-2.elb.amazonaws.com/healthz

### Via command line
```
curl laravel-dev-alb-874188047.ap-southeast-2.elb.amazonaws.com/healthz
```


## Notes

### Considerations
- As I am not familiar with PHP and Laravel, I decided to look for an existing application code (https://github.com/alfikiafan/laravel-guestbook) in Github to use for this exercise and allow me to focus on setting up the infrastructure and CI/CD.
- In containerizing the application, I went with the monolith approach (i.e., PHP-FPM, Nginx, and Supervisor are in the same image) for easier configuration in networking and deployment.
- Building and uploading the image requires multiple commands. To avoid manual steps, I added the script `docker/deploy.sh`.
- In the interest of time, I used AWS CDK (Python) for IaC as I am more used to it than Terraform.
- For security, ECS Fargate service is deployed in private subnets. VPC endpoints were created to connect to and pull images from ECR, and publish logs to Cloudwatch. I chose VPC endpoint over NAT Gateway because it offers lower cost and better security (i.e., no need to use public internet).
- For consistency (i.e., single source of truth for infrastructure configuration), all AWS resources, including task definition, are managed in AWS CDK app. This means that whenever Github pipeline is run, the image used in ECS service will be updated due to force deployment, but values defined in task definition will remain the same.

### Limitations / Difficulties encountered
- Running the image locally works as expected -- Laravel application can be accessed via http://localhost:80. However, when using the **same** image in ECS Fargate, only the Nginx welcome page is displayed when accessing ALB DNS. Accessing /healthz route in the Laravel application returns HTTP 404 which causes health check to fail and the Cloudformation stack to get stuck in UPDATE_IN_PROGRESS status. To not block the deployment, health check route is temporarily set to "/" in CDK app instead. 

### Improvement points
- Create a base image where installation of dependencies will be done. This will then be used as the base of the image that will be used by ECS. Doing this will speed up the build time of the image whenever the Laravel application is updated.
- Fix the configurations (i.e., docker, cdk) to properly host the application. Once done, set health check route to "/healthz".
- For flexibility, consider removing the management of ECS task definition from CDK. Create an ECS task definition JSON file and store it in the repository. This will then be used and updated via Github actions whenever there are changes in the application code.
