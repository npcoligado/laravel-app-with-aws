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


class NetworkStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.create_vpc()
        self.create_vpc_endpoints()
        self.create_security_groups()

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

    def create_vpc_endpoints(self):
        aws_ec2.InterfaceVpcEndpoint(
            self,
            f"laravel-{STAGE}-ecr-api-endpoint",
            vpc=self.vpc,
            service=aws_ec2.InterfaceVpcEndpointAwsService.ECR,
            subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_ISOLATED),
            private_dns_enabled=True
        )

        aws_ec2.InterfaceVpcEndpoint(
            self,
            f"laravel-{STAGE}-ecr-docker-endpoint",
            vpc=self.vpc,
            service=aws_ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
            subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_ISOLATED),
            private_dns_enabled=True
        )

        aws_ec2.GatewayVpcEndpoint(
            self,
            f"laravel-{STAGE}-s3-endpoint",
            vpc=self.vpc,
            service=aws_ec2.GatewayVpcEndpointAwsService.S3,
            subnets=[aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_ISOLATED)]
        )

        aws_ec2.InterfaceVpcEndpoint(
            self,
            f"laravel-{STAGE}-cloudwatch-logs-endpoint",
            vpc=self.vpc,
            service=aws_ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
            subnets=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PRIVATE_ISOLATED),
            private_dns_enabled=True
        )

    def create_security_groups(self):
        self.alb_security_group = aws_ec2.SecurityGroup(
            self,
            f"laravel-{STAGE}-alb-sg",
            security_group_name=f"laravel-{STAGE}-alb-sg",
            vpc=self.vpc,
            description="Allow HTTP traffic",
            allow_all_outbound=True
        )
        self.alb_security_group.add_ingress_rule(
            aws_ec2.Peer.any_ipv4(), aws_ec2.Port.tcp(80), "Allow HTTP traffic"
        )

        self.fargate_security_group = aws_ec2.SecurityGroup(
            self,
            f"laravel-{STAGE}-fargate-sg",
            security_group_name=f"laravel-{STAGE}-fargate-sg",
            vpc=self.vpc,
            description="Allow ALB traffic",
            allow_all_outbound=True
        )
        self.fargate_security_group.add_ingress_rule(
            self.alb_security_group, aws_ec2.Port.tcp(80), "Allow ALB traffic"
        )
