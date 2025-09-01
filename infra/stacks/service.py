from aws_cdk import (
    aws_ec2,
    aws_ecr,
    aws_ecs,
    aws_elasticloadbalancingv2 as elbv2,
    Duration,
    RemovalPolicy,
    Stack
)
from constructs import Construct

from config import STAGE


class ServiceStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.create_vpc()
        self.create_alb()
        self.create_ecr()
        self.create_ecs_cluster()

    def create_vpc(self):
        self.vpc = aws_ec2.Vpc(
            self, f"laravel-{STAGE}-vpc",
            max_azs=2,
            subnet_configuration=[
                aws_ec2.SubnetConfiguration(
                    name=f"laravel-{STAGE}-public-subnet-",
                    subnet_type=aws_ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                aws_ec2.SubnetConfiguration(
                    name=f"laravel-{STAGE}-private-subnet",
                    subnet_type=aws_ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24
                ),
            ]
        )

    def create_alb(self):
        security_group = aws_ec2.SecurityGroup(
            self, f"laravel-{STAGE}-alb-sg",
            vpc=self.vpc,
            description="Allow HTTP traffic",
            allow_all_outbound=True
        )
        security_group.add_ingress_rule(
            aws_ec2.Peer.any_ipv4(), aws_ec2.Port.tcp(80), "Allow HTTP traffic"
        )

        self.alb = elbv2.ApplicationLoadBalancer(
            self,
            f"laravel-{STAGE}-alb",
            vpc=self.vpc,
            internet_facing=True,
            load_balancer_name=f"laravel-{STAGE}-alb",
            security_group=security_group
        )

        self.target_group = elbv2.ApplicationTargetGroup(
            self,
            f"laravel-{STAGE}-alb-target-group",
            vpc=self.vpc,
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.IP,
            port=80
        )

        self.alb.add_listener(
            f"laravel-{STAGE}-alb-listener",
            default_target_groups=[self.target_group],
            port=80,
            open=True
        )

    def create_ecr(self):
        self.ecr_repository = aws_ecr.Repository(
            self, f"laravel-{STAGE}-ecr-repo",
            removal_policy=RemovalPolicy.DESTROY
        )
    
    def create_ecs_cluster(self):
        ecs_cluster = aws_ecs.Cluster(
            self, f"laravel-{STAGE}-ecs-cluster",
            vpc=self.vpc
        )

        # TODO: Create and define task role
        fargate_task_definition = aws_ecs.FargateTaskDefinition(
            self, f"laravel-{STAGE}-ecs-task-definition",
            memory_limit_mib=512,
            cpu=256
        )

        fargate_task_definition.add_container(
           f"laravel-{STAGE}-ecs-container",
            image=aws_ecs.ContainerImage.from_ecr_repository(self.ecr_repository, "latest"),
            logging=aws_ecs.LogDrivers.aws_logs(stream_prefix=f"laravel-{STAGE}-ecs-service"),
            port_mappings=[aws_ecs.PortMapping(container_port=80)],
            health_check=aws_ecs.HealthCheck(
                command=["CMD-SHELL", "curl -f http://localhost/healthz || exit 1"],
                interval=Duration.seconds(300),
                timeout=Duration.seconds(30),
                retries=3,
                start_period=Duration.seconds(60)
            )
        )

        fargate_service = aws_ecs.FargateService(
            self,
            f"laravel-{STAGE}-ecs-service",
            cluster=ecs_cluster,
            task_definition=fargate_task_definition,
            desired_count=2,
            min_healthy_percent=50,
        )

        fargate_service.attach_to_application_target_group(self.target_group)
