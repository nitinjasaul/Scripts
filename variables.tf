variable "public_key_path" {
  description = <<DESCRIPTION
Path to the SSH public key to be used for authentication.
Ensure this keypair is added to your local SSH agent so provisioners can
connect.

Example: ~/.ssh/terraform.pub
DESCRIPTION
  default = "xyz.pub"
}

variable "key_name" {
  description = "Desired name of AWS key pair"
  default = "xyz"
}

variable "aws_region" {
  description = "AWS region to launch servers."
  default = "us-west-2"
}

# AutoScaling AMI (64)
variable "aws_scaling_ami" {
  default = "ami-1209d571"
}
# AutoScaling Security Group
variable "aws_security_group" {    
  default = ""
}

# AutoScaling ELB
variable "aws_elb_name" {
  default = ""
}

# AutoScaling Subnet Id
variable "aws_subnet_id" {
  default = ""
}

# AutoScaling Desire Instances
variable "desired-capacity" {
  default = "1"
}

