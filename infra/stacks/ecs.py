from aws_cdk import (
    aws_ec2,
    aws_ecr,
    aws_ecs,
    aws_iam,
    aws_elasticloadbalancingv2 as elbv2,
    Duration,
    RemovalPolicy,
    Stack
)
from constructs import Construct

from config import STAGE


class EcsStack(Stack):

    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc: aws_ec2.Vpc,
        fargate_security_group: aws_ec2.SecurityGroup,
        ecr_repository: aws_ecr.Repository,
        target_group: elbv2.ApplicationTargetGroup,
        **kwargs
    ):
        super().__init__(scope, id, **kwargs)

        self.vpc = vpc
        self.fargate_security_group = fargate_security_group
        self.ecr_repository = ecr_repository
        self.target_group = target_group

        self.create_roles()
        self.create_ecs_cluster()

    def create_roles(self):
        self.execution_role = aws_iam.Role(
            self,
            f"laravel-{STAGE}-ecs-execution-role",
            assumed_by=aws_iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )
        self.execution_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=[
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=["*"]
            )
        )

        self.task_role = aws_iam.Role(
            self,
            f"laravel-{STAGE}-ecs-task-role",
            assumed_by=aws_iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )

    def create_ecs_cluster(self):
        ecs_cluster = aws_ecs.Cluster(
            self,
            f"laravel-{STAGE}-ecs-cluster",
            cluster_name=f"laravel-{STAGE}-ecs-cluster",
            vpc=self.vpc
        )

        fargate_task_definition = aws_ecs.FargateTaskDefinition(
            self, f"laravel-{STAGE}-ecs-task-definition",
            execution_role=self.execution_role,
            task_role=self.task_role,
            memory_limit_mib=512,
            cpu=256
        )

        fargate_task_definition.add_container(
           f"laravel-{STAGE}-ecs-container",
            image=aws_ecs.ContainerImage.from_ecr_repository(self.ecr_repository, "latest"),
            logging=aws_ecs.LogDrivers.aws_logs(stream_prefix=f"laravel-{STAGE}-ecs-service"),
            port_mappings=[aws_ecs.PortMapping(container_port=80)],
        )

        fargate_service = aws_ecs.FargateService(
            self,
            f"laravel-{STAGE}-ecs-service",
            service_name=f"laravel-{STAGE}-ecs-service",
            cluster=ecs_cluster,
            task_definition=fargate_task_definition,
            desired_count=2,
            min_healthy_percent=50,
            max_healthy_percent=200,
            vpc_subnets=aws_ec2.SubnetSelection(
                subnet_type=aws_ec2.SubnetType.PRIVATE_ISOLATED
            ),
            security_groups=[self.fargate_security_group]
        )

        fargate_service.attach_to_application_target_group(self.target_group)

        scaling = fargate_service.auto_scale_task_count(
            min_capacity=2,
            max_capacity=4
        )

        scaling.scale_on_cpu_utilization(
            f"laravel-{STAGE}-ecs-cpu-scaling",
            target_utilization_percent=50
        )
