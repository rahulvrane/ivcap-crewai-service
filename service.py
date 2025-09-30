# Do this before importing other libraries, in case they use posthog during their initialisation
from no_posthog import no_posthog
no_posthog()

import datetime
import os
# Remove when we use our own telemetry
os.environ["OTEL_SDK_DISABLED"] = "true"
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional
import argparse
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field
import utils # noqa  # imported for side effects (runs module-level code)

# According to https://docs.crewai.com/en/telemetry#telemetry this will disable crewAI's telemetry.
# But this appears not to work, either in crewai 0.121.1 or 0.134.0.
# We still see requests going out to posthog.com.
# Perhaps some other library also uses posthog?
# Instead we monkey-patch it using no_posthog (above), which seems to work.
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
from crewai import LLM
from crewai.types.usage_metrics import UsageMetrics
from crewai_tools import DirectoryReadTool, FileReadTool, WebsiteSearchTool

from ivcap_service import getLogger, Service, JobContext
from ivcap_ai_tool import start_tool_server, ToolOptions, ivcap_ai_tool, logging_init

from service_types import BuiltinWrapper, CrewA, TaskResponse, add_supported_tools
from llm_factory import get_llm_factory

# Load environment variables from the .env file
load_dotenv()

# LiteLLM Proxy Configuration
LITELLM_PROXY_URL = os.getenv("LITELLM_PROXY_URL")
LITELLM_DEFAULT_MODEL = os.getenv("LITELLM_DEFAULT_MODEL", "gpt-4o")
LITELLM_FALLBACK_MODEL = os.getenv("LITELLM_FALLBACK_MODEL", "gpt-3.5-turbo")

logging_init("./logging.json")
logger = getLogger("app")

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

service = Service(
    name="CrewAI Agent Runner",
    version=os.environ.get("VERSION", "???"),
    contact={
        "name": "Mary Doe",
        "email": "mary.doe@acme.au",
    },
)

class CrewRequest(BaseModel):
    jschema: str = Field("urn:sd-core:schema.crewai.request.1", alias="$schema")
    name: Optional[str] = Field(None, description="Name of the crew conversation.")
    inputs: Optional[Dict[str, str]] = Field(None, description="List of placeholders to be filled into the Crew definition.")
    crew_ref: Optional[str] = Field(None, description="Reference to a Crew definition.", alias="crew-ref")
    crew: Optional[CrewA] = Field(None, description="Crew definition to be executed.")

    # Optional artifact support - backward compatible
    artifact_urns: Optional[List[str]] = Field(None, description="Optional IVCAP artifact URNs to download as input.", alias="artifact-urns")

    model_config = ConfigDict(populate_by_name=True) # Allow using `crew_ref`

class CrewResponse(BaseModel):
    jschema: str = Field("urn:sd:schema:icrew.answer.2", alias="$schema")
    answer: str
    crew_name: str
    place_holders: List[str] = Field([], description="list of placeholders inserted into crew's template")
    task_responses: List[TaskResponse]


    created_at: str = Field(description="time this answer was created ISO")
    process_time_sec: float
    run_time_sec: float
    token_usage: UsageMetrics = Field(description="tokens used while executing this crew")


add_supported_tools({
    # "urn:sd-core:crewai.builtin.serperDevTool": lambda _, ctxt: SerperDevTool(config=ctxt.vectordb_config),

    # DirectoryReadTool - only works if inputs_dir exists
    "urn:sd-core:crewai.builtin.directoryReadTool":
        lambda _, ctxt: DirectoryReadTool(directory=ctxt.inputs_dir) if ctxt.inputs_dir else None,

    # FileReadTool - only works if inputs_dir exists
    "urn:sd-core:crewai.builtin.fileReadTool":
        lambda _, ctxt: FileReadTool(file_path=ctxt.inputs_dir) if ctxt.inputs_dir else None,

    # Keep WebsiteSearchTool as is
    "urn:sd-core:crewai.builtin.websiteSearchTool":
        lambda _, ctxt: BuiltinWrapper(WebsiteSearchTool(config=ctxt.vectordb_config)),
})

def get_auth_token(jobCtxt: JobContext) -> Optional[str]:
    """Extract JWT token from JobContext if available."""
    # The @ivcap_ai_tool decorator provides the token in JobContext
    # Check for auth_token or headers
    if hasattr(jobCtxt, 'auth_token'):
        return jobCtxt.auth_token
    elif hasattr(jobCtxt, 'headers'):
        auth_header = jobCtxt.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]  # Remove 'Bearer ' prefix
    # Try to get from request context if available
    elif hasattr(jobCtxt, 'request') and hasattr(jobCtxt.request, 'headers'):
        auth_header = jobCtxt.request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
    return None

def download_artifacts(job_id: str, artifact_urns: List[str], ivcap_client) -> Optional[str]:
    """Download artifacts if provided. Returns inputs directory path or None."""
    if not artifact_urns:
        return None

    inputs_dir = Path(f"runs/{job_id}/inputs")
    inputs_dir.mkdir(parents=True, exist_ok=True)

    try:
        for urn in artifact_urns:
            try:
                logger.info(f"Downloading artifact: {urn}")
                artifact = ivcap_client.get_artifact(urn)

                # Save with sanitized filename
                safe_name = os.path.basename(artifact.name)
                file_path = inputs_dir / safe_name

                with open(file_path, 'wb') as f:
                    content = artifact.as_file()
                    f.write(content.read() if hasattr(content, 'read') else content)

                logger.info(f"Downloaded {urn} to {file_path}")

            except Exception as e:
                logger.warning(f"Failed to download {urn}: {e}")
                # Continue with other artifacts

        return str(inputs_dir)

    except Exception as e:
        logger.error(f"Artifact download failed: {e}")
        if inputs_dir.exists():
            shutil.rmtree(inputs_dir)
        return None

def cleanup_artifacts(job_id: str):
    """Clean up downloaded artifacts if they exist."""
    inputs_dir = Path(f"runs/{job_id}/inputs")
    if inputs_dir.exists():
        try:
            shutil.rmtree(inputs_dir)
            logger.info(f"Cleaned up artifacts for job {job_id}")
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")

@ivcap_ai_tool("/", opts=ToolOptions(tags=["CrewAI Runner"]))
async def crew_runner(req: CrewRequest, jobCtxt: JobContext) -> CrewResponse:
    """Provides the ability to request a crew of agents to execute
    their plan on a CrewAI runtime."""

    inputs_dir = None

    try:
        # Extract JWT token from JobContext
        jwt_token = get_auth_token(jobCtxt)
        if jwt_token:
            logger.info("JWT token detected, will use for LiteLLM proxy authentication")
        else:
            logger.warning("No JWT token found, will attempt fallback authentication")

        # Download artifacts if provided (optional)
        if req.artifact_urns:
            inputs_dir = download_artifacts(jobCtxt.job_id, req.artifact_urns, jobCtxt.ivcap)
            if inputs_dir:
                # Add to inputs so crews can reference it
                if req.inputs is None:
                    req.inputs = {}
                req.inputs['inputs_directory'] = inputs_dir
                logger.info(f"Artifacts available at: {inputs_dir}")

        # Existing code - no changes
        if req.crew_ref:
            crewDef = CrewA.from_aspect(req.crew_ref)
        else:
            crewDef = req.crew
        if not crewDef:
            raise ValueError("No crew definition provided.")
        if not crewDef.name:
            crewDef.name = req.name

        # UPDATED: Create LLM with JWT token support
        llm_factory = get_llm_factory()

        # Allow request to override model if specified
        model_override = req.inputs.get("llm_model") if req.inputs else None

        llm = llm_factory.create_llm(
            jwt_token=jwt_token,
            model=model_override,
            temperature=0.7,  # Default temperature, can be configured
            max_tokens=4000   # Default max tokens, can be configured
        )

        # Create crew with configured LLM
        crew = crewDef.as_crew(
            llm=llm,
            memory=False,
            verbose=False,
            planning=True,
            job_id=jobCtxt.job_id,
            inputs_dir=inputs_dir,  # Optional parameter
            jwt_token=jwt_token  # Pass JWT for per-agent LLM configuration
        )

        logger.info(f"processing crew '{req.name}' for '{jobCtxt.job_id}'")
        # (crew, ctxt, template) = crew_from_file(crew_fd, inputs, log_fd)
        start_time = (time.process_time(), time.time())
        cres = crew.kickoff(req.inputs)
        # with redirect_stdout(log_fd):
        #     answer = crew.kickoff(inputs)
        end_time = (time.process_time(), time.time())

        # Existing response - no changes
        resp = CrewResponse(
            answer=cres.raw,
            crew_name=req.name,
            place_holders=[],
            task_responses=[TaskResponse.from_task_output(r) for r in cres.tasks_output],

            created_at=datetime.datetime.now().astimezone().replace(microsecond=0).isoformat(),
            process_time_sec=end_time[0] - start_time[0],
            run_time_sec=end_time[1] - start_time[1],

            token_usage=cres.token_usage
        )
        return resp

    finally:
        # Cleanup if artifacts were downloaded
        if inputs_dir:
            cleanup_artifacts(jobCtxt.job_id)

def service_args(parser: argparse.ArgumentParser) -> argparse.Namespace:
    parser.add_argument('--litellm-proxy', type=str,
                       default=os.getenv('LITELLM_PROXY_URL'),
                       help='LiteLLM Proxy URL (overrides LITELLM_PROXY_URL env var)')
    parser.add_argument('--default-model', type=str,
                       default=os.getenv('LITELLM_DEFAULT_MODEL', 'gpt-4o'),
                       help='Default LLM model to use')
    #parser.add_argument('--tmp-dir', type=str, help=f"The 'scratch' directory to use for temporary files [{tmp_dir_prefix}]")
    #parser.add_argument('--testing', action="store_true", help='Add tools for testing (testing.py)')
    args = parser.parse_args()

    # Update environment variables if CLI args provided
    if args.litellm_proxy:
        os.environ["LITELLM_PROXY_URL"] = args.litellm_proxy
        logger.info(f"Using LiteLLM proxy: {args.litellm_proxy}")

    if args.default_model:
        os.environ["LITELLM_DEFAULT_MODEL"] = args.default_model
        logger.info(f"Using default model: {args.default_model}")

    logger.info(f"OTEL_SDK_DISABLED={os.getenv('OTEL_SDK_DISABLED')}")
    return args

if __name__ == "__main__":
    start_tool_server(service)
