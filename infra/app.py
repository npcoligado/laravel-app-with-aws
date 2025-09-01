from aws_cdk import App, Tags

from config import STAGE
from stacks.service import ServiceStack


app = App()

service = ServiceStack(app, f"laravel-{STAGE}-service")

Tags.of(app).add("PROJECT", "laravel")
Tags.of(app).add("STAGE", STAGE)

app.synth()
