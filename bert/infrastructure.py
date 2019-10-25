import logging

from troposphere import Parameter, Ref, Template, GetAZs, iam
from troposphere.ec2 import *
from troposphere import autoscaling as asg
from awacs.aws import Allow, Statement, Principal, Policy, PolicyDocument, Action
from awacs.sts import AssumeRole
import util
import base64

def create_infra_template() -> Template:
    t = Template()
    keyname_param = t.add_parameter(Parameter(
        "KeyName",
        Description="EC2 SSH keypair to use",
        Type="String",
    ))

    instance_type_param = t.add_parameter(Parameter(
        "InstanceType",
        Description="Instance type",
        Type="String",
        Default="p3dn.24xlarge",
    ))

    ami_param = t.add_parameter(Parameter(
        "AMI",
        Description="AMI image",
        Type="String",
    ))

    ec2_role = t.add_resource(
        iam.Role(
            "EC2DefaultRoleWithS3",
            AssumeRolePolicyDocument=Policy(
                Statement=[
                    Statement(
                        Effect=Allow,
                        Action=[AssumeRole],
                        Principal=Principal("Service", ["ec2.amazonaws.com"])
                    )
                ]
            ),
            Policies=[
                iam.Policy(
                    PolicyName='S3AccessPolicy',
                    PolicyDocument=Policy(
                        Statement=[
                            Statement(
                                Sid='S3Access',
                                Effect=Allow,
                                Action=[Action("s3", "*")],
                                Resource=["arn:aws:s3:::*"]
                            )
                        ]
                    )
                )
            ]
        )
    )

    instance_profile = t.add_resource(
        iam.InstanceProfile(
            "EC2InstanceProfile",
            Roles=[Ref(ec2_role)]
        )
    )

    cluster_sg = t.add_resource(
        SecurityGroup(
            "ClusterSG",
            GroupDescription="Allow SSH inbound and all traffic between cluster nodes.",
            SecurityGroupIngress=[
                {"FromPort": 22, "ToPort": 22, "IpProtocol": "tcp", "CidrIp": "0.0.0.0/0"}
            ],
        )
    )
    cluster_sg_ingress_rule_internal = t.add_resource(
        SecurityGroupIngress(
            "InterClusterAccessSGIngressRule",
            GroupName=Ref(cluster_sg),
            IpProtocol='-1',
            SourceSecurityGroupName=Ref(cluster_sg),
            FromPort='-1',
            ToPort='-1',
            DependsOn='ClusterSG'
        )
    )

    placement_group = t.add_resource(PlacementGroup(
        "ClusteredPlacementGroup",
        Strategy="cluster"
    ))

    launch_template_data = LaunchTemplateData(
        "EC2LaunchTemplateData",
        BlockDeviceMappings=[
            BlockDeviceMapping(
                DeviceName="/dev/sda1",
                Ebs=EBSBlockDevice(
                    VolumeSize="800",
                    VolumeType="gp2"
                )
            )
        ],

        InstanceType=Ref(instance_type_param),
        ImageId=Ref(ami_param),
        KeyName=Ref(keyname_param),
        TagSpecifications=[
            TagSpecifications(
                ResourceType='instance',
                Tags=[
                    Tag(Key="Name", Value='bert-A'),
                    Tag(Key="label", Value='benchmark')
                ],
            )
        ],
        NetworkInterfaces=[
            NetworkInterfaces(
                AssociatePublicIpAddress=True,
                DeleteOnTermination=True,
                Description="efa0",
                InterfaceType="efa",
                DeviceIndex=0,
                Groups=[
                    cluster_sg.GetAtt('GroupId')
                ]
            )
        ],
        Placement=Placement(
            #GroupName=placement_group.name,
            GroupName=Ref(placement_group)
        ),
        IamInstanceProfile=IamInstanceProfile(
            Arn=instance_profile.GetAtt("Arn")
        ),
        UserData=base64.b64encode(util.assemble_userdata(
#            ('userdata.py', 'text/x-shellscript'),
            ('cloud-config', 'text/cloud-config')
        ).as_bytes()).decode()
    )


    launch_template = t.add_resource(LaunchTemplate(
        "LunchTemplate",
        LaunchTemplateName="LunchTemplate",
        LaunchTemplateData=launch_template_data,
        DependsOn=placement_group.name
    ))

    t.add_resource(asg.AutoScalingGroup(
        "ASG",
        DependsOn=[launch_template.name],
        AvailabilityZones=GetAZs(Ref('AWS::Region')),
        LaunchTemplate=asg.LaunchTemplateSpecification(
            #LaunchTemplateName='LunchTemplate',
            LaunchTemplateName=launch_template.name,
            Version="1"
        ),
        AutoScalingGroupName="Bert",
        DesiredCapacity=1,
        MaxSize=8,
        MinSize=0
    ))
    return t


def create_asg_template() -> Template:
    t = Template()
    t.add_resource(asg.AutoScalingGroup(
        "ASG",
        AvailabilityZones=['us-west-2a'],
        LaunchTemplate=asg.LaunchTemplateSpecification(
            LaunchTemplateName='LunchTemplate',
            Version="1"
        ),
        AutoScalingGroupName="Bert",
        DesiredCapacity=1,
        MaxSize=1,
        MinSize=1
    ))
    return t



