# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""D2 diagram example templates organized by category.

Provides ready-to-use D2 examples that demonstrate AWS architecture patterns,
GenAI/Bedrock patterns, serverless, containers, networking, security, and
D2 animation features. Examples use ${ICON:Name} placeholders for AWS icons.
"""

from awslabs.aws_diagram_mcp_server.models import DiagramExample


_EXAMPLES: dict[str, DiagramExample] = {
    # --- AWS Architecture ---
    'aws_three_tier': DiagramExample(
        title='Three-Tier Web Application',
        description=(
            'Classic three-tier architecture with load balancer, web servers, and database. '
            'Try rendering with shadow=True for drop shadows, three_d=True for 3D shapes, '
            'or both for a polished presentation look.'
        ),
        category='aws',
        d2_source="""direction: right

users: Users {
  shape: person
}

lb: Elastic Load Balancing {
  icon: ${ICON:Elastic-Load-Balancing}
}

web: Web Tier {
  ec2_1: Amazon EC2 {
    icon: ${ICON:Amazon-EC2}
  }
  ec2_2: Amazon EC2 {
    icon: ${ICON:Amazon-EC2}
  }
}

db: Database Tier {
  rds_primary: Amazon RDS Primary {
    icon: ${ICON:Amazon-RDS}
  }
  rds_replica: Amazon RDS Read Replica {
    icon: ${ICON:Amazon-RDS}
  }
  rds_primary -> rds_replica: replication
}

users -> lb: HTTPS
lb -> web.ec2_1
lb -> web.ec2_2
web.ec2_1 -> db.rds_primary
web.ec2_2 -> db.rds_primary
""",
    ),
    'aws_microservices': DiagramExample(
        title='Serverless Microservices (with shadows)',
        description=(
            'API Gateway + Lambda + DynamoDB microservices pattern with shadow styling. '
            'Demonstrates **.style.shadow glob for applying shadows to all shapes. '
            'Try also with three_d=True or shadow=True tool parameters.'
        ),
        category='aws',
        d2_source="""# Global style: shadow on all shapes
**.style.shadow: true

direction: right

client: Client App {
  shape: person
}

apigw: Amazon API Gateway {
  icon: ${ICON:Amazon-API-Gateway}
}

services: Microservices {
  users_fn: Users Service {
    icon: ${ICON:AWS-Lambda}
  }
  orders_fn: Orders Service {
    icon: ${ICON:AWS-Lambda}
  }
  payments_fn: Payments Service {
    icon: ${ICON:AWS-Lambda}
  }
}

data: Data Stores {
  users_db: Users Table {
    icon: ${ICON:Amazon-DynamoDB}
  }
  orders_db: Orders Table {
    icon: ${ICON:Amazon-DynamoDB}
  }
}

client -> apigw: REST API
apigw -> services.users_fn: /users
apigw -> services.orders_fn: /orders
apigw -> services.payments_fn: /payments

services.users_fn -> data.users_db
services.orders_fn -> data.orders_db
services.payments_fn -> data.orders_db
""",
    ),
    'aws_event_driven': DiagramExample(
        title='Event-Driven Architecture',
        description='EventBridge + SQS + Lambda event-driven processing pattern.',
        category='aws',
        d2_source="""direction: right

sources: Event Sources {
  api: Amazon API Gateway {
    icon: ${ICON:Amazon-API-Gateway}
  }
  s3: Amazon S3 {
    icon: ${ICON:Amazon-Simple-Storage-Service}
  }
}

bus: Amazon EventBridge {
  icon: ${ICON:Amazon-EventBridge}
}

queues: Processing Queues {
  orders_q: Orders Queue {
    icon: ${ICON:Amazon-Simple-Queue-Service}
  }
  notifications_q: Notifications Queue {
    icon: ${ICON:Amazon-Simple-Queue-Service}
  }
}

processors: Processors {
  order_processor: Order Processor {
    icon: ${ICON:AWS-Lambda}
  }
  notifier: Notification Sender {
    icon: ${ICON:AWS-Lambda}
  }
}

sources.api -> bus: events
sources.s3 -> bus: events
bus -> queues.orders_q: order events
bus -> queues.notifications_q: notification events
queues.orders_q -> processors.order_processor
queues.notifications_q -> processors.notifier
""",
    ),
    'aws_data_lake': DiagramExample(
        title='Data Lake Architecture',
        description='S3-based data lake with Glue ETL and Athena analytics.',
        category='aws',
        d2_source="""direction: right

ingestion: Data Ingestion {
  kinesis: Amazon Data Firehose {
    icon: ${ICON:Amazon-Kinesis}
  }
}

storage: Data Lake (S3) {
  raw: Raw Zone {
    icon: ${ICON:Amazon-Simple-Storage-Service}
  }
  processed: Processed Zone {
    icon: ${ICON:Amazon-Simple-Storage-Service}
  }
  curated: Curated Zone {
    icon: ${ICON:Amazon-Simple-Storage-Service}
  }
}

processing: Processing {
  glue: AWS Glue {
    icon: ${ICON:AWS-Glue}
  }
  catalog: AWS Glue Data Catalog {
    icon: ${ICON:AWS-Glue}
  }
}

analytics: Analytics {
  athena: Amazon Athena {
    icon: ${ICON:Amazon-Athena}
  }
  quicksight: Amazon QuickSight {
    icon: ${ICON:Amazon-QuickSight}
  }
}

ingestion.kinesis -> storage.raw
storage.raw -> processing.glue: ETL
processing.glue -> storage.processed
processing.glue -> storage.curated
processing.glue -> processing.catalog: register schema
analytics.athena -> processing.catalog: query
analytics.athena -> storage.curated
analytics.quicksight -> analytics.athena: visualize
""",
    ),
    # --- GenAI / Bedrock ---
    'genai_rag_pipeline': DiagramExample(
        title='RAG Pipeline with Bedrock',
        description='Retrieval-Augmented Generation using Bedrock Knowledge Bases and OpenSearch.',
        category='genai',
        d2_source="""direction: right

user: User {
  shape: person
}

app: Application {
  icon: ${ICON:AWS-Lambda}
}

bedrock: Amazon Bedrock {
  kb: Knowledge Base {
    icon: ${ICON:Amazon-Bedrock}
  }
  fm: Foundation Model {
    icon: ${ICON:Amazon-Bedrock}
  }
}

vector_store: Amazon OpenSearch Serverless {
  icon: ${ICON:Amazon-OpenSearch-Service}
}

docs: Amazon S3 {
  icon: ${ICON:Amazon-Simple-Storage-Service}
}

user -> app: question
app -> bedrock.kb: retrieve context
bedrock.kb -> vector_store: semantic search
bedrock.kb -> docs: fetch documents
bedrock.kb -> bedrock.fm: augmented prompt
bedrock.fm -> app: generated answer
app -> user: response
""",
    ),
    'genai_agent': DiagramExample(
        title='Bedrock Agent Architecture',
        description='Bedrock Agent with Lambda action groups and knowledge base.',
        category='genai',
        d2_source="""direction: right

user: User {
  shape: person
}

agent: Bedrock Agent {
  icon: ${ICON:Amazon-Bedrock}
  style.stroke: "#FF9900"
}

actions: Action Groups {
  lookup: Lookup Orders {
    icon: ${ICON:AWS-Lambda}
  }
  process: Process Returns {
    icon: ${ICON:AWS-Lambda}
  }
}

kb: Knowledge Base {
  icon: ${ICON:Amazon-Bedrock}
}

data: Data Sources {
  orders_db: Orders DB {
    icon: ${ICON:Amazon-DynamoDB}
  }
  docs: Amazon S3 {
    icon: ${ICON:Amazon-Simple-Storage-Service}
  }
}

user -> agent: natural language request
agent -> actions.lookup: invoke action
agent -> actions.process: invoke action
agent -> kb: retrieve knowledge
actions.lookup -> data.orders_db
actions.process -> data.orders_db
kb -> data.docs
""",
    ),
    'genai_multi_model': DiagramExample(
        title='Multi-Model Routing',
        description='Intelligent routing across multiple foundation models based on task type.',
        category='genai',
        d2_source="""direction: right

client: Client {
  shape: person
}

router: Model Router {
  icon: ${ICON:AWS-Lambda}
}

models: Foundation Models {
  claude: Claude (Complex Reasoning) {
    icon: ${ICON:Amazon-Bedrock}
  }
  nova: Nova (Fast Tasks) {
    icon: ${ICON:Amazon-Bedrock}
  }
  titan: Titan Embeddings {
    icon: ${ICON:Amazon-Bedrock}
  }
}

cache: Amazon ElastiCache {
  icon: ${ICON:Amazon-ElastiCache}
}

client -> router: prompt + task type
router -> models.claude: complex analysis
router -> models.nova: summarization
router -> models.titan: embeddings
router -> cache: check cache
""",
    ),
    # --- Serverless ---
    'serverless_api': DiagramExample(
        title='Serverless REST API',
        description='Full serverless API with authentication, CRUD, and monitoring.',
        category='serverless',
        d2_source="""direction: right

client: Client {
  shape: person
}

auth: Amazon Cognito {
  icon: ${ICON:Amazon-Cognito}
}

api: Amazon API Gateway {
  icon: ${ICON:Amazon-API-Gateway}
}

functions: AWS Lambda Functions {
  create: Create {
    icon: ${ICON:AWS-Lambda}
  }
  read: Read {
    icon: ${ICON:AWS-Lambda}
  }
  update: Update {
    icon: ${ICON:AWS-Lambda}
  }
  delete: Delete {
    icon: ${ICON:AWS-Lambda}
  }
}

db: Amazon DynamoDB {
  icon: ${ICON:Amazon-DynamoDB}
}

monitoring: Amazon CloudWatch {
  icon: ${ICON:Amazon-CloudWatch}
}

client -> auth: authenticate
client -> api: CRUD operations
api -> functions.create: POST
api -> functions.read: GET
api -> functions.update: PUT
api -> functions.delete: DELETE
functions.create -> db
functions.read -> db
functions.update -> db
functions.delete -> db
functions.create -> monitoring: logs & metrics
""",
    ),
    'serverless_async': DiagramExample(
        title='Async Processing Pipeline',
        description='Asynchronous processing with SQS, Lambda, and Step Functions.',
        category='serverless',
        d2_source="""direction: right

api: Amazon API Gateway {
  icon: ${ICON:Amazon-API-Gateway}
}

queue: Amazon SQS {
  icon: ${ICON:Amazon-Simple-Queue-Service}
}

processor: AWS Lambda {
  icon: ${ICON:AWS-Lambda}
}

workflow: AWS Step Functions {
  icon: ${ICON:AWS-Step-Functions}
}

dlq: Dead Letter Queue {
  icon: ${ICON:Amazon-Simple-Queue-Service}
  style.stroke: "#FF0000"
}

results: Amazon S3 {
  icon: ${ICON:Amazon-Simple-Storage-Service}
}

api -> queue: enqueue job
queue -> processor: trigger
processor -> workflow: start execution
workflow -> results: save output
queue -> dlq: failed messages {
  style.stroke-dash: 3
}
""",
    ),
    # --- Containers ---
    'containers_ecs': DiagramExample(
        title='ECS Fargate Deployment',
        description='Containerized application on ECS Fargate with ALB and ECR.',
        category='containers',
        d2_source="""direction: right

users: Users {
  shape: person
}

alb: Elastic Load Balancing {
  icon: ${ICON:Elastic-Load-Balancing}
}

ecs: Amazon ECS Cluster {
  service: Fargate Service {
    icon: ${ICON:Amazon-Elastic-Container-Service}
    task1: Task 1
    task2: Task 2
    task3: Task 3
  }
}

ecr: Amazon ECR {
  icon: ${ICON:Amazon-Elastic-Container-Registry}
}

rds: Amazon Aurora {
  icon: ${ICON:Amazon-Aurora}
}

users -> alb: HTTPS
alb -> ecs.service.task1
alb -> ecs.service.task2
alb -> ecs.service.task3
ecr -> ecs.service: pull images
ecs.service.task1 -> rds
ecs.service.task2 -> rds
ecs.service.task3 -> rds
""",
    ),
    # --- Networking ---
    'networking_vpc': DiagramExample(
        title='VPC Architecture',
        description='VPC with public/private subnets, NAT, and Internet Gateway.',
        category='networking',
        d2_source="""direction: down

internet: Internet {
  shape: cloud
}

vpc: VPC (10.0.0.0/16) {
  igw: Internet Gateway

  public: Public Subnets {
    az1_pub: AZ1 Public (10.0.1.0/24) {
      nat: NAT Gateway
      bastion: Bastion Host {
        icon: ${ICON:Amazon-EC2}
      }
    }
    az2_pub: AZ2 Public (10.0.2.0/24) {
      alb: Elastic Load Balancing {
        icon: ${ICON:Elastic-Load-Balancing}
      }
    }
  }

  private: Private Subnets {
    az1_priv: AZ1 Private (10.0.3.0/24) {
      app1: App Server {
        icon: ${ICON:Amazon-EC2}
      }
    }
    az2_priv: AZ2 Private (10.0.4.0/24) {
      app2: App Server {
        icon: ${ICON:Amazon-EC2}
      }
    }
  }
}

internet -> vpc.igw
vpc.igw -> vpc.public.az1_pub
vpc.igw -> vpc.public.az2_pub
vpc.public.az1_pub.nat -> vpc.private.az1_priv: outbound
vpc.public.az2_pub.alb -> vpc.private.az1_priv.app1
vpc.public.az2_pub.alb -> vpc.private.az2_priv.app2
""",
    ),
    # --- Security ---
    'security_waf': DiagramExample(
        title='CloudFront + WAF + ALB',
        description='Secure web delivery with CloudFront, WAF, and ALB.',
        category='security',
        d2_source="""direction: right

users: Users {
  shape: person
}

cloudfront: Amazon CloudFront {
  icon: ${ICON:Amazon-CloudFront}
}

waf: AWS WAF {
  icon: ${ICON:AWS-WAF}
}

alb: Elastic Load Balancing {
  icon: ${ICON:Elastic-Load-Balancing}
}

targets: Origin Servers {
  web1: Web Server 1 {
    icon: ${ICON:Amazon-EC2}
  }
  web2: Web Server 2 {
    icon: ${ICON:Amazon-EC2}
  }
}

shield: AWS Shield {
  icon: ${ICON:AWS-Shield}
}

users -> cloudfront: HTTPS
shield -> cloudfront: DDoS protection {
  style.stroke-dash: 3
}
waf -> cloudfront: filter requests {
  style.stroke-dash: 3
}
cloudfront -> alb: origin request
alb -> targets.web1
alb -> targets.web2
""",
    ),
    # --- Data ---
    'data_streaming': DiagramExample(
        title='Real-Time Data Streaming',
        description='Kinesis-based real-time data streaming and analytics pipeline.',
        category='data',
        d2_source="""direction: right

producers: Data Producers {
  iot: IoT Devices
  apps: Applications
  logs: Log Streams
}

kinesis: Amazon Kinesis Data Streams {
  icon: ${ICON:Amazon-Kinesis}
}

consumers: Consumers {
  analytics: Amazon Kinesis Data Analytics {
    icon: ${ICON:Amazon-Kinesis}
  }
  firehose: Amazon Data Firehose {
    icon: ${ICON:Amazon-Kinesis}
  }
  lambda: AWS Lambda {
    icon: ${ICON:AWS-Lambda}
  }
}

destinations: Destinations {
  s3: Amazon S3 {
    icon: ${ICON:Amazon-Simple-Storage-Service}
  }
  opensearch: Amazon OpenSearch Service {
    icon: ${ICON:Amazon-OpenSearch-Service}
  }
  redshift: Amazon Redshift {
    icon: ${ICON:Amazon-Redshift}
  }
}

producers.iot -> kinesis
producers.apps -> kinesis
producers.logs -> kinesis
kinesis -> consumers.analytics: real-time
kinesis -> consumers.firehose: batch
kinesis -> consumers.lambda: transform
consumers.firehose -> destinations.s3
consumers.analytics -> destinations.opensearch
consumers.lambda -> destinations.redshift
""",
    ),
    # --- GenAI / AgentCore ---
    'genai_agentcore_fullstack': DiagramExample(
        title='Bedrock AgentCore Full-Stack',
        description=(
            'Full-stack agentic AI application using Amazon Bedrock AgentCore. '
            'React frontend with Cognito auth, AgentCore Runtime for agent hosting, '
            'Gateway for MCP tool access, Memory, Code Interpreter, and Observability.'
        ),
        category='genai',
        d2_source="""direction: right

user: User {
  shape: person
}

frontend: Frontend {
  cloudfront: Amazon CloudFront {
    icon: ${ICON:Amazon-CloudFront}
  }
  react: React App
}

auth: Amazon Cognito {
  icon: ${ICON:Amazon-Cognito}
}

agentcore: Bedrock AgentCore {
  style.stroke: "#FF9900"

  runtime: AgentCore Runtime {
    icon: ${ICON:Amazon-Bedrock}
  }

  gateway: AgentCore Gateway {
    icon: ${ICON:Amazon-Bedrock}
  }

  memory: AgentCore Memory {
    icon: ${ICON:Amazon-Bedrock}
  }

  code_interp: Code Interpreter {
    icon: ${ICON:Amazon-Bedrock}
  }
}

tools: Tool Functions {
  tool_a: Tool A {
    icon: ${ICON:AWS-Lambda}
  }
  tool_b: Tool B {
    icon: ${ICON:AWS-Lambda}
  }
  tool_c: Tool C {
    icon: ${ICON:AWS-Lambda}
  }
}

bedrock_fm: Amazon Bedrock FM {
  icon: ${ICON:Amazon-Bedrock}
}

observability: Observability {
  cw: Amazon CloudWatch {
    icon: ${ICON:Amazon-CloudWatch}
  }
  xray: AWS X-Ray
}

user -> frontend.cloudfront: HTTPS
frontend.cloudfront -> frontend.react
frontend.react -> auth: authenticate
auth -> agentcore.runtime: token-based auth
agentcore.runtime -> agentcore.memory: conversation history
agentcore.runtime -> agentcore.gateway: MCP protocol
agentcore.runtime -> agentcore.code_interp: execute code
agentcore.runtime -> bedrock_fm: model inference
agentcore.gateway -> tools.tool_a
agentcore.gateway -> tools.tool_b
agentcore.gateway -> tools.tool_c
agentcore.runtime -> observability.cw: metrics & logs
agentcore.runtime -> observability.xray: traces {
  style.stroke-dash: 3
}
""",
    ),
    'genai_agentcore_gateway': DiagramExample(
        title='AgentCore Gateway (MCP Server Pattern)',
        description=(
            'AgentCore Gateway converts Lambda functions and REST APIs into '
            'MCP-compatible tools with authentication, semantic discovery, and tracing.'
        ),
        category='genai',
        d2_source="""direction: right

clients: MCP Clients {
  ide: IDE Agent
  cli: CLI Agent
  app: Custom App
}

gateway: AgentCore Gateway {
  style.stroke: "#FF9900"
  mcp_layer: MCP Protocol Layer
  auth: Authentication {
    icon: ${ICON:Amazon-Cognito}
  }
  discovery: Semantic Tool Discovery
  interceptor: Request Interceptor
}

tools: Backend Tools {
  fn_search: Search API {
    icon: ${ICON:AWS-Lambda}
  }
  fn_crud: CRUD Operations {
    icon: ${ICON:AWS-Lambda}
  }
  fn_notify: Notifications {
    icon: ${ICON:AWS-Lambda}
  }
  rest_api: External REST API
}

observability: Observability {
  cw: Amazon CloudWatch {
    icon: ${ICON:Amazon-CloudWatch}
  }
}

clients.ide -> gateway.mcp_layer: MCP
clients.cli -> gateway.mcp_layer: MCP
clients.app -> gateway.mcp_layer: MCP
gateway.mcp_layer -> gateway.auth: verify token
gateway.auth -> gateway.discovery: authorized
gateway.discovery -> gateway.interceptor: route
gateway.interceptor -> tools.fn_search
gateway.interceptor -> tools.fn_crud
gateway.interceptor -> tools.fn_notify
gateway.interceptor -> tools.rest_api
gateway.interceptor -> observability.cw: trace calls {
  style.stroke-dash: 3
}
""",
    ),
    'genai_bedrock_guardrails': DiagramExample(
        title='Bedrock with Guardrails',
        description=(
            'Bedrock Agent with Guardrails for content filtering, PII redaction, '
            'topic denial, and automated reasoning. Enterprise safety pattern.'
        ),
        category='genai',
        d2_source="""direction: right

user: User {
  shape: person
}

api: Amazon API Gateway {
  icon: ${ICON:Amazon-API-Gateway}
}

guardrails_in: Input Guardrails {
  style.stroke: "#DD3333"
  content_filter: Content Filters
  pii_redact: PII Redaction
  topic_deny: Topic Denial
}

agent: Bedrock Agent {
  icon: ${ICON:Amazon-Bedrock}
  style.stroke: "#FF9900"
}

kb: Knowledge Base {
  icon: ${ICON:Amazon-Bedrock}
}

actions: Action Groups {
  fn: AWS Lambda {
    icon: ${ICON:AWS-Lambda}
  }
}

guardrails_out: Output Guardrails {
  style.stroke: "#DD3333"
  hallucination: Hallucination Check
  reasoning: Automated Reasoning
  pii_mask: PII Masking
}

user -> api: request
api -> guardrails_in: filter input
guardrails_in -> agent: safe input
agent -> kb: retrieve context
agent -> actions.fn: invoke
agent -> guardrails_out: raw response
guardrails_out -> api: safe response
api -> user: filtered answer
""",
    ),
    'genai_serverless_ai': DiagramExample(
        title='Serverless AI Architecture',
        description=(
            'Five-layer serverless AI architecture: event trigger, processing, '
            'inference, post-processing, and output. AWS Prescriptive Guidance pattern.'
        ),
        category='genai',
        d2_source="""direction: right

trigger: Event Trigger {
  apigw: Amazon API Gateway {
    icon: ${ICON:Amazon-API-Gateway}
  }
  eventbridge: Amazon EventBridge {
    icon: ${ICON:Amazon-EventBridge}
  }
  s3_event: Amazon S3 {
    icon: ${ICON:Amazon-Simple-Storage-Service}
  }
}

processing: Processing {
  lambda_pre: Preprocessing {
    icon: ${ICON:AWS-Lambda}
  }
  stepfn: AWS Step Functions {
    icon: ${ICON:AWS-Step-Functions}
  }
}

inference: Inference {
  bedrock: Amazon Bedrock {
    icon: ${ICON:Amazon-Bedrock}
  }
  sagemaker: Amazon SageMaker {
    icon: ${ICON:Amazon-SageMaker}
  }
}

postprocess: Post-Processing {
  lambda_post: Decision Logic {
    icon: ${ICON:AWS-Lambda}
  }
  sns: Notifications {
    icon: ${ICON:Amazon-Simple-Notification-Service}
  }
}

output: Output {
  dynamodb: Results DB {
    icon: ${ICON:Amazon-DynamoDB}
  }
  s3_out: Output Bucket {
    icon: ${ICON:Amazon-Simple-Storage-Service}
  }
}

trigger.apigw -> processing.lambda_pre
trigger.eventbridge -> processing.stepfn
trigger.s3_event -> processing.lambda_pre
processing.lambda_pre -> inference.bedrock
processing.stepfn -> inference.sagemaker
inference.bedrock -> postprocess.lambda_post
inference.sagemaker -> postprocess.lambda_post
postprocess.lambda_post -> postprocess.sns: notify
postprocess.lambda_post -> output.dynamodb: store
postprocess.lambda_post -> output.s3_out: archive
""",
    ),
    # --- AWS Architecture (additional) ---
    'aws_multi_region': DiagramExample(
        title='Multi-Region Active-Active',
        description=(
            'Multi-region active-active architecture with Route 53 latency-based '
            'routing, API Gateway, Lambda, and DynamoDB Global Tables.'
        ),
        category='aws',
        d2_source="""direction: down

dns: Amazon Route 53 {
  icon: ${ICON:Amazon-Route-53}
}

region_a: US-East-1 {
  apigw_a: Amazon API Gateway {
    icon: ${ICON:Amazon-API-Gateway}
  }
  lambda_a: AWS Lambda {
    icon: ${ICON:AWS-Lambda}
  }
  ddb_a: Amazon DynamoDB {
    icon: ${ICON:Amazon-DynamoDB}
  }

  apigw_a -> lambda_a
  lambda_a -> ddb_a
}

region_b: EU-West-1 {
  apigw_b: Amazon API Gateway {
    icon: ${ICON:Amazon-API-Gateway}
  }
  lambda_b: AWS Lambda {
    icon: ${ICON:AWS-Lambda}
  }
  ddb_b: Amazon DynamoDB {
    icon: ${ICON:Amazon-DynamoDB}
  }

  apigw_b -> lambda_b
  lambda_b -> ddb_b
}

dns -> region_a.apigw_a: latency routing
dns -> region_b.apigw_b: latency routing

region_a.ddb_a <-> region_b.ddb_b: Global Tables replication {
  style.stroke-dash: 3
  style.stroke: "#FF9900"
}
""",
    ),
    # --- Security (additional) ---
    'security_defense_in_depth': DiagramExample(
        title='Defense-in-Depth Serverless Security',
        description=(
            'Seven-layer security architecture: Shield, WAF, Cognito, API Gateway, '
            'VPC, Lambda with IAM roles, Secrets Manager, and GuardDuty monitoring.'
        ),
        category='security',
        d2_source="""direction: right

edge: Edge Protection {
  shield: AWS Shield {
    icon: ${ICON:AWS-Shield}
  }
  waf: AWS WAF {
    icon: ${ICON:AWS-WAF}
  }
  cloudfront: Amazon CloudFront {
    icon: ${ICON:Amazon-CloudFront}
  }
}

auth: Authentication {
  cognito: Amazon Cognito {
    icon: ${ICON:Amazon-Cognito}
  }
}

api: API Security {
  apigw: Amazon API Gateway {
    icon: ${ICON:Amazon-API-Gateway}
  }
}

compute: Compute {
  lambda: AWS Lambda {
    icon: ${ICON:AWS-Lambda}
  }
  secrets: AWS Secrets Manager {
    icon: ${ICON:AWS-Secrets-Manager}
  }
}

data: Data Layer {
  ddb: Amazon DynamoDB {
    icon: ${ICON:Amazon-DynamoDB}
  }
}

monitoring: Monitoring {
  guardduty: Amazon GuardDuty {
    icon: ${ICON:Amazon-GuardDuty}
  }
  cloudtrail: AWS CloudTrail {
    icon: ${ICON:AWS-CloudTrail}
  }
  cloudwatch: Amazon CloudWatch {
    icon: ${ICON:Amazon-CloudWatch}
  }
}

edge.shield -> edge.waf -> edge.cloudfront
edge.cloudfront -> auth.cognito: verify identity
auth.cognito -> api.apigw: authorized request
api.apigw -> compute.lambda: invoke
compute.lambda -> compute.secrets: fetch credentials
compute.lambda -> data.ddb: read/write

monitoring.guardduty -> edge: threat detection {
  style.stroke-dash: 3
}
monitoring.cloudtrail -> api: audit {
  style.stroke-dash: 3
}
monitoring.cloudwatch -> compute: alerts {
  style.stroke-dash: 3
}
""",
    ),
    # --- Animation ---
    'animation_data_flow': DiagramExample(
        title='Animated Data Flow',
        description=(
            'Animated connection lines showing data flow through a serverless web '
            'application. Uses style.animated: true on connections for moving dashes. '
            'All nodes stay in fixed positions — only connections animate. '
            'Green connections show the return path.'
        ),
        category='animation',
        uses_animation=True,
        d2_source="""direction: right

client: Client {
  shape: person
}

cdn: Amazon CloudFront {
  icon: ${ICON:Amazon-CloudFront}
}

api: Amazon API Gateway {
  icon: ${ICON:Amazon-API-Gateway}
}

lambda: AWS Lambda {
  icon: ${ICON:AWS-Lambda}
}

db: Amazon DynamoDB {
  icon: ${ICON:Amazon-DynamoDB}
}

client -> cdn: HTTPS {
  style.animated: true
}
cdn -> api: forward {
  style.animated: true
}
api -> lambda: invoke {
  style.animated: true
}
lambda -> db: query {
  style.animated: true
}
db -> lambda: results {
  style.animated: true
  style.stroke: "#00AA00"
}
lambda -> api: response {
  style.animated: true
  style.stroke: "#00AA00"
}
api -> cdn: response {
  style.animated: true
  style.stroke: "#00AA00"
}
cdn -> client: response {
  style.animated: true
  style.stroke: "#00AA00"
}
""",
    ),
    'animation_scenario_multi_agent': DiagramExample(
        title='Multi-Agent SRE Assistant (Scenarios)',
        description=(
            'AgentCore multi-agent SRE architecture with two alternate incident response '
            'scenarios. Uses D2 scenarios: to show different paths through the same '
            'architecture. Scenario 1: K8s infrastructure investigation. Scenario 2: '
            'application log analysis. Inactive agents are dimmed per scenario. '
            'Based on the AWS multi-agent SRE assistant pattern. '
            'Requires SVG output with animate-interval for scenario transitions.'
        ),
        category='animation',
        uses_animation=True,
        d2_source="""direction: right

user: SRE Engineer {
  shape: person
}

supervisor: Supervisor Agent {
  icon: ${ICON:Amazon-Bedrock}
  style.stroke: "#FF9900"
}

agents: Collaborator Agents {
  k8s: K8s Infrastructure {
    icon: ${ICON:Amazon-Elastic-Kubernetes-Service}
  }
  logs: App Logs Analyzer {
    icon: ${ICON:Amazon-CloudWatch}
  }
  metrics: Perf Metrics {
    icon: ${ICON:Amazon-Bedrock}
  }
  runbooks: Runbook Executor {
    icon: ${ICON:AWS-Lambda}
  }
}

memory: AgentCore Memory {
  icon: ${ICON:Amazon-Bedrock}
}

user -> supervisor: incident alert
supervisor -> agents.k8s
supervisor -> agents.logs
supervisor -> agents.metrics
supervisor -> agents.runbooks
supervisor -> memory: recall history

scenarios: {
  infra_investigation: {
    user -> supervisor: pod crash loop {
      style.animated: true
    }
    supervisor -> agents.k8s: investigate pods {
      style.animated: true
      style.stroke: "#FF9900"
    }
    supervisor -> agents.metrics: check CPU/memory {
      style.animated: true
      style.stroke: "#FF9900"
    }
    agents.logs.style.opacity: 0.3
    agents.runbooks.style.opacity: 0.3
  }
  log_analysis: {
    user -> supervisor: 500 error spike {
      style.animated: true
    }
    supervisor -> agents.logs: analyze errors {
      style.animated: true
      style.stroke: "#FF9900"
    }
    supervisor -> agents.runbooks: execute remediation {
      style.animated: true
      style.stroke: "#FF9900"
    }
    agents.k8s.style.opacity: 0.3
    agents.metrics.style.opacity: 0.3
  }
}
""",
    ),
    'animation_rag_flow': DiagramExample(
        title='Animated RAG Pipeline',
        description=(
            'Bedrock RAG pipeline with animated connections showing the data flow: '
            'question → retrieve → semantic search → augment → generate → respond. '
            'Green animated connections show the return path with retrieved data. '
            'Uses style.animated: true for moving dashes on all connections.'
        ),
        category='animation',
        uses_animation=True,
        d2_source="""direction: right

user: User {
  shape: person
}

app: Application {
  icon: ${ICON:AWS-Lambda}
}

bedrock: Amazon Bedrock {
  kb: Knowledge Base {
    icon: ${ICON:Amazon-Bedrock}
  }
  fm: Foundation Model {
    icon: ${ICON:Amazon-Bedrock}
  }
}

opensearch: Amazon OpenSearch Service {
  icon: ${ICON:Amazon-OpenSearch-Service}
}

s3: Document Store {
  icon: ${ICON:Amazon-Simple-Storage-Service}
}

user -> app: question {
  style.animated: true
}
app -> bedrock.kb: retrieve {
  style.animated: true
}
bedrock.kb -> opensearch: semantic search {
  style.animated: true
}
opensearch -> bedrock.kb: relevant chunks {
  style.animated: true
  style.stroke: "#00AA00"
}
bedrock.kb -> s3: fetch source docs {
  style.animated: true
}
bedrock.kb -> bedrock.fm: augmented prompt {
  style.animated: true
}
bedrock.fm -> app: generated answer {
  style.animated: true
  style.stroke: "#00AA00"
}
app -> user: response {
  style.animated: true
  style.stroke: "#00AA00"
}
""",
    ),
}

# Category registry for filtering
CATEGORIES = sorted({ex.category for ex in _EXAMPLES.values()})


def get_examples(category: str | None = None) -> dict[str, DiagramExample]:
    """Get D2 diagram examples, optionally filtered by category.

    Args:
        category: Category name to filter by (case-insensitive),
                  or 'all'/None for all examples.

    Returns:
        Dictionary mapping example name to DiagramExample.
    """
    if category is None or category.lower() == 'all':
        return dict(_EXAMPLES)

    cat_lower = category.lower()
    return {
        name: example
        for name, example in _EXAMPLES.items()
        if example.category.lower() == cat_lower
    }


def get_available_categories() -> list[str]:
    """Get list of available example categories.

    Returns:
        Sorted list of unique category names.
    """
    return list(CATEGORIES)
