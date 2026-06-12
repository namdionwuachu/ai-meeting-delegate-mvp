from pathlib import Path

from aws_cdk import (
    BundlingOptions,
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_apigateway as apigw,
    aws_cloudwatch as cloudwatch,
    aws_dynamodb as ddb,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_s3 as s3,
    aws_sns as sns,
    aws_bedrock as bedrock,
)
from constructs import Construct



class AIDelegateStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        service_code_path = str(Path(__file__).resolve().parents[3] / "services")

        persona_table = ddb.Table(
            self,
            "PersonaTable",
            table_name=f"{construct_id}-persona",
            partition_key=ddb.Attribute(name="persona_id", type=ddb.AttributeType.STRING),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        examples_table = ddb.Table(
            self,
            "StyleExamplesTable",
            table_name=f"{construct_id}-style-examples",
            partition_key=ddb.Attribute(name="persona_id", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="example_id", type=ddb.AttributeType.STRING),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        examples_table.add_global_secondary_index(
            index_name="IntentIndex",
            partition_key=ddb.Attribute(name="intent", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="persona_id", type=ddb.AttributeType.STRING),
            projection_type=ddb.ProjectionType.ALL,
        )

        voice_table = ddb.Table(
            self,
            "VoiceProfilesTable",
            table_name=f"{construct_id}-voice-profiles",
            partition_key=ddb.Attribute(name="voice_profile_id", type=ddb.AttributeType.STRING),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        sessions_table = ddb.Table(
            self,
            "MeetingSessionsTable",
            table_name=f"{construct_id}-meeting-sessions",
            partition_key=ddb.Attribute(name="meeting_id", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="event_ts", type=ddb.AttributeType.STRING),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="ttl",
            removal_policy=RemovalPolicy.DESTROY,
        )

        docs_bucket = s3.Bucket(
            self,
            "DocsBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
            enforce_ssl=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        audit_bucket = s3.Bucket(
            self,
            "AuditBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
            enforce_ssl=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        audio_bucket = s3.Bucket(
            self,
            "AudioBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
            enforce_ssl=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.GET],
                    allowed_origins=["*"],
                    allowed_headers=["*"],
                    max_age=3000,
                )
            ],
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="ExpireGeneratedAudioAfter30Days",
                    prefix="audio/",
                    expiration=Duration.days(30),
                )
            ], 
        )
            
        avatar_static_bucket = s3.Bucket(
            self,
            "AvatarStaticBucket",
            bucket_name=f"{construct_id.lower()}-avatar-static",
            website_index_document="avatar.html",
            public_read_access=True,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            ),
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        
        )

        ssm_parameter_prefix = f"/{construct_id}"
        elevenlabs_api_key_param = f"{ssm_parameter_prefix}/elevenlabs/api-key"
        elevenlabs_voice_id_param = f"{ssm_parameter_prefix}/elevenlabs/voice-id"
        recall_api_key_param = f"{ssm_parameter_prefix}/recall/api-key"
        recall_api_base_url_param = f"{ssm_parameter_prefix}/recall/api-base-url"
        heygen_api_key_param = f"{ssm_parameter_prefix}/heygen/api-key"
        heygen_avatar_id_param = f"{ssm_parameter_prefix}/heygen/avatar-id"
        did_api_key_param = f"{ssm_parameter_prefix}/did/api-key"

        guardrail = bedrock.CfnGuardrail(
            self,
            "AIDelegateGuardrail",
            name=f"{construct_id}-guardrail",
            description="Guardrail for AI Meeting Delegate restricted topics and sensitive data",
            blocked_input_messaging="I am not authorised to answer that. I will flag it for human review.",
            blocked_outputs_messaging="I cannot provide that response. I will flag it for human review.",
            topic_policy_config=bedrock.CfnGuardrail.TopicPolicyConfigProperty(
                topics_config=[
                    bedrock.CfnGuardrail.TopicConfigProperty(
                        name="LegalAdvice",
                        definition="Advice, interpretation, or recommendation about legal matters, legal obligations, legal disputes, contracts, or liability.",
                        examples=[
                            "Can we legally terminate this contract?",
                            "What legal position should we take?",
                            "Are we liable for this?",
                        ],
                        type="DENY",
                    ),
                    bedrock.CfnGuardrail.TopicConfigProperty(
                        name="MedicalAdvice",
                        definition="Medical, clinical, diagnosis, treatment, prescription, patient-specific or healthcare advice.",
                        examples=[
                            "What medication should this patient take?",
                            "Can you diagnose this symptom?",
                            "Should the patient stop taking this medicine?",
                        ],
                        type="DENY",
                    ),
                    bedrock.CfnGuardrail.TopicConfigProperty(
                        name="HRSalaryTermination",
                        definition="Human resources matters including salary, compensation, hiring, firing, termination, disciplinary action, performance management, or employment disputes.",
                        examples=[
                            "Should we fire this person?",
                            "Can you approve this salary increase?",
                            "What should we say in the disciplinary meeting?",
                        ],
                        type="DENY",
                    ),
                    bedrock.CfnGuardrail.TopicConfigProperty(
                        name="CommercialContracts",
                        definition="Commercial negotiation, contract terms, pricing commitments, purchasing commitments, budget approval, or binding business commitments.",
                        examples=[
                            "Can we approve this contract?",
                            "Can we commit to this price?",
                            "Can you approve this budget?",
                        ],
                        type="DENY",
                    ),
                ]
            ),
            sensitive_information_policy_config=bedrock.CfnGuardrail.SensitiveInformationPolicyConfigProperty(
                pii_entities_config=[
                    bedrock.CfnGuardrail.PiiEntityConfigProperty(
                        type="EMAIL",
                        action="ANONYMIZE",
                    ),
                    bedrock.CfnGuardrail.PiiEntityConfigProperty(
                        type="PHONE",
                        action="ANONYMIZE",
                    ),
                ],
                regexes_config=[
                    bedrock.CfnGuardrail.RegexConfigProperty(
                        name="AwsAccountId",
                        description="Detects 12-digit AWS account IDs",
                        pattern=r"\b\d{12}\b",
                        action="ANONYMIZE",
                    ),
                    bedrock.CfnGuardrail.RegexConfigProperty(
                        name="AwsAccessKey",
                        description="Detects AWS access key IDs",
                        pattern=r"\b(AKIA|ASIA)[A-Z0-9]{16}\b",
                        action="BLOCK",
                    ),
                ],
            ),
        )

        escalation_topic = sns.Topic(
            self,
            "EscalationTopic",
            topic_name=f"{construct_id}-escalations",
            display_name="AI Delegate escalation alerts",
        )

        common_env = {
            "PERSONA_TABLE": persona_table.table_name,
            "EXAMPLES_TABLE": examples_table.table_name,
            "VOICE_TABLE": voice_table.table_name,
            "SESSIONS_TABLE": sessions_table.table_name,
            "DOCS_BUCKET": docs_bucket.bucket_name,
            "ORCHESTRATOR_FUNCTION_NAME": f"{construct_id}-delegate-orchestrator",
            "AVATAR_STATIC_BUCKET": avatar_static_bucket.bucket_name,
            "AVATAR_STATIC_URL": f"http://{avatar_static_bucket.bucket_website_domain_name}",
            "AUDIT_BUCKET": audit_bucket.bucket_name,
            "AUDIO_BUCKET": audio_bucket.bucket_name,
            "MEETING_REALTIME_URL_PARAM": f"{ssm_parameter_prefix}/meeting/realtime-url",
            "ELEVENLABS_API_KEY_PARAM": elevenlabs_api_key_param,
            "ELEVENLABS_VOICE_ID_PARAM": elevenlabs_voice_id_param,
            "LIVEAVATAR_API_KEY_PARAM": f"{ssm_parameter_prefix}/liveavatar/api-key",
            "LIVEAVATAR_AVATAR_ID_PARAM": f"{ssm_parameter_prefix}/liveavatar/avatar-id",
            "RECALL_API_KEY_PARAM": recall_api_key_param,
            "RECALL_API_BASE_URL_PARAM": recall_api_base_url_param,
            "AVATAR_TOKEN_API_URL": f"https://ichk94c7o2.execute-api.us-east-1.amazonaws.com/prod/avatar/token",
            "HEYGEN_API_KEY_PARAM": heygen_api_key_param,
            "HEYGEN_AVATAR_ID_PARAM": heygen_avatar_id_param,
            "DID_API_KEY_PARAM": did_api_key_param,
            "BEDROCK_GUARDRAIL_ID": guardrail.attr_guardrail_id,
            "BEDROCK_GUARDRAIL_VERSION": "DRAFT",
            "ESCALATION_TOPIC_ARN": escalation_topic.topic_arn,
            "BEDROCK_MODEL_ID": "amazon.nova-lite-v1:0",
            "BEDROCK_MAX_TOKENS": "450",
            "BEDROCK_TEMPERATURE": "0.3",
            "BEDROCK_TOP_P": "0.9",
            "BEDROCK_READ_TIMEOUT_SECONDS": "20",
            "BEDROCK_CONNECT_TIMEOUT_SECONDS": "5",
            "MAX_PROMPT_TOKENS": "6000",
            "MAX_COST_PER_RESPONSE_USD": "0.05",
            "BEDROCK_INPUT_COST_PER_1K": "0.00025",
            "BEDROCK_OUTPUT_COST_PER_1K": "0.00125",
            "DEFAULT_VOICE_PROFILE_ID": "namdi-v1",
            "LOG_LEVEL": "INFO",
            "VECTOR_BACKEND": "s3_vectors",
            "S3_VECTOR_BUCKET_NAME": f"{construct_id.lower()}-vectors",
            "S3_VECTOR_INDEX_NAME": "ai-delegate-rag",
            "S3_VECTORS_BATCH_SIZE": "50",
            "RAG_INDEX_PREFIX": "rag-index",
            "RAG_TOP_K": "5",
            "RAG_CHUNK_MAX_CHARS": "1800",
            "EMBEDDING_MODEL_ID": "amazon.titan-embed-text-v2:0",
            "EMBEDDING_DIMENSIONS": "1024",
            "ELEVENLABS_MODEL_ID": "eleven_turbo_v2_5",
            "RETURN_PRESIGNED_AUDIO_URL": "true",
            "AUDIO_URL_TTL_SECONDS": "900",
            "DEFAULT_OWNER_NAME": "Namdi Onwuachu",
            "DEFAULT_AVATAR_ID": "",
        }

        orchestrator_fn = _lambda.Function(
            self,
            "DelegateOrchestratorFunction",
            function_name=f"{construct_id}-delegate-orchestrator",
            runtime=_lambda.Runtime.PYTHON_3_12,
            architecture=_lambda.Architecture.ARM_64,
            handler="orchestrator.lambda_handler.handler",
            code=_lambda.Code.from_asset(
                service_code_path,
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "pip install --upgrade pip && "
                        "pip install --platform manylinux2014_aarch64 "
                        "--implementation cp "
                        "--python-version 3.12 "
                        "--only-binary=:all: "
                        "-r requirements.txt "
                        "-t /asset-output && "
                        "cp -au . /asset-output && "
                        "echo '--- miniaudio files ---' && "
                        "find /asset-output -iname '*miniaudio*' -print && "
                        "SO_FILE=$(find /asset-output -name '_miniaudio*.so' | head -n 1) && "
                        "echo \"SO_FILE=$SO_FILE\" && "
                        "test -n \"$SO_FILE\" && "
                        "cp \"$SO_FILE\" /asset-output/_miniaudio.abi3.so && "
                        "ls -l /asset-output/_miniaudio.abi3.so"
                    ],
                ),
            ),
            timeout=Duration.seconds(90),
            memory_size=512,
            log_group=logs.LogGroup.from_log_group_name(
                self,
                "DelegateOrchestratorFunctionLogGroup",
                f"/aws/lambda/{construct_id}-delegate-orchestrator",
            ),
            tracing=_lambda.Tracing.ACTIVE,
            environment=common_env,
        )
   
         
        voice_fn = _lambda.Function(
            self,
            "VoiceFunction",
            function_name=f"{construct_id}-voice-service",
            runtime=_lambda.Runtime.PYTHON_3_12,
            architecture=_lambda.Architecture.ARM_64,
            handler="voice.lambda_handler.handler",
            code=_lambda.Code.from_asset(service_code_path),
            timeout=Duration.seconds(30),
            memory_size=512,
            log_group=logs.LogGroup.from_log_group_name(
                self, "VoiceFunctionLogGroup",
                f"/aws/lambda/{construct_id}-voice-service",
            ),
            tracing=_lambda.Tracing.ACTIVE,
            environment=common_env,
        )

        rag_ingestion_fn = _lambda.Function(
            self,
            "RagIngestionFunction",
            function_name=f"{construct_id}-rag-ingestion",
            runtime=_lambda.Runtime.PYTHON_3_12,
            architecture=_lambda.Architecture.ARM_64,
            handler="rag.ingestion_handler.handler",
            code=_lambda.Code.from_asset(service_code_path),
            timeout=Duration.seconds(60),
            memory_size=512,
            log_group=logs.LogGroup.from_log_group_name(
                self, "RagIngestionFunctionLogGroup",
                f"/aws/lambda/{construct_id}-rag-ingestion",
            ),
            tracing=_lambda.Tracing.ACTIVE,
            environment=common_env,
        )

        seed_fn = _lambda.Function(
            self,
            "SeedPersonaFunction",
            function_name=f"{construct_id}-seed-persona",
            runtime=_lambda.Runtime.PYTHON_3_12,
            architecture=_lambda.Architecture.ARM_64,
            handler="seed.persona_seed_handler.handler",
            code=_lambda.Code.from_asset(service_code_path),
            timeout=Duration.seconds(30),
            memory_size=512,
            log_group=logs.LogGroup.from_log_group_name(
                self, "SeedPersonaFunctionLogGroup",
                f"/aws/lambda/{construct_id}-seed-persona",
            ),
            tracing=_lambda.Tracing.ACTIVE,
            environment=common_env,
        )

        meeting_fn = _lambda.Function(
            self,
            "MeetingConnectorFunction",
            function_name=f"{construct_id}-meeting-connector",
            runtime=_lambda.Runtime.PYTHON_3_12,
            architecture=_lambda.Architecture.ARM_64,
            handler="meeting.lambda_handler.handler",
            code=_lambda.Code.from_asset(service_code_path),
            timeout=Duration.seconds(30),
            memory_size=512,
            log_group=logs.LogGroup.from_log_group_name(
                self, "MeetingConnectorFunctionLogGroup",
                f"/aws/lambda/{construct_id}-meeting-connector",
            ),
            tracing=_lambda.Tracing.ACTIVE,
            environment=common_env,
        )
        
        
        meeting_realtime_fn = _lambda.Function(
            self,
            "MeetingRealtimeFunction",
            function_name=f"{construct_id}-meeting-realtime",
            runtime=_lambda.Runtime.PYTHON_3_12,
            architecture=_lambda.Architecture.ARM_64,
            handler="meeting.realtime_handler.handler",
            code=_lambda.Code.from_asset(service_code_path),
            timeout=Duration.seconds(30),
            memory_size=512,
            log_group=logs.LogGroup.from_log_group_name(
                self, "MeetingRealtimeFunctionLogGroup",
                f"/aws/lambda/{construct_id}-meeting-realtime",
            ),
            tracing=_lambda.Tracing.ACTIVE,
            environment=common_env,
        )
        
        output_media_fn = _lambda.Function(
            self,
            "MeetingOutputMediaFunction",
            function_name=f"{construct_id}-meeting-output-media",
            runtime=_lambda.Runtime.PYTHON_3_12,
            architecture=_lambda.Architecture.ARM_64,
            handler="meeting.output_media_handler.handler",
            code=_lambda.Code.from_asset(service_code_path),
            timeout=Duration.seconds(30),
            memory_size=512,
            log_group=logs.LogGroup.from_log_group_name(
                self, "MeetingOutputMediaFunctionLogGroup",
                f"/aws/lambda/{construct_id}-meeting-output-media",
            ),
            tracing=_lambda.Tracing.ACTIVE,
            environment=common_env,
        )

        avatar_fn = _lambda.Function(
            self,
            "AvatarFunction",
            function_name=f"{construct_id}-avatar-service",
            runtime=_lambda.Runtime.PYTHON_3_12,
            architecture=_lambda.Architecture.ARM_64,
            handler="avatar.lambda_handler.handler",
            code=_lambda.Code.from_asset(
                service_code_path,
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ],
                ),
            ),
            timeout=Duration.seconds(30),
            memory_size=512,
            log_group=logs.LogGroup.from_log_group_name(
                self, "AvatarFunctionLogGroup",
                f"/aws/lambda/{construct_id}-avatar-service",
            ),
            tracing=_lambda.Tracing.ACTIVE,
            environment=common_env,
        )
        
        
        avatar_token_fn = _lambda.Function(
            self,
            "AvatarTokenFunction",
            function_name=f"{construct_id}-avatar-token",
            runtime=_lambda.Runtime.PYTHON_3_12,
            architecture=_lambda.Architecture.ARM_64,
            handler="avatar.token_handler.handler",
            code=_lambda.Code.from_asset(
                service_code_path,
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_12.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ],
                ),
            ),
            timeout=Duration.seconds(10),
            memory_size=256,
            log_group=logs.LogGroup.from_log_group_name(
                self, "AvatarTokenFunctionLogGroup",
                f"/aws/lambda/{construct_id}-avatar-token",
            ),
            tracing=_lambda.Tracing.ACTIVE,
            environment=common_env,
        )

        functions = [
            orchestrator_fn,
            voice_fn,
            rag_ingestion_fn,
            seed_fn,
            meeting_fn,
            meeting_realtime_fn,   # <-- add this
            output_media_fn,
            avatar_fn,
            avatar_token_fn,  # ← add this
        ]

        for fn in functions:
            persona_table.grant_read_write_data(fn)
            examples_table.grant_read_write_data(fn)
            voice_table.grant_read_write_data(fn)
            sessions_table.grant_read_write_data(fn)
            docs_bucket.grant_read_write(fn)
            audit_bucket.grant_read_write(fn)
            audio_bucket.grant_read_write(fn)
            escalation_topic.grant_publish(fn)

            fn.add_to_role_policy(
                iam.PolicyStatement(
                    actions=[
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream",
                        "bedrock:ApplyGuardrail",
                    ],
                    resources=["*"],
                )
            )

            fn.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["polly:SynthesizeSpeech"],
                    resources=["*"],
                )
            )

            fn.add_to_role_policy(
                iam.PolicyStatement(
                    actions=[
                        "s3vectors:CreateVectorBucket",
                        "s3vectors:GetVectorBucket",
                        "s3vectors:ListVectorBuckets",
                        "s3vectors:CreateIndex",
                        "s3vectors:GetIndex",
                        "s3vectors:ListIndexes",
                        "s3vectors:PutVectors",
                        "s3vectors:QueryVectors",
                        "s3vectors:GetVectors",
                        "s3vectors:ListVectors",
                        "s3vectors:DeleteVectors",
                    ],
                    resources=["*"],
                )
            )

            fn.add_to_role_policy(
                iam.PolicyStatement(
                    actions=[
                        "ssm:GetParameter",
                        "ssm:GetParameters",
                        "ssm:GetParametersByPath",
                    ],
                    resources=[
                        f"arn:aws:ssm:{self.region}:{self.account}:parameter/{construct_id}/*"
                    ],
                )
            )

            fn.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["kms:Decrypt"],
                    resources=["*"],
                    conditions={
                        "StringEquals": {
                            "kms:ViaService": f"ssm.{self.region}.amazonaws.com"
                        }
                    },
                )
            )

            fn.add_to_role_policy(
                iam.PolicyStatement(
                    actions=[
                        "xray:PutTraceSegments",
                        "xray:PutTelemetryRecords",
                    ],
                    resources=["*"],
                )
            )
            
        meeting_realtime_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                resources=[orchestrator_fn.function_arn],
            )
        )    

        api = apigw.RestApi(
            self,
            "AIDelegateApi",
            rest_api_name=f"{construct_id}-api",
            description="API for the AI Meeting Delegate MVP",
            deploy_options=apigw.StageOptions(
                stage_name="prod",
                tracing_enabled=True,
                logging_level=apigw.MethodLoggingLevel.INFO,
                data_trace_enabled=False,
                metrics_enabled=True,
            ),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["Content-Type", "Authorization", "X-Api-Key", "x-api-key"],
            ),
        )
        

        api_key = api.add_api_key(
            "AIDelegateApiKey",
            api_key_name=f"{construct_id}-api-key",
        )

        usage_plan = api.add_usage_plan(
            "AIDelegateUsagePlan",
            name=f"{construct_id}-usage-plan",
            throttle=apigw.ThrottleSettings(
                rate_limit=10,
                burst_limit=20,
            ),
            quota=apigw.QuotaSettings(
                limit=1000,
                period=apigw.Period.DAY,
            ),
        )

        usage_plan.add_api_key(api_key)
        usage_plan.add_api_stage(stage=api.deployment_stage)

        delegate = api.root.add_resource("delegate")
        respond = delegate.add_resource("respond")
        respond.add_method(
            "POST",
            apigw.LambdaIntegration(orchestrator_fn, proxy=True),
            api_key_required=True,
        )

        voice = api.root.add_resource("voice")
        speak = voice.add_resource("speak")
        speak.add_method(
            "POST",
            apigw.LambdaIntegration(voice_fn, proxy=True),
            api_key_required=True,
        )

        rag = api.root.add_resource("rag")
        ingest = rag.add_resource("ingest")
        ingest.add_method(
            "POST",
            apigw.LambdaIntegration(rag_ingestion_fn, proxy=True),
            api_key_required=True,
        )

        seed = api.root.add_resource("seed")
        seed_persona = seed.add_resource("persona")
        seed_persona.add_method(
            "POST",
            apigw.LambdaIntegration(seed_fn, proxy=True),
            api_key_required=True,
        )

        meeting = api.root.add_resource("meeting")
        join = meeting.add_resource("join")
        join.add_method(
            "POST",
            apigw.LambdaIntegration(meeting_fn, proxy=True),
            api_key_required=True,
        )
        
        realtime = meeting.add_resource("realtime")
        realtime.add_method(
            "POST",
            apigw.LambdaIntegration(meeting_realtime_fn, proxy=True),
            api_key_required=False,
        )
        
     
        
        output_media = meeting.add_resource("output-media")
        output_media_start = output_media.add_resource("start")
        output_media_start.add_method(
            "POST",
            apigw.LambdaIntegration(output_media_fn, proxy=True),
            api_key_required=True,
        )

        avatar = api.root.add_resource("avatar")
        speak_avatar = avatar.add_resource("speak")
        speak_avatar.add_method(
            "POST",
            apigw.LambdaIntegration(avatar_fn, proxy=True),
            api_key_required=True,
        )
        
        avatar_token = avatar.add_resource("token")
        avatar_token.add_method(
            "GET",
            apigw.LambdaIntegration(avatar_token_fn, proxy=True),
            api_key_required=False,
        )

        health = api.root.add_resource("health")
        health.add_method("GET", apigw.LambdaIntegration(orchestrator_fn, proxy=True))

        for fn in functions:
            cloudwatch.Alarm(
                self,
                f"{fn.node.id}ErrorsAlarm",
                metric=fn.metric_errors(period=Duration.minutes(5)),
                threshold=1,
                evaluation_periods=1,
                alarm_description=f"Errors detected in {fn.function_name}",
            )

            cloudwatch.Alarm(
                self,
                f"{fn.node.id}DurationAlarm",
                metric=fn.metric_duration(period=Duration.minutes(5)),
                threshold=25000,
                evaluation_periods=1,
                alarm_description=f"High duration detected in {fn.function_name}",
            )

        CfnOutput(self, "ApiUrl", value=api.url)
        CfnOutput(self, "DelegateRespondUrl", value=f"{api.url}delegate/respond")
        CfnOutput(self, "MeetingRealtimeUrl", value=f"{api.url}meeting/realtime")  # ✅
        CfnOutput(self, "VoiceSpeakUrl", value=f"{api.url}voice/speak")
        CfnOutput(self, "RagIngestUrl", value=f"{api.url}rag/ingest")
        CfnOutput(self, "SeedPersonaUrl", value=f"{api.url}seed/persona")
        CfnOutput(self, "MeetingJoinUrl", value=f"{api.url}meeting/join")
        CfnOutput(self, "AvatarSpeakUrl", value=f"{api.url}avatar/speak")
        CfnOutput(self, "DocsBucketName", value=docs_bucket.bucket_name)
        CfnOutput(self, "AuditBucketName", value=audit_bucket.bucket_name)
        CfnOutput(self, "AudioBucketName", value=audio_bucket.bucket_name)
        CfnOutput(self, "S3VectorBucketName", value=f"{construct_id.lower()}-vectors")
        CfnOutput(self, "S3VectorIndexName", value="ai-delegate-rag")
        CfnOutput(self, "PersonaTableName", value=persona_table.table_name)
        CfnOutput(self, "StyleExamplesTableName", value=examples_table.table_name)
        CfnOutput(self, "VoiceProfilesTableName", value=voice_table.table_name)
        CfnOutput(self, "SsmParameterPrefix", value=ssm_parameter_prefix)
        CfnOutput(self, "ElevenLabsApiKeyParameter", value=elevenlabs_api_key_param)
        CfnOutput(self, "ElevenLabsVoiceIdParameter", value=elevenlabs_voice_id_param)
        CfnOutput(self, "GuardrailId", value=guardrail.attr_guardrail_id)
        CfnOutput(self, "GuardrailVersion", value="DRAFT")
        CfnOutput(self, "AvatarStaticUrl", value=f"http://{avatar_static_bucket.bucket_website_domain_name}")
        CfnOutput(self, "AvatarStaticBucketName", value=avatar_static_bucket.bucket_name)
        CfnOutput(self, "AvatarTokenUrl", value=f"{api.url}avatar/token")