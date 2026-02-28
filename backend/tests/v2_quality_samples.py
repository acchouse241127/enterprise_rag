# V2.0 Quality Test Samples - 20 annotated samples

# Part 1: Hallucination Detection Samples (10 samples)
HALLUCINATION_SAMPLES = [
    {
        "id": "H001",
        "context": "公司成立于2018年，总部位于北京。主营业务为企业级RAG系统开发，提供智能问答、知识库管理等服务。公司目前有50名员工，已服务超过100家企业客户。",
        "answer": "该公司成立于2018年，总部在北京，主要做企业级RAG系统开发。",
        "expected_hallucination": False,
        "expected_faithfulness_min": 0.8,
    },
    {
        "id": "H002",
        "context": "合同违约金一般为合同总金额的10%-30%。如果违约方能够证明实际损失较小，法院可能会适当降低违约金数额。",
        "answer": "合同违约金通常是合同总金额的10%-30%，但具体数额可以根据实际损失协商调整，最高不超过50%。",
        "expected_hallucination": True,
        "expected_faithfulness_min": 0.5,
    },
    {
        "id": "H003",
        "context": "产品保修期为一年，从购买日期开始计算。在保修期内，如果产品出现非人为损坏的故障，用户可以免费维修或更换。",
        "answer": "产品保修期为三年，并且提供终身维护服务。用户还可以享受每年一次的免费上门检修。",
        "expected_hallucination": True,
        "expected_faithfulness_min": 0.1,
    },
    {
        "id": "H004",
        "context": "系统支持的最大文件上传大小为200MB。支持的文件格式包括PDF、Word、Excel、PowerPoint等常见办公文档格式。",
        "answer": "用户可以上传最大200MB的文件，系统兼容PDF、Word、Excel和PPT等格式。",
        "expected_hallucination": False,
        "expected_faithfulness_min": 0.9,
    },
    {
        "id": "H005",
        "context": "系统采用BGE-M3作为向量嵌入模型，使用ChromaDB作为向量数据库。检索时结合BM25和向量检索，使用RRF算法进行融合。",
        "answer": "系统使用BGE-M3模型和ChromaDB数据库，采用BM25与向量检索的混合方案，并通过RRF算法融合结果。系统还支持多语言自动翻译功能。",
        "expected_hallucination": True,
        "expected_faithfulness_min": 0.6,
    },
    {
        "id": "H006",
        "context": "2023年公司营收达到5000万元，同比增长25%。预计2024年营收将达到6500万元。",
        "answer": "公司2023年营收5000万元，增长25%，预计2024年营收8000万元。",
        "expected_hallucination": True,
        "expected_faithfulness_min": 0.5,
    },
    {
        "id": "H007",
        "context": "项目A预算100万元，已使用60万元。项目B预算80万元，已使用50万元。项目C预算120万元，已使用40万元。",
        "answer": "三个项目的总预算是300万元，目前已使用150万元，剩余预算150万元。",
        "expected_hallucination": False,
        "expected_faithfulness_min": 0.9,
    },
    {
        "id": "H008",
        "context": "张三是技术总监，负责研发团队管理。李四是产品经理，负责产品规划和需求分析。王五是销售总监，负责市场拓展和客户关系维护。",
        "answer": "张三负责产品规划，李四负责研发团队，王五负责市场拓展。",
        "expected_hallucination": True,
        "expected_faithfulness_min": 0.3,
    },
    {
        "id": "H009",
        "context": "系统于2024年1月完成V1.0版本开发，2024年6月发布V1.5版本。V2.0版本计划于2025年第一季度发布。",
        "answer": "V1.0于2024年1月发布，V1.5于2024年12月发布，V2.0于2024年第四季度发布。",
        "expected_hallucination": True,
        "expected_faithfulness_min": 0.4,
    },
    {
        "id": "H010",
        "context": "本系统提供以下核心功能：1. 知识库管理：支持文档上传、分类、版本控制 2. 智能问答：基于RAG技术的问答系统 3. 用户管理：支持多角色权限控制 4. 数据分析：提供检索日志和用户行为分析",
        "answer": "系统主要包括知识库管理、智能问答、用户管理和数据分析四大功能模块。",
        "expected_hallucination": False,
        "expected_faithfulness_min": 0.9,
    },
]

# Part 2: Citation Verification Samples (5 samples)
CITATION_SAMPLES = [
    {
        "id": "C001",
        "contexts": [
            {"id": 1, "content": "系统支持的最大文件大小为200MB。"},
            {"id": 2, "content": "支持的文件格式包括PDF、Word、Excel。"},
        ],
        "answer": "系统支持最大200MB的文件[ID:1]，兼容PDF、Word等格式[ID:2]。",
        "expected_accuracy_min": 0.9,
    },
    {
        "id": "C002",
        "contexts": [
            {"id": 1, "content": "公司成立于2018年。"},
            {"id": 2, "content": "总部位于北京。"},
        ],
        "answer": "公司成立于2018年[ID:1]，有100名员工[ID:2]。",
        "expected_accuracy_min": 0.4,
    },
    {
        "id": "C003",
        "contexts": [{"id": 1, "content": "产品价格1000元。"}],
        "answer": "产品售价1000元[ID:1]，支持分期付款[ID:5]。",
        "expected_accuracy_min": 0.3,
    },
    {
        "id": "C004",
        "contexts": [{"id": 1, "content": "系统功能包括知识库管理。"}],
        "answer": "这是一个功能强大的系统。",
        "expected_accuracy_min": 0.8,
    },
    {
        "id": "C005",
        "contexts": [
            {"id": 1, "content": "用户可以使用账号密码登录。"},
            {"id": 2, "content": "系统支持双因素认证。"},
            {"id": 3, "content": "登录失败会锁定账号30分钟。"},
        ],
        "answer": "用户可以账号密码登录[ID:1]，支持双因素认证[ID:2]，登录失败会永久封号[ID:3]。",
        "expected_accuracy_min": 0.5,
    },
]

# Part 3: Refusal Accuracy Samples (5 samples)
REFUSAL_SAMPLES = [
    {"id": "R001", "context": "", "question": "请介绍一下公司的股票代码和上市情况。", "should_refuse": True},
    {"id": "R002", "context": "系统支持PDF、Word、Excel等文件格式上传。", "question": "请告诉我如何做红烧肉。", "should_refuse": True},
    {"id": "R003", "context": "", "question": "明天的天气怎么样？", "should_refuse": True},
    {"id": "R004", "context": "系统支持的知识库类型包括：通用知识库、FAQ知识库、文档知识库。", "question": "系统支持哪些类型的知识库？", "should_refuse": False},
    {"id": "R005", "context": "公司成立于2018年。", "question": "请详细介绍公司的发展历程、业务范围和未来规划。", "should_refuse": False},
]
