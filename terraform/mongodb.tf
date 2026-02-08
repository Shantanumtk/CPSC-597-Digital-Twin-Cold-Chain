# =============================================================================
# Cold Chain Digital Twin - MongoDB EC2 Instance (Phase 3)
# =============================================================================

# -----------------------------------------------------------------------------
# Security Group for MongoDB
# -----------------------------------------------------------------------------

resource "aws_security_group" "mongodb" {
  name        = "${var.project_name}-mongodb-sg"
  description = "Security group for MongoDB"
  vpc_id      = aws_vpc.main.id

  # MongoDB from EKS nodes
  ingress {
    description     = "MongoDB from EKS"
    from_port       = 27017
    to_port         = 27017
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  # MongoDB from MQTT broker (for testing)
  ingress {
    description     = "MongoDB from MQTT broker"
    from_port       = 27017
    to_port         = 27017
    protocol        = "tcp"
    security_groups = [aws_security_group.mqtt_broker.id]
  }

  # SSH from MQTT broker (bastion)
  ingress {
    description     = "SSH from MQTT broker"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.mqtt_broker.id]
  }

  # All outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-mongodb-sg"
  }
}

# -----------------------------------------------------------------------------
# IAM Role for MongoDB EC2
# -----------------------------------------------------------------------------

resource "aws_iam_role" "mongodb" {
  name = "${var.project_name}-mongodb-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-mongodb-role"
  }
}

resource "aws_iam_role_policy_attachment" "mongodb_ssm" {
  role       = aws_iam_role.mongodb.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "mongodb" {
  name = "${var.project_name}-mongodb-profile"
  role = aws_iam_role.mongodb.name
}

# -----------------------------------------------------------------------------
# MongoDB EC2 Instance (Private Subnet)
# -----------------------------------------------------------------------------

resource "aws_instance" "mongodb" {
  ami                    = data.aws_ami.ubuntu_24.id
  instance_type          = var.mongodb_instance_type
  key_name               = var.key_pair_name
  subnet_id              = aws_subnet.private[0].id
  vpc_security_group_ids = [aws_security_group.mongodb.id]
  iam_instance_profile   = aws_iam_instance_profile.mongodb.name

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 50
    encrypted             = true
    delete_on_termination = true
  }

  user_data = base64encode(templatefile("${path.module}/scripts/mongodb-init.sh", {
    mongo_db_name = var.mongodb_database_name
  }))

  tags = {
    Name = "${var.project_name}-mongodb"
  }

  depends_on = [aws_nat_gateway.main]
}