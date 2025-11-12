"""Enhanced version with detailed logging to track LLM API errors.

Changes:
- Added comprehensive logging for all LLM calls
- Logging of request/response details including headers, models, and endpoints
- Request/response interceptor for litellm
- Tracking of 502 errors with full context
- Fixed rich library recursion error
- Added retry logic for 502 errors
- Fixed timedelta formatting in logging callbacks (use .total_seconds())
"""

import os
import logging
import time
from datetime import datetime
from crewai.agent import Agent
from crewai.crew import Crew, Process
from crewai.llm import LLM
from crewai.task import Task
from crewai_tools import SerperDevTool, WebsiteSearchTool
import litellm

litellm.drop_params = True
litellm.additional_drop_params = ["stop"]

# Setup detailed logging - avoid rich library conflicts
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(f'litellm_debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ],
    force=True
)
logger = logging.getLogger(__name__)

# Disable rich library for crewai to avoid recursion issues
os.environ['CREWAI_DISABLE_TELEMETRY'] = 'true'

litellm.set_verbose = True
litellm.drop_params = True

DEFAULT_MODEL = os.environ.get("LITELLM_MODEL", "gemini-2.5-flash")
PLANNING_MODEL = os.environ.get("LITELLM_PLANNING_MODEL", "gemini-2.5-pro")

# Track API call statistics
api_stats = {
    'total_calls': 0,
    'successful_calls': 0,
    'failed_calls': 0,
    'errors_by_type': {}
}

def log_success_callback(kwargs, completion_response, start_time, end_time):
    """Track successful LLM API calls."""
    api_stats['total_calls'] += 1
    api_stats['successful_calls'] += 1
    
    logger.info(f"✅ LLM CALL SUCCESS #{api_stats['total_calls']}")
    logger.info(f"  Model: {kwargs.get('model')}")
    logger.info(f"  Duration: {(end_time - start_time).total_seconds():.2f}s")
    logger.info(f"  Messages count: {len(kwargs.get('messages', []))}")
    if hasattr(completion_response, 'usage'):
        logger.info(f"  Prompt tokens: {completion_response.usage.prompt_tokens}")
        logger.info(f"  Completion tokens: {completion_response.usage.completion_tokens}")
        logger.info(f"  Total tokens: {completion_response.usage.total_tokens}")

def log_failure_callback(kwargs, completion_response, start_time, end_time):
    """Track failed LLM API calls."""
    api_stats['total_calls'] += 1
    api_stats['failed_calls'] += 1
    
    error_type = type(completion_response).__name__ if completion_response else "Unknown"
    api_stats['errors_by_type'][error_type] = api_stats['errors_by_type'].get(error_type, 0) + 1
    
    logger.error(f"❌ LLM CALL FAILED #{api_stats['total_calls']}")
    logger.error(f"  Model: {kwargs.get('model')}")
    logger.error(f"  Base URL: {kwargs.get('base_url', 'default')}")
    logger.error(f"  Duration: {(end_time - start_time).total_seconds():.2f}s")
    logger.error(f"  Messages count: {len(kwargs.get('messages', []))}")
    logger.error(f"  API key present: {bool(kwargs.get('api_key'))}")
    logger.error(f"  API key prefix: {kwargs.get('api_key', '')[:10]}...")
    logger.error(f"  Headers: {kwargs.get('extra_headers', {})}")
    logger.error(f"  Error type: {error_type}")
    logger.error(f"  Error response: {str(completion_response)[:500]}")
    
    # Detect 502 errors
    if "502" in str(completion_response):
        logger.error("🔴 502 SERVER ERROR DETECTED")
        logger.error("  Backend LiteLLM service is experiencing issues")
        logger.error(f"  This is error #{api_stats['errors_by_type'].get(error_type, 0)} of this type")

litellm.success_callback = [log_success_callback]
litellm.failure_callback = [log_failure_callback]

# Log environment setup
token = os.environ.get("IVCAP_TOKEN", "")
logger.info("=" * 80)
logger.info("🔧 ENVIRONMENT SETUP")
logger.info("=" * 80)
logger.info(f"  IVCAP_TOKEN present: {bool(token)}")
logger.info(f"  IVCAP_TOKEN length: {len(token)}")
logger.info(f"  IVCAP_TOKEN prefix: {token[:20]}...")
logger.info(f"  litellm.drop_params: {litellm.drop_params}")
logger.info(f"  litellm.set_verbose: {litellm.set_verbose}")

# Create LLMs with detailed logging and retry logic
logger.info("=" * 80)
logger.info("📝 CREATING LLM INSTANCES")
logger.info("=" * 80)

def create_llm_with_retry(model_name, max_retries=3, delay=2):
    """Create LLM with retry logic for transient errors."""
    base_url = (
        os.environ.get("OPENAI_API_BASE")
        or os.environ.get("OPENAI_BASE_URL")
        or os.environ.get("BASE_URL")
    )

    for attempt in range(max_retries):
        try:
            logger.info(f"  Attempt {attempt + 1}/{max_retries}: Creating {model_name} LLM...")
            llm_instance = LLM(
                model=model_name,
                api_key=token,
                default_headers={"Authorization": f"Bearer {token}"},
                base_url=base_url
            )
            logger.info(f"  ✅ {model_name} LLM created successfully")
            return llm_instance
        except Exception as e:
            logger.error(f"  ❌ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                logger.info(f"  ⏳ Waiting {delay}s before retry...")
                time.sleep(delay)
            else:
                logger.error(f"  ❌ All {max_retries} attempts failed for {model_name}")
                raise

llm = create_llm_with_retry("gemini-2.5-flash")
planning_llm = create_llm_with_retry("gemini-2.5-flash")

# Test initial LLM call
logger.info("=" * 80)
logger.info("🧪 TESTING INITIAL LLM CALL")
logger.info("=" * 80)

# Test primary LLM (llm)
try:
    logger.info("  Calling LLM (llm) with test message...")
    response = llm.call(messages=[{"role": "user", "content": "Hello, how are you?"}])
    logger.info(f"  ✅ Test call (llm) successful")
    #logger.info(f"  Response preview (llm): {str(response)[:200]}...")
    print("[llm response]\n", response)
except Exception as e:
    logger.error(f"  ❌ Test call (llm) failed: {e}", exc_info=True)
    raise

# Test planning LLM (planning_llm)
try:
    logger.info("  Calling planning LLM (planning_llm) with test message...")
    planning_response = planning_llm.call(messages=[{"role": "user", "content": "Hello, how are you? (planning)"}])
    logger.info(f"  ✅ Test call (planning_llm) successful")
    #logger.info(f"  Response preview (planning_llm): {str(planning_response)[:200]}...")
    print("[planning_llm response]\n", planning_response)
except Exception as e:
    logger.error(f"  ❌ Test call (planning_llm) failed: {e}", exc_info=True)
    raise

# Your original inputs
inputs = {
    "topic": "LiteLLM vs openrouter",
    "keywords": "routers for llms",
    "additional_info": "",
}
logger.info("=" * 80)
logger.info(f"📥 INPUTS: {inputs}")
logger.info("=" * 80)

# Create agents
logger.info("=" * 80)
logger.info("👥 CREATING AGENTS")
logger.info("=" * 80)

os.environ["OPENAI_API_KEY"] = token
os.environ["OPENAI_API_BASE"] = "https://mindweaver.develop.ivcap.io/litellm/"

website_search_tool = WebsiteSearchTool()
serper_dev_tool = SerperDevTool(enable_cache=True)
researcher = Agent(
    name="researcher",
    role="Academic Research Specialist",
    goal=(
        "Surface high-quality, well-cited findings for {topic} using"
        " strategic search patterns around {keywords} while respecting"
        " the requester context {additional_info}."
    ),
    backstory=(
        "Expert academic researcher known for uncovering difficult-to-find"
        " primary sources, validating claims across multiple outlets, and"
        " documenting citations meticulously."
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False,
    memory=False,
    tools=[serper_dev_tool, website_search_tool],
)
logger.info("  ✅ Researcher agent created")

writer = Agent(
    name="writer",
    role="Academic Publication Specialist",
    goal=(
        "Transform vetted research insights about {topic} into a coherent"
        " narrative that highlights implications, controversies, and"
        " recommended next steps."
    ),
    backstory=(
        "Seasoned analyst and writer who produces publication-ready"
        " reports, balancing depth with clarity and emphasizing proper"
        " attribution."
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False,
    memory=False,
)
logger.info("  ✅ Writer agent created")

# Create tasks
logger.info("=" * 80)
logger.info("📋 CREATING TASKS")
logger.info("=" * 80)

research_task = Task(
    name="Research Topic",
    description=(
        "Conduct focused desk research on '{topic}' leveraging Serper"
        " for web discovery. Gather 8-12 credible sources spanning academic, industry,"
        " news, and government outlets. For each source capture title,"
        " publication date, 1-2 key findings, and why it matters."
        " Highlight conflicting viewpoints, note methodological"
        " strengths or weaknesses, and tie findings back to"
        " '{additional_info}' when relevant."
    ),
    expected_output=(
        "Markdown with sections: 1) Source Table (ID, Title, Outlet,"
        " Date, Key Insight, Credibility Notes), 2) Thematic Findings"
        " (at least three themes with supporting source IDs), 3)"
        " Open Questions / Gaps, 4) Quick reference list of source URLs."
    ),
    agent=researcher,
)
logger.info("  ✅ Research task created")

summary_task = Task(
    name="Draft Summary",
    description=(
        "Review the research dossier and craft a structured executive"
        " briefing (4-6 paragraphs) on '{topic}'. Emphasize the most"
        " consequential themes, synthesize differing perspectives,"
        " and recommend actionable next steps. Quote statistics or"
        " notable statements with inline source IDs (e.g., [S3])."
        " Close with a short risk/opportunity assessment tied to"
        " '{additional_info}'."
    ),
    expected_output=(
        "# Executive Briefing on {topic}\n\n## Key Insights\n- Bullet list"
        " referencing source IDs\n\n## Strategic Analysis\n[3-4 paragraphs]"
        "\n\n## Recommended Actions\n- Action 1\n- Action 2\n\n## Risks &"
        " Watchpoints\n- Risk 1\n- Risk 2"
    ),
    agent=writer,
    context=[research_task],
)
logger.info("  ✅ Summary task created")

# Create crew
logger.info("=" * 80)
logger.info("🚀 CREATING CREW")
logger.info("=" * 80)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, summary_task],
    process=Process.sequential,
    verbose=True,
    planning_llm=planning_llm,
    planning=False,
    embedder = {
        "provider": "openai",
        "config": {
            "model": "text-embedding-3-small",
            "api_key": os.environ.get("IVCAP_TOKEN"),
            "api_base": "https://mindweaver.develop.ivcap.io/litellm",
            "default_headers": {"Authorization": f"Bearer {token}"}
        }
    }
)
logger.info("  ✅ Crew created successfully")


# Execute
logger.info("=" * 80)
logger.info("🎬 STARTING CREW EXECUTION")
logger.info("=" * 80)

try:
    result = crew.kickoff(inputs=inputs)
    
    logger.info("=" * 80)
    logger.info("✅ CREW EXECUTION COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)
    logger.info(f"📊 API CALL STATISTICS:")
    logger.info(f"  Total calls: {api_stats['total_calls']}")
    logger.info(f"  Successful: {api_stats['successful_calls']}")
    logger.info(f"  Failed: {api_stats['failed_calls']}")
    logger.info(f"  Success rate: {api_stats['successful_calls']/api_stats['total_calls']*100:.1f}%" if api_stats['total_calls'] > 0 else "  Success rate: N/A")
    logger.info(f"  Errors by type: {api_stats['errors_by_type']}")
    logger.info("=" * 80)
    logger.info(f"Result preview:\n{str(result)[:500]}...")
    
    print("\nResult:")
    print(result)
    
except Exception as e:
    logger.error("=" * 80)
    logger.error("❌ CREW EXECUTION FAILED")
    logger.error("=" * 80)
    logger.error(f"Error type: {type(e).__name__}")
    logger.error(f"Error message: {str(e)}")
    logger.error("=" * 80)
    logger.error(f"📊 API CALL STATISTICS AT FAILURE:")
    logger.error(f"  Total calls: {api_stats['total_calls']}")
    logger.error(f"  Successful: {api_stats['successful_calls']}")
    logger.error(f"  Failed: {api_stats['failed_calls']}")
    logger.error(f"  Errors by type: {api_stats['errors_by_type']}")
    logger.error("=" * 80)
    
    # 502 error analysis
    if "502" in str(e):
        logger.error("🔍 502 ERROR ANALYSIS:")
        logger.error("  - Backend LiteLLM service at mindweaver.develop.ivcap.io is returning 502")
        logger.error("  - This indicates the backend gateway/proxy cannot reach the model service")
        logger.error(
            "  - Models: %s (main tasks) + %s (planning)",
            DEFAULT_MODEL,
            PLANNING_MODEL,
        )
        logger.error("  - The service may be overloaded, restarting, or misconfigured")
        logger.error("  - RECOMMENDATION: Contact service administrator or try again later")
    
    # Recursion error analysis
    if "recursion" in str(e).lower() or "_FileProxy" in str(e):
        logger.error("🔍 RECURSION ERROR ANALYSIS:")
        logger.error("  - Rich library file proxy recursion detected")
        logger.error("  - This is typically caused by crewai's telemetry/logging")
        logger.error("  - CREWAI_DISABLE_TELEMETRY was set but may not be working")
    
    logger.error("Full traceback:", exc_info=True)
    raise