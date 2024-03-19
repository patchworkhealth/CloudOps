"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws

# S3 Bucket Names
qxglobal_bucket_name = "qxglobal-dashboard"
pulumi_state_s3 = "pw-iac-pulumi-state"

# Create an AWS resource (S3 PW-IAC Bucket)
bucket = aws.s3.Bucket(pulumi_state_s3, acl="private", bucket=pulumi_state_s3)

# Create an AWS resource QXB Bucket (S3 QXB Dashboard)
bucket = aws.s3.Bucket(qxglobal_bucket_name, acl="private", bucket=qxglobal_bucket_name)

# Use AWS S3 as the Pulumi backend
backend = aws.s3.BucketObject('pulumi-state-backend',
    bucket=bucket.id,
    key='pulumi-state'
)

# Export the name of the bucket
pulumi.export('bucket_name', bucket.id)

# Create ECR Repository
repository = aws.ecr.Repository("qxglobal_dashboard", name="qxglobal_dashboard", image_scanning_configuration={
    "scanOnPush": True,
})

# Create a new VPC
vpc = aws.ec2.Vpc("pw-dashboard-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
)

# Define ECS Cluster
cluster = aws.ecs.Cluster("qxglobal_dashboard",
    name="qxglobal_dashboard"
)

# Create a new security group for the VPC
security_group = aws.ec2.SecurityGroup("pw-dashboard-security-group",
    vpc_id=vpc.id,
    description="Security group for pw-dashboard-vpc",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": ["0.0.0.0/0"],
        },
        {
            "protocol": "tcp",
            "from_port": 443,
            "to_port": 443,
            "cidr_blocks": ["0.0.0.0/0"],
        },
    ],
    egress=[{
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"],
    }],
)

#subnets = aws.ec2.get_subnets(vpc.id)
subnets = aws.ec2.get_subnets(vpc.id[0])
pulumi.export("subnets", subnets.ids)

# Define Task Execution Role
task_execution_role = aws.iam.Role("qxglobal_dashboard_task_execution_role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Principal": {
                "Service": "ecs-tasks.amazonaws.com"
            },
            "Effect": "Allow",
            "Sid": ""
        }]
    }"""
)

# Attach Task Execution Policy
task_execution_policy_attachment = aws.iam.RolePolicyAttachment("qxglobal_dashboard_task_execution_policy_attachment",
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
    role=task_execution_role.name
)

# Define Task Definition
task_definition = aws.ecs.TaskDefinition("qxglobal_dashboard_task",
    family="qxglobal_dashboard",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    execution_role_arn=task_execution_role.arn,
    container_definitions=pulumi.Output.all(repository.repository_url).apply(lambda args: f"""[
        {{
            "name": "qxglobal_dashboard",
            "image": "{args[0]}",
            "portMappings": [
                {{
                    "containerPort": 80,
                    "hostPort": 80,
                    "protocol": "tcp"
                }}
            ]
        }}
    ]"""),
)

# Run Task in ECS Cluster
service = aws.ecs.Service("qxglobal_dashboard_service",
    cluster=cluster.arn,
    task_definition=task_definition.arn,
    desired_count=1,  # Number of tasks to run
)

# Output ECR Login Command
#pulumi.export("ecr_login_command", pulumi.Output.all(repository.registry_id, repository.repository_name).apply(lambda args: f"aws ecr get-login-password | docker login --username AWS --password-stdin {args[0]}.dkr.ecr.{pulumi.get_stack()}.amazonaws.com/{args[1]}"))
pulumi.export("ecr_login_command", pulumi.Output.all(repository.id))

# Export Load Balancer DNS Name
# pulumi.export("load_balancer_dns_name", load_balancer.dns_name)

# Output ECS Cluster Name
pulumi.export("ecs_cluster_name", cluster.name)
