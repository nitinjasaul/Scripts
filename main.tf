provider "aws" {
  region = "${var.aws_region}"
}

resource "aws_launch_configuration" "prod_app_lcf_conf" {
    name_prefix = "prod_app_lcf_conf"
    image_id = "${var.aws_scaling_ami}"
    instance_type = "t2.small"
    security_groups = ["${var.aws_security_group}"]
    key_name = "${var.key_name}"
    lifecycle {
      create_before_destroy = true
    }
}

resource "aws_autoscaling_group" "prod_app_asg" {
  load_balancers = ["${var.aws_elb_name}"]
  vpc_zone_identifier = ["${var.aws_subnet_id}"]
  name = "prod_app_asg"
  max_size = 2
  min_size = 1
  health_check_grace_period = 300
  health_check_type = "ELB"
  desired_capacity = "${var.desired-capacity}"
  force_delete = true
  launch_configuration = "${aws_launch_configuration.prod_app_lcf_conf.name}"
  termination_policies = ["OldestInstance"]
  tag {
        key = "Name"
        value = "4dxfitness-backend-app"
        key = "Environment"
        value = "prod"
        key = "Project"
        value = "4dxfitness"
        propagate_at_launch = true
  }

  lifecycle {
      create_before_destroy = true
    }

}

resource "aws_autoscaling_policy" "prod_app_scaleup" {
    name = "prod_app-scaleup"
    scaling_adjustment = 2
    adjustment_type = "ChangeInCapacity"
    cooldown = 300
    autoscaling_group_name = "${aws_autoscaling_group.prod_app_asg.name}"
}

resource "aws_cloudwatch_metric_alarm" "prod_app_scaleupcpualarm" {
    alarm_name = "prod_app-scaleupcpualarm"
    comparison_operator = "GreaterThanOrEqualToThreshold"
    evaluation_periods = "2"
    metric_name = "CPUUtilization"
    namespace = "AWS/EC2"
    period = "120"
    statistic = "Average"
    threshold = "60"
    dimensions {
        AutoScalingGroupName = "${aws_autoscaling_group.prod_app_asg.name}"
    }
    alarm_description = "This metric monitor app-ec2 cpu utilization"
    alarm_actions = ["${aws_autoscaling_policy.prod_app_scaleup.arn}"]
}

resource "aws_autoscaling_policy" "prod_app_scaledown" {
    name = "prod_app-scaledown"
    scaling_adjustment = -2
    adjustment_type = "ChangeInCapacity"
    cooldown = 300
    autoscaling_group_name = "${aws_autoscaling_group.prod_app_asg.name}"
}

resource "aws_cloudwatch_metric_alarm" "prod_app_scaledowncpualarm" {
    alarm_name = "prod-app-scaledowncpualarm"
    comparison_operator = "LessThanOrEqualToThreshold"
    evaluation_periods = "2"
    metric_name = "CPUUtilization"
    namespace = "AWS/EC2"
    period = "120"
    statistic = "Average"
    threshold = "60"
    dimensions {
        AutoScalingGroupName = "${aws_autoscaling_group.prod_app_asg.name}"
    }
    alarm_description = "This metric monitor app-ec2 cpu utilization"
    alarm_actions = ["${aws_autoscaling_policy.prod_app_scaledown.arn}"]
}
