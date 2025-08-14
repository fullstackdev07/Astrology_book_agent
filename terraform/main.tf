# terraform/main.tf

provider "aws" {
  region = "us-east-1"
}

variable "project_name" {
  description = "astrology_book_agent"
  type        = string
  default     = "AstrologyBookFactory"
}

variable "unique_suffix" {
  description = "A unique suffix for resource names to avoid collisions."
  type        = string
  # IMPORTANT: CHANGE "your-initials-123" to something unique to you!
  default     = "astrology-initials-123" 
}

resource "aws_secretsmanager_secret" "api_keys" {
  name = "${var.project_name}-ApiKeys-${var.unique_suffix}"
  description = "API Keys for Astrology, OpenAI, etc."
}

resource "aws_s3_bucket" "books_bucket" {
  bucket = "astrology-books-${var.unique_suffix}"
}

resource "aws_dynamodb_table" "orders_table" {
  name         = "${var.project_name}-Orders"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "OrderID"

  # This is the corrected block
  attribute {
    name = "OrderID"
    type = "S"
  }
}

resource "aws_iam_role" "lambda_exec_role" {
  name = "${var.project_name}-LambdaRole-${var.unique_suffix}"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [{ Action = "sts:AssumeRole", Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }}]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_custom_permissions" {
  name = "LambdaCustomPermissions"
  role = aws_iam_role.lambda_exec_role.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      { Action = ["s3:PutObject"], Effect = "Allow", Resource = "${aws_s3_bucket.books_bucket.arn}/*" },
      { Action = ["dynamodb:PutItem", "dynamodb:UpdateItem"], Effect = "Allow", Resource = aws_dynamodb_table.orders_table.arn },
      { Action = ["secretsmanager:GetSecretValue"], Effect = "Allow", Resource = aws_secretsmanager_secret.api_keys.arn }
    ]
  })
}

resource "aws_lambda_function" "book_generator" {
  function_name = "${var.project_name}-Generator-${var.unique_suffix}"
  role          = aws_iam_role.lambda_exec_role.arn
  
  filename         = "${path.module}/../lambda_payload.zip"
  source_code_hash = filebase64sha256("${path.module}/../lambda_payload.zip")
  handler          = "handler.lambda_handler"
  runtime          = "python3.9"

  timeout = 300 # 5 minutes
  memory_size = 512 # Increase memory for PDF generation

  environment {
    variables = {
      SECRETS_ARN    = aws_secretsmanager_secret.api_keys.arn
      BUCKET_NAME    = aws_s3_bucket.books_bucket.id
      DYNAMODB_TABLE = aws_dynamodb_table.orders_table.id
    }
  }
}