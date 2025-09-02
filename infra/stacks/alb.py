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


class AlbStack(Stack):

    def __init__(self, scope: Construct, id: str, vpc: aws_ec2.Vpc, alb_security_group: aws_ec2.SecurityGroup, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.alb = elbv2.ApplicationLoadBalancer(
            self,
            f"laravel-{STAGE}-alb",
            vpc=vpc,
            internet_facing=True,
            load_balancer_name=f"laravel-{STAGE}-alb",
            security_group=alb_security_group
        )

        self.target_group = elbv2.ApplicationTargetGroup(
            self,
            f"laravel-{STAGE}-alb-target-group",
            target_group_name=f"laravel-{STAGE}-alb-target-group",
            vpc=vpc,
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.IP,
            port=80
        )

        # Temporarily disable health check for /healthz while debugging connections
        self.target_group.configure_health_check(
            # path="/healthz",
            path="/",
            port="80",
            interval=Duration.seconds(30),
            timeout=Duration.seconds(10),
            healthy_threshold_count=2,
            unhealthy_threshold_count=2
        )

        self.alb.add_listener(
            f"laravel-{STAGE}-alb-listener",
            default_target_groups=[self.target_group],
            port=80,
            open=True
        )
