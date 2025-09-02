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


class EcrStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.ecr_repository = aws_ecr.Repository(
            self,
            f"laravel-{STAGE}-ecr-repo",
            repository_name=f"laravel-{STAGE}-repo",
            removal_policy=RemovalPolicy.DESTROY if STAGE == "dev" else RemovalPolicy.RETAIN,
            empty_on_delete=True
        )
