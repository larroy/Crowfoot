import logging

from troposphere import Parameter, Ref, Template
from troposphere.ec2 import *
from troposphere import autoscaling as asg
from troposphere.iam import *
from awacs.aws import Allow, Statement, Principal, PolicyDocument, Action
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

#    ec2_role = t.add_resource(Role(
#        "EC2DefaultRole",
#        AssumeRolePolicyDocument=PolicyDocument(
#            Statement=[Statement(
#                Principal="*",
#                Effect=Allow,
#                Action=[Action("s3", "*")],
#                Resource=["*"]
#            )]
#        )
#    ))

#    ec2_role = t.add_resource(Role(
#        "EC2DefaultRole",
#        AssumeRolePolicyDocument=
#            {
#                "Version": "2012-10-17",
#                "Statement": [
#                    {
#                    "Effect": "Allow",
#                    "Action": "s3:*",
#                    "Resource": "arn:aws:s3:::*",
#                    "Principal": "*"
#                    }
#                ]
#            }
#    ))
#



    cluster_sg = t.add_resource(SecurityGroup(
        "ClusterSG",
        #GroupName="ClusterSG",
        GroupDescription="Allow traffic from this group",
    ))

#    cluster_access_sg = t.add_resource(SecurityGroup(
#        "ClusterSGAccess",
#        #GroupName="ClusterSGAccessEFA",
#        GroupDescription="allow traffic across EFA interfaces",
#        SecurityGroupIngress=[
#            SecurityGroupIngress(
#                "ClusterSGAccessIngress",
#                IpProtocol='-1',
#                #SourceSecurityGroupId=cluster_sg.GetAtt('name')
#                SourceSecurityGroupId=Ref(cluster_sg),
#                GroupId=Ref(cluster_sg),
#            )
#        ],
#        SecurityGroupEgress=[
#            SecurityGroupEgress(
#                "ClusterSGAccessEgress",
#                IpProtocol='-1',
#                #GroupId="ClusterSGAccess",
#                DestinationSecurityGroupId=Ref(cluster_sg),
#                GroupId=Ref(cluster_sg),
#                #GroupId=cluster_sg.GetAtt('name')
#            )
#        ]
#    ))

    security_group = t.add_resource(SecurityGroup(
        "SSHSecurityGroup",
        SecurityGroupIngress=[
            {"ToPort": "22", "IpProtocol": "tcp", "CidrIp": "0.0.0.0/0",
             "FromPort": "22"}],
        GroupDescription="Allow SSH",
    ))

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
                    VolumeSize="400",
                    VolumeType="gp2"
                )
            )
        ],

        InstanceType=Ref(instance_type_param),
        ImageId=Ref(ami_param),
        KeyName=Ref(keyname_param),
        #SecurityGroups=[
        #    Ref(security_group)
        #],
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
                    #"ClusterSGAccessEFA"
                    #Ref(cluster_sg)
                    #cluster_sg.GetAtt('GroupId')
                    "sg-01437c22a98805c3f",
                    "sg-064417bbc14a1e42a"
                ]
            )
        ],
        Placement=Placement(
            #GroupName=placement_group.name,
            GroupName=Ref(placement_group)
        ),
        IamInstanceProfile=IamInstanceProfile(
            #Arn=ec2_role.GetAtt('Arn')
            Arn='arn:aws:iam::926857016169:instance-profile/EC2DefaultRoleWithS3'
        ),
        UserData=base64.b64encode(util.assemble_userdata(
            ('userdata.py', 'text/x-shellscript'),
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
        AvailabilityZones=['us-west-2b'],
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



