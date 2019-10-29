import logging

from troposphere import Parameter, Ref, Template, GetAZs, iam
from troposphere.ec2 import *
from troposphere import autoscaling as asg
from awacs.aws import Allow, Statement, Principal, Policy, PolicyDocument, Action
from awacs.sts import AssumeRole
import util
import base64

def create_infra_template(config) -> Template:
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

    name_param = t.add_parameter(Parameter(
        "ResourceName",
        Description="Name",
        Type="String",
    ))


    ec2_role = t.add_resource(
        iam.Role(
            "EC2InstanceRoleWithS3",
            AssumeRolePolicyDocument=Policy(
                Statement=[
                    Statement(
                        Effect=Allow,
                        Action=[AssumeRole],
                        Principal=Principal("Service", ["ec2.amazonaws.com"])
                    )
                ]
            ),
            ManagedPolicyArns=[
                'arn:aws:iam::aws:policy/AmazonS3FullAccess',
            ],
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
            ]
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
    cluster_sg_egress_rule_default = t.add_resource(
        SecurityGroupEgress(
            "DefaultSGEgressRule",
            GroupId=cluster_sg.GetAtt("GroupId"),
            IpProtocol='-1',
            FromPort='-1',
            ToPort='-1',
            CidrIp="0.0.0.0/0",
            DependsOn='ClusterSG'
        )
    )
    cluster_sg_egress_rule_internal = t.add_resource(
        SecurityGroupEgress(
            "InterClusterAccessSGEgressRule",
            GroupId=cluster_sg.GetAtt("GroupId"),
            IpProtocol='-1',
            DestinationSecurityGroupId=cluster_sg.GetAtt("GroupId"),
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
                    Tag(Key="Name", Value=Ref(name_param)),
                    Tag(Key="label", Value=Ref(name_param))
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
            GroupName=Ref(placement_group)
        ),
        IamInstanceProfile=IamInstanceProfile(
            #Arn='arn:aws:iam::926857016169:instance-profile/EC2DefaultRoleWithS3'
            Arn=instance_profile.GetAtt("Arn")
        ),
        UserData=base64.b64encode(util.assemble_userdata(
            ('cloud-config', 'text/cloud-config'),
            ('userdata.py', 'text/x-shellscript')
        ).as_bytes()).decode()
    )


    launch_template = t.add_resource(LaunchTemplate(
        config['resource_name'] + "LT",
        LaunchTemplateName=config['resource_name']+"LT",
        LaunchTemplateData=launch_template_data,
        DependsOn=[placement_group]
    ))

    t.add_resource(asg.AutoScalingGroup(
        config['resource_name'] + "ASG",
        DependsOn=[launch_template],
        AvailabilityZones=GetAZs(Ref('AWS::Region')),
        LaunchTemplate=asg.LaunchTemplateSpecification(
            LaunchTemplateId=Ref(launch_template),
            Version=launch_template.GetAtt("LatestVersionNumber")
        ),
        AutoScalingGroupName=Ref(name_param),
        DesiredCapacity=64,
        MaxSize=64,
        MinSize=0
    ))
    return t



