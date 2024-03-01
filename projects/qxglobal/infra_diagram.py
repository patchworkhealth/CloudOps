from diagrams import Diagram, Cluster
from diagrams.aws.compute import ECS
from diagrams.aws.network import VPC, ALB
from diagrams.aws.security import SecurityGroup

with Diagram("AWS Infrastructure", show=False):
    with Cluster("VPC: pw-services-vpc"):
        vpc = VPC("VPC")
        security_group = SecurityGroup("Security Group")
        vpc - security_group

    with Cluster("ECS Cluster"):
        ecs_cluster = ECS("Cluster")
        ecs_cluster - ecs_cluster
        ecs_cluster - ecs_cluster

    alb = ALB("Application Load Balancer")
    alb - ECS - vpc

