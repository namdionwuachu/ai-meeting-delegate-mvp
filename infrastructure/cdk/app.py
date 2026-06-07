#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.ai_delegate_stack import AIDelegateStack

app = cdk.App()
AIDelegateStack(app, "AIDelegateMvpStack")
app.synth()
