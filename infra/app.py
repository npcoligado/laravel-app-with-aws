from aws_cdk import App, Tags

from config import STAGE
from stacks.alb import AlbStack
from stacks.ecr import EcrStack
from stacks.ecs import EcsStack
from stacks.network import NetworkStack


app = App()

ecr = EcrStack(app, f"laravel-{STAGE}-ecr")

network = NetworkStack(app, f"laravel-{STAGE}-network")

alb = AlbStack(
    app,
    f"laravel-{STAGE}-alb",
    vpc=network.vpc,
    alb_security_group=network.alb_security_group
)
alb.add_dependency(network)

ecs = EcsStack(
    app,
    f"laravel-{STAGE}-ecs",
    vpc=network.vpc,
    fargate_security_group=network.fargate_security_group,
    ecr_repository=ecr.ecr_repository,
    target_group=alb.target_group
)
ecs.add_dependency(network)
ecs.add_dependency(ecr)
ecs.add_dependency(alb)

Tags.of(app).add("PROJECT", "laravel")
Tags.of(app).add("STAGE", STAGE)

app.synth()
